"""Chapter 1 - Networking fundamentals for absolute beginners.

Every chapter follows the same teaching shape so the material is predictable:

  1. What it is      - a plain-English analogy with no jargon
  2. How it works    - step by step, with real numbers
  3. How to remember - a mnemonic or shortcut that actually sticks
  4. Commands        - real, copy-pasteable commands
  5. Try it yourself - a short hands-on exercise
  6. Learning vs Production - what changes when it is real
"""

CHAPTER = """<h2>1. What Is a Network?</h2>

<p>A network is simply two or more computers that can talk to each other. That
is the whole idea. Everything else - routers, subnets, protocols, DNS - exists
only to make that conversation reliable, fast and private.</p>

<p><strong>The best analogy:</strong> a city. Houses are computers, streets are
networks, house numbers are IP addresses, and postal codes are subnet masks.
The postman is the router. A phone book is DNS.</p>

<h3>Why bother connecting machines?</h3>
<ul>
<li><strong>Share resources</strong> - one printer, one disk, one licence.</li>
<li><strong>Share data</strong> - your web browser fetches pages from servers.</li>
<li><strong>Separate concerns</strong> - the database runs on a different machine
so it can be scaled and secured independently.</li>
<li><strong>Reliability</strong> - if one machine dies, the service keeps
running somewhere else.</li>
</ul>

<h2>2. Packets: How Data Actually Moves</h2>

<p>When you send data it is not sent as one giant lump. It is chopped into small
pieces called <strong>packets</strong>. Each packet carries a label saying where
it came from and where it is going.</p>

<p><strong>Analogy:</strong> posting a book. You do not courier the whole book in
one van. You split it into chapters, put each in an envelope with an address, and
a courier delivers them. The envelopes may arrive in any order, but the reader
reassembles the book.</p>

<p>Why split it?</p>
<ul>
<li>If one packet is lost, you resend only that packet, not the whole file.</li>
<li>Different packets can take different routes across the internet.</li>
<li>Several computers can share the same cable at the same time.</li>
</ul>

<h3>The layers of a packet</h3>
<p>Every packet is built in layers, like envelopes inside envelopes. Each layer
only talks to the layers above and below it, which is why you can replace a
cable without rewriting the application.</p>

<table>
<tr><th>OSI Layer</th><th>What it does</th><th>Example protocols</th><th>Typical device</th></tr>
<tr><td>7 Application</td><td>What the data means</td><td>HTTP, DNS, SSH, SMTP</td><td>Your computer</td></tr>
<tr><td>6 Presentation</td><td>Encoding, compression, encryption</td><td>TLS, JPEG, ASCII</td><td>Your computer</td></tr>
<tr><td>5 Session</td><td>Start, sync and end conversations</td><td>NetBIOS, RPC, Sockets</td><td>Server</td></tr>
<tr><td>4 Transport</td><td>Reliable delivery, ports, segmentation</td><td>TCP, UDP</td><td>Firewall, load balancer</td></tr>
<tr><td>3 Network</td><td>Logical addressing and routing between networks</td><td>IP, ICMP, BGP</td><td>Router, L3 switch</td></tr>
<tr><td>2 Data Link</td><td>Local delivery using MAC addresses and frames</td><td>Ethernet, Wi-Fi, ARP</td><td>Switch, NIC, access point</td></tr>
<tr><td>1 Physical</td><td>Actual signals on wire or radio</td><td>Cables, fibre, radio</td><td>Cable, transceiver</td></tr>
</table>

<p><strong>Memory trick for OSI, bottom up:</strong> Please Do Not Throw
Sausage Pizza Away.</p>
<p>1 Physical, 2 Data Link, 3 Network, 4 Transport, 5 Session, 6 Presentation,
7 Application.</p>

<h2>3. The Two Models You Must Know</h2>

<h3>OSI (7 layers) - the teaching model</h3>
<p>OSI is what textbooks and interviews use. Excellent for reasoning, rarely used
in real configuration.</p>

<h3>TCP/IP (4 layers) - the real internet</h3>
<p>This is what actually runs on the internet, and what you will configure.</p>

<table>
<tr><th>TCP/IP layer</th><th>Maps to OSI</th><th>Real protocols</th></tr>
<tr><td>Application</td><td>Layers 7, 6, 5</td><td>HTTP, HTTPS, DNS, SSH, FTP, DHCP</td></tr>
<tr><td>Transport</td><td>Layer 4</td><td>TCP, UDP</td></tr>
<tr><td>Internet</td><td>Layer 3</td><td>IP, ICMP, ARP, BGP</td></tr>
<tr><td>Network Access</td><td>Layers 2, 1</td><td>Ethernet, Wi-Fi, cables, MAC addresses</td></tr>
</table>

<h2>4. Key Words You Will Hear Immediately</h2>

<table>
<tr><th>Word</th><th>Plain English</th><th>Why you care</th></tr>
<tr><td>Latency</td><td>Delay before data arrives</td><td>Users judge a site as slow even when throughput is fine</td></tr>
<tr><td>Bandwidth</td><td>Maximum capacity of a link</td><td>The size of the pipe, not the flow speed</td></tr>
<tr><td>Throughput</td><td>Actual useful data per second</td><td>Always lower than bandwidth because of overhead</td></tr>
<tr><td>Jitter</td><td>Variation in latency</td><td>Kills VoIP and video quality more than high latency does</td></tr>
<tr><td>MTU</td><td>Largest packet allowed on a link</td><td>A mismatch causes silent fragmentation or drops</td></tr>
<tr><td>Subnet</td><td>A slice of a bigger network</td><td>How an organisation splits into departments</td></tr>
<tr><td>Gateway</td><td>Doorway into another network</td><td>Where your traffic leaves</td></tr>
<tr><td>NAT</td><td>Translation of private IPs to a public IP</td><td>How thousands of devices share one public address</td></tr>
<tr><td>Subnet mask</td><td>Which part of the IP is the street</td><td>Decides who is local and who needs a router</td></tr>
</table>

<h2>5. Latency vs Bandwidth - The Classic Confusion</h2>

<p><strong>Bandwidth is the width of the pipe. Latency is the length of the
pipe.</strong> A fat but very long pipe (high bandwidth, high latency) feels
slow. A thin but short pipe (low bandwidth, low latency) feels instant.</p>

<p>This is why a satellite link can offer more bandwidth than fibre yet feel
slower: roughly 600 ms round trip just for the signal to bounce off a
satellite.</p>

<h2>6. Try It Yourself (10 minutes)</h2>
<pre>ping 8.8.8.8
tracert google.com
ipconfig /all
nslookup github.com</pre>

<ul>
<li><strong>ping</strong> tests reachability and shows round-trip time in ms.</li>
<li><strong>tracert</strong> shows every hop a packet passes through.</li>
<li><strong>ipconfig /all</strong> shows your IP, mask, gateway and DNS servers.</li>
<li><strong>nslookup</strong> asks a DNS server to turn a name into an address.</li>
</ul>

<h2>7. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Network size</td><td>One laptop, maybe a Raspberry Pi</td><td>VPCs or VLANs across regions</td></tr>
<tr><td>Latency</td><td>Negligible, everything local</td><td>Milliseconds accumulate; users abandon slow pages</td></tr>
<tr><td>Bandwidth</td><td>Home Wi-Fi, gigabit</td><td>Shaped, metered and billed per GB</td></tr>
<tr><td>Failure</td><td>Unplug and restart</td><td>Redundant paths, health checks, automated failover</td></tr>
<tr><td>Security</td><td>Open ports on your home router</td><td>Firewalls, least privilege, network segmentation</td></tr>
<tr><td>Visibility</td><td>None at all</td><td>Metrics, logs and alerts on latency, loss and errors</td></tr>
<tr><td>Documentation</td><td>It is all in your head</td><td>Written network diagrams and runbooks</td></tr>
</table>

<h2>8. Key Takeaways</h2>
<ul>
<li>A network is just computers talking; everything else is detail.</li>
<li>Data travels as small labelled packets, not one lump.</li>
<li>OSI has 7 layers for theory; TCP/IP has 4 for reality.</li>
<li>Bandwidth is pipe width, latency is pipe length, and users feel latency.</li>
<li>The concepts are identical in production; failure and visibility are not.</li>
</ul>
"""