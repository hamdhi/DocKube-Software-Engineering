"""Chapter - SDLC, Agile and Scrum, taught from zero.

Explains the software lifecycle before Agile, then Agile, then Scrum in full,
and finally how Scrum connects to CI/CD pipelines.
"""

CHAPTER = """<h2>1. What is the SDLC?</h2>

<p>The Software Development Life Cycle is the set of stages a project passes
through, from an idea to something running in production. Every team uses one,
even if they never name it.</p>

<pre>Idea -> Requirements -> Design -> Build -> Test -> Deploy -> Maintain -> Repeat</pre>

<p><strong>Why it matters:</strong> the SDLC exists to answer three questions
before they become expensive. What are we building, who needs it, and how do we
know it works?</p>

<h2>2. The Lifecycle Models Compared</h2>

<table>
<tr><th>Model</th><th>How work is divided</th><th>Feedback arrives</th><th>Best when</th><th>Biggest risk</th></tr>
<tr><td>Waterfall</td><td>One phase at a time, in order</td><td>At the very end</td><td>Regulated, fixed-scope projects</td><td>Discovering it is wrong after building it</td></tr>
<tr><td>Iterative</td><td>Repeating cycles of design, build, test</td><td>Every cycle</td><td>Requirements are moderately clear</td><td>Scope and schedule drift</td></tr>
<tr><td>Agile</td><td>Short sprints of working software</td><td>Every sprint</td><td>Requirements change often</td><td>Documentation gaps, scope creep</td></tr>
<tr><td>DevOps</td><td>Continuous integration, delivery and feedback</td><td>Continuously</td><td>Running services in production</td><td>Process overhead if done badly</td></tr>
<tr><td>Lean</td><td>Eliminate waste, maximise flow</td><td>Continuously</td><td>Struggling to deliver value</td><td>Teams feel rushed without context</td></tr>
<tr><td>Kanban</td><td>A continuous flow of work, no sprints</td><td>Continuously</td><td>Support and maintenance queues</td><td>Stale work builds up silently</td></tr>
</table>

<p><strong>Memory trick:</strong> Waterfall is <b>W</b>ater all at once,
<b>A</b>gile is a fast <b>I</b>teration loop, <b>D</b>evOps is the engine that
keeps shipping. In real companies they are often used together, not chosen
between.</p>

<h2>3. Waterfall, in Case You Meet It</h2>

<pre>1. Requirements   -> a document describing what to build
2. Design         -> architecture, database schema, mockups
3. Development    -> writing the code
4. Testing        -> QA finds the bugs
5. Deployment     -> release to production
6. Maintenance    -> fix and enhance</pre>

<p>Each phase has a defined exit gate. The problem is not that phases exist, it
is that all the uncertainty is front-loaded into a document written before
anyone builds anything.</p>

<p><strong>Where you will still meet it:</strong> government contracts, hardware
and safety-critical systems, and any project where the regulatory authority
demands written sign-off at each stage.</p>

<h2>4. Agile Manifesto</h2>

<p>Published in 2001, four sentences that reversed the traditional priorities:</p>

<table>
<tr><th>We value</th><th>Over</th><th>Because</th></tr>
<tr><td>Working software</td><td>Comprehensive documentation</td><td>Software is the point, the document supports it</td></tr>
<tr><td>Welcoming change</td><td>Following a plan</td><td>Change arrives; a plan that cannot bend fails</td></tr>
<tr><td>Customer collaboration</td><td>Contract negotiation</td><td>The customer learns what they want from the product</td></tr>
<tr><td>Delivering value</td><td>Producing artefacts and processes</td><td>Progress is only real if something useful ships</td></tr>
</table>

<p><strong>Memory trick:</strong> the four "over" words are
<b>d</b>ocumentation, <b>p</b>lan, <b>c</b>ontract negotiation,
<b>a</b>rtifact and process. Agile still writes documents and follows plans, it
just does not value them above shipping.</p>

<h2>5. Agile Principles in Plain English</h2>

<ul>
<li><strong>Deliver early and often.</strong> Waiting months to see anything is
the biggest source of wasted work.</li>
<li><strong>Welcome changing requirements.</strong> Change late is cheaper than
change never, because it is cheap while you are still building.</li>
<li><strong>Deliver working software frequently.</strong> Monthly beats yearly.</li>
<li><strong>Business people and developers work together daily.</strong> Not once
at the start.</li>
<li><strong>Build projects around motivated individuals.</strong> Give people
the problem and trust them.</li>
<li><strong>Working software is the primary measure of progress.</strong> Not
task completion.</li>
<li><strong>Sustainable pace.</strong> Teams that work 70 hours a week for a
quarter produce less over a year than teams working 40.</li>
<li><strong>Technical excellence and good design.</strong> Technical debt is
paid for by every future sprint.</li>
<li><strong>Simplicity, the art of maximising work not done.</strong></li>
<li><strong>Self-organising teams.</strong> Someone decides how, the team
decides what.</li>
<li><strong>Regular reflection and tuning.</strong> Change the way you work
based on what you learn.</li>
</ul>

<h2>6. Scrum - The Full Framework</h2>

<p>Scrum is the most widely used Agile framework. It is deliberately simple: three
roles, five events, three artefacts. Everything else is detail.</p>

<table>
<tr><th>Role</th><th>Who</th><th>Accountable for</th><th>The one question they ask</th></tr>
<tr><td>Product Owner</td><td>One person, not a committee</td><td>Maximising product value and ordering the backlog</td><td>"What should we build next?"</td></tr>
<tr><td>Scrum Master</td><td>One person, often not a manager</td><td>Team effectiveness and the framework itself</td><td>"What is stopping the team?"</td></tr>
<tr><td>Developers</td><td>Whoever builds it, 3 to 9 people</td><td>Creating a usable increment every sprint</td><td>"How will we build it?"</td></tr>
</table>

<p><strong>Memory trick:</strong> the Product Owner owns the <b>what</b> and the
<b>order</b>, the Scrum Master owns the <b>how the team works</b>, the
Developers own the <b>how they build</b>. One decision owner each, which is what
makes Scrum work.</p>

<h2>7. The Five Scrum Events</h2>

<table>
<tr><th>Event</th><th>Duration</th><th>Purpose</th><th>Key question</th></tr>
<tr><td>Sprint</td><td>1 to 4 weeks, fixed length</td><td>The container for all other events</td><td>"What will we finish this sprint?"</td></tr>
<tr><td>Sprint Planning</td><td>Max 8 hours</td><td>Agree the goal and pick work</td><td>"Why are we doing this, and what is the goal?"</td></tr>
<tr><td>Daily Scrum</td><td>15 minutes, every day</td><td>Re-plan the day toward the goal</td><td>"What will I do today, and is anything in the way?"</td></tr>
<tr><td>Sprint Review</td><td>Max 4 hours</td><td>Show working software and gather feedback</td><td>"What did we build, and what should change?"</td></tr>
<tr><td>Sprint Retrospective</td><td>Max 3 hours</td><td>Improve how the team works</td><td>"What should we stop, start and try?"</td></tr>
</table>

<p><strong>Memory trick for the flow:</strong> <b>Plan</b> in the morning of day
one, <b>Daily</b> every day, <b>Review</b> the product with stakeholders at the
end, <b>Retro</b> on ourselves right after. And every event has a timebox in
proportional hours, which is worth memorising.</p>

<h3>The Sprint, the Goal, and the Increment</h3>
<p>The <strong>Sprint</strong> is a fixed-length container. The
<strong>Sprint Goal</strong> is the single objective for it. The
<strong>Increment</strong> is the working product added to the product, and it
must be usable, not "90 percent done".</p>

<p>Sprint length is a commitment. Two weeks is the most common. Shorter gives
faster feedback but less work per sprint; longer wastes more if the goal is
wrong.</p>

<h3>The Daily Scrum in detail</h3>
<p>Fifteen minutes, standing, same time and place every day, focused on the goal.
Everyone answers three questions:</p>
<ul>
<li>What have I done since the last Daily Scrum?</li>
<li>What will I do before the next one?</li>
<li>What is blocking my progress?</li>
</ul>

<p>If there are deeper problems, discuss them after. The Daily Scrum is not a
status report to a manager.</p>

<h3>Review versus Retrospective - the classic confusion</h3>
<table>
<tr><th>Aspect</th><th>Sprint Review</th><th>Sprint Retrospective</th></tr>
<tr><td>Audience</td><td>Stakeholders and the whole team</td><td>The team only</td></tr>
<tr><td>Subject</td><td>The product, the increment, the roadmap</td><td>The people and the process</td></tr>
<tr><td>Question</td><td>"What did we build and what do you think?"</td><td>"How did we work and what will we change?"</td></tr>
<tr><td>Output</td><td>Updated Product Backlog</td><td>One or two concrete improvements</td></tr>
</table>

<p><strong>Memory trick:</strong> Review is about the <b>product</b>, Retro is
about the <b>team</b>.</p>

<h2>8. The Three Artefacts</h2>

<table>
<tr><th>Artefact</th><th>Owner</th><th>Refined in</th><th>Committed to</th><th>Purpose</th></tr>
<tr><td>Product Backlog</td><td>Product Owner</td><td>Continuous</td><td>Product Goal</td><td>Everything wanted, ordered by value</td></tr>
<tr><td>Sprint Backlog</td><td>Developers</td><td>During Planning</td><td>Sprint Goal</td><td>What the team will do this sprint, with a plan</td></tr>
<tr><td>Increment</td><td>Developers</td><td>Every sprint</td><td>Sprint Goal</td><td>Usable product added to the previous one</td></tr>
</table>

<h3>How a story travels</h3>

<pre>Epic        -> Product Owner writes it in the Product Backlog
  Story     -> A slice of that epic, with value and acceptance criteria
    Task    -> A technical step the Developers split it into
      Commit -> An actual line of code change</pre>

<p><strong>Memory trick:</strong> Epic is big, Story is deliverable in one
sprint, Task is smaller still. A story that cannot be finished in a sprint is
too big.</p>

<h3>User Stories and Acceptance Criteria</h3>

<pre>As a shop owner
I want to see daily sales totals
So that I know whether to restock

Acceptance criteria:
  - Totals load within 2 seconds
  - Shows today, yesterday and last week
  - Exports to CSV
  - Empty state shown when there are no sales</pre>

<p><strong>Memory trick:</strong> as a, I want, so that. The "so that" is the
most important part, because it states the value. Criteria are written by the
team and are really a conversation starter.</p>

<h3>Definition of Done</h3>
<p>The team's shared checklist for what "finished" means. It usually includes code
reviewed, tests written and passing, no known security issues, documentation
updated, deployed to staging, and monitored. A story is only done when it meets
this, regardless of what the sprint board says.</p>

<p><strong>Memory trick:</strong> "Done" is a definition, not a feeling. If two
people disagree about whether something is done, the DoD is missing.</p>

<h2>9. Estimation and Forecasting</h2>

<table>
<tr><th>Technique</th><th>How it works</th><th>Good for</th><th>Watch out for</th></tr>
<tr><td>Story points</td><td>Relative size: 1, 2, 3, 5, 8, 13, 21</td><td>Agile backlogs, sizing relative effort</td><td>Not hours, and not comparable across teams</td></tr>
<tr><td>T-shirt sizing</td><td>Small, medium, large, XL</td><td>Rough sizing without precision</td><td>Too coarse for forecasting</td></tr>
<tr><td>Hours</td><td>Direct developer estimates</td><td>Fixed, well-understood work</td><td>Developers estimate optimistically, then overrun</td></tr>
<tr><td>Planning poker</td><td>Team estimates together, then reveals</td><td>Surfacing disagreement and assumptions</td><td>Takes time every sprint</td></tr>
</table>

<p><strong>Memory trick:</strong> the Fibonacci sequence is used because the gap
between 8 and 13 is deliberately large, signalling "this is much bigger". A 6
is not offered.</p>

<h3>Velocity</h3>
<p>Velocity is the sum of story points completed per sprint. It is a forecasting
tool for <em>this</em> team, not a productivity score to compare teams with. The
usual question is not "what is your velocity" but "how much of the backlog can
we finish by this date".</p>

<h3>Burndown and Burnup</h3>
<table>
<tr><th>Chart</th><th>Shows</th><th>Use it to</th></tr>
<tr><td>Burndown</td><td>Remaining work against time</td><td>Spot scope creep and whether the goal is still reachable</td></tr>
<tr><td>Burnup</td><td>Completed work against time</td><td>See added and removed scope, and true throughput</td></tr>
<tr><td>Cumulative flow</td><td>Work in each state over time</td><td>Spot a bottleneck and over-polishing</td></tr>
</table>

<h2>10. Anti-Patterns - How Teams Break Scrum</h2>

<table>
<tr><th>Anti-pattern</th><th>What it looks like</th><th>Why it is wrong</th><th>The fix</th></tr>
<tr><td>Sprint as a waterfall</td><td>Design, then code, then test, all inside the sprint</td><td>No feedback until the sprint ends</td><td>Test as you build; demo working software weekly</td></tr>
<tr><td>Sprint of chores</td><td>Sprint Goal is "clear the tech debt"</td><td>Deliverable value is not the goal</td><td>Pair cleanup with user value</td></tr>
<tr><td>Shu, shu, shu</td><td>Team says Scrum but nothing changes</td><td>Process without purpose</td><td>Scrum Master exists to change the system</td></tr>
<tr><td>Too many Scrum Masters</td><td>Coordinators across teams</td><td>Creates overhead, fragments accountability</td><td>One per team; scale across teams instead</td></tr>
<tr><td>Product Owner as figurehead</td><td>PO never actually decides</td><td>Backlog ordering is a popularity contest</td><td>Give the PO real authority and time</td></tr>
<tr><td>Sprint Goal as a list</td><td>"Do login, fix search, update profile"</td><td>Tasks, not an outcome</td><td>Write a sentence describing the change users see</td></tr>
<tr><td>Committed, not done</td><td>Work moved to the next sprint repeatedly</td><td>No real forecast, no trust</td><td>Split stories so they fit; reduce Sprint Goal</td></tr>
<tr><td>Scrum but the org is a project</td><td>Fixed scope, date and budget</td><td>Agile cannot absorb that</td><td>Make the three fixed: time, quality, scope flexes</td></tr>
</table>

<p><strong>Memory trick:</strong> if a sprint produces no working software that a
real user could touch, it was not Scrum.</p>

<h2>11. Scrum versus Kanban versus SAFe</h2>

<table>
<tr><th>Aspect</th><th>Scrum</th><th>Kanban</th><th>SAFe</th></tr>
<tr><td>Cadence</td><td>Fixed sprints</td><td>Continuous flow</td><td>Program increments, often quarterly</td></tr>
<tr><td>Roles</td><td>Three, defined</td><td>None required</td><td>Many: Product Owner, Team, System Architect, Scrum Master, Programme Management</td></tr>
<tr><td>Work in progress</td><td>Limited by the Sprint Backlog</td><td>Explicit WIP limit per column</td><td>Per team</td></tr>
<tr><td>Change</td><td>Backlog can change any time</td><td>Any time</td><td>Change is managed with Product Backlog and trains</td></tr>
<tr><td>Best for</td><td>Product development with regular delivery</td><td>Support, maintenance, continuous flow</td><td>Very large organisations, many teams</td></tr>
<tr><td>Risk</td><td>Ceremony for teams that do not need it</td><td>Work stalls silently without limits</td><td>Bureaucracy and slow decisions</td></tr>
</table>

<p><strong>Memory trick:</strong> Scrum works in <b>sprints</b> with defined
roles; Kanban works as a <b>flow</b> with WIP limits and no roles; SAFe is
Scrum scaled to many teams.</p>

<h2>12. How Scrum Connects to CI/CD</h2>

<p>Scrum and DevOps are complementary. Scrum decides <em>what</em> to build and
<em>when</em>. CI/CD decides how reliably that work ships. Together they form a
feedback loop from idea to production to customer feedback.</p>

<pre>Product Owner     Backlog        Sprint Planning       Sprint
  prioritises      ordered by     team commits to a     Developers build
  value            value          Sprint Goal           every day

  Sprint Review -> demo working software in staging
  Sprint Retrospective -> improve how the team works

Every commit -> CI builds and tests automatically
Green build   -> CD deploys to staging automatically
Staging OK    -> promote to production
Production    -> metrics feed back to the backlog</pre>

<table>
<tr><th>Agile concept</th><th>DevOps counterpart</th><th>Shared goal</th></tr>
<tr><td>Definition of Done</td><td>Pipeline passes all quality gates</td><td>Both mean "finished and verified"</td></tr>
<tr><td>Sprint Review demo</td><td>Deployment to staging</td><td>Real feedback on real software</td></tr>
<tr><td>Product Backlog</td><td>Infrastructure backlog</td><td>Both need prioritisation and grooming</td></tr>
<tr><td>Sprint Goal</td><td>Release milestone</td><td>Both are dated commitments of value</td></tr>
<tr><td>Retrospective action item</td><td>Pipeline improvement, such as adding a test gate</td><td>Both close the loop by improving the system</td></tr>
</table>

<p><strong>Memory trick:</strong> Scrum is the <b>plan</b>, CI/CD is the
<b>pipes</b>. You need both. A sprint without a pipeline ships by hand, and a
pipeline without a sprint ships random changes.</p>

<h3>Common scaling situations</h3>
<table>
<tr><th>Situation</th><th>What is often missing</th><th>What usually helps</th></tr>
<tr><td>Two teams sharing one codebase</td><td>Ownership and merge coordination</td><td>Clear code ownership, trunk-based development, small PRs</td></tr>
<tr><td>Five teams, one release</td><td>A release train or plan</td><td>Explicit release cadence agreed up front</td></tr>
<tr><td>Sprints with frequent releases</td><td>Nothing, this is good practice</td><td>Keep it; releasing per sprint is the goal</td></tr>
</table>

<h2>13. Try It Yourself (45 minutes)</h2>
<ul>
<li>Write one epic with three stories beneath it, each with acceptance criteria
and a "so that" clause.</li>
<li>Run a 15-minute Daily Scrum on your own work, using the three questions.</li>
<li>Estimate ten tasks in story points, then rank them. Notice how much harder
relative sizing is than hours.</li>
<li>Plot a burndown for your current project and see whether scope grew.</li>
<li>Write a Definition of Done for a small project and check whether it removes
ambiguity.</li>
<li>Map a recent project onto the five Scrum events and notice what was
missing.</li>
<li>Take one anti-pattern from the table and think about how to fix it in a team
you have worked in.</li>
</ul>

<h2>14. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Frameworks</td><td>Scrum, because it teaches the ideas</td><td>Whatever fits; the principles matter more than the ceremonies</td></tr>
<tr><td>Sprint length</td><td>One week, to see results fast</td><td>One or two weeks, matched to release cadence</td></tr>
<tr><td>Estimation</td><td>Story points, to learn them</td><td>Still common; some teams prefer hours on well-understood work</td></tr>
<tr><td>Velocity</td><td>Tracked and displayed proudly</td><td>Used privately for forecasting, never compared between teams</td></tr>
<tr><td>Meetings</td><td>Attended happily</td><td>Timeboxed, with agendas and recorded actions</td></tr>
<tr><td>Scope</td><td>Fixed by the backlog owner informally</td><td>One accountable Product Owner, backlog ordered by value</td></tr>
<tr><td>Definition of Done</td><td>Loose, "it works on my machine"</td><td>Automated gates in the pipeline: tests, scans, reviews</td></tr>
<tr><td>Retrospective</td><td>Sometimes skipped</td><td>Held every sprint, with tracked action items</td></tr>
<tr><td>Shipping</td><td>Manual deploys at the end</td><td>Automated CD, deploying per sprint or more often</td></tr>
<tr><td>Metrics</td><td>Story points and burndown</td><td>DORA metrics: deployment frequency, lead time, failure rate, recovery time</td></tr>
</table>

<h2>15. Key Takeaways</h2>
<ul>
<li>The SDLC is a set of stages; the model you pick changes when you get feedback.</li>
<li>Agile values working software over documentation, and change over a plan.</li>
<li>Scrum is three roles, five events, three artefacts, nothing more.</li>
<li>The Product Owner owns the what, the Scrum Master owns the process, the Developers own the how.</li>
<li>Review is about the product; Retrospective is about the team.</li>
<li>Done is a shared definition, not a feeling.</li>
<li>Story points are relative and not comparable across teams.</li>
<li>Scrum is the plan, CI/CD is the pipes; you need both.</li>
</ul>
"""