"""Chapter - Business logic: how shops, SaaS and companies actually work."""

CHAPTER = """<h2>1. What Is Business Logic?</h2>

<p>Business logic is the part of an application that knows how the business works,
as opposed to how the computer works. It is the rules, not the plumbing.</p>

<p>Displaying a page, talking to a database and rendering HTML are all technical.
Deciding that an order over 50 pounds needs a signature, that a refund is only
allowed within 30 days, or that an invoice becomes overdue after 14 days, is
business logic.</p>

<p><strong>Memory trick:</strong> business logic is the part that would still make
sense if you rewrote the whole system in a different language. If it changes
because of a framework, it is plumbing, not business.</p>

<h2>2. The Vocabulary Of A Shop</h2>

<table>
<tr><th>Term</th><th>What it actually is</th></tr>
<tr><td>SKU</td><td>One specific product, one size, one colour. The thing with a barcode.</td></tr>
<tr><td>Product</td><td>A group of related SKUs, like "T-shirt, size large, blue"</td></tr>
<tr><td>Variant</td><td>One combination within a product</td></tr>
<tr><td>Inventory</td><td>How many units of each SKU are in stock</td></tr>
<tr><td>Cart</td><td>What the customer intends to buy. Not yet an order.</td></tr>
<tr><td>Basket or order</td><td>What the customer committed to buy</td></tr>
<tr><td>Line item</td><td>One row on an order: product, quantity, price at that moment</td></tr>
<tr><td>Checkout</td><td>Turning a basket into an order plus a payment</td></tr>
<tr><td>Fulfilment</td><td>Picking, packing and shipping</td></tr>
<tr><td>Receipt</td><td>Proof of purchase for the customer</td></tr>
<tr><td>Invoice</td><td>A request for payment, usually for B2B, often with payment terms</td></tr>
<tr><td>Refund</td><td>Money returned, usually as a new transaction</td></tr>
<tr><td>Return</td><td>The physical goods coming back</td></tr>
<tr><td>Discount</td><td>A reduction applied before payment</td></tr>
<tr><td>Tax or VAT</td><td>Calculated by law, often item by item</td></tr>
<tr><td>Margin</td><td>Price minus cost. Not the same as revenue.</td></tr>
</table>

<p><strong>Memory trick:</strong> a receipt and an invoice are different documents
with different jobs. A receipt says "this already happened". An invoice says "please
pay this". Confusing them creates real disputes.</p>

<h2>3. How A Purchase Actually Works</h2>

<p>The full journey, and every step is a place where software gets it wrong.</p>

<pre>1. Customer adds items to a basket       (reserved, with an expiry)
2. Prices are re-checked at checkout      (never trust the cart's stored price)
3. Stock is reserved                       (so two people cannot buy the last one)
4. Payment is authorised
5. Order and payment are recorded        (in ONE database transaction)
6. Stock is decremented
7. Receipt is issued, confirmation emailed
8. Later: the payment is captured or settled
9. Much later: the customer may return it  (a refund, which is a NEW transaction)</pre>

<p>Steps 4 and 5 are where everything goes wrong. If the payment succeeds and the
database write fails, the customer has been charged for an order that does not
exist. That is why step 5 is wrapped in a transaction and why reconciliation
between your ledger and the payment provider exists at all.</p>

<p><strong>Memory trick:</strong> never take money without being able to prove what
it was for. An unrecorded payment is money you have to give back.</p>

<h2>4. Inventory - Why It Is Harder Than It Looks</h2>

<table>
<tr><th>Problem</th><th>What goes wrong</th><th>The fix</th></tr>
<tr><td>Overselling</td><td>Two customers buy the last unit</td><td>Reserve stock when the basket is created</td></tr>
<tr><td>Price changes</td><td>Basket showed last week's price</td><td>Re-price at checkout, tell the customer</td></tr>
<tr><td>Partial refunds</td><td>Someone returns one of five items</td><td>Refund per line, against the amount charged</td></tr>
<tr><td>Concurrent orders</td><td>Two threads both read stock as 1</td><td>An atomic decrement, not read-then-write</td></tr>
<tr><td>Stock arrives late</td><td>Customer was told two weeks</td><td>Backorders and partial dispatch</td></tr>
</table>

<pre>-- Not safe: two transactions can both read 1 and both decrement
SELECT quantity FROM stock WHERE sku = 'ABC'   -- reads 1
UPDATE stock SET quantity = quantity - 1        -- both write 0, both sold

-- Safe: the database guarantees only one can win
UPDATE stock SET quantity = quantity - 1
WHERE sku = 'ABC' AND quantity &gt; 0;   -- check the affected row count</pre>

<p><strong>Memory trick:</strong> never trust a number you read a moment ago.
Check that your write actually changed something.</p>

<h2>5. Receipts, Invoices And Reports</h2>

<p>Three documents that get confused constantly:</p>

<table>
<tr><th></th><th>Receipt</th><th>Invoice</th><th>Report</th></tr>
<tr><td>Means</td><td>Proof the customer already paid</td><td>A request that they pay</td><td>Information, no money moves</td></tr>
<tr><td>When</td><td>Immediately after payment</td><td>Before or after, by agreement</td><td>Any time</td></tr>
<tr><td>Who sees it</td><td>The customer</td><td>The customer</td><td>Staff, managers, accountants</td></tr>
<tr><td>Contains</td><td>Items, tax, payment method, total</td><td>Same, plus payment terms and due date</td><td>Aggregates over time</td></tr>
<tr><td>Legally</td><td>Evidence of sale</td><td>A demand for payment</td><td>Internal, usually</td></tr>
</table>

<p>And money has three kinds, which is the part most people have never been told:</p>

<ul>
<li><strong>Revenue</strong> is what you sold, ignoring what it cost you.</li>
<li><strong>Gross margin</strong> is revenue minus the direct cost of what you sold.</li>
<li><strong>Profit</strong> is what remains after every cost, including rent and salaries.</li>
</ul>

<p>A shop can have falling revenue and still be profitable, because its costs fell
faster. This is why "revenue" and "profit" are tracked separately.</p>

<p><strong>Memory trick:</strong> revenue is the top of the funnel, profit is the
bottom. Only the second one pays anyone.</p>

<h2>6. How A Point Of Sale Works</h2>

<p>POS is the software at the till, and it is a full accounting system that happens
to take payments.</p>

<ul>
<li><strong>Basket and pricing</strong> - scan, apply promotions, calculate tax per item.</li>
<li><strong>Tendering</strong> - take card, cash, or split payment across several methods.</li>
<li><strong>Cash drawer</strong> - opening float, cash drops, and the shift report that
must balance at close.</li>
<li><strong>Offline mode</strong> - a shop must still sell when the network is down.</li>
<li><strong>Receipts and returns</strong> - exchange something bought last Tuesday.</li>
</ul>

<p>Offline mode is where most POS systems are genuinely hard. A payment approved
offline has to be captured later, and if the card was declined in the meantime
the shop has sold something for money it will not receive.</p>

<p><strong>Memory trick:</strong> a till is not a calculator with a card reader. It
is a cash control system that has to reconcile at the end of every shift.</p>

<h2>7. How SaaS Works</h2>

<p>Software as a service is a different business from a shop, and the differences
are structural rather than cosmetic.</p>

<table>
<tr><th></th><th>Retail</th><th>SaaS</th></tr>
<tr><td>Revenue from</td><td>Each sale once</td><td>A subscription, every month</td></tr>
<tr><td>What you sell</td><td>A thing, delivered</td><td>Continued access to something</td></tr>
<tr><td>Cancellation</td><td>Not applicable</td><td>The biggest cause of churn</td></tr>
<tr><td>Growth measured by</td><td>Sales this month</td><td>New customers and retained customers</td></tr>
<tr><td>Marginal cost</td><td>Real cost per item</td><td>Near zero, once built</td></tr>
<tr><td>Key metric</td><td>Gross margin</td><td>MRR, churn rate, lifetime value</td></tr>
</table>

<pre>Monthly Recurring Revenue  = sum of monthly subscription fees
Churn rate                = customers who left this month / customers at the start
Lifetime Value            = (monthly fee / churn rate), roughly
Payback period            = how long until a customer repaid their acquisition cost</pre>

<p>A subscription business is judged almost entirely on whether existing customers
stay. Making that number go up is worth far more than making it twice as big.</p>

<p><strong>Memory trick:</strong> in retail, acquisition wins. In SaaS, retention
wins, because a customer who stays pays you forever.</p>

<h2>8. How A Company Actually Works</h2>

<p>Most engineers find this genuinely surprising, so it is worth stating plainly.</p>

<table>
<tr><th>Function</th><th>What it does</th><th>Why a tech team cares</th></tr>
<tr><td>Finance</td><td>Budgets, forecasting, invoices, payroll, tax</td><td>Signs off every purchase over a limit</td></tr>
<tr><td>Legal</td><td>Contracts, privacy, terms, licences</td><td>Reviews data processing agreements</td></tr>
<tr><td>Sales</td><td>Finds customers, negotiates, brings revenue in</td><td>Sets the promises engineering must keep</td></tr>
<tr><td>Support</td><td>Answers customers after they buy</td><td>Where reliability problems show up first</td></tr>
<tr><td>People</td><td>Hiring, performance, culture</td><td>Turnover destroys tacit knowledge</td></tr>
<tr><td>Operations</td><td>How the business actually delivers</td><td>Turns into process, then into software</td></tr>
</table>

<p>The sequence that surprises people: what a customer is <em>promised</em> is
usually negotiated by sales, and engineering inherits it as a requirement. That is
why knowing who decides things is as useful as knowing the code.</p>

<h2>9. Authentication - Proving Who You Are</h2>

<table>
<tr><th>Concept</th><th>Means</th></tr>
<tr><td>Authentication</td><td>Proving who you are. "Are you really Alice?"</td></tr>
<tr><td>Authorisation</td><td>What you may do. "Alice is an admin, so she may delete users."</td></tr>
<tr><td>Password hashing</td><td>Storing a slow one-way hash, never the password itself</td></tr>
<tr><td>Salt</td><td>A random value per password, so identical passwords differ in storage</td></tr>
<tr><td>Session</td><td>Server-side state proving the user logged in</td></tr>
<tr><td>JWT</td><td>A signed token carrying claims, with an expiry</td></tr>
<tr><td>MFA</td><td>A second factor: something you know, have, or are</td></tr>
<tr><td>SSO</td><td>One identity provider for many applications</td></tr>
<tr><td>OAuth</td><td>Let a third party grant limited access without your password</td></tr>
<tr><td>OpenID Connect</td><td>OAuth with an identity token, so the app knows who signed in</td></tr>
</table>

<p><strong>Memory trick:</strong> authentication is the door, authorisation is what
is inside the room. A locked door with no locks on the cupboards is still a
security problem, and that is the most common real-world flaw.</p>

<p>Sessions versus tokens: a session stores state on the server and the browser
holds an opaque id, so you can revoke it instantly. A JWT is self-contained and
verified without a database call, which is fast but cannot be revoked before it
expires. That single trade-off explains most authentication design decisions.</p>

<h2>10. CORS - Why The Browser Blocks Things</h2>

<p>CORS, the Cross-Origin Resource Sharing rules, exists for one reason: to stop
another website from using your logged-in session to send actions as you.</p>

<p>You open your bank in one tab and an attacker's page in another. Without CORS,
JavaScript on the attacker's page could quietly call your bank's API, and the
browser would attach your cookies, because it cannot tell your request from a
forged one.</p>

<pre>Access-Control-Allow-Origin: https://myapp.com
Access-Control-Allow-Methods: POST, GET
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true</pre>

<table>
<tr><th>Rule</th><th>Meaning</th></tr>
<tr><td>Same-origin</td><td>Same scheme, host and port. No CORS involved.</td></tr>
<tr><td>Simple request</td><td>GET, POST or HEAD with simple headers. Sent, then blocked on the reply.</td></tr>
<tr><td>Preflight</td><td>The browser asks permission with OPTIONS before the real request.</td></tr>
<tr><td>No wildcard with credentials</td><td>You cannot send cookies and allow every origin</td></tr>
<tr><td>CORS is not server security</td><td>Only browsers enforce it. A curl script ignores it entirely</td></tr>
</table>

<p><strong>Memory trick:</strong> CORS protects the <em>browser</em>, not your API.
Your server must still check authorisation on every request, because any program
can ignore CORS.</p>

<h2>11. CSRF - The Attack CORS Prevents</h2>

<p>Cross-site request forgery works because of how cookies behave. Cookies are sent
by the browser automatically to any matching domain, without the page's JavaScript
asking.</p>

<p>So if you are logged in to your bank, a page anywhere else can contain a form
that silently submits a transfer, and your browser will attach your session cookie
to it.</p>

<table>
<tr><th>Defence</th><th>How it works</th></tr>
<tr><td>SameSite cookies</td><td>The strongest and simplest fix: do not send the cookie on cross-site requests</td></tr>
<tr><td>CSRF token</td><td>A hidden random value per form, checked by the server against the session</td></tr>
<tr><td>Double submit cookie</td><td>Token in the form and in a cookie; the attacker can read neither to match them</td></tr>
<tr><td>Never use GET for changes</td><td>A GET can be triggered by an image tag, with no script at all</td></tr>
</table>

<pre>Set-Cookie: session=abc123; HttpOnly; Secure; SameSite=Lax</pre>

<p><strong>Memory trick:</strong> CSRF is about cookies being sent when you did not
intend it. SameSite cookies solve it by not sending them.</p>

<h2>12. The Rest Of The Web Security Vocabulary</h2>

<table>
<tr><th>Term</th><th>Means</th></tr>
<tr><td>XSS</td><td>Injecting script into a page the user views. Steals sessions.</td></tr>
<tr><td>SQL injection</td><td>User input treated as SQL code, letting an attacker read or change the database</td></tr>
<tr><td>Clickjacking</td><td>An invisible page layered over a button you meant to click</td></tr>
<tr><td>Open redirect</td><td>A login link that sends you to an attacker's site afterwards</td></tr>
<tr><td>SSL or TLS</td><td>Encrypting the connection. HTTPS is HTTP inside TLS.</td></tr>
<tr><td>HSTS</td><td>Telling browsers to refuse plain HTTP for your domain</td></tr>
<tr><td>Rate limiting</td><td>Capping requests per user or IP to stop brute force</td></tr>
<tr><td>Least privilege</td><td>Give the minimum access needed, and nothing more</td></tr>
<tr><td>Input validation</td><td>Never trust anything arriving from outside the system</td></tr>
</table>

<p><strong>Memory trick:</strong> most web vulnerabilities come from trusting input.
Validate at the edge, escape on output, and parameterise every query, and most of
this table stops applying to you.</p>

<h2>13. Common Rules Worth Knowing</h2>

<ul>
<li>An order is never stored by trusting the price the browser sent. Re-price it.</li>
<li>Stock is decremented atomically, never read then written.</li>
<li>Money is stored as an integer of minor units, never a float.</li>
<li>A refund is a new transaction, never a deletion or an edit of the original.</li>
<li>Every payment endpoint takes an idempotency key.</li>
<li>Every state-changing request is authorised on the server, every time.</li>
<li>Every cookie holding a session is HttpOnly, Secure and SameSite.</li>
</ul>

<p><strong>Try it yourself:</strong> take the shop journey above and write down the
database tables it needs. Basket, order, line item, product, inventory, payment,
refund and customer, plus the relationship between each. When you have done that,
most application design problems stop being mysterious.</p>

<p><strong>Learning vs production:</strong> a small shop runs a single till and one
database, and the rules above are enough. Production adds concurrency, multiple
tills, tax jurisdictions, partial refunds, chargebacks, payment retries,
reconciliation and an audit trail. The rules do not change; the number of ways they
can be violated does.</p>"""
