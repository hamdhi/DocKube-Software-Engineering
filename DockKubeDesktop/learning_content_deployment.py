r"""Chapter 25 - Deployment strategies: big bang to canary, and how to roll back."""

CHAPTER = r"""<h2>1. What A Deployment Strategy Actually Is</h2>

<p>Deployment strategy is the answer to one question: <em>how do new code
users get from the old version to the new one without the business stopping?</em>
The code is already tested; this is about the minutes or hours when both
versions exist at once.</p>

<p><strong>Memory trick:</strong> every strategy is a trade between three
things - <strong>speed</strong> (how fast the new code arrives),
<strong>risk</strong> (how many users are hit if it is broken) and
<strong>cost</strong> (how much extra infrastructure runs during the switch).</p>

<h2>2. The Strategies Compared</h2>

<table>
<tr><th>Strategy</th><th>How it works</th><th>Downtime</th><th>Risk blast radius</th><th>Rollback</th><th>Best when</th></tr>
<tr><td>Big bang</td><td>Stop old, deploy new everywhere at once</td><td>Yes, usually</td><td>100% of users, instantly</td><td>Re-deploy the old version (slow)</td><td>Demos, internal tools, first deploy ever</td></tr>
<tr><td>Rolling</td><td>Replace a few instances at a time until all are new</td><td>No</td><td>The batch size, e.g. 25%</td><td>Easy - stop the rollout, roll back batches</td><td>Stateless services, Kubernetes, VM fleets</td></tr>
<tr><td>Blue-green</td><td>Two identical environments; traffic switches from blue (old) to green (new) in one step</td><td>No</td><td>100% at the switch, but instant and reversible</td><td>Flip the switch back - seconds</td><td>Releases that need a hard cut-over, schema checks</td></tr>
<tr><td>Canary</td><td>Send 1% -&gt; 5% -&gt; 25% -&gt; 100% of traffic to the new version, watching metrics between each step</td><td>No</td><td>Starts at 1% of users</td><td>Stop early, most users never noticed</td><td>Anything customer-facing, high risk</td></tr>
<tr><td>Phased (staged)</td><td>Roll out by group: internal staff -&gt; one region -&gt; one customer tier -&gt; everyone</td><td>No</td><td>One group at a time</td><td>Freeze the phase, fix, resume</td><td>Mobile apps, multi-region, enterprise cohorts</td></tr>
<tr><td>Shadow</td><td>Send real traffic to both versions; only the old one answers users, compare outputs</td><td>No</td><td>Zero (new version answers nobody)</td><td>Simply delete it</td><td>Validating a rewrite or a risky change</td></tr>
<tr><td>Feature flag</td><td>New code ships dark; a runtime switch turns behaviour on per user/segment</td><td>No</td><td>Whatever the flag targets</td><td>Turn the flag off - no redeploy</td><td>Continuous delivery, dark launches, experiments</td></tr>
</table>

<h2>3. The Topologies, Drawn</h2>

<pre>ROLLING              BLUE-GREEN
                     load balancer
old old old new         |            switch!
 [batch 1][2][3]       v
                     [ BLUE (v1) ]  ----+----&gt; users (today)
replace 1..n until      |
all are new           [ GREEN (v2) ] ---+----&gt; users (after switch)

CANARY                       PHASED / COHORT
        traffic
         |                    Phase 1: staff
    +----+----+               Phase 2: region EU
    v    v    v               Phase 3: all customers
  [v1] [v1] [v2]  &lt;- start 1% on v2
              |
      1% -&gt; 5% -&gt; 25% -&gt; 100% on v2, watching metrics
</pre>

<h2>4. A Canary Step By Step</h2>

<pre># 1. Deploy the new version alongside the old (nobody routed to it yet)
kubectl apply -f app-v2.yaml          # or: docker compose up -d app-v2

# 2. Move 1% of traffic to it
kubectl patch virtualservice app \
  --type merge -p '{"spec":{"http":[{"route":[{"destination":{"host":"app","subset":"v1","weight":95}},{"destination":{"host":"app","subset":"v2","weight":5}}]}}]}'

# 3. Watch the canary signals for the soak period (5-30 minutes)
#    error rate, p95 latency, saturation - compare v2 against v1
kubectl top pod -l version=v2

# 4. Good? Increase weight: 5 -&gt; 25 -&gt; 50 -&gt; 100.  Bad? Roll back:
kubectl patch virtualservice app --type merge \
  -p '{"spec":{"http":[{"route":[{"destination":{"host":"app","subset":"v1","weight":100}}]}}]}'
</pre>

<p><strong>Memory trick:</strong> a canary was the coal-miner's bird. If the
bird dies, you leave the mine. If the 1% deployment's error rate moves, you
stop - before the rest of the users are involved.</p>

<h2>5. Rollback, Runbooks And The Safety Net</h2>

<table>
<tr><th>Mechanism</th><th>What it does</th><th>Rule</th></tr>
<tr><td>Instant rollback</td><td>Re-point traffic at the previous artefact (blue, or previous image tag)</td><td>Must be one command, tested before you need it</td></tr>
<tr><td>Database migrations</td><td>Schema changes outlive deployments</td><td>Expand - migrate - contract: add columns first, backfill, only later remove. Never deploy code that needs a column the old version lacks</td></tr>
<tr><td>Health checks</td><td>Automatic rollback trigger</td><td>5xx rate or latency over threshold during canary -&gt; abort</td></tr>
<tr><td>Runbook</td><td>The written steps: what changed, how to verify, how to roll back</td><td>If it is not written, it is 3am and nobody remembers</td></tr>
<tr><td>Smoke test</td><td>Post-deploy: login, browse, buy</td><td>Runs automatically; failure rolls back for you</td></tr>
</table>

<h2>6. Choosing A Strategy</h2>

<pre>Risk to users of being wrong is HIGH (payments, auth, anything public)?
  yes -&gt; canary or phased, with feature flags inside
  no  -&gt; is the app stateless and replicated?
           yes -&gt; rolling (simplest default on Kubernetes)
           no   -&gt; blue-green (instant, clean rollback)

Need to test behaviour before showing it?        -&gt; feature flag
Doubtful rewrite, want production data?          -&gt; shadow
Just want the demo working today?                -&gt; big bang
</pre>

<p>Microservices usually combine them: rolling deploys of each service,
canary at the edge, feature flags inside the code.</p>

<h2>7. What Breaks Deployments (And How Strategies Handle It)</h2>

<table>
<tr><th>Failure</th><th>Big bang</th><th>Rolling / canary</th><th>Blue-green</th></tr>
<tr><td>Bad binary</td><td>Everyone down until fixed</td><td>Canary catches it at 1%; rolling halts mid-way</td><td>Flip back in seconds</td></tr>
<tr><td>Config error</td><td>Outage</td><td>Contained to the batch</td><td>Old env untouched</td></tr>
<tr><td>Incompatible schema</td><td>Outage + data risk</td><td>Mixed versions collide - use expand/contract migrations</td><td>Both versions share one database - same rule applies</td></tr>
<tr><td>Missed dependency</td><td>Full rollback</td><td>Stop the rollout</td><td>Flip back</td></tr>
</table>

<h2>8. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Strategy</td><td>Big bang: stop, replace, start</td><td>Rolling or canary, automated by Argo Rollouts / Spinnaker / ECS</td></tr>
<tr><td>Rollback</td><td>Redeploy the old build if you still have it</td><td>One command, rehearsed, under a minute (SLO)</td></tr>
<tr><td>Signals</td><td>"Looks fine"</td><td>Error rate, latency, saturation compared per version</td></tr>
<tr><td>Flags</td><td>if statements in code</td><td>Flag service (LaunchDarkly, Unleash) with owners and expiry dates</td></tr>
<tr><td>Schema</td><td>Edit the table by hand</td><td>Versioned migrations, expand/contract, reversible</td></tr>
<tr><td>Approval</td><td>You press the button</td><td>Pipeline gates: tests green, review, then progressive rollout</td></tr>
</table>

<h2>9. Key Takeaways</h2>
<ul>
<li>Speed, risk and cost - every strategy trades between those three.</li>
<li>Rolling is the Kubernetes default; blue-green buys an instant hard
cut-over; canary keeps blast radius to 1% while you watch real metrics.</li>
<li>Phased rollouts are canaries across <em>groups of people</em> instead of
percentages of traffic.</li>
<li>Feature flags separate <em>deploying</em> from <em>releasing</em>: code
ships dark, behaviour turns on later, rollback is a switch not a redeploy.</li>
<li>Migrations must be safe for both versions at once: expand, migrate,
contract.</li>
<li>If rollback has never been rehearsed, you do not have one.</li>
</ul>

<p><strong>Exercise:</strong> write a one-page runbook for your own project:
what ships, which strategy it should use, the exact rollback command, and
the three metrics that prove it worked.</p>
"""