"""Chapter 8 - Software engineering essentials for a beginner."""

CHAPTER = """<h2>1. What Software Engineering Actually Means</h2>

<p>Writing code that works once is easy. Writing code that still works in six
months, after four other people have edited it, is engineering. Engineering is
about making code cheap to change.</p>

<h2>2. The Four Pillars</h2>

<table>
<tr><th>Pillar</th><th>Question it answers</th><th>Practical meaning</th></tr>
<tr><td>Readability</td><td>Can a stranger understand it?</td><td>Clear names, small functions, consistent structure</td></tr>
<tr><td>Reliability</td><td>Does it do what it promises?</td><td>Tests, error handling, safe defaults</td></tr>
<tr><td>Efficiency</td><td>Is it fast and cheap to run?</td><td>Right data structures, sensible queries, caching</td></tr>
<tr><td>Maintainability</td><td>Can it be changed safely?</td><td>Version control, small diffs, automation</td></tr>
</table>

<p><strong>Memory trick:</strong> code is written to be read, by someone who has
never met you. Optimise for the reader.</p>

<h2>3. The Four Pillars of OOP</h2>

<table>
<tr><th>Pillar</th><th>Meaning</th><th>Example</th></tr>
<tr><td>Encapsulation</td><td>Hide internal state, expose behaviour</td><td>A BankAccount with deposit() rather than a public balance field</td></tr>
<tr><td>Abstraction</td><td>Show what, hide how</td><td>A PaymentProcessor interface, not the payment API calls</td></tr>
<tr><td>Inheritance</td><td>Reuse by extending</td><td>AdminUser extends User. Use sparingly, it couples tightly</td></tr>
<tr><td>Polymorphism</td><td>One name, many behaviours</td><td>Different payment types behind one call</td></tr>
</table>

<h2>4. SOLID - The Five Rules</h2>

<table>
<tr><th>Letter</th><th>Name</th><th>Meaning</th><th>Smell it fixes</th></tr>
<tr><td>S</td><td>Single responsibility</td><td>One reason to change</td><td>A class that both validates and emails</td></tr>
<tr><td>O</td><td>Open, closed</td><td>Open to extension, closed to modification</td><td>A chain of if-else that grows forever</td></tr>
<tr><td>L</td><td>Liskov substitution</td><td>Subtypes must be usable as the parent</td><td>A subclass that throws when used normally</td></tr>
<tr><td>I</td><td>Interface segregation</td><td>Small interfaces beat one huge one</td><td>A class forced to implement methods it never uses</td></tr>
<tr><td>D</td><td>Dependency inversion</td><td>Depend on abstractions, not concrete classes</td><td>Hard to test because you cannot swap the dependency</td></tr>
</table>

<p><strong>Memory trick:</strong> read the letters as a phrase: "Super
Superior, Superior, Leave, Interface, Dependency". Concretely, remember: one job
per class, extend rather than edit, and depend on interfaces.</p>

<h2>5. Common Design Patterns</h2>

<table>
<tr><th>Pattern</th><th>Problem it solves</th><th>Real example</th></tr>
<tr><td>Singleton</td><td>Exactly one instance</td><td>A database connection pool, a logger</td></tr>
<tr><td>Factory</td><td>Creating objects of the right type</td><td>Choosing a payment provider by country</td></tr>
<tr><td>Strategy</td><td>Swappable algorithm</td><td>Sorting by name, date or price</td></tr>
<tr><td>Observer</td><td>Notify many when one changes</td><td>Event listeners, webhooks, pub/sub</td></tr>
<tr><td>Repository</td><td>Hide database access</td><td>UserRepository so services never write SQL</td></tr>
<tr><td>Adapter</td><td>Make incompatible things work</td><td>Wrapping a third-party payment SDK</td></tr>
</table>

<p><strong>Do not over-apply them.</strong> A pattern that makes the code harder
to read than the problem it solved is a mistake.</p>

<h2>6. Data Structures You Must Know</h2>

<table>
<tr><th>Structure</th><th>What it is for</th><th>Lookup speed</th></tr>
<tr><td>Array or list</td><td>Ordered items, fast iteration</td><td>Index O(1), search O(n)</td></tr>
<tr><td>Dictionary or map</td><td>Key to value lookup</td><td>Get and set O(1)</td></tr>
<tr><td>Set</td><td>Unique items, fast membership</td><td>Contains O(1)</td></tr>
<tr><td>Stack</td><td>Last in, first out</td><td>O(1)</td></tr>
<tr><td>Queue</td><td>First in, first out</td><td>O(1)</td></tr>
<tr><td>Tree</td><td>Hierarchies and ordered ranges</td><td>O(log n)</td></tr>
<tr><td>Graph</td><td>Relationships between things</td><td>Varies</td></tr>
</table>

<p><strong>Memory trick:</strong> if you are always scanning a list to find
something, you probably wanted a dictionary.</p>

<h2>7. The N+1 Query Problem</h2>

<p>You fetch a list of 100 users, then loop over them and fetch each one's
orders. That is 101 queries instead of 1. It is the most common performance bug
in real applications and it hides easily in development because the data set is
tiny.</p>

<pre># Bad: 1 + N queries
for user in users:
    user.orders = db.query("SELECT * FROM orders WHERE user_id = ?", user.id)

# Good: 1 query with a join
users = db.query("SELECT * FROM users")
orders = db.query("SELECT * FROM orders WHERE user_id IN (...)")
# attach in memory</pre>

<h2>8. REST and API Design</h2>

<p>REST designs APIs around resources, not around actions. The HTTP method
expresses the action.</p>

<pre>GET    /users        list users
GET    /users/1      get one user
POST   /users        create a user
PUT    /users/1      replace a user
PATCH  /users/1      update part of a user
DELETE /users/1      delete a user</pre>

<p><strong>Memory trick:</strong> the URL names the noun, the HTTP method names
the verb. Never put a verb in the URL such as <code>/getUser</code>.</p>

<h2>9. Authentication vs Authorization</h2>

<table>
<tr><th>Concept</th><th>Question it answers</th><th>Common methods</th></tr>
<tr><td>Authentication</td><td>Who are you?</td><td>Passwords, MFA, OAuth 2.0, OIDC, SAML</td></tr>
<tr><td>Authorization</td><td>What may you do?</td><td>RBAC roles, ABAC policies, ACLs</td></tr>
<tr><td>Encryption in transit</td><td>Is the wire safe?</td><td>TLS</td></tr>
<tr><td>Encryption at rest</td><td>Is the disk safe?</td><td>Disk encryption, encrypted volumes</td></tr>
</table>

<p><strong>Memory trick:</strong> authentication is the bouncer checking your ID.
Authorization is the bouncer deciding which rooms you may enter.</p>

<h2>10. Testing</h2>

<table>
<tr><th>Level</th><th>Scope</th><th>Speed</th><th>Catches</th></tr>
<tr><td>Unit test</td><td>One function or class</td><td>Milliseconds</td><td>Logic mistakes</td></tr>
<tr><td>Integration test</td><td>Several parts together</td><td>Seconds</td><td>Wiring and config problems</td></tr>
<tr><td>End-to-end test</td><td>The whole system as a user</td><td>Minutes</td><td>Broken user journeys</td></tr>
</table>

<p>Test behaviour, not implementation. A test that breaks whenever you rename a
private helper is a test of the wrong thing.</p>

<h2>11. Layered Architecture</h2>
<pre>Presentation (UI)  ->  Service (business logic)  ->  Repository (data access)
        HTTP layer             domain rules                 SQL and queries</pre>

<p>Each layer only talks to the one below it. This is why you can swap the
database without touching the UI.</p>

<h2>12. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Code style</td><td>Whatever runs</td><td>Linters, formatters and hooks in CI</td></tr>
<tr><td>Tests</td><td>A few happy paths</td><td>Coverage targets, integration tests, flake detection</td></tr>
<tr><td>Errors</td><td>Print and move on</td><td>Structured logging, error tracking, retries with backoff</td></tr>
<tr><td>Secrets</td><td>In a .env file that is committed</td><td>Secret manager, rotated, never in git</td></tr>
<tr><td>Deploys</td><td>Manual, whenever</td><td>Automated pipelines with rollback</td></tr>
<tr><td>Database</td><td>Migrations run by hand</td><td>Versioned migrations gated in the pipeline</td></tr>
<tr><td>Reviews</td><td>Nobody checks</td><td>Peer review, branch protection, CODEOWNERS</td></tr>
</table>

<h2>13. Key Takeaways</h2>
<ul>
<li>Write code for the person who reads it later, which is usually not you.</li>
<li>SOLID keeps classes small and dependencies replaceable.</li>
<li>Design patterns are tools, not a goal.</li>
<li>The N+1 problem is the most common hidden performance bug.</li>
<li>URLs name nouns; HTTP methods are the verbs.</li>
<li>Authentication is who you are; authorization is what you may do.</li>
</ul>
"""