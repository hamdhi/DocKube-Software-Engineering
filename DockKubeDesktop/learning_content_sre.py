"""Chapter - Site Reliability Engineering: SLIs, SLOs and error budgets."""

CHAPTER = """<h2>1. What Is SRE?</h2>

<p>Site Reliability Engineering is applying engineering methods to running a
service. The name comes from Google's original SRE book, where the job was
defined with a twist: SREs are expected to spend a set amount of their time on
reliability and the rest on building. The cap is deliberate.</p>

<p>You cannot spend 100% of your time on reliability and the system will ever
improve. SRE teams limit themselves to roughly half, and the rest goes into
making the next release safer.</p>

<p><strong>Memory trick:</strong> SRE is the discipline of making reliability a
number you manage, not a quality you hope for.</p>

<h2>2. Why "99.9% Uptime" Is Not A Goal</h2>

<p>Every level of availability hides a question nobody asked: how many users,
for how long, and how bad was it?</p>

<table>
<tr><th>Availability</th><th>Downtime per year</th><th>Downtime per day</th></tr>
<tr><td>99% ("two nines")</td><td>3.65 days</td><td>14.4 minutes</td></tr>
<tr><td>99.9% ("three nines")</td><td>8.76 hours</td><td>1.44 minutes</td></tr>
<tr><td>99.95%</td><td>4.38 hours</td><td>43 seconds</td></tr>
<tr><td>99.99% ("four nines")</td><td>52.6 minutes</td><td>8.6 seconds</td></tr>
<tr><td>99.999% ("five nines")</td><td>5.26 minutes</td><td>0.86 seconds</td></tr>
</table>

<p>Those numbers only mean something against a measured window. An SLO makes the
window, the measure and the number all explicit, which is what turns "reliable"
into something a team can argue about.</p>

<h2>3. SLI - The Thing You Measure</h2>

<p>A <strong>Service Level Indicator</strong> is the actual measurement, taken
from the user's point of view. Good SLIs describe what the user experiences,
not what your server happens to report.</p>

<table>
<tr><th>SLI</th><th>Measures</th><th>Where it comes from</th></tr>
<tr><td>Availability</td><td>Successful requests over total requests</td><td>Load balancer or proxy logs</td></tr>
<tr><td>Latency</td><td>Proportion of requests under a threshold</td><td>Server timing headers</td></tr>
<tr><td>Throughput</td><td>Requests per second</td><td>Same place</td></tr>
<tr><td>Correctness</td><td>Proportion returning the right result</td><td>Synthetic checks and business metrics</td></tr>
<tr><td>Freshness</td><td>How current the data is</td><td>Timestamp on the data itself</td></tr>
<tr><td>Durability</td><td>How reliably data survives</td><td>Backup restore tests</td></tr>
</table>

<p><strong>Memory trick:</strong> a good SLI is something you would complain about
if it got worse. If no user would notice, it is not an SLI, it is a curiosity.</p>

<h2>4. SLO - The Target You Set</h2>

<p>A <strong>Service Level Objective</strong> is the target for an SLI over a
stated window. It is a decision, and the most important part is usually the
window.</p>

<pre>SLI:     proportion of requests to /checkout returning 2xx
SLO:     99.5% over 28 days
Window:  28 rolling days</pre>

<p>A 28-day rolling window is deliberate. Monthly calendars are too short to see
trends and too sharp: one bad day eats a third of a monthly budget. A rolling
window smooths that.</p>

<p><strong>Memory trick:</strong> pick 28 days, not 30. It divides neatly by 4
and by 7, which makes budget maths painless.</p>

<h2>5. SLOs Must Be Achievable</h2>

<p>A 99.99% target on a system with no redundancy is a target you will miss,
because it permits about five minutes of downtime a month and any deploy will
use some of it. SLOs have to account for the fact that you will deploy.</p>

<table>
<tr><th>Feature</th><th>Availability</th><th>Why</th></tr>
<tr><td>Static site</td><td>100%</td><td>Nothing to fail at runtime</td></tr>
<tr><td>Read-only API, replicated</td><td>99.95% or better</td><td>No writes to lose</td></tr>
<tr><td>Standard user-facing service</td><td>99.9%</td><td>The usual starting point</td></tr>
<tr><td>Money or safety critical</td><td>99.95% and a real failover plan</td><td>Extra cost is justified</td></tr>
</table>

<p>Set the target at the level your current architecture can actually sustain,
then improve the architecture. Setting it higher produces a permanently burning
budget and a permanently exhausted team.</p>

<h2>6. Error Budget - The Spending Permission</h2>

<p>The error budget is the allowed unreliability, expressed as a number you can
spend. If 99.9% is the objective over 28 days, the budget is the 0.1%.</p>

<pre>28 days = 2,419,200 seconds
Budget at 99.9%   = 0.001  x 2,419,200 = 2,419 seconds  (~40 minutes)
Budget at 99.95%  = 0.0005 x 2,419,200 = 1,210 seconds  (~20 minutes)</pre>

<p>Then the rule that makes the whole thing work: <strong>when the budget is
healthy, you may ship faster. When it is exhausted, you stop releasing features
and fix reliability until it recovers.</strong></p>

<p>This is the part that makes SRE different from a target on a slide. The number
changes what people are allowed to do this week.</p>

<p><strong>Memory trick:</strong> the error budget is the permission slip for
taking risks. Spend it on experiments while you have it, and you have to pay the
bill later.</p>

<h2>7. Multi-Window Multi-Burn-Rate Alerts</h2>

<p>Alerting on "we have exceeded the SLO" is far too late: by then the budget is
already gone. Instead, alert on how fast the budget is being spent.</p>

<pre>A burn rate of 1.0 means you are consuming the budget exactly as fast as
time passes. Faster than 1.0 means you are overspending.

1 hour window +  5 minute window &gt; 14.4x  -&gt;  page, budget nearly gone
6 hour window + 30 minute window &gt;  6x    -&gt;  page
1 day window   +  2 hour window  &gt;  3x    -&gt;  ticket
3 day window   +  6 hour window  &gt;  1x    -&gt;  ticket</pre>

<p>A short window catches the fast outage before users notice. The long window
stops you paging for something that has already recovered. Both are needed
together, which is why it is called multi-window.</p>

<p><strong>Memory trick:</strong> page on how fast you are burning, not on how
much you have already burned.</p>

<h2>8. The Other Reliability Terms</h2>

<table>
<tr><th>Term</th><th>Meaning</th></tr>
<tr><td>SLI</td><td>The measurement, from the user's view</td></tr>
<tr><td>SLO</td><td>The target for that measurement, over a window</td></tr>
<tr><td>SLA</td><td>A contract with a customer, usually with financial penalties</td></tr>
<tr><td>Error budget</td><td>The allowed unreliability, as spendable time</td></tr>
<tr><td>Burn rate</td><td>How fast the budget is being consumed relative to time</td></tr>
<tr><td>Toil</td><td>Manual, repetitive, automatable work eating your time</td></tr>
<tr><td>MTTR</td><td>Mean time to restore, from detection to recovery</td></tr>
<tr><td>MTTD</td><td>Mean time to detect, how long a failure went unnoticed</td></tr>
<tr><td>Postmortem</td><td>A blameless review after an incident</td></tr>
</table>

<p><strong>Toil</strong> is the one worth fighting hardest. Google measured that
SREs spend no more than 50% of their time on operational work, and toil is what
pushes that over. Every hour spent by hand should become an alert or an
automation, or it is a task you will do again next week.</p>

<h2>9. What SRE Actually Changes Day To Day</h2>

<p>This is the part that surprises people, because most of the work is not
incident response at all:</p>

<ul>
<li><strong>Writing SLOs</strong> and putting them in the service documentation.</li>
<li><strong>Load testing</strong> until you know where the system breaks.</li>
<li><strong>Capacity planning</strong>, so scaling happens before demand arrives.</li>
<li><strong>Automation</strong> to remove toil, and measuring toil to prove it worked.</li>
<li><strong>Chaos experiments</strong>, deliberately breaking something small to
prove your monitoring actually notices.</li>
<li><strong>Postmortems</strong> after every incident, focused on systems rather
than people.</li>
</ul>

<p><strong>Try it yourself:</strong> take one service you run. Write down its
availability and latency SLIs, give each an SLO over 28 days, and work out the
error budget in minutes. It takes ten minutes and it is the single clearest
summary of how reliable that service is allowed to be.</p>

<p><strong>Learning vs production:</strong> the maths is the same everywhere. What
changes is that a real SLO has consequences: a product team wants to ship, the
budget says no, and somebody has to have that conversation with a number rather
than an opinion.</p>"""
