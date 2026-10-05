"""Chapter 4 - Ports and sockets, and how processes claim them."""

CHAPTER = """<h2>1. What Is a Port?</h2>

<p>An IP address gets a packet to the right machine. A <strong>port</strong> gets
it to the right program on that machine.</p>

<p><strong>Analogy:</strong> the IP is the building address and the port is the flat
number inside. 22 Baker Street (IP), flat 4B (port). Many apps can run on one
machine only because their doors have different numbers.</p>

<p>Both numbers fit into one value, a <strong>socket</strong>: an IP address plus a
port. A TCP socket is written as <code>192.168.1.10:8080</code>.</p>

<h2>2. Why Not One Service Per Machine?</h2>

<p>Before ports existed, a machine could run one network service at a time. Ports
let many programs share one IP. Your laptop is simultaneously running a web
server on 8000, a database on 5432 and a remote shell on 22.</p>

<h2>3. Port Ranges</h2>

<table>
<tr><th>Range</th><th>Name</th><th>Purpose</th><th>Examples</th></tr>
<tr><td>0 - 1023</td><td>Well-known</td><td>Standard services, need admin rights to bind</td><td>22 SSH, 25 SMTP, 53 DNS, 80 HTTP, 443 HTTPS</td></tr>
<tr><td>1024 - 49151</td><td>Registered</td><td>Applications registered with IANA</td><td>3306 MySQL, 5432 Postgres, 27017 MongoDB</td></tr>
<tr><td>49152 - 65535</td><td>Dynamic or ephemeral</td><td>Temporary client ports chosen by the OS</td><td>A browser picks a random source port</td></tr>
</table>

<p><strong>Memory trick:</strong> the ones you will see constantly number under
1000, and the number usually hints at the service. 22 SSH, 53 DNS, 80 HTTP,
443 HTTPS.</p>

<h2>4. Ports You Will Meet Every Day</h2>

<table>
<tr><th>Port</th><th>Protocol</th><th>Used by</th></tr>
<tr><td>20, 21</td><td>FTP</td><td>File transfer, insecure</td></tr>
<tr><td>22</td><td>SSH, SFTP</td><td>Secure remote shell and file transfer</td></tr>
<tr><td>25</td><td>SMTP</td><td>Sending mail between servers</td></tr>
<tr><td>53</td><td>DNS</td><td>Turning names into IP addresses</td></tr>
<tr><td>80</td><td>HTTP</td><td>Unencrypted web traffic</td></tr>
<tr><td>443</td><td>HTTPS</td><td>Encrypted web traffic, also many APIs</td></tr>
<tr><td>3306</td><td>MySQL</td><td>MySQL database</td></tr>
<tr><td>5432</td><td>Postgres</td><td>PostgreSQL database</td></tr>
<tr><td>6379</td><td>Redis</td><td>In-memory cache and datastore</td></tr>
<tr><td>8080</td><td>HTTP alt</td><td>Jenkins, proxies, dev servers</td></tr>
<tr><td>27017</td><td>MongoDB</td><td>MongoDB database</td></tr>
<tr><td>6443</td><td>HTTPS</td><td>Kubernetes API server</td></tr>
</table>

<h2>5. Connections Use Two Ports - This Confuses Everyone</h2>

<p>When you browse to a site on port 443, your machine also opens an
<strong>ephemeral port</strong> of its own. Every connection needs a port at each
end.</p>

<pre>Your machine (192.168.1.10:54321)  -->  Website (93.184.216.34:443)
          source port                          destination port</pre>

<p>Your OS picks the source port automatically from the ephemeral range, and the
server replies back to 192.168.1.10:54321. Many simultaneous connections are
possible because each uses a different source port.</p>

<h2>6. One IP Can Only Use a Port Once, Per Protocol</h2>

<p>Two processes cannot both listen on 192.168.1.10:8080 over TCP. The second
fails with <em>address already in use</em>. That is why you must stop the old
process before starting a new one on the same port.</p>

<p>TCP and UDP are tracked separately, so TCP 8080 and UDP 8080 can coexist on the
same machine.</p>

<h2>7. Finding and Killing a Process by Port</h2>

<p>Use the Port Manager in this app, or work from the command line:</p>

<pre># Windows: find what is using a port
netstat -ano | findstr :8080
tasklist /FI "PID eq 1234"
taskkill /PID 1234 /F /T

# Linux and macOS
lsof -i :8080
netstat -tulnp | grep 8080
kill -9 1234</pre>

<p>Worth remembering: <b>-ano</b> shows all, numeric and owning PID. <b>/F</b>
forces the kill. <b>/T</b> also kills child processes.</p>

<h2>8. Reading netstat States</h2>

<table>
<tr><th>State</th><th>Meaning</th><th>What to do</th></tr>
<tr><td>LISTENING</td><td>A server is waiting for connections</td><td>Usually a service you started</td></tr>
<tr><td>ESTABLISHED</td><td>An active conversation</td><td>Leave it alone unless you know why</td></tr>
<tr><td>TIME_WAIT</td><td>Closed, waiting to be sure nothing returns</td><td>Normal after a short connection closes</td></tr>
<tr><td>CLOSE_WAIT</td><td>Remote side closed but we have not</td><td>Often a sign of a buggy application</td></tr>
<tr><td>SYN_SENT</td><td>Connection attempt in progress</td><td>Normal during connect, or a firewall dropping you</td></tr>
</table>

<h2>9. Try It Yourself (10 minutes)</h2>
<ul>
<li>Open the Port Manager in the sidebar of this app and press Refresh.</li>
<li>Search for a port you know, such as 5432 or 3306.</li>
<li>Run <code>netstat -ano | findstr LISTENING</code> and compare with the table.</li>
<li>Notice how many processes share port 80 and explain why.</li>
<li>Start a small server and watch it appear: <code>python -m http.server 8080</code></li>
</ul>

<h2>10. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Exposure</td><td>Server on localhost, fire and forget</td><td>Bound to 0.0.0.0 behind a load balancer and firewall</td></tr>
<tr><td>Ingress</td><td>kubectl port-forward for everything</td><td>Ingress controller plus a managed load balancer and TLS</td></tr>
<tr><td>Port choice</td><td>Anything free</td><td>Well-known ports, documented and reserved</td></tr>
<tr><td>Discovery</td><td>netstat by hand</td><td>Service mesh, metrics, automated port inventory</td></tr>
<tr><td>Many replicas</td><td>One process, one port</td><td>Many pods share a Service that load balances</td></tr>
<tr><td>Security</td><td>Assume everyone is friendly</td><td>Security groups, NetworkPolicy, least exposure</td></tr>
</table>

<h2>11. Key Takeaways</h2>
<ul>
<li>IP finds the machine, port finds the program.</li>
<li>Well-known ports are 0-1023; ephemeral ports are chosen automatically.</li>
<li>Every connection uses one source port and one destination port.</li>
<li>Two TCP programs cannot share one port on one IP.</li>
<li>netstat -ano with taskkill is how you free a stuck port.</li>
<li>In production you rarely expose a port directly; you put a proxy in front.</li>
</ul>
"""