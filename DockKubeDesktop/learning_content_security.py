"""Chapter - Security Testing: what to test, when, and what belongs in CI/CD."""

CHAPTER = """<h2>1. What Is Security Testing?</h2>

<p>Security testing is the part of quality work that asks a different question
from every other test. A functional test asks <em>does it do the right thing?</em>
Security testing asks <em>can someone make it do the wrong thing on purpose?</em></p>

<p>Anyone can use your software, including people who did not buy it and do not
want to help you. Security testing is how you find their moves before they do.</p>

<p><strong>Memory trick:</strong> you are not looking for bugs that break the
system. You are looking for bugs that let an attacker <em>use</em> the system for
something other than what it is for.</p>

<h2>2. The Four Kinds of Security Testing</h2>

<table>
<tr><th>Type</th><th>What it inspects</th><th>Needs the app running?</th><th>Typical name</th></tr>
<tr><td>Static (SAST)</td><td>The source code, without running it</td><td>No</td><td>bandit, semgrep, CodeQL</td></tr>
<tr><td>Dynamic (DAST)</td><td>A running application, from the outside</td><td>Yes</td><td>OWASP ZAP, Burp</td></tr>
<tr><td>Dependency (SCA)</td><td>The libraries you imported</td><td>No</td><td>pip-audit, npm audit, trivy</td></tr>
<tr><td>Interactive (IAST)</td><td>Running code, instrumented as it executes</td><td>Yes</td><td>SonarQube</td></tr>
</table>

<p>SAST is fast and finds coding mistakes. DAST finds what an attacker would
actually reach. SCA is the one teams forget, and it is the one that produces the
most real incidents, because most of your code was written by other people.</p>

<h2>3. What Tests Commonly Run</h2>

<table>
<tr><th>Test</th><th>What it finds</th><th>Phase</th></tr>
<tr><td>Code review</td><td>Logic errors, secrets in commits, bad design</td><td>Every change</td></tr>
<tr><td>SAST scan</td><td>SQL injection in code, hardcoded credentials, weak crypto</td><td>Every commit</td></tr>
<tr><td>Secret scanning</td><td>API keys and passwords committed by accident</td><td>Every commit</td></tr>
<tr><td>Dependency audit</td><td>Known CVEs in imported packages</td><td>Every build</td></tr>
<tr><td>Container image scan</td><td>CVEs baked into the image, plus bad base images</td><td>Before deploy</td></tr>
<tr><td>Unit security tests</td><td>Your own auth and validation logic, verified as code</td><td>Every commit</td></tr>
<tr><td>DAST scan</td><td>Live vulnerabilities in a staging deployment</td><td>Nightly</td></tr>
<tr><td>API fuzzing</td><td>Unexpected input that crashes or bypasses logic</td><td>Nightly</td></tr>
<tr><td>Infrastructure scan</td><td>Open ports, misconfigured storage, weak IAM</td><td>Weekly</td></tr>
<tr><td>Penetration test</td><td>A real attacker working against you on purpose</td><td>Before launch</td></tr>
</table>

<h2>4. The OWASP Top 10</h2>

<p>Almost every web security test on that list exists to check one of these.
Learn these ten by name and you can talk about application security properly:</p>

<table>
<tr><th>Risk</th><th>Plain meaning</th></tr>
<tr><td>Broken access control</td><td>Users can reach things that are not theirs. The number one real-world web flaw.</td></tr>
<tr><td>Cryptographic failures</td><td>Sensitive data sent or stored unprotected.</td></tr>
<tr><td>Injection</td><td>User input treated as code. SQL injection is the classic.</td></tr>
<tr><td>Insecure design</td><td>Missing a control entirely. No scanner can find this one.</td></tr>
<tr><td>Misconfiguration</td><td>Defaults left on, directories browsable, debug mode on.</td></tr>
<tr><td>Vulnerable components</td><td>Using a library with a known CVE.</td></tr>
<tr><td>Authentication failures</td><td>Weak login, missing MFA, sessions that never expire.</td></tr>
<tr><td>Software and data integrity</td><td>Trusting updates or files that were never verified.</td></tr>
<tr><td>Logging and monitoring gaps</td><td>The attack happened, and nobody noticed.</td></tr>
<tr><td>Server-side request forgery</td><td>Tricking your server into fetching a URL you should not reach.</td></tr>
</table>

<p><strong>Memory trick:</strong> the first one is the one that actually gets
companies breached. Broken access control means someone changes an ID in a URL
and sees someone else's data.</p>

<h2>5. Which Phase Each Test Belongs To</h2>

<p>Security is cheapest when it happens early and most expensive when it happens
late. That is why the SDLC needs a security activity at every stage, not one
big audit before launch.</p>

<table>
<tr><th>SDLC phase</th><th>Security activity</th><th>Catches</th></tr>
<tr><td>Requirements</td><td>Threat modelling. What are we building, and how would someone attack it?</td><td>Design flaws, impossible to fix cheaply later</td></tr>
<tr><td>Design</td><td>Review the data flow. Where does sensitive data go and who may see it?</td><td>Missing authorisation, unsafe storage choices</td></tr>
<tr><td>Development</td><td>Secure coding rules, peer review, SAST in the editor</td><td>Injection, hardcoded secrets, bad validation</td></tr>
<tr><td>Testing</td><td>Security test cases written alongside functional ones</td><td>Logic flaws the happy path never touches</td></tr>
<tr><td>Staging</td><td>DAST against the deployed candidate</td><td>Misconfiguration and real attack paths</td></tr>
<tr><td>Release</td><td>Dependency and image scanning, penetration test</td><td>Known CVEs shipped to production</td></tr>
<tr><td>Production</td><td>Monitoring, patching, periodic rescanning</td><td>Newly disclosed vulnerabilities</td></tr>
</table>

<p><strong>Memory trick:</strong> the earlier the phase, the cheaper the fix.
A flaw found in requirements is a paragraph change. The same flaw found in
production is an incident, a page, and an apology.</p>

<h2>6. What Should Run In The CI/CD Build?</h2>

<p>A build gate has to be fast and automatic, or engineers will route around it.
That rules out anything needing a running application or a human judgement call,
and leaves four checks that belong on every single commit.</p>

<pre># 1. Secrets: instant, and a leaked key is an incident, not a bug
gitleaks detect --source .

# 2. Static analysis: reads the code, needs nothing running
bandit -r src
semgrep --config auto .

# 3. Dependencies: catches the CVEs you did not write yourself
pip-audit -r requirements.txt
npm audit

# 4. Container image, once the image exists
trivy image --severity HIGH,CRITICAL --exit-code 1 myapp:1.0</pre>

<p>Note the <code>--exit-code 1</code> on the last one. Without it the scan runs,
prints a scary table, and the build goes green anyway. A scanner that cannot
fail a build is decoration.</p>

<h2>7. Writing A Pipeline Gate</h2>

<pre>name: Security
on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Secret scanning
        uses: gitleaks/gitleaks-action@v2
      - name: Static analysis
        run: |
          pip install bandit
          bandit -r . -ll          # -ll only reports medium and up
      - name: Dependencies
        run: pip install pip-audit &amp;&amp; pip-audit -r requirements.txt
      - name: Build and scan the image
        run: |
          docker build -t myapp:${{ github.sha }} .
          trivy image --exit-code 1 --severity HIGH,CRITICAL myapp:${{ github.sha }}</pre>

<p>The Secrets and Dependency steps are fast enough to run on every push. A full
DAST scan takes minutes and needs a deployed environment, so put that on a
schedule instead, where a failure reaches a human who is awake.</p>

<h2>8. Choosing A Severity Policy</h2>

<p>Blocking a build on <em>every</em> finding trains people to ignore the gate, so
decide in advance what actually stops you:</p>

<table>
<tr><th>Severity</th><th>Policy</th><th>Why</th></tr>
<tr><td>Critical</td><td>Block the build, always</td><td>Actively exploited or trivially remote</td></tr>
<tr><td>High</td><td>Block, with a 7-day exception process</td><td>Usually real, sometimes a false positive</td></tr>
<tr><td>Medium</td><td>Ticket, never block</td><td>Needs context you do not have at build time</td></tr>
<tr><td>Low</td><td>Report only</td><td>Noise; useful for trend charts</td></tr>
</table>

<p>Exceptions need an expiry date and a named owner. An exception with no expiry
is a vulnerability you decided to keep.</p>

<h2>9. Common Mistakes</h2>

<table>
<tr><th>Mistake</th><th>Why it is bad</th></tr>
<tr><td>Scanning only on release</td><td>A hundred commits accumulate before anyone looks</td></tr>
<tr><td>No failing exit code</td><td>The scan runs, nobody blocks anything</td></tr>
<tr><td>Ignoring the false positives</td><td>The gate gets muted, and real findings go with it</td></tr>
<tr><td>Only scanning code</td><td>Misconfiguration breaches beat code bugs in the real world</td></tr>
<tr><td>No severity policy</td><td>Everyone argues about severity instead of fixing things</td></tr>
<tr><td>Scanning other people's systems</td><td>Illegal in most countries. Always get written permission.</td></tr>
</table>

<p><strong>Try it yourself:</strong> run <code>gitleaks detect</code> over a
repository you own. Almost everyone finds a leftover key in their history the
first time, which is exactly why it belongs in CI rather than in a checklist.</p>

<p><strong>Learning vs production:</strong> a scan of your laptop catches what a
scanner can see. Real attackers chain a small misconfiguration with a leaked key
and a weak password policy, and no single tool reports the chain. Automated
scanning raises the floor; it does not replace thinking, or a real penetration
test before something important launches.</p>
"""