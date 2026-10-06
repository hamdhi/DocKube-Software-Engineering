r"""Chapter 42 - Platform engineering and emerging tech: internal developer platforms, golden paths, Backstage."""

CHAPTER = r"""<h2>1. Why Platform Engineering Exists</h2>

<p>Every DevOps team eventually hits the same wall: twenty product teams
each assembling the same pipeline, the same Kubernetes boilerplate, the
same dashboards - badly. Platform engineering is the answer: a dedicated
team builds <strong>one internal platform</strong> so product teams ship
features instead of plumbing.</p>

<table>
<tr><th>Old world (DevOps at scale)</th><th>Platform world</th></tr>
<tr><td>Every team owns its toolchain; expertise is uneven</td><td>One paved road, maintained by specialists</td></tr>
<tr><td>Ticket ops: file a ticket, wait three days</td><td>Self-service with guardrails: click, get a database</td></tr>
<tr><td>Config sprawl, every repo different</td><td>Golden paths: templates that encode the standards</td></tr>
<tr><td>Cognitive load on every developer</td><td>Developers think about the product, not the platform</td></tr>
<tr><td>Platform is a side duty nobody owns</td><td>Platform is a product with users, SLAs and a roadmap</td></tr>
</table>

<p><strong>Memory trick:</strong> DevOps changed <em>how teams work</em>;
platform engineering changes <em>what each team has to know</em>. The
product of a platform team is a <em>paved road</em>, and adoption - not
uptime - is its real metric.</p>

<h2>2. The Internal Developer Platform, Down To The Atom</h2>

<p>An IDP is the golden path made clickable. Every atom a service needs:</p>

<table>
<tr><th>Layer</th><th>The platform provides</th><th>Under the hood</th></tr>
<tr><td>Compute</td><td>"New service" button -&gt; deployed workload</td><td>K8s namespace / VM / serverless, autoscaling, rollout policy</td></tr>
<tr><td>Networking</td><td>Hostname, ingress, service discovery, mTLS</td><td>Gateway, DNS record, cert-manager, mesh policy</td></tr>
<tr><td>Storage</td><td>Volume / bucket self-service</td><td>PVC templates, S3 buckets with lifecycle rules</td></tr>
<tr><td>Databases</td><td>Provisioned DB with backups on</td><td>Operator (CloudNativePG, Postgres operator), PITR, credentials injected</td></tr>
<tr><td>Secrets</td><td>Team secrets store, automatic injection</td><td>Vault / AWS SM, short-lived leases, no secret in git</td></tr>
<tr><td>CI/CD</td><td>Build, test, sign, deploy from one file</td><td>GitHub Actions/Tekton, supply chain (cosign, SBOM), progressive delivery</td></tr>
<tr><td>Environments</td><td>Preview / staging / prod from templates</td><td>Ephemeral preview envs per PR, prod behind approvals</td></tr>
<tr><td>Observability</td><td>Dashboards, logs, traces, alerts auto-wired</td><td>OpenTelemetry, Prometheus, Grafana, on-call rotation defaults</td></tr>
<tr><td>Policy</td><td>Guardrails you cannot turn off</td><td>OPA/Gatekeeper: no privileged pods, images from approved registries</td></tr>
<tr><td>FinOps</td><td>Cost per team, per service</td><td>Labels, showback dashboards, budget alerts</td></tr>
</table>

<h2>3. Internal Developer Portal - The Catalog</h2>

<p>The <strong>internal developer portal</strong> (Backstage is the reference
implementation) is the UI over all of it: a live catalog of every service,
its owner, its docs, its scorecards, and a button to scaffold a new one.</p>

<pre>Software catalog (the core object model)
  Component   - a service, a library, a website
  API         - contracts components expose
  System      - grouping of components delivering one capability
  Resource    - DB, bucket, topic a component consumes
  User/Team   - owners; every entity HAS an owner

Every entity gets: description, owner, tags, links, on-call, docs,
dashboards, scorecards - generated when scaffolded, kept live from CI.

Scaffolder template (golden path as code):
  1. developer clicks "New Node service"
  2. template fills repo: FastAPI structure, Dockerfile, CI, OTel, alerts
  3. registers it in the catalog with owner = your team
  4. provisions staging DB + secrets, wires dashboards
  5. first deploy -&gt; production behind the standard progressive rollout
</pre>

<table>
<tr><th>Scorecard (examples)</th><th>Gate</th></tr>
<tr><td>Has owner + on-call rotation</td><td>Required to graduate to prod</td></tr>
<tr><td>SLO defined, error budget visible</td><td>Blocks high-risk changes when burned</td></tr>
<tr><td>CI runs tests + SAST + dependency scan</td><td>Branch protection requires it</td></tr>
<tr><td>Runs the golden-path base image</td><td>Non-compliant = tracked debt with a deadline</td></tr>
<tr><td>Deploys via standard pipeline</td><td>No ad-hoc kubectl to prod, ever</td></tr>
</table>

<h2>4. Golden Paths, Templates And Self-Service</h2>

<pre>Golden path = the easiest way to do the right thing, and a visible door
for every other way (with friction, review, and a recorded exception).

Not: "you MUST use our JVM library" (platform as bureaucracy)
Yes: "new service? 15 minutes, secure defaults, zero tickets" - and if you
     deviate, you own the tests, dashboards and security review for it.

Scaffold sources of truth:
  repo templates (Cookiecutter, create-*)  -&gt; code lives in git
  Helm/Jsonnet/Kustomize overlays           -&gt; infra lives in git
  Crossplane / Terraform modules            -&gt; cloud resources as code
  API-first IDP                             -&gt; everything callable, everything audited
</pre>

<h2>5. The Team Topology View</h2>

<table>
<tr><th>Team</th><th>Responsibility</th><th>Interfaces</th></tr>
<tr><td>Platform team</td><td>The paved road: IDP, pipelines, runtime, DBs, observability</td><td>Self-service APIs + docs + office hours</td></tr>
<tr><td>Enabling team</td><td>Coaches stuck product teams onto the platform</td><td>Temporary pairing, playbooks</td></tr>
<tr><td>Stream-aligned (product) teams</td><td>Business value, own services end to end</td><td>Platform golden paths</td></tr>
<tr><td>Enabling vs X-as-a-Service</td><td>XaaS publishes consumable capabilities; enabling teaches</td><td>-</td></tr>
</table>

<p><strong>Thinnest viable platform:</strong> start with ONE golden path
(build + deploy + database) that a single team loves, publish it, measure
adoption, then expand. A platform nobody adopts is expensive shelfware.
Anti-pattern to watch: the platform team blocking product teams with
reviews - guardrails should be automatic, not human queues.</p>

<h2>6. GitOps - The Platform\'s Control Loop</h2>

<pre>git push (desired state)
   -&gt; Flux / Argo CD watches the repo
   -&gt; diffs live cluster vs git
   -&gt; applies changes, reports status back
   -&gt; drift? cluster is RECONCILED back to git automatically

Why it matters for platforms:
  - self-service = open a PR; approval is code review
  - every change auditable, revertible (git revert), and reviewable
  - cluster credentials stay with the controller, not with developers
  - multi-cluster: one repo, many overlays (staging, prod, regions)
</pre>

<h2>7. Emerging Tech Around The Platform</h2>

<table>
<tr><th>Trend</th><th>What it is</th><th>Why it matters now</th></tr>
<tr><td>Platform engineering</td><td>IDPs and golden paths</td><td>Cognitive load is the bottleneck at scale</td></tr>
<tr><td>AI-assisted ops (AIOps + copilots)</td><td>LLMs reading logs/alerts, suggesting fixes, writing pipelines</td><td>Reduces MTTR; keep a human on the approve button</td></tr>
<tr><td>WebAssembly (WASM) at the edge/server</td><td>Sandboxed near-native components</td><td>Plugin systems, edge functions, safer untrusted code</td></tr>
<tr><td>Edge computing</td><td>Compute near the user (CDN functions, IoT gateways)</td><td>Latency-sensitive features without central round-trips</td></tr>
<tr><td>FinOps engineering</td><td>Cost as an engineering metric in the platform</td><td>Unit economics per feature, showback drives behaviour</td></tr>
<tr><td>Supply-chain security</td><td>SLSA, SBOM, cosign signing, provenance</td><td>Attacks moved upstream to build systems</td></tr>
<tr><td>Confidential computing</td><td>Encrypted memory enclaves (SEV/TDX)</td><td>Compliance for regulated workloads in the cloud</td></tr>
<tr><td>Sustainable/green computing</td><td>Carbon-aware scheduling, efficiency metrics</td><td>Cost and compliance are converging</td></tr>
</table>

<h2>8. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Platform</td><td>One laptop running minikube + a Makefile</td><td>Multi-tenant IDP with quotas, quotas per team, SSO, audit</td></tr>
<tr><td>Provisioning</td><td>Ticket or click in a console</td><td>Self-service API, policy-gated, costed, auto-decommissioned if idle</td></tr>
<tr><td>Standards</td><td>README advice</td><td>Scorecards enforced at the pipeline with escape hatches</td></tr>
<tr><td>Adoption</td><td>-</td><td>Measured: % services on golden path, lead time, onboarding time</td></tr>
<tr><td>Support</td><td>Ask the one person who built it</td><td>Docs, office hours, SLO for the platform itself</td></tr>
</table>

<h2>9. Key Takeaways</h2>
<ul>
<li>Platform engineering = product thinking applied to internal tooling:
users, adoption metrics, paved roads.</li>
<li>The IDP covers compute, network, storage, databases, secrets, CI/CD,
observability, policy and cost - self-service with the guardrails built
in.</li>
<li>The catalog (Backstage) makes ownership and standards visible;
scorecards make them enforceable.</li>
<li>GitOps turns every change into a reviewed, revertible commit and fixes
drift automatically.</li>
<li>Start with the thinnest viable platform; adoption is the only metric
that counts at first.</li>
<li>AI, WASM, edge and supply-chain security are the next waves landing ON
the platform - which is exactly why the platform exists.</li>
</ul>

<p><strong>Exercise:</strong> draw your dream IDP as a catalog: list every
atom a new service needs (from the table in section 2), mark which are
tickets today, and sketch the one golden path that would remove the most
tickets.</p>
"""