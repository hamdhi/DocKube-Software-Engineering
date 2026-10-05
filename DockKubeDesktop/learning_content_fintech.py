"""Chapter - FinTech: payments, ledgers, cards and financial regulation."""

CHAPTER = """<h2>1. What Is FinTech?</h2>

<p>FinTech is the business of using software to improve financial services, or to
provide a financial service that did not exist before. It ranges from a bank
moving its core system to the cloud, to a phone app that sends money abroad in
seconds.</p>

<p>What makes it different from ordinary software is not the technology. It is
that financial software moves other people's money, which means errors are
measured in other people's money too.</p>

<p><strong>Memory trick:</strong> in fintech, a rounding error is not a bug, it is
an incident. Everything else follows from taking that seriously.</p>

<h2>2. The Basic Vocabulary</h2>

<table>
<tr><th>Term</th><th>Means</th></tr>
<tr><td>Payment</td><td>Moving money from one party to another</td></tr>
<tr><td>Transaction</td><td>One recorded movement of money, with an id</td></tr>
<tr><td>Account</td><td>A balance belonging to an owner, that money moves between</td></tr>
<tr><td>Ledger</td><td>The authoritative record of every movement</td></tr>
<tr><td>Merchant</td><td>The business being paid</td></tr>
<tr><td>Acquirer</td><td>The bank that gives a merchant their card terminal</td></tr>
<tr><td>Issuer</td><td>The bank that issues a card to a customer</td></tr>
<tr><td>Scheme</td><td>The network connecting them: Visa, Mastercard</td></tr>
<tr><td>Processor</td><td>The middleman moving the message between them</td></tr>
<tr><td>Chargeback</td><td>A customer asking their bank to reverse a payment</td></tr>
<tr><td>Settlement</td><td>Moving the money for real, usually days after the sale</td></tr>
<tr><td>Clearing</td><td>Agreeing on which payments succeeded</td></tr>
</table>

<p><strong>Memory trick:</strong> authorisation is "may I?", capture is "did it
happen?", and settlement is "when does the money actually move?". Three
different moments that are routinely confused.</p>

<h2>3. How A Card Payment Actually Happens</h2>

<p>More people understand this than any other part of fintech, which makes it the
best place to start. A single contactless tap involves five organisations and two
days.</p>

<pre>1. Customer taps      -&gt; merchant terminal creates a payment request
2. Acquirer           -&gt; sends the card details to the scheme, encrypted
3. Scheme             -&gt; routes to the issuing bank
4. Issuer             -&gt; checks the PIN, balance, and fraud rules
                         -&gt; approves or declines, and returns the answer back up
5. Merchant           -&gt; gets an approval code and prints a receipt
6. HOURS OR DAYS LATER: the scheme clears the batch, and money moves</pre>

<p>Step 4 is the only part that can be refused, and the only part that happens in
under a second. Everything after is bookkeeping.</p>

<p><strong>Memory trick:</strong> the customer sees step 5 instantly. The money does
not move until step 6, which is why a shop can have taken payment and still not
been paid.</p>

<h3>Where the money actually sits</h3>
<p>The customer's bank pays the merchant's bank. At no point does money physically
move. What moves is an instruction and a ledger entry, and the balances change to
reflect it.</p>

<h2>4. Card Networks And Why There Is An Interchange Fee</h2>

<p>There are two sides to a card: the <strong>issuer</strong> that issued the card
to your customer, and the <strong>acquirer</strong> who signed up the merchant.
The scheme charges both, and the fee the acquirer pays the issuer is called
interchange.</p>

<p>It exists because the networks and banks built enormous acceptance
infrastructure worldwide, and somebody has to pay for it. It is also the single
largest cost in most small retail businesses, and the reason card fees are a
political issue in several countries.</p>

<table>
<tr><th>Term</th><th>Meaning</th></tr>
<tr><td>Scheme fee</td><td>What the network charges, often around 0.2 percent</td></tr>
<tr><td>Issuer fee</td><td>What the bank issuing the card charges, set by the regulator</td></tr>
<tr><td>Acquirer markup</td><td>What the merchant's bank adds on top</td></tr>
<tr><td>Chargeback fee</td><td>What the merchant pays when a customer disputes</td></tr>
</table>

<p><strong>Memory trick:</strong> the merchant is the only party who cannot
negotiate with anyone in this chain. That is where all the cost lands.</p>

<h2>5. Payment Methods Beyond Cards</h2>

<table>
<tr><th>Method</th><th>How the money moves</th><th>Typical use</th></tr>
<tr><td>Card</td><td>Through the scheme, in two days</td><td>Everything, everywhere</td></tr>
<tr><td>Bank transfer</td><td>Direct between accounts</td><td>Large invoices, B2B, some payroll</td></tr>
<tr><td>Direct debit</td><td>Pulled from the customer by mandate</td><td>Subscriptions, utility bills</td></tr>
<tr><td>Wallet</td><td>Stored value or a tokenised card</td><td>Mobile, faster checkout</td></tr>
<tr><td>Buy now pay later</td><td>A short-term credit facility</td><td>Larger consumer purchases</td></tr>
<tr><td>Cryptocurrency</td><td>On a public blockchain</td><td>Cross-border, settlement</td></tr>
<tr><td>Cash</td><td>Physically, at a till</td><td>Still a large share of retail</td></tr>
</table>

<p>Every one of these has different costs, different settlement timing, and
different fraud risk. That difference is why a shop always supports more than one.</p>

<h2>6. Double-Entry Bookkeeping - The Core Idea</h2>

<p>Every serious financial system is built on this, and it is one idea that will
change how you write software.</p>

<p>Every transaction has at least two entries, and every entry moves value from
one account to another. Money is never created or destroyed, only moved.</p>

<pre>Customer buys a 10.00 coffee

  DEBIT   Cash          10.00     (money in)
  CREDIT  Coffee Sales  10.00     (revenue)
  --------------------------------------------
  Total    10.00          =        10.00      balanced

Customer is refunded their 10.00

  DEBIT   Refunds       10.00
  CREDIT  Cash          10.00     (money out)
  --------------------------------------------
  Total    10.00          =        10.00      balanced</pre>

<p>The sum of all debits always equals the sum of all credits. If it does not,
something is wrong, and the database will tell you exactly where.</p>

<p><strong>Memory trick:</strong> every entry has a destination. There is no "money
appears from nowhere" in a correct ledger, which is precisely why a double-entry
system catches bugs a single-entry one never would.</p>

<p>This is why financial databases are relational and why transactions matter so
much. It is not bureaucracy, it is a self-checking invariant.</p>

<h2>7. Idempotency - The Most Important Fintech Concept</h2>

<p>A payment request can be sent twice because a customer double-taps, a network
retries, or a server times out after the payment actually succeeded. Without a
defence, the customer is charged twice and you have to refund one.</p>

<p>The defence is an idempotency key: the client generates a unique id, sends it
with every attempt, and the server records that it has seen it. The second
attempt returns the <em>original result</em> rather than doing the work again.</p>

<pre>client -&gt; POST /payments   Idempotency-Key: 7f2a-99
server: key 7f2a not seen -&gt; do the work, save the result against the key

client -&gt; POST /payments   Idempotency-Key: 7f2a-99   (retry)
server: key 7f2a seen -&gt; return the stored result, do nothing</pre>

<p><strong>Memory trick:</strong> every mutating payment endpoint takes an
idempotency key. Without one, you have a support queue instead of a finance
department.</p>

<h2>8. PCI DSS And Why Card Details Are So Restricted</h2>

<p>Storing a real card number creates a legal obligation: the Payment Card
Industry Data Security Standard. In short, card data may never be stored after
authorisation, and the network's security controls become an audited requirement
rather than good practice.</p>

<p>That single rule is why checkout flows tokenise: the card details go straight
from the customer to the payment provider, and your server only ever sees a
one-time token it can charge later.</p>

<p><strong>Memory trick:</strong> if your database contains a card number, you have
a compliance problem and probably a security problem too.</p>

<h2>9. KYC, AML And Fraud</h2>

<table>
<tr><th>Term</th><th>Means</th></tr>
<tr><td>KYC</td><td>Know Your Customer: verify who they are before allowing large transactions</td></tr>
<tr><td>AML</td><td>Anti-Money Laundering: spot activity designed to disguise where money came from</td></tr>
<tr><td>Sanctions screening</td><td>Check parties against sanctioned individuals and entities</td></tr>
<tr><td>Chargeback</td><td>The customer disputes, and their bank reverses the payment</td></tr>
<tr><td>Chargeback ratio</td><td>Disputes over total sales; a high rate closes merchant accounts</td></tr>
</table>

<p>The practical consequences for anyone building payments: you need an audit
trail, you need to be able to explain any transaction, and you need monitoring
that spots unusual behaviour rather than just failed payments.</p>

<p><strong>Memory trick:</strong> in fintech you are expected to answer "why did
this happen" months later, with the logs still available.</p>

<h2>10. Building A Payment System - The Hard Parts</h2>

<table>
<tr><th>Problem</th><th>Why it is hard</th><th>The usual answer</th></tr>
<tr><td>Double charges</td><td>Networks retry, users double-tap</td><td>Idempotency keys</td></tr>
<tr><td>Partial failure</td><td>Charge succeeded, your database write failed</td><td>Write intent first, reconcile later</td></tr>
<tr><td>Never losing money</td><td>A crash between two steps</td><td>Ledger entries in a transaction</td></tr>
<tr><td>Multiple currencies</td><td>Which rate, and whose</td><td>Store minor units as integers, never floats</td></tr>
<tr><td>Refunds</td><td>Partial, delayed, and sometimes disputed</td><td>Model as a new transaction, never an edit</td></tr>
<tr><td>Reconciliation</td><td>Your ledger and the provider's will differ</td><td>Automated daily comparison</td></tr>
</table>

<pre># Never store money as a float. 0.1 + 0.2 is not 0.3.
amount_cents INTEGER     -- 1999 means 19.99
currency     CHAR(3)     -- ISO 4217, uppercase</pre>

<p><strong>Memory trick:</strong> store money as an integer count of the smallest
unit. Everything else is arithmetic that eventually surprises you.</p>

<p><strong>Try it yourself:</strong> design the data model for a payment. Start
with the ledger and the idempotency key, and work outwards to orders and
receipts. Designing from the customer record inwards produces systems that lose
money, because they never model the failure cases.</p>

<p><strong>Learning vs production:</strong> a demo can assume the payment provider
responds instantly and once. Production deals with timeouts, duplicates,
disputes, partial refunds, provider outages and reconciliation against a statement
that does not match your database. None of that is conceptually hard; all of it is
mandatory.</p>"""
