"""Chapter 5 - TCP vs UDP, and how to choose."""

CHAPTER = """<h2>1. What Are They?</h2>

<p>TCP and UDP are the two transport protocols at OSI layer 4. TCP is careful and
reliable; UDP is fast and careless. Both move data between two ports.</p>

<p><strong>Analogy:</strong> TCP is registered post with tracking and a signature.
UDP is a courier who sprints to your door and hands over the parcel without
checking any ID.</p>

<h2>2. The TCP Three-Way Handshake</h2>

<p>Before any data flows, both sides confirm they can hear each other. That buys
reliability and ordering.</p>

<pre>Client                          Server
  | ---- SYN -------------------> |   I would like to connect
  | <--- SYN + ACK -------------- |   Yes, and I would like to connect
  | ---- ACK -------------------> |   Great, we agree
  | ---- DATA ------------------> |   The conversation starts</pre>

<ul>
<li><strong>SYN</strong> - I want to open a connection.</li>
<li><strong>SYN + ACK</strong> - I agree, and I also want to connect.</li>
<li><strong>ACK</strong> - Confirmed by both sides.</li>
</ul>

<p>UDP sends data immediately, with no handshake at all.</p>

<h2>3. Side by Side Comparison</h2>

<table>
<tr><th>Feature</th><th>TCP</th><th>UDP</th></tr>
<tr><td>Connection</td><td>Handshake first, then data</td><td>None, just send</td></tr>
<tr><td>Reliability</td><td>Lost packets are resent</td><td>No resending</td></tr>
<tr><td>Ordering</td><td>Reassembled in order</td><td>Arrival order not guaranteed</td></tr>
<tr><td>Speed</td><td>Slower, more handshaking</td><td>Very fast, no waiting</td></tr>
<tr><td>Header size</td><td>20 bytes or more</td><td>8 bytes</td></tr>
<tr><td>Congestion control</td><td>Yes, slows down when congested</td><td>No, can flood the network</td></tr>
<tr><td>Flow control</td><td>Yes, protects the receiver</td><td>No</td></tr>
<tr><td>Broadcast and multicast</td><td>Not possible</td><td>Supported</td></tr>
<tr><td>Data unit</td><td>A byte stream</td><td>Discrete messages</td></tr>
</table>

<h2>4. How to Remember the Choice</h2>

<p><strong>Use TCP when losing data would be wrong</strong>: web pages, email, file
transfers, databases, SSH.</p>

<p><strong>Use UDP when being late is worse than losing something</strong>: live
video, voice calls, gaming, DNS lookups.</p>

<p><strong>Memory trick:</strong> TCP is <b>T</b>rouble-free, <b>C</b>autious,
<b>P</b>atient. UDP is <b>U</b>nreliable but <b>D</b>azzlingly quick.</p>

<h2>5. Real Examples - Know Which One Each Uses</h2>

<table>
<tr><th>Application</th><th>Protocol</th><th>Why</th></tr>
<tr><td>HTTP and HTTPS</td><td>TCP</td><td>A page must arrive complete</td></tr>
<tr><td>SSH and SFTP</td><td>TCP</td><td>Interactive commands cannot be lost</td></tr>
<tr><td>Email, SMTP, IMAP</td><td>TCP</td><td>Partial mail is useless</td></tr>
<tr><td>Database traffic</td><td>TCP</td><td>Corrupt queries are unacceptable</td></tr>
<tr><td>DNS lookup</td><td>UDP</td><td>One small question, one small answer</td></tr>
<tr><td>DHCP</td><td>UDP</td><td>Broadcast discovery before any IP exists</td></tr>
<tr><td>Video and voice calls</td><td>UDP</td><td>A late frame is worthless, drop it</td></tr>
<tr><td>Online gaming</td><td>UDP</td><td>Position updates must be current</td></tr>
<tr><td>Streaming live TV</td><td>UDP</td><td>Continuity beats completeness</td></tr>
</table>

<p>DNS is the classic surprise. People assume DNS uses TCP, but ordinary lookups
use UDP port 53 because the question and answer are tiny. TCP is used when the
response is too large for a single packet and for zone transfers between DNS
servers.</p>

<h2>6. Flow Control and Congestion Control</h2>

<p><strong>Flow control</strong> stops a fast sender drowning a slow receiver. TCP
uses a sliding window and signals "I have room for N more bytes right now".</p>

<p><strong>Congestion control</strong> stops the network being overwhelmed by too
many senders. TCP increases its rate cautiously and backs off when it detects
loss, which it treats as a sign of congestion.</p>

<p>UDP does neither, which is why large UDP floods are dangerous to a network.</p>

<h2>7. Seeing It in Practice</h2>
<pre># Windows: test a TCP port
Test-NetConnection -ComputerName example.com -Port 443

# Windows: test a UDP port
Test-NetConnection -ComputerName 1.1.1.1 -Port 53 -Udp

# Linux and macOS
nc -vz example.com 443
ss -tan state established</pre>

<h2>8. Try It Yourself (15 minutes)</h2>
<ul>
<li>Run <code>Test-NetConnection example.com -Port 443</code> and read
<span>TCPTestSucceeded</span>.</li>
<li>Compare the timing against a filtered port. Notice the difference between
connection refused and a timeout.</li>
<li>Run the UDP variant against port 53 and observe the speed.</li>
<li>Run <code>nslookup</code> and notice how instant it is, because DNS uses UDP.</li>
</ul>

<h2>9. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Handshake cost</td><td>Hardly noticed on localhost</td><td>Dominates at scale, so connections are reused</td></tr>
<tr><td>HTTP</td><td>New connection every request</td><td>HTTP/2 or HTTP/3 multiplex over one connection</td></tr>
<tr><td>UDP usage</td><td>Mostly DNS and games</td><td>Also QUIC, service meshes, telemetry and load testing</td></tr>
<tr><td>Congestion</td><td>Single flow, no issue</td><td>Latency and loss actively managed and monitored</td></tr>
<tr><td>Timeouts</td><td>Long, just retry</td><td>Tight budgets with backoff and circuit breakers</td></tr>
<tr><td>Default choice</td><td>TCP everywhere</td><td>Still TCP, with UDP only where latency is critical</td></tr>
</table>

<h2>10. Key Takeaways</h2>
<ul>
<li>TCP handshakes first, then guarantees order and resends losses.</li>
<li>UDP sends immediately with no guarantees at all.</li>
<li>TCP when losing data would be wrong; UDP when lateness is worse.</li>
<li>Web, SSH and databases use TCP; DNS, video calls and gaming use UDP.</li>
<li>TCP has flow and congestion control; UDP has neither.</li>
<li>Production mostly runs TCP, using UDP where latency really matters.</li>
</ul>
"""