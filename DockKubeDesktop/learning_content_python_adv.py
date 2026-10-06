r"""Chapter 27 - Python advanced: lambda, map, threads, Pydantic model_dump."""

CHAPTER = r"""<h2>1. Lambda - Small Anonymous Functions</h2>

<p>A <code>lambda</code> is a one-expression function with no name. It exists
for the moments when you need a tiny function <em>right here</em>, usually as
an argument.</p>

<pre>square = lambda x: x * x                 # works, but def square(x) is better

# The four places lambda genuinely earns its keep:
sorted(orders, key=lambda o: o["total"], reverse=True)
players.sort(key=lambda p: (-p["score"], p["name"]))
items = list(filter(lambda x: x &gt; 0, raw))
buttons = [ctk.CTkButton(win, text=n, command=lambda n=n: open(n)) for n in names]
</pre>

<table>
<tr><th>Rule</th><th>Why</th></tr>
<tr><td>One expression only</td><td>No loops, no assignments - if you need those, write a def</td></tr>
<tr><td>Name it with def when reused</td><td><code>key=age_of</code> reads better than a lambda in a stack trace</td></tr>
<tr><td>Loop variables need binding</td><td><code>lambda: i</code> captures the variable, not the value - use <code>lambda i=i: i</code> or functools.partial</td></tr>
<tr><td>Never assign to a name twice</td><td>PEP 8: lambda should be where you need an expression, not a def in disguise</td></tr>
</table>

<h2>2. map, filter, reduce And Comprehensions</h2>

<pre>names  = list(map(str.upper, users))                 # apply to every item
emails = list(filter(lambda u: u.active, users))     # keep matching items
from functools import reduce
total  = reduce(lambda a, b: a + b.price, cart.items, 0)

# The same three, as comprehensions - usually preferred:
names  = [u.name.upper() for u in users]
emails = [u.email for u in users if u.active]
total  = sum(item.price for item in cart.items)

# Dict and set comprehensions too:
by_id = {u.id: u for u in users}
sizes = {len(word) for word in words}
</pre>

<table>
<tr><th>Tool</th><th>Reads as</th><th>Prefer when</th></tr>
<tr><td>map(f, xs)</td><td>"apply f to each"</td><td>f already exists as a function; chains lazily with map</td></tr>
<tr><td>filter(p, xs)</td><td>"keep where p"</td><td>predicate exists; comprehension is clearer otherwise</td></tr>
<tr><td>reduce(f, xs)</td><td>"fold into one value"</td><td>almost never - sum()/any()/all()/min() are clearer</td></tr>
<tr><td>comprehension</td><td>"build this list"</td><td>default choice: readable, Pythonic, fast</td></tr>
</table>

<p><strong>Memory trick:</strong> map transforms, filter selects, reduce
folds. If you have to reread it, use a comprehension instead.</p>

<h2>3. itertools - Loops Without Loops</h2>

<pre>from itertools import chain, groupby, islice, count, product

merged   = chain(list_a, list_b)                    # lazy concatenation
first_10 = islice(rows, 10)                         # head of an iterator
for key, group in groupby(sorted(rows, key=lambda r: r.city), key=lambda r: r.city):
    print(key, list(group))                         # grouped runs
pairs    = product(colors, sizes)                   # cartesian product
infinite = islice(count(0, 2), 5)                   # [0, 2, 4, 6, 8]
</pre>

<h2>4. Threads - Concurrent I/O In One Process</h2>

<p>A <strong>thread</strong> is a second stream of execution inside the same
program, sharing the same memory. Python has a <strong>Global Interpreter
Lock (GIL)</strong>: only one thread executes Python bytecode at a time, so
threads do <em>not</em> speed up number crunching - they hide waiting. Waiting
on a network, a disk, an API: threads win. Pure computation: use processes
(Chapter 28) or NumPy.</p>

<pre>import threading
import time

def fetch(url):
    print(f"start {url} on {threading.current_thread().name}")
    time.sleep(1)            # stands in for a network call
    print(f"done  {url}")

# 1. Raw threads
threads = [threading.Thread(target=fetch, args=(u,), name=f"t{i}")
           for i, u in enumerate(urls)]
for t in threads: t.start()
for t in threads: t.join()          # wait for all; without join the main
                                    # thread exits and kills them

# 2. The pool you should actually use
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=8) as pool:
    futures = {pool.submit(fetch, u): u for u in urls}
    for future in as_completed(futures):
        result = future.result()    # raises here if the task raised
</pre>

<h2>5. Shared Memory Needs A Lock</h2>

<pre>counter = 0
lock = threading.Lock()

def bump():
    global counter
    with lock:                 # only one thread at a time inside
        counter += 1           # read-modify-write is not atomic

# Rules:
# - with lock:  is always safer than lock.acquire() (exception-safe)
# - hold the lock for the shortest possible time
# - queue.Queue is often better than a lock: producers put, consumers get
# - daemon=True threads die with the program - fine for background pings,
#   wrong for work that must finish
</pre>

<table>
<tr><th>Tool</th><th>Use for</th></tr>
<tr><td>threading.Thread</td><td>One-off background jobs</td></tr>
<tr><td>ThreadPoolExecutor</td><td>Many similar I/O tasks - the default choice</td></tr>
<tr><td>threading.Lock / RLock</td><td>Protecting a shared variable</td></tr>
<tr><td>queue.Queue</td><td>Handing work between threads safely (producer/consumer)</td></tr>
<tr><td>threading.Event</td><td>Signalling "stop now" to a worker</td></tr>
<tr><td>concurrent.futures</td><td>Futures, timeouts, error propagation</td></tr>
</table>

<p><strong>Memory trick:</strong> GIL means threads share one CPU core for
Python code - pick threads to <em>wait</em>, processes to <em>compute</em>.</p>

<h2>6. Pydantic v2 - model_dump() And Validation</h2>

<p>Pydantic validates at the boundary and gives you typed objects inside.
<code>model_dump()</code> turns the object back into plain data for JSON,
databases or logs.</p>

<pre>from pydantic import BaseModel, EmailStr, Field, ValidationError

class UserIn(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=80)
    age: int = Field(ge=0, le=130)
    tags: list[str] = []

# Validate at the edge - bad input raises before your code runs:
try:
    user = UserIn.model_validate({"email": "a@b.co", "name": "Ada", "age": 36})
except ValidationError as e:
    print(e.errors())            # structured, JSON-serialisable errors

user = UserIn(email="a@b.co", name="Ada", age=36)

user.model_dump()                  # {"email": "a@b.co", "name": "Ada", ...}
user.model_dump(mode="json")       # JSON-safe types (datetime -&gt; str)
user.model_dump(exclude={"tags"})  # leave fields out
user.model_dump(by_alias=True)     # send database field names
user.model_dump_json()             # straight to a JSON string
user.model_copy(update={"age": 37})  # immutable-ish update
UserIn.model_validate_json(raw)    # validate straight from bytes
</pre>

<table>
<tr><th>Method</th><th>Direction</th><th>Use it for</th></tr>
<tr><td>model_validate / model_validate_json</td><td>outside -&gt; object</td><td>API request bodies, config files, webhooks</td></tr>
<tr><td>model_dump / model_dump_json</td><td>object -&gt; outside</td><td>Responses, caching, logs</td></tr>
<tr><td>model_fields</td><td>introspection</td><td>Generating docs or forms</td></tr>
</table>

<p><strong>model_dump vs dict():</strong> v2's <code>model_dump()</code> is the
supported way; <code>dict(user)</code> is the v1 habit and hides options like
<code>mode="json"</code> and <code>exclude=</code>. FastAPI itself calls
model_dump when serialising your response models.</p>

<h2>7. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Lambda</td><td>Everywhere it fits</td><td>Only for one-line keys; named functions everywhere else</td></tr>
<tr><td>Threads</td><td>One thread, hope for the best</td><td>Pools with bounded workers, timeouts, graceful shutdown</td></tr>
<tr><td>Shared state</td><td>Globals and hope</td><td>Queues and locks, or no shared state at all</td></tr>
<tr><td>Validation</td><td>if checks scattered in the route</td><td>One Pydantic model at every boundary</td></tr>
<tr><td>Serialisation</td><td>json.dumps(dict(obj))</td><td>model_dump(mode="json") - typed, tested, consistent</td></tr>
</table>

<h2>8. Key Takeaways</h2>
<ul>
<li>Lambda is an expression for one-off callbacks, not a function style.</li>
<li>map/filter/reduce exist; comprehensions and sum()/any() are usually
clearer.</li>
<li>The GIL makes threads good at waiting and useless at computing - use
ThreadPoolExecutor for I/O, processes for CPU.</li>
<li>Always join your threads, or bound them with an executor.</li>
<li>Validate at the boundary with Pydantic; serialise with
model_dump(mode="json").</li>
</ul>

<p><strong>Exercise:</strong> write a script that fetches five URLs with
sequential requests, then with ThreadPoolExecutor(max_workers=5), and compare
the wall-clock times with time.perf_counter().</p>
"""