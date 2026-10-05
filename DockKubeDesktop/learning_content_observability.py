"""Chapter - Observability: logs, metrics and traces, and fixing bugs early."""

CHAPTER = """<h2>1. What Is Observability?</h2>

<p>Monitoring asks whether a system is working. Observability asks whether you
can <em>understand</em> a system from the outside, with no prior knowledge of
its internals.</p>

<p>That distinction matters. A monitor can only alert on the failures you
predicted. An observable system lets you ask a question you did not think of in
advance and get an answer.</p>

<p><strong>Memory trick:</strong> monitoring is a smoke detector. Observability is
being able to walk into an unfamiliar building in the dark and find your way out.</p>

<h2>2. The Three Signals</h2>

<table>
<tr><th>Signal</th><th>Answers</th><th>Cost at scale</th><th>Good for</th></tr>
<tr><td>Logs</td><td>What exactly happened in this one request?</td><td>Highest, and grows without limit</td><td>Debugging a specific failure</td></tr>
<tr><td>Metrics</td><td>How often, how fast, how much?</td><td>Cheap, fixed size over time</td><td>Alerting, trends, capacity</td></tr>
<tr><td>Traces</td><td>Where did the time go across services?</td><td>Medium, needs instrumentation</td><td>Finding slow requests in a distributed system</td></tr>
</table>

<p>You need all three. Metrics tell you something is wrong, logs tell you what
happened, and traces tell you where in the chain it went wrong.</p>

<h2>3. Metrics - The Golden Signals</h2>

<p>You do not need thousands of metrics. These four tell you almost everything,
and they are known as the golden signals:</p>

<table>
<tr><th>Signal</th><th>What it means</th><th>Bad example</th></tr>
<tr><td>Latency</td><td>How long a request takes</td><td>A slow request while the average looks fine</td></tr>
<tr><td>Traffic</td><td>How much work is arriving</td><td>A spike nobody planned for</td></tr>
<tr><td>Errors</td><td>How often requests fail</td><td>Errors rising slowly, unnoticed for a week</td></tr>
<tr><td>Saturation</td><td>How full the resource is</td><td>CPU fine, but the connection pool is exhausted</td></tr>
</table>

<p><strong>Memory trick:</strong> you will feel the four in your body. Latency is
how slow it feels, traffic is how busy, errors is how broken, saturation is how
stuffed the system is.</p>

<h3>Measure percentiles, never averages</h3>
<p>This is the single most important rule in the chapter. An average hides the
users having a terrible time.</p>
<pre>// The truth: 1% of requests take 8 seconds, 99% take 50ms
average = 130ms      # looks fine
p50     =  50ms      # a typical user is fine
p95     = 300ms      # some users are suffering
p99     = 8000ms     # your worst users are having a terrible time</pre>
<p>Averages hide the tail. Percentiles show it.</p>

<h2>4. Logs - Structured, Not Sentences</h2>

<p>A log line a machine can read beats a sentence a human wrote.</p>

<pre># Bad: free text, nothing can query this
Something went wrong with the user thing again

# Good: structured, every field is queryable
{"timestamp":"2026-10-05T11:04:22Z","level":"error","service":"checkout",
 "msg":"payment failed","userId":4471,"orderId":"ord-9932",
 "durationMs":8123,"error":"gateway_timeout","traceId":"7f2a91c"}</pre>

<p>Every line needs a timestamp, a level, a message, and an identifier you can
follow through the system: a user id, an order id, or a trace id.</p>

<p><strong>Memory trick:</strong> a log without an id in it is a rumour. With an
id it is evidence.</p>

<h3>Log levels</h3>
<table>
<tr><th>Level</th><th>Means</th><th>Who cares</th></tr>
<tr><td>ERROR</td><td>Something failed and a human may need to act</td><td>On call, immediately</td></tr>
<tr><td>WARN</td><td>Odd but handled</td><td>On call, during working hours</td></tr>
<tr><td>INFO</td><td>A significant event happened</td><td>Useful history</td></tr>
<tr><td>DEBUG</td><td>Detail for development</td><td>Nobody, in production</td></tr>
</table>

<p>Logging everything at ERROR to make sure you see the failures is how teams
learn to ignore ERROR.</p>

<h2>5. Traces - Following One Request</h2>

<p>A trace is one request stitched together across every service it touched. Each
hop is a span with a start time, an end time, and a parent, and the whole tree is
drawn as a waterfall.</p>

<p>When a request takes four seconds, a trace tells you which two hundred
milliseconds of it were the database and which two were a payment gateway that
should have been called in parallel.</p>

<p><strong>Memory trick:</strong> logs are a diary, metrics are a chart, traces are
a video. Only the video shows you the shape of the delay.</p>

<h2>6. The ELK Stack - Logs At Scale</h2>

<p>ELK is the traditional answer to "we generate too many logs to grep".</p>

<table>
<tr><th>Piece</th><th>Job</th><th>Analogy</th></tr>
<tr><td>Elasticsearch</td><td>Stores and indexes the logs so they are searchable</td><td>The library</td></tr>
<tr><td>Logstash</td><td>Reads logs from everywhere, parses and enriches them</td><td>The librarian who files them</td></tr>
<tr><td>Kibana</td><td>The web interface for searching and dashboards</td><td>The reading room</td></tr>
</table>

<p>The chain is a pipeline: your apps write logs, a shipper (Filebeat) forwards
them, Logstash parses and enriches, Elasticsearch indexes, Kibana shows it.</p>

<p>Modern stacks increasingly replace Logstash with a lighter shipper such as
Fluent Bit or OpenTelemetry Collector. The shape is the same, and the reason ELK
is worth understanding is that it appears in every job description.</p>

<h2>7. Prometheus And Grafana - Metrics And Dashboards</h2>

<p><strong>Prometheus</strong> scrapes metrics from your services on a schedule
and stores them in a local time-series database. It is pull-based: your services
expose a metrics endpoint and Prometheus comes to collect.</p>

<pre># Is it up?
up{job="api"} 1

# Request rate, by status code
http_requests_total{job="api", status="500"} 47

# Latency as a histogram, which is how percentiles are calculated
http_request_duration_seconds_bucket{le="0.5"} 18234

# How full is the connection pool?
pool_connections_in_use 47
pool_connections_max 50</pre>

<h3>PromQL - asking questions of your metrics</h3>
<pre># Request rate per second over five minutes
rate(http_requests_total[5m])

# Fraction of requests failing, 0 to 1
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))

# 95th percentile latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# CPU across every machine
1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m]))</pre>

<p><strong>Grafana</strong> sits on top and turns those queries into dashboards.
Its real value is not the pretty graphs, it is that everyone looks at the same
screen during an incident instead of comparing notes.</p>

<h2>8. The ELK, Prometheus, Grafana Comparison</h2>

<table>
<tr><th></th><th>Logs (ELK)</th><th>Metrics (Prometheus)</th><th>Traces</th></tr>
<tr><td>Stores</td><td>Individual events</td><td>Numbers over time</td><td>Request waterfalls</td></tr>
<tr><td>Good at</td><td>"What happened to this one request?"</td><td>"Is the system healthy?"</td><td>"Why was this slow?"</td></tr>
<tr><td>Retention</td><td>Days to weeks, then indexed cheaply</td><td>Months, small fixed size</td><td>Days, then sampled</td></tr>
<tr><td>Cost</td><td>The most expensive to store</td><td>The cheapest</td><td>Expensive to instrument</td></tr>
</table>

<h2>9. Alerting - Less Is More</h2>

<p>An alert nobody trusts is worse than no alert, because it teaches the team to
ignore the channel where the real one would arrive.</p>

<table>
<tr><th>Rule</th><th>Reason</th></tr>
<tr><td>Alert on symptoms, not causes</td><td>Pages for high CPU train people to ignore pages for real failures.</td></tr>
<tr><td>Alert on user impact</td><td>"Checkout is failing for 5% of users" beats "CPU is above 80%".</td></tr>
<tr><td>Every alert must be actionable</td><td>If there is no action, it is a dashboard, not a page.</td></tr>
<tr><td>Start with one page per service</td><td>Fifteen alerts per incident means nobody reads any of them.</td></tr>
<tr><td>Test the alert</td><td>Break something on purpose and confirm the page arrives.</td></tr>
</table>

<pre># Prometheus alerting rule: user-facing failure rate
- alert: CheckoutFailing
  expr: |
    sum(rate(http_requests_total{job="checkout",status=~"5.."}[5m]))
      / sum(rate(http_requests_total{job="checkout"}[5m])) &gt; 0.02
  for: 10m
  labels: { severity: page }
  annotations:
    summary: "5% of checkout requests are failing"</pre>

<p><strong>Memory trick:</strong> if the answer to "what would I do about this at
3am" is nothing, it should not be paging anyone.</p>

<h2>10. OpenTelemetry - One Standard For All Three Signals</h2>

<p>Writing logs, metrics and traces with three different libraries is painful.
OpenTelemetry is the vendor-neutral standard that instruments all three from one
piece of code, then exports to whichever backend you use.</p>

<p>Its real value is future proofing: the instrumentation stays the same when you
change from one vendor's monitoring to another.</p>

<p><strong>Try it yourself:</strong> add Prometheus metrics to something small.
Expose an endpoint, scrape it, and graph a counter. Watch a request increment it.
It is the shortest complete example of the whole metric pipeline.</p>

<p><strong>Learning vs production:</strong> on one machine, any of this is an
afternoon. In production you are running several Prometheus servers for
availability, a long-term store, log shipping that survives a node loss, and
alert routing that reaches whoever is actually on call. The concepts do not
change, only the amount of machinery around them.</p>"""
