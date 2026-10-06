r"""Chapter 28 - Python internals: metaclasses, descriptors, MRO, dunder methods and more."""

CHAPTER = r"""<h2>1. Metaclasses - The Class Of A Class</h2>

<p>Every class is an instance of something. <code>type</code> builds normal
classes; a <strong>metaclass</strong> is a class whose instances <em>are
classes</em>. Control <code>__new__</code> of the metaclass and you control how
classes are constructed: validate fields, register plugins, inject methods.</p>

<pre>class Meta(type):
    def __new__(mcls, name, bases, ns):
        # Runs at class-definition time, before the class exists.
        registry[name] = ns.get("kind", name)     # auto-register plugins
        for key, value in ns.items():
            if key.startswith("field_") and not isinstance(value, property):
                raise TypeError(f"{name}.{key} must be a property")
        return super().__new__(mcls, name, bases, ns)

    def __init__(cls, name, bases, ns):
        cls.schema = {k: v.type for k, v in ns.items() if isinstance(v, property)}

class Model(metaclass=Meta):
    kind = "base"

class User(Model):
    kind = "user"                                 # registry["User"] == "user"

# You already use metaclasses: ABCMeta (abstractmethod) and ORM models like
# SQLAlchemy declarative bases are built on them.
</pre>

<p><strong>Memory trick:</strong> <code>__init__</code> of a class initialises
an <em>instance</em>; <code>Meta.__init__</code> initialises a <em>class</em>.</p>

<h2>2. Descriptors - The Engine Under property</h2>

<p>A descriptor is any object with <code>__get__</code> (and optionally
<code>__set__</code>/<code>__delete__</code>) that lives in a class body. Every
attribute lookup on an instance checks the type's MRO for a data descriptor
first - which is exactly how <code>property</code>, <code>classmethod</code>
and <code>staticmethod</code> work.</p>

<pre>class Validated:                       # a data descriptor
    def __init__(self, name, kind=str, required=True):
        self.name, self.kind, self.required = name, kind, required
    def __set_name__(self, owner, name):      # called once at class creation
        self.private = "_" + name
    def __get__(self, obj, owner=None):
        if obj is None: return self
        return getattr(obj, self.private, None)
    def __set__(self, obj, value):            # validation happens HERE
        if not isinstance(value, self.kind):
            raise TypeError(f"{self.name} must be {self.kind.__name__}")
        if self.required and value in (None, ""):
            raise ValueError(f"{self.name} is required")
        setattr(obj, self.private, value)

class Account:
    owner = Validated("owner", str)
    email = Validated("email", str)

a = Account(); a.owner = "Ada"        # every assignment validated, no code in Account

# property is the built-in descriptor shortcut:
class Temp:
    def __init__(self, c): self._c = c
    @property
    def f(self): return self._c * 9 / 5 + 32      # __get__
    @f.setter
    def f(self, v): self._c = (v - 32) * 5 / 9     # __set__
</pre>

<table>
<tr><th>Descriptor</th><th>Has</th><th>Controls</th></tr>
<tr><td>Non-data (only __get__)</td><td>__get__</td><td>Reads; instance dict wins if present</td></tr>
<tr><td>Data (__get__ + __set__)</td><td>__get__, __set__</td><td>Reads AND writes; shadows the instance dict</td></tr>
</table>

<h2>3. Advanced Decorators - Classes, Arguments, Wrapping</h2>

<pre># A class-based decorator (anything callable with __call__ works):
class CountCalls:
    def __init__(self, func): self.func, self.calls = func, 0
    def __call__(self, *a, **kw):
        self.calls += 1
        return self.func(*a, **kw)

# A decorator THAT TAKES ARGUMENTS - the shape that confuses everyone.
# Three nested functions: outer receives the arguments, middle receives the
# function, inner receives the call.
def retries(max_attempts=3, delay=0.5):
    def decorator(func):
        import functools, time
        @functools.wraps(func)                # keep __name__, __doc__!
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt == max_attempts: raise
                    time.sleep(delay * attempt)      # exponential-ish backoff
        return wrapper
    return decorator

@retries(max_attempts=3, delay=0.2)
def call_api(url): ...

# Stacking: decorators apply bottom-up.
@login_required            # runs second (outermost)
@cache(ttl=60)             # runs first (innermost)
def get_report(month): ...
</pre>

<p><strong>Memory trick:</strong> <code>@decorator</code> is sugar for
<code>f = decorator(f)</code>; <code>@decorator(x)</code> is sugar for
<code>f = decorator(x)(f)</code> - one call returns the real decorator.</p>

<h2>4. Coroutines And asyncio - Concurrency Without Threads</h2>

<p>An <strong>async def</strong> function is a coroutine: it can pause at
<code>await</code> and let the event loop run something else. One thread,
no GIL fight, thousands of concurrent I/O operations.</p>

<pre>import asyncio, httpx

async def fetch(client, url):           # coroutine function
    r = await client.get(url)           # PAUSES here; loop does other work
    return r.status_code

async def main():
    async with httpx.AsyncClient() as client:
        urls = [f"https://httpbin.org/get?i={i}" for i in range(20)]
        tasks = [asyncio.create_task(fetch(client, u)) for u in urls]
        results = await asyncio.gather(*tasks)   # run all, collect in order
        # return_exceptions=True would put failures in the list instead
        print(results)

asyncio.run(main())                     # builds the loop, runs, cleans up
</pre>

<table>
<tr><th>Tool</th><th>Choose it when</th></tr>
<tr><td>asyncio + gather</td><td>Thousands of socket/HTTP waits, one process, FastAPI endpoints</td></tr>
<tr><td>ThreadPoolExecutor</td><td>Blocking libraries you cannot make async</td></tr>
<tr><td>ProcessPoolExecutor</td><td>CPU-heavy work (see next section)</td></tr>
<tr><td>Background tasks (asyncio.create_task)</td><td>Fire-and-forget work after a response</td></tr>
</table>

<p><strong>Rules:</strong> never <code>await</code> in a non-async function;
never call a blocking library inside async code (it freezes the whole loop -
use asyncio.to_thread); <code>gather</code> for fan-out,
<code>Queue</code> for producer/consumer, <code>wait_for</code> for timeouts.</p>

<h2>5. Multiprocessing - Real Cores, Real Isolation</h2>

<p>The GIL means one Python bytecode at a time <em>per process</em>.
<strong>Multiprocessing</strong> spawns separate OS processes, each with its
own interpreter, GIL and memory - true parallelism on every core, at the cost
of pickling data across process boundaries.</p>

<pre>from multiprocessing import Process, Pool
import os

def cpu_job(n):                        # must be importable (top level)
    return sum(i * i for i in range(n))

if __name__ == "__main__":             # REQUIRED on Windows/macOS:
    #     without it every child re-imports __main__ and re-runs the app.
    with Pool(processes=4) as pool:
        results = pool.map(cpu_job, [10_000_000] * 8)   # 8 jobs on 4 cores
        # pool.imap for lazy results, pool.apply_async for fire-and-collect
</pre>

<table>
<tr><th></th><th>Thread</th><th>Process</th></tr>
<tr><td>Shares memory</td><td>Yes (needs locks)</td><td>No - picklable args only</td></tr>
<tr><td>Parallel CPU work</td><td>No (GIL)</td><td>Yes</td></tr>
<tr><td>Startup cost</td><td>Microseconds</td><td>Milliseconds</td></tr>
<tr><td>Failure isolation</td><td>One crash kills all</td><td>Separate address spaces</td></tr>
<tr><td>Use for</td><td>Network/disk waits</td><td>Compute, sandboxes, native libs that release memory</td></tr>
</table>
<h2>6. Generators And Iterators - Lazy Data</h2>

<p>An <strong>iterator</strong> is anything with <code>__iter__</code> and
<code>__next__</code>. A <strong>generator</strong> is the easiest way to write
one: <code>yield</code> suspends and hands a value back, keeping its local
state, so nothing is computed until you ask.</p>

<pre>def read_large_file(path):              # constant memory on a 100 GB file
    with open(path) as fh:
        for line in fh:
            if line.startswith("ERROR"):
                yield line.rstrip()

errors = read_large_file("app.log")     # nothing read yet
count = sum(1 for _ in errors)          # now it streams

# Infinite sequence, bounded by islice:
def natural():
    n = 0
    while True:
        n += 1
        yield n
first_even = (x for x in natural() if x % 2 == 0)   # generator expression
import itertools
print(list(islice(first_even, 5)))      # [2, 4, 6, 8, 10]

# send(): coroutines get their data back in - the root of async/await:
def accumulator():
    total = 0
    while True:
        value = yield total              # pause; receive via .send()
        if value is None: return
        total += value
</pre>

<table>
<tr><th>Concept</th><th>Means</th></tr>
<tr><td>Lazy evaluation</td><td>Compute on demand; a generator expression of a million rows costs one row at a time</td></tr>
<tr><td>One-shot</td><td>A generator is exhausted after one pass - wrap with a function that recreates it if you need repeats</td></tr>
<tr><td>yield from</td><td>Delegates to a sub-generator, flattening the pipeline</td></tr>
<tr><td>Backpressure</td><td>The consumer drives: stop pulling and production stops - natural flow control for streams</td></tr>
</table>

<h2>7. CPython Memory Management</h2>

<table>
<tr><th>Mechanism</th><th>What it does</th></tr>
<tr><td>Reference counting</td><td>Every object has a count; +1 when referenced, -1 when dropped; hitting 0 frees it immediately</td></tr>
<tr><td>Cycles</td><td>a refers to b refers to a - counts never reach 0</td></tr>
<tr><td>Generational GC</td><td>gc module periodically finds unreachable cycles; 3 generations, scanned every 700/10/10 allocations</td></tr>
<tr><td>Allocators</td><td>Small objects: per-size pools (pymalloc). Large: malloc directly</td></tr>
<tr><td>Interning</td><td>Small ints (-5..256) and short identifiers are shared, so they are the same object</td></tr>
<tr><td>sys.getrefcount</td><td>Shows the count (one higher than you expect - the argument reference counts too)</td></tr>
</table>

<pre>import gc, sys

a = []; b = [a]; a.append(b)     # cycle: neither reaches refcount 0
print(sys.getrefcount(a))        # inspect
print(gc.collect())              # force the cycle collector; returns freed count

class Expensive:
    def __init__(self): self.buf = bytearray(10_000_000)
    def __del__(self): print("freed")     # called when refs hit 0 (usually)

# Finding leaks: objgraph.show_backrefs() or tracemalloc - take two snapshots
import tracemalloc
tracemalloc.start()
snap1 = tracemalloc.take_snapshot()
... # suspected leak code ...
snap2 = tracemalloc.take_snapshot()
for stat in snap2.compare_to(snap1, "lineno")[:5]:
    print(stat)                  # who allocated the memory that stayed
</pre>

<p><strong>Memory trick:</strong> refcounting frees <em>acyclic</em> objects
instantly; the generational collector exists only for <em>cycles</em>. Real
"memory leaks" in Python are almost always a list or cache that keeps a
reference alive.</p>

<h2>8. MRO - Method Resolution Order</h2>

<p>With multiple inheritance, which <code>foo()</code> runs? Python uses
<strong>C3 linearization</strong>: a deterministic order that respects local
precedence (your base list order) and monotonicity (a class never appears
before its own bases).</p>

<pre>class A:    def who(self): return "A"
class B(A): def who(self): return "B"
class C(A): def who(self): return "C"
class D(B, C): pass

print(D.__mro__)
# (&lt;class 'D'&gt;, &lt;class 'B'&gt;, &lt;class 'C'&gt;, &lt;class 'A'&gt;, &lt;class 'object'&gt;)
print(D().who())          # "B" - leftmost base wins

# super() walks the MRO, not "the parent":
class Base:
    def render(self): return "base"
class Left(Base):
    def render(self): return "[" + super().render() + "]"
class Right(Base):
    def render(self): return "{" + super().render() + "}"
class Both(Left, Right):
    def render(self): return "&lt;" + super().render() + "&gt;"

Both().render()   # "&lt;[{base}]&gt;" - super() follows Both.__mro__ precisely
</pre>

<p><strong>Diamond problem:</strong> A is a base of both B and C - without a
single linear order, <code>A.method</code> could run twice. C3 guarantees each
class appears exactly once. <code>TypeError: Cannot create a consistent MRO</code>
means you asked for an impossible ordering (usually conflicting base lists).</p>

<h2>9. Dunder Methods - making your objects act like built-ins</h2>

<pre>class Money:
    def __init__(self, amount, currency="EUR"):
        self.amount, self.currency = amount, currency
    def __add__(self, other):  return Money(self.amount + other.amount)      # a + b
    def __iadd__(self, other): self.amount += other.amount; return self      # a += b
    def __eq__(self, other):   return self.amount == other.amount            # a == b
    def __lt__(self, other):   return self.amount &lt; other.amount             # sorted(a)
    def __bool__(self):        return self.amount != 0                       # if a:
    def __len__(self):         return len(str(self.amount))                  # len(a)
    def __contains__(self, x): return x in str(self.amount)                  # x in a
    def __getitem__(self, i):  return str(self.amount)[i]                    # a[i]
    def __iter__(self):        return iter(str(self.amount))                 # for x in a
    def __repr__(self):        return f"Money({self.amount})"                # f-string, logs
    def __str__(self):         return f"{self.amount} {self.currency}"       # print(a)
    def __call__(self):        return self.amount * 2                        # a()
    def __enter__(self): ...; def __exit__(self, *e): ...                    # with a:
    def __new__(cls, *a):      ...                                           # control creation
    def __slots__ = ("amount", "currency")   # fixed layout, no __dict__, saves RAM

# Type-specific hooks you will meet:
# __hash__      dict/set keys (define __eq__ without __hash__ and the object
#               becomes unhashable)
# __format__    format(m, ",.2f")
# __index__     range(m) / list[m]
# __matmul__    the @ operator (NumPy matmul)
# __del__       last reference dropped (do not rely on it for cleanup)
</pre>

<p><strong>Memory trick:</strong> dunder methods are <em>protocols</em>, not
inheritance: if your object does the operations, Python will call them. That
is "duck typing" written down.</p>

<h2>10. Custom Context Managers - Guaranteed Cleanup</h2>

<pre># The class form - two methods, no exceptions swallowed:
class OpenDB:
    def __init__(self, dsn): self.dsn = dsn
    def __enter__(self):
        self.conn = connect(self.dsn)
        return self.conn                  # bound to the 'as' name
    def __exit__(self, exc_type, exc, tb):
        self.conn.close()
        return False                      # False: let exceptions propagate
                                           # True: swallow them (rarely right)

with OpenDB(dsn) as conn:
    conn.execute(...)

# The generator form - shorter, uses finally implicitly:
from contextlib import contextmanager

@contextmanager
def temp_cd(path):
    import os
    old = os.getcwd()
    os.chdir(path)
    try:
        yield os.getcwd()                 # everything before yield = __enter__
    finally:
        os.chdir(old)                     # everything after = __exit__

with temp_cd("/tmp/build") as cwd:
    ...

# Also in the toolbox:
# contextlib.suppress(KeyError)   - ignore specific exceptions
# contextlib.redirect_stdout(...) - capture prints
# contextlib.ExitStack            - enter many managed resources dynamically
# contextlib.closing(obj)         - call obj.close() on exit for anything
</pre>

<p><strong>Why it matters:</strong> files, locks, sockets, transactions and
temporary directories all have an "acquire now, release no matter what"
shape. The <code>with</code> statement is the only thing that runs cleanup
when the body raises.</p>

<h2>11. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Metaclasses / descriptors</td><td>Cool demos</td><td>ORMs, validation frameworks, plugin registries - use them, rarely write them</td></tr>
<tr><td>asyncio</td><td>async def because it looks modern</td><td>async at the edges only; sync in the core, no blocking calls in the loop</td></tr>
<tr><td>Multiprocessing</td><td>Forgotten __main__ guard crashes Windows</td><td>Pools sized to cores, chunks for big data, timeouts on every task</td></tr>
<tr><td>Generators</td><td>Lists of everything</td><td>Streams: pipelines of generators over logs, rows, events</td></tr>
<tr><td>Memory</td><td>Trust the GC</td><td>tracemalloc snapshots, bounded caches, __slots__ on hot objects</td></tr>
<tr><td>Context managers</td><td>try/finally you forget to write</td><td>Every resource goes through with - including timing and tracing spans</td></tr>
</table>

<h2>12. Key Takeaways</h2>
<ul>
<li>Metaclasses run when a class is created; descriptors run on every
attribute access - property is a descriptor.</li>
<li>A decorator with arguments is three nested functions; functools.wraps
keeps the metadata.</li>
<li>asyncio hides <em>waiting</em> on one thread; multiprocessing gets real
cores - and needs the <code>if __name__ == "__main__"</code> guard on
Windows.</li>
<li>Generators give lazy, constant-memory, backpressure-aware pipelines.</li>
<li>Reference counting frees acyclic objects instantly; the GC only exists
for cycles.</li>
<li>MRO is C3 linearisation: deterministic, leftmost-first, each class once;
super() walks that exact list.</li>
<li>Dunder methods are the protocols that make objects work with operators,
loops and with-statements.</li>
</ul>

<p><strong>Exercise:</strong> build a validated Model with a metaclass that
forbids mutable class attributes, then a generator that streams a 1 GB file
and counts matches while staying under 50 MB RSS (watch with task manager or
ps).</p>
"""