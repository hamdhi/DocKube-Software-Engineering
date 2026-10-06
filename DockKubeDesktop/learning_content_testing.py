r"""Chapter 24 - Testing: unit, integration, regression, A/B, black box and white box."""

CHAPTER = r"""<h2>1. What Testing Really Buys You</h2>

<p>A test is a machine that answers one question: <em>does the code still do
what we think it does?</em> Writing it down as code means the answer arrives in
seconds, forever, without a human having to remember what the feature used to
do.</p>

<p><strong>Memory trick:</strong> bugs found in requirements cost 1x to fix,
in design 5x, in code 10x, in production 100x. Every cheap test you write
moves a bug left, where it is cheap.</p>

<h2>2. The Test Levels, The Order You Do Them, And The Phase They Run In</h2>

<p>Tests are written and run in a fixed order, fastest first. If a unit test
cannot pass, there is no point starting the integration test behind it.</p>

<table>
<tr><th>Level</th><th>What it exercises</th><th>Order you do it</th><th>Phase it runs in</th><th>Speed</th><th>Typical tool</th></tr>
<tr><td>Unit test</td><td>One function or class, alone, with its neighbours faked</td><td>1st - written while you code, minutes after the code</td><td>Every save (pre-commit) and every commit</td><td>Milliseconds</td><td>pytest, unittest, Jest</td></tr>
<tr><td>Integration test</td><td>Two or more real parts together: API + database, app + queue</td><td>2nd - once units are green</td><td>Every push / pull request in CI</td><td>Seconds</td><td>pytest + TestClient, Testcontainers</td></tr>
<tr><td>System / end-to-end</td><td>The whole running system, driven like a user</td><td>3rd - after integration passes</td><td>Merge to main, nightly, or pre-release</td><td>Minutes</td><td>Playwright, Selenium, Cypress</td></tr>
<tr><td>Regression test</td><td>Every bug that ever shipped, re-checked forever</td><td>Continuous - each fix adds a case</td><td>Every pipeline run, forever</td><td>Same as the level the bug lived at</td><td>Any suite; golden/snapshot files</td></tr>
<tr><td>Acceptance test</td><td>Whether the software satisfies the agreed requirements</td><td>Last - before sign-off</td><td>Pre-release, UAT, alpha/beta</td><td>Hours</td><td>Cucumber, manual UAT scripts</td></tr>
</table>

<p><strong>Memory trick:</strong> Unit, Integration, System, Acceptance -
<strong>UISA</strong>. Write them in that order, run them in that order, and
stop the pipeline at the first red stage.</p>

<h2>3. The Test Pyramid</h2>

<pre>        /  E2E   \          few, slow, expensive, brittle
       /------------\ 
      / Integration  \      medium count, medium speed
     /----------------\ 
    /     Unit tests    \   many, fast, cheap, precise
   /______________________\
</pre>

<p>Wide base, narrow top. A suite that is mostly end-to-end tests is slow and
flaky; a suite with no end-to-end tests never checks that the parts actually
connect. Aim for roughly 70% unit, 20% integration, 10% end-to-end - the
ratios matter less than the shape.</p>

<h2>4. Unit Tests</h2>

<p>A unit test calls one thing with given inputs and asserts the output. It
touches no network, no disk, no database, no real clock. The three-part
shape is <strong>Arrange, Act, Assert</strong>.</p>

<pre>def test_discount_applies_above_threshold():
    # Arrange
    cart = Cart(items=[Item(price=50), Item(price=30)])
    # Act
    total = cart.total(discount=0.1)
    # Assert
    assert total == 72.0   # (50 + 30) - 10%


def test_empty_cart_is_free():
    assert Cart(items=[]).total() == 0
</pre>

<p>Good unit tests are <strong>FIRST</strong>: Fast, Independent, Repeatable,
Self-validating, Timely. If two tests cannot run in any order, they are
coupled and one of them will lie to you.</p>

<p><strong>What not to test:</strong> private helpers you might rename
tomorrow, third-party library behaviour, or framework boilerplate. Test your
decisions, not your syntax.</p>

<h2>5. Integration Tests</h2>

<p>Units can all pass while the app is broken - the wiring is wrong, the
query is misspelled, the config key does not exist. Integration tests run
real pieces together.</p>

<pre>from fastapi.testclient import TestClient
from app.main import app   # your FastAPI application

client = TestClient(app)

def test_create_order_persists():
    response = client.post("/orders", json={"sku": "A1", "qty": 2})
    assert response.status_code == 201
    body = response.json()
    # The database must really contain it, not just the response.
    stored = client.get(f"/orders/{body['id']}")
    assert stored.json()["qty"] == 2
</pre>

<p><strong>Learning vs reality:</strong> while learning you point tests at a
local database. In production CI, each job spins its own throwaway database
(Testcontainers starts a Docker container per run) so jobs never collide.</p>

<h2>6. System, End-to-End And Acceptance</h2>

<table>
<tr><th>Type</th><th>Question it answers</th><th>Who owns it</th><th>Failure means</th></tr>
<tr><td>System / E2E</td><td>Does the whole stack work for a real user journey?</td><td>Developers + QA</td><td>Something between the parts is broken</td></tr>
<tr><td>UAT (user acceptance)</td><td>Is this the software the business asked for?</td><td>Product / customer</td><td>Wrong feature, missing requirement</td></tr>
<tr><td>Alpha / beta</td><td>Does it survive real users and real data?</td><td>Real users</td><td>Assumptions that no test could anticipate</td></tr>
<tr><td>Smoke test</td><td>After a deploy: is the site up and login works?</td><td>Pipeline</td><td>Roll back immediately</td></tr>
</table>

<h2>7. Regression Testing</h2>

<p><strong>Regression</strong> means an old thing that worked is broken now.
Regression testing is not a separate tool - it is the discipline of turning
every bug fix into a permanent test so the bug can never come back.</p>

<pre># The bug: applying a coupon twice gave money back.
def test_coupon_applies_only_once():
    cart = Cart(coupon="SAVE10")
    first = cart.total()
    second = cart.total()        # calling again must not re-apply
    assert first == second
</pre>

<p>Golden (snapshot) files are regression tests for output shape: dump the
JSON, the rendered HTML, the CLI help text to a file; the test compares and
fails on any diff; a human approves intentional changes. Most regression
failures are accidental side effects you never considered - that is exactly
what they are for.</p>

<p><strong>Memory trick:</strong> a bug fixed without a test is a bug on
parole.</p>
<h2>8. Black-Box Testing - Testing From The Outside</h2>

<p><strong>Black box</strong> means the tester cannot see the code. Judgement
comes only from the requirements and the inputs and outputs. Anyone can do it:
a manual tester, a customer, an automated script written from the spec.</p>

<table>
<tr><th>Technique</th><th>How it works</th><th>Example (field: age, valid 18-120)</th></tr>
<tr><td>Equivalence partitioning</td><td>Split inputs into classes that should behave the same; test one from each</td><td>One case each: 17 (too young), 30 (valid), 121 (too old)</td></tr>
<tr><td>Boundary value analysis</td><td>Off-by-one bugs live on the edges, so test the edges and their neighbours</td><td>17, 18, 19, 119, 120, 121</td></tr>
<tr><td>Decision table</td><td>List every combination of conditions as rows</td><td>logged in x subscribed x premium -> expected outcome</td></tr>
<tr><td>State transition</td><td>Walk the states and the legal/illegal moves between them</td><td>order: new -&gt; paid -&gt; shipped; what about new -&gt; shipped?</td></tr>
<tr><td>Error guessing</td><td>Try what always breaks: empty string, 0, negative, huge, SQL quotes, emoji, null</td><td>age = -1, age = 999999999, age = "twenty"</td></tr>
<tr><td>Use case / exploratory</td><td>Script a realistic user goal, then improvise around it</td><td>Register, add card, buy, refund, buy again</td></tr>
</table>

<pre># Black-box in code: no knowledge of internals, only the contract.
def test_age_boundaries():
    assert validate_age(18) is True     # just inside
    assert validate_age(17) is False    # just outside
    assert validate_age(120) is True
    assert validate_age(121) is False
</pre>

<h2>9. White-Box Testing - Testing From The Inside</h2>

<p><strong>White box</strong> (glass box / structural) means you can see the
source, and you design tests to execute its paths. The tester is usually the
developer.</p>

<table>
<tr><th>Coverage type</th><th>Question it answers</th><th>Example where it catches a gap</th></tr>
<tr><td>Statement</td><td>Did every line run?</td><td>An error branch never entered</td></tr>
<tr><td>Branch</td><td>Did both outcomes of every if/else run?</td><td><code>if user: ... else: ...</code> - the else never tested</td></tr>
<tr><td>Path</td><td>Did every route through the function run?</td><td>Combination of two conditions never exercised together</td></tr>
<tr><td>Condition</td><td>Did each sub-condition get true and false?</td><td><code>if a and b:</code> - only a=True, b=True tested</td></tr>
<tr><td>Cyclomatic complexity</td><td>How many independent paths exist? (decisions + 1)</td><td>A function with complexity 12 needs ~12 tests to cover it</td></tr>
</table>

<pre># White-box: the branch exists, so both sides must be tested.
def tax_for(price, is_member):
    if is_member and price &gt; 100:      # two conditions, one branch
        return price * 0.05
    return price * 0.10

# Covering branch (both outcomes) implies:
assert tax_for(200, True)  == 10.0
assert tax_for(50,  True)  == 5.0
assert tax_for(200, False) == 20.0
</pre>

<table>
<tr><th></th><th>Black box</th><th>White box</th></tr>
<tr><td>Sees the code?</td><td>No</td><td>Yes</td></tr>
<tr><td>Designed from</td><td>Requirements, specification</td><td>Source, control flow, branches</td></tr>
<tr><td>Who does it</td><td>QA, customers, anyone</td><td>Developers</td></tr>
<tr><td>Best at</td><td>Missing features, wrong behaviour, usability</td><td>Untested branches, dead code, complexity</td></tr>
<tr><td>Blind spot</td><td>Cannot know which paths were never written</td><td>Assumes the code is the spec - it may be wrong</td></tr>
</table>

<p><strong>Memory trick:</strong> black box asks "is the <em>right</em>
software built?" white box asks "is the software <em>built right</em>?" You
need both.</p>

<h2>10. Coverage - What It Measures And What It Does Not</h2>

<pre>pytest --cov=app --cov-report=term-missing
# Name       Stmts   Miss  Cover   Missing
# app/orders.py    80      6    92%   41-46
</pre>

<ul>
<li>Coverage counts lines executed, not correctness. 100% coverage with
dumb assertions proves nothing.</li>
<li>Treat it as a <em>gap detector</em>: read the missing lines and ask why
they are untested.</li>
<li>Branch coverage is a better target than line coverage.</li>
<li>A practical gate for most teams: 80% overall, 100% on money, auth and
other critical paths.</li>
</ul>

<h2>11. TDD, BDD And The Pipeline</h2>

<pre>Red     - write a test that fails (you have not written the code yet)
Green   - write the smallest code that makes it pass
Refactor- improve the code, tests stay green
Repeat  - one behaviour per cycle, minutes not hours
</pre>

<p><strong>BDD</strong> (behaviour-driven development) writes the same idea in
plain language: <code>Given a logged-in user, When they click Buy, Then an
order is created</code>. The sentence becomes an automated test, so business
and code stay in the same document.</p>

<table>
<tr><th>Pipeline stage</th><th>Runs</th><th>Gate</th></tr>
<tr><td>Pre-commit hook</td><td>Lint, format, fast unit tests</td><td>Cannot commit broken code</td></tr>
<tr><td>Pull request</td><td>All unit + integration tests, coverage, SAST</td><td>Review blocked until green</td></tr>
<tr><td>Merge / main</td><td>Full suite + a few E2E journeys</td><td>Deploy blocked until green</td></tr>
<tr><td>Nightly</td><td>Slow E2E, load tests, full regression</td><td>Failure opens a ticket</td></tr>
<tr><td>Pre-release</td><td>Smoke + acceptance + UAT sign-off</td><td>Release blocked until green</td></tr>
<tr><td>Post-deploy</td><td>Smoke test against production</td><td>Automatic rollback on failure</td></tr>
</table>

<h2>12. A/B Testing - Experiments On Real Users</h2>

<p>Unit tests tell you whether the code works. <strong>A/B testing</strong>
tells you which version works <em>better for humans</em>: split users at
random into A (control) and B (variant), measure the same metric on both,
and keep the winner.</p>

<table>
<tr><th>Step</th><th>What you do</th><th>Classic mistake</th></tr>
<tr><td>1. Hypothesis</td><td>"Changing the button to green will raise clicks"</td><td>Running a test with no stated hypothesis</td></tr>
<tr><td>2. Metric</td><td>One primary metric (click-through, conversion) + guardrails (latency, refunds)</td><td>Choosing the metric after seeing results</td></tr>
<tr><td>3. Randomisation</td><td>Assign users randomly, 50/50, sticky per user</td><td>Re-randomising per page view, splitting a team</td></tr>
<tr><td>4. Sample size</td><td>Decide up front how many users you need (power analysis)</td><td>Stopping as soon as it looks good</td></tr>
<tr><td>5. Significance</td><td>Run a full business cycle (a week, incl. weekends); check p &lt; 0.05 or a confidence interval excluding zero</td><td>Peeking daily and stopping early - this inflates false positives</td></tr>
<tr><td>6. Decide</td><td>Ship, iterate, or kill; document the result</td><td>Shipping variant B because the CEO prefers it</td></tr>
</table>

<pre>import math

def ab_summary(visitors_a, conversions_a, visitors_b, conversions_b):
    pa, pb = conversions_a / visitors_a, conversions_b / visitors_b
    pooled = (conversions_a + conversions_b) / (visitors_a + visitors_b)
    # Standard error of the difference between two proportions.
    se = math.sqrt(pooled * (1 - pooled) * (1/visitors_a + 1/visitors_b))
    z = (pb - pa) / se if se else 0
    lift = (pb - pa) / pa * 100 if pa else float("inf")
    return {"control": pa, "variant": pb, "lift_pct": lift, "z": z}

# |z| &gt; 1.96 means the difference is significant at 95% confidence.
print(ab_summary(10_000, 320, 10_000, 372))
</pre>

<p><strong>Memory trick:</strong> an A/B test is a <em>measurement</em>, not a
vote. Decide the metric and duration before you look, and never peek-and-stop.</p>

<h2>13. Non-Functional Tests</h2>

<table>
<tr><th>Kind</th><th>Question</th><th>Tools</th></tr>
<tr><td>Performance / load</td><td>How many users before it falls over?</td><td>k6, JMeter, Locust,wrk</td></tr>
<tr><td>Security</td><td>Can an attacker make it do the wrong thing?</td><td>SAST: bandit - DAST: OWASP ZAP</td></tr>
<tr><td>Accessibility</td><td>Can a screen-reader user complete the task?</td><td>axe, Lighthouse</td></tr>
<tr><td>Resilience / chaos</td><td>What happens when a dependency dies?</td><td>Chaos Monkey, toxiproxy</td></tr>
<tr><td>Usability</td><td>Can a human figure it out without instructions?</td><td>Five users, one moderator</td></tr>
</table>

<h2>14. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Tests you write</td><td>A few happy paths</td><td>Happy paths + boundaries + every past bug</td></tr>
<tr><td>Speed</td><td>Run them by hand</td><td>Automated in seconds on every push</td></tr>
<tr><td>Fakes</td><td>Mock everything, tests are trivial</td><td>Fake only the slow/unstable edges; test the real database</td></tr>
<tr><td>Coverage</td><td>Not measured</td><td>Reported, gated on critical paths</td></tr>
<tr><td>Flaky tests</td><td>Re-run until green</td><td>Quarantined and fixed - a flaky test is treated as a broken build</td></tr>
<tr><td>Manual QA</td><td>You click around</td><td>Exploratory testing for what scripts cannot express; scripts own the rest</td></tr>
<tr><td>A/B tests</td><td>Not applicable</td><td>Hypothesis, metric, sample size and significance decided up front</td></tr>
</table>

<h2>15. Key Takeaways</h2>
<ul>
<li>Unit, Integration, System, Acceptance - write and run them in that
order; stop the pipeline at the first red stage.</li>
<li>Regression testing turns every bug fix into a permanent test. A bug
fixed without a test is a bug on parole.</li>
<li>Black box tests the specification; white box tests the code. Both are
necessary.</li>
<li>Coverage finds gaps; it does not prove correctness.</li>
<li>A/B testing is a controlled experiment: hypothesis, metric, random
assignment, sample size, significance - in that order.</li>
<li>Keep the pyramid wide at the bottom; end-to-end tests are the slowest
and the most brittle.</li>
</ul>

<p><strong>Exercise:</strong> take any function you have written and add one
equivalence-partition test, one boundary-value test and one branch-coverage
test. Run pytest -not -v and count how many lines the new tests uncovered.</p>
"""