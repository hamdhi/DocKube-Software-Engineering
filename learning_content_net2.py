"""Chapter 2 - IP addresses: what they are, how they split, how to read them."""

CHAPTER = """<h2>1. What Is an IP Address?</h2>

<p>An IP address is a unique number given to every device that joins a network.
Its only job is to act as a <strong>delivery address</strong>.</p>

<p><strong>Analogy:</strong> your home address. "Flat 4B, 22 Baker Street, London,
NW1 6XE." The flat and number find the exact door, the street and city locate you
quickly, and the postcode helps the postman route efficiently. An IP works the
same way.</p>

<h2>2. IPv4: The Dotted Decimal Form</h2>

<p>An IPv4 address is 32 bits, written as four numbers between 0 and 255 separated
by dots, such as <code>192.168.10.25</code>.</p>

<p>Why four groups? Because 32 bits split into four chunks of 8 bits gives four
numbers, and each 8-bit chunk can represent 0 to 255.</p>

<table>
<tr><th>Octet</th><th>Decimal</th><th>Binary (8 bits)</th></tr>
<tr><td>1</td><td>192</td><td>11000000</td></tr>
<tr><td>2</td><td>168</td><td>10101000</td></tr>
<tr><td>3</td><td>10</td><td>00001010</td></tr>
<tr><td>4</td><td>25</td><td>00011001</td></tr>
</table>

<h3>Converting decimal to binary by hand</h3>
<p>Each set bit is worth a power of two counted from the right: 1, 2, 4, 8, 16, 32,
64, 128. For 192 that is 128 plus 64:</p>
<pre>128  64  32  16  8  4  2  1
 1    1   0   0   0  0  0  0   = 11000000</pre>

<p><strong>Memory trick:</strong> memorise that single row as
<b>128 64 32 16 8 4 2 1</b>. Any decimal number is just a sum of those values.
Once you can read that row both ways, binary is finished.</p>

<h2>3. IPv6 - Why It Exists</h2>

<p>IPv4 offers about 4.3 billion addresses and the internet ran out. IPv6 is 128
bits, giving roughly 3.4 x 10 to the power 38 addresses.</p>

<table>
<tr><th>Version</th><th>Bits</th><th>Written as</th><th>Total space</th></tr>
<tr><td>IPv4</td><td>32</td><td>Dotted decimal, for example 192.168.10.25</td><td>About 4.3 billion</td></tr>
<tr><td>IPv6</td><td>128</td><td>Eight hex groups, for example 2001:db8::1</td><td>About 3.4 x 10^38</td></tr>
</table>

<p>The address <code>2001:0db8:0000:0000:0000:0000:0000:0001</code> shortens to
<code>2001:db8::1</code>. The double colon means "fill the rest with zeros" and
may appear only once.</p>

<h2>4. Public vs Private Addresses</h2>

<p>This is the single most important idea for a beginner. Not every IP reaches the
internet.</p>

<table>
<tr><th>Range</th><th>Name</th><th>Reachable from the internet?</th></tr>
<tr><td>10.0.0.0 - 10.255.255.255</td><td>Private, 10/8</td><td>No, only inside your network</td></tr>
<tr><td>172.16.0.0 - 172.31.255.255</td><td>Private, 172.16/12</td><td>No, only inside your network</td></tr>
<tr><td>192.168.0.0 - 192.168.255.255</td><td>Private, 192.168/16</td><td>No, only inside your network</td></tr>
<tr><td>127.0.0.1</td><td>Loopback</td><td>No, means this machine</td></tr>
<tr><td>0.0.0.0</td><td>Any / unspecified</td><td>Means all interfaces when binding</td></tr>
<tr><td>169.254.x.x</td><td>Link-local, APIPA</td><td>Self-assigned when DHCP fails</td></tr>
<tr><td>Everything else</td><td>Public</td><td>Yes, if routing allows it</td></tr>
</table>

<p><strong>Memory trick:</strong> 10 is the easy one, 172 is the middle one, 192
is the one you see at home. Learn them as 10, 172, 192 and they will not slip.</p>

<p><strong>Why private addresses exist:</strong> IPv4 ran short. NAT lets thousands
of private devices share one public IP. Your laptop uses 192.168.1.42, the router
owns 203.0.113.7, and the router swaps the numbers as packets leave and
return.</p>

<h2>5. How an IP Address Splits - The Core Concept</h2>

<p>This is what subnetting rests on. Every IP is divided into two parts:</p>

<ul>
<li><strong>Network portion</strong> - which street you are on</li>
<li><strong>Host portion</strong> - which house number on that street</li>
</ul>

<p>The <strong>subnet mask</strong> is the rule that says where the split falls. In
binary it is a run of 1s followed by a run of 0s.</p>

<p>Take <code>192.168.10.25/24</code> whose mask is <code>255.255.255.0</code>:</p>

<table>
<tr><th>Part</th><th>Address</th><th>Mask</th><th>Binary mask</th><th>Meaning</th></tr>
<tr><td>Network</td><td>192.168.10</td><td>255.255.255</td><td>11111111.11111111.11111111</td><td>The street</td></tr>
<tr><td>Host</td><td>25</td><td>0</td><td>00000000</td><td>The house number</td></tr>
</table>

<h3>The rule you will use forever</h3>
<p>Write the mask in binary, count the 1s, and that number is the CIDR prefix.</p>

<pre>255.255.255.0
11111111 . 11111111 . 11111111 . 00000000
 24 ones -> /24

255.255.254.0
11111111 . 11111111 . 11111110 . 00000000
 23 ones -> /23</pre>

<p><strong>Memory trick:</strong> the prefix length is simply the count of 1s in
the mask. Nothing else. Count the ones and you have your answer.</p>

<h3>How a computer decides local or remote</h3>
<p>To send a packet, your machine ANDs the destination address with the mask. If
the result equals its own network portion, the destination is local and it uses a
MAC address. Otherwise it hands the packet to the gateway.</p>

<pre>My IP:       192.168.10.25
Mask:        255.255.255.0
My network:  192.168.10.0

To 192.168.10.99 -> same network  -> send directly using MAC
To 8.8.8.8       -> other network -> send to the gateway</pre>

<p>That single comparison is why your printer at 192.168.1.50 answers directly,
while a website has to go through the router.</p>

<h2>6. Special Addresses Worth Memorising</h2>

<table>
<tr><th>Address</th><th>Meaning</th><th>Note</th></tr>
<tr><td>0.0.0.0</td><td>Any address, all interfaces</td><td>Use when a server should bind everywhere</td></tr>
<tr><td>127.0.0.1</td><td>Localhost, this machine</td><td>Never leaves your computer</td></tr>
<tr><td>255.255.255.255</td><td>Broadcast</td><td>Every device on the local network</td></tr>
<tr><td>x.x.x.0 for a /24</td><td>Network address of the subnet</td><td>Cannot be assigned to a host</td></tr>
<tr><td>x.x.x.255 for a /24</td><td>Broadcast for that subnet</td><td>Cannot be assigned to a host</td></tr>
</table>

<h2>7. Commands</h2>
<pre>ipconfig /all
ip addr show
ping 192.168.10.1
tracert 8.8.8.8
nslookup google.com</pre>

<h2>8. Try It Yourself (15 minutes)</h2>
<ul>
<li>Run <code>ipconfig /all</code> and find your IPv4 address and subnet mask.</li>
<li>Count the 1s in your mask and write the CIDR beside it.</li>
<li>Work out your network address by ANDing your IP with the mask.</li>
<li>Ping your own IP; it replies instantly without leaving the machine.</li>
<li>Compare your IP with your router gateway. Matching first three octets means
traffic never touches the internet.</li>
</ul>

<h2>9. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Addressing</td><td>192.168.1.x handed out by your home router</td><td>Planned CIDR blocks reserved per environment</td></tr>
<tr><td>Overlaps</td><td>Overlap with home and ignore it</td><td>Overlapping VPCs break VPN routing and must be planned</td></tr>
<tr><td>Public IPs</td><td>None, everything stays private</td><td>Rarely used; load balancers and NAT gateways instead</td></tr>
<tr><td>IPv6</td><td>Often switched off entirely</td><td>Frequently mandatory on cloud providers</td></tr>
<tr><td>Allocation</td><td>Typed manually in a terminal</td><td>IPAM, DHCP scopes, Terraform, Kubernetes Services</td></tr>
<tr><td>Source of truth</td><td>Your memory</td><td>IPAM, so no engineer guesses</td></tr>
</table>

<h2>10. Key Takeaways</h2>
<ul>
<li>An IP address is a delivery address split into network and host parts.</li>
<li>IPv4 is 32 bits as four numbers; IPv6 is 128 bits as eight hex groups.</li>
<li>The prefix length is just the count of 1s in the subnet mask.</li>
<li>10, 172.16-31 and 192.168 are private and never route to the internet.</li>
<li>Same network means direct delivery; a different network means via the gateway.</li>
</ul>
"""