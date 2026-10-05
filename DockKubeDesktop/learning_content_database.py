"""Chapter - Database Management: modelling, normalisation, SQL and NoSQL."""

CHAPTER = """<h2>1. What Is A Database, Really?</h2>

<p>A database is a program that answers two questions and refuses to answer
anything else: <strong>what data do I have</strong>, and <strong>what can I change
without breaking it</strong>.</p>

<p>Every feature of every database product exists to protect the second question.
That is why they are slower than a text file, and that is why you should not be
reaching for one when a text file would do.</p>

<p><strong>Memory trick:</strong> a database trades speed for the ability to let
several people, on several machines, change the same data at once without
inventing a story about who changed what.</p>

<h2>2. Relational Versus NoSQL</h2>

<table>
<tr><th></th><th>Relational (SQL)</th><th>NoSQL (document, key-value, graph, wide-column)</th></tr>
<tr><td>Data shape</td><td>Tables with fixed columns</td><td>Flexible documents, key-value pairs, or graphs</td></tr>
<tr><td>Schema</td><td>Defined up front, enforced by the database</td><td>Optional, flexible, varies per record</td></tr>
<tr><td>Relations</td><td>Joins across tables</td><td>Embed or reference instead of joining</td></tr>
<tr><td>Scaling</td><td>Grows vertically, harder to shard</td><td>Grows horizontally by design</td></tr>
<tr><td>Transactions</td><td>Full ACID, guaranteed</td><td>Varies; many drop multi-document transactions</td></tr>
<tr><td>Good for</td><td>Money, inventory, anything with rules</td><td>Huge volumes, changing shape, simple access patterns</td></tr>
</table>

<p>This is not a religion. Big companies run both, usually with a relational core
for the data that must be correct and a document store for everything else.</p>

<h2>3. Tables, Keys And Relationships</h2>

<p>A <strong>primary key</strong> identifies a row uniquely. A <strong>foreign
key</strong> points at another table's primary key, and it is how tables are
related rather than merely sitting in the same database.</p>

<p><strong>Memory trick:</strong> the primary key is a name tag. The foreign key
is someone pointing at that name tag and saying "this belongs to that".</p>

<h3>The three cardinalities</h3>

<table>
<tr><th>Relationship</th><th>Means</th><th>Example</th><th>How to store it</th></tr>
<tr><td>One to one</td><td>Each row links to at most one other</td><td>A person and one passport</td><td>Put the foreign key on either side</td></tr>
<tr><td>One to many</td><td>One parent, many children</td><td>A customer, many orders</td><td>Foreign key on the many side</td></tr>
<tr><td>Many to many</td><td>Many of each</td><td>Students and courses</td><td>Always a third table with two foreign keys</td></tr>
</table>

<p>The one to many rule is worth memorising: <strong>the foreign key always lives
on the "many" side</strong>. Each order has one customer, so the order row carries
the customer id.</p>

<h3>The many-to-many join table</h3>
<p>You cannot put a list of course ids in a student row and expect the database
to keep it consistent. A third table is the answer, and this is the single most
common thing beginners get wrong:</p>

<pre>-- The join table that makes many-to-many possible
CREATE TABLE enrollments (
    student_id  INT REFERENCES students(id),
    course_id   INT REFERENCES courses(id),
    enrolled_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (student_id, course_id)
);</pre>

<p>The compound primary key also stops the same student enrolling in the same
course twice, which is a rule you would otherwise have to enforce in code.</p>

<h2>4. Normalisation</h2>

<p>Normalisation is the process of splitting tables so each fact is stored in
exactly one place. Its purpose is not tidiness. It is that you update a value in
one place and never have to hunt for the other copies.</p>

<h3>First normal form - one value per cell</h3>
<p>No lists, no comma-separated values, no repeating groups.</p>
<pre>-- Before: a whole list in one cell, which no index can help with
customers(id, name, phone_numbers)
1  Alice  "555-1111, 555-2222, 555-3333"

-- After: one row per phone number
customers(id, name)
phones(id, customer_id, number)</pre>

<h3>Second normal form - the whole key</h3>
<p>In first normal form, every non-key column depends on the <em>whole</em> primary
key, not part of it. This only bites on composite keys.</p>
<pre>-- Not 2NF: order_id is part of the key, but product_name depends only on product_id
order_items(order_id, product_id, product_name, quantity, PRIMARY KEY (order_id, product_id))

-- 2NF: split it
order_items(order_id, product_id, quantity, PRIMARY KEY (order_id, product_id))
products(product_id, product_name)</pre>

<h3>Third normal form - nothing depends on a non-key</h3>
<p>Non-key columns must not depend on other non-key columns. This is the one you
meet most, and it is always the same shape: a detail column that duplicates
something already held elsewhere.</p>
<pre>-- Not 3NF: customer_city depends on city, which depends on postal_code
customers(id, name, city, postal_code)

-- 3NF
customers(id, name, postal_code)
cities(postal_code, city, country)</pre>

<h3>BCNF</h3>
<p>Stricter than 3NF: every attribute must depend on the key, nothing else. Real
schemas reach 3NF almost always and BCNF occasionally.</p>

<p><strong>Memory trick:</strong> 1NF is one value per cell, 2NF is the whole key,
3NF is nothing but the key. Every step is removing a dependency that is smaller
than it looks.</p>

<h3>When To Stop Normalising</h3>
<p>Normalise until you are about to read, because joins cost. When a report runs
often and the data rarely changes, deliberately de-normalise on purpose: store a
denormalised copy, and keep the normalised one as the truth. That is a conscious
trade of consistency for speed, and it belongs in a comment.</p>

<h2>5. The SQL You Actually Need</h2>

<pre>-- Read
SELECT name, email FROM customers WHERE active = true ORDER BY name;
SELECT COUNT(*) FROM orders WHERE created_at &gt; now() - interval '30 days';

-- Insert, update, delete
INSERT INTO customers (name, email) VALUES ('Alice', 'alice@example.com');
UPDATE customers SET email = 'new@example.com' WHERE id = 1;
DELETE FROM orders WHERE id = 42;

-- Joins: the three you need
SELECT c.name, COUNT(o.id) AS orders
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
GROUP BY c.name;

SELECT o.id, c.name, o.total
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.status = 'paid';

SELECT p.name, SUM(oi.quantity) AS sold
FROM order_items oi
JOIN products p ON p.id = oi.product_id
GROUP BY p.name
ORDER BY sold DESC;</pre>

<p><strong>Memory trick:</strong> a plain <code>JOIN</code> keeps only rows with a
match on both sides, a <code>LEFT JOIN</code> keeps every row from the left even
with no match, and <code>GROUP BY</code> collapses many rows into one summary row
per group.</p>

<h3>Aggregation</h3>
<pre>SELECT status, COUNT(*) AS n, SUM(total) AS revenue, AVG(total) AS average
FROM orders
GROUP BY status
HAVING COUNT(*) &gt; 10;
</pre>
<p><code>WHERE</code> filters rows before grouping. <code>HAVING</code> filters
the groups afterwards. Putting a row filter in <code>HAVING</code> is the classic
beginner mistake and it will not give you the count you expected.</p>

<h3>Transactions - All Of It Or None Of It</h3>
<pre>BEGIN;
    UPDATE accounts SET balance = balance - 100 WHERE id = 1;
    UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;   -- or ROLLBACK if either update fails</pre>
<p>Moving money without a transaction is how balances stop matching reality.</p>

<h2>6. Indexes: Why Queries Get Slow</h2>

<p>An index is a sorted copy of a column, maintained by the database. Without
one the database reads every row to answer your query; with one it jumps
straight to the right place.</p>

<pre>CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_created   ON orders(created_at);
CREATE UNIQUE INDEX idx_customers_email ON customers(email);</pre>

<table>
<tr><th>Rule</th><th>Reason</th></tr>
<tr><td>Index columns you filter, join and sort on</td><td>Anything else is written to disk and never read back</td></tr>
<tr><td>Every index makes writes slower</td><td>Each insert must update every index on that row</td></tr>
<tr><td>Index foreign keys</td><td>Otherwise every join on that column is a full scan</td></tr>
<tr><td>Never index a low-cardinality column alone</td><td>An index on a boolean has two entries and is useless</td></tr>
<tr><td>Find unused indexes and drop them</td><td>They cost write performance and return nothing</td></tr>
</table>

<pre>-- Which indexes are actually being used?
SELECT relname, indexrelname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0;

-- Why is this query slow? Read the plan before changing anything.
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 1;</pre>

<p><strong>Memory trick:</strong> an index is a price you pay on every write to
make some reads fast. Add one when a specific query is measurably slow, not
speculatively.</p>

<h2>7. Drawing The Schema</h2>

<p>Draw an entity relationship diagram before you create the tables. It catches
the one-to-many that was meant to be many-to-many, and the column that belongs on
another table, before they are baked in.</p>

<pre># Render a dbdiagram.io file and generate the SQL from it
dbml-renderer schema.dbml
dbml2sql schema.dbml &gt; schema.sql

# Or export what you already have
pg_dump -s -d appdb &gt; schema.sql
mysqldump --no-data appdb &gt; schema.sql</pre>

<p>Generating the SQL from the diagram, rather than writing both by hand, is what
stops them from disagreeing.</p>

<h2>8. NoSQL - The Four Families</h2>

<table>
<tr><th>Type</th><th>Shape</th><th>Good for</th></tr>
<tr><td>Document</td><td>JSON-like records</td><td>Varied data read as a whole, such as a product catalogue</td></tr>
<tr><td>Key-value</td><td>A key and an opaque value</td><td>Session storage and caches</td></tr>
<tr><td>Wide-column</td><td>Rows keyed by partition</td><td>Enormous write volumes, time-series and sensor data</td></tr>
<tr><td>Graph</td><td>Nodes and the edges between them</td><td>Recommendations and fraud rings, where the relationships are the data</td></tr>
</table>

<p>Document stores are the ones you will meet most, so they are what the rest of
this section is about.</p>

<h3>Embedding Versus Referencing</h3>
<p>In a document store you choose, per relationship, whether to embed the related
data inside the document or reference it by id. This is the decision relational
design makes for you with joins, and NoSQL hands to you:</p>

<table>
<tr><th>Choose</th><th>When</th><th>Because</th></tr>
<tr><td>Embed</td><td>The child always belongs to the parent and is read with it</td><td>One read instead of a join, and the child cannot exist alone</td></tr>
<tr><td>Reference</td><td>The data is unbounded, or shared between parents</td><td>An embedded array cannot grow forever, and duplicating it wastes space</td></tr>
</table>

<pre>// Embed: an order with its lines. They are always read together.
{
  "_id": "order-123",
  "customerId": "cust-9",
  "total": 84.50,
  "lines": [
    { "productId": "p1", "quantity": 2, "price": 20.00 },
    { "productId": "p2", "quantity": 1, "price": 44.50 }
  ]
}

// Reference: a product appears in thousands of orders, so keep it once.
{ "_id": "order-124", "lines": [ { "productId": "p3", "quantity": 1 } ] }</pre>

<p><strong>Memory trick:</strong> embed when the child has no life of its own,
reference when it does. An order line is meaningless without its order, so embed
it. A product is a real thing, so reference it.</p>

<h3>The sixteen megabyte rule</h3>
<p>MongoDB will not accept a document larger than 16 MB, and a document that huge
is slow to read even when it fits. That ceiling is a design tool: it is what
stops you embedding an entire product catalogue into a customer record.</p>

<h3>Querying</h3>
<pre>// Find, filter, project: only ask for the fields you need
db.orders.find({ status: "paid" }, { customerId: 1, total: 1 })
db.orders.find({ total: { $gt: 50, $lt: 200 } }).sort({ createdAt: -1 }).limit(20)

// Aggregation: the same pipeline idea as SQL GROUP BY
db.orders.aggregate([
  { $match: { status: "paid" } },
  { $group: { _id: "$customerId", total: { $sum: "$total" } } },
  { $sort: { total: -1 } },
  { $limit: 10 }
])</pre>

<h3>Indexes In MongoDB</h3>
<pre>db.orders.createIndex({ customerId: 1, createdAt: -1 })   # compound
db.orders.createIndex({ status: 1 }, { unique: true })     # unique constraint
db.orders.getIndexes()
db.orders.find({ status: "paid" }).explain("executionStats")</pre>

<p>Compound index field order matters. An index on <code>{customerId, createdAt}</code>
serves "orders for this customer" and "orders for this customer sorted by date",
but not "all paid orders sorted by date" without a customer filter.</p>

<h3>Where SQL Wins And Where NoSQL Wins</h3>

<table>
<tr><th>Situation</th><th>Pick</th></tr>
<tr><td>Money, stock levels, anything that must never be wrong</td><td>Relational. Transactions are the reason.</td></tr>
<tr><td>Reports across many relationships</td><td>Relational. Joins exist for this.</td></tr>
<tr><td>A product where every item is different</td><td>Document. A column per attribute would be mostly null.</td></tr>
<tr><td>Millions of writes per second</td><td>Either, depending on shape. Horizontal scaling is easier in NoSQL.</td></tr>
<tr><td>Team skill and existing tooling</td><td>Whichever the team already knows.</td></tr>
</table>

<p><strong>Try it yourself:</strong> model a library two ways. First as tables
with foreign keys, then as documents with embedded and referenced books. The
moment you decide whether a loan history belongs inside the book document or
beside it, you have understood the difference better than any definition will
teach you.</p>

<p><strong>Learning vs production:</strong> a schema in one database server is
simple either way. In production the same model has to survive backups, schema
changes on live data, and a second region, and the decision you agonised over
in the design becomes a migration you have to roll out without downtime.</p>"""
