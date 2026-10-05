"""Chapter 7 - Network devices and the layer each one works at."""

CHAPTER = """<h2>1. The Devices, Side by Side</h2>

<p>Each device has one main job and one OSI layer it belongs to. Learn the table
and the rest follows.</p>

<table>
<tr><th>Device</th><th>OSI layer</th><th>Its one job</th><th>Knows about</th><th>Does not know</th></tr>
<tr><td>Repeater or hub</td><td>1 Physical</td><td>Boost the signal</td><td>Electrical signals</td><td>Anything above</td></tr>
<tr><td>Bridge or switch</td><td>2 Data Link</td><td>Connect devices, forward by MAC</td><td>MAC addresses</td><td>IP addresses, networks</td></tr>
<tr><td>Router</td><td>3 Network</td><td>Move traffic between networks</td><td>IP addresses, routing tables</td><td>Which application is talking</td></tr>
<tr><td>Modem</td><td>1 Physical</td><td>Convert digital data to a line signal</td><td>Signal modulation</td><td>Nothing above</td></tr>
<tr><td>Access point</td><td>2 Data Link</td><td>Bridge Wi-Fi to wired Ethernet</td><td>MAC addresses</td><td>Routing</td></tr>
<tr><td>Firewall</td><td>3 and 4</td><td>Allow or block traffic by rule</td><td>IP, ports, sometimes app data</td><td>Content unless it inspects deeply</td></tr>
<tr><td>Load balancer</td><td>4 and 7</td><td>Spread requests across servers</td><td>Ports, and at L7 URLs and headers</td><td>Data correctness</td></tr>
<tr><td>Proxy</td><td>7 Application</td><td>Terminate a connection and forward it</td><td>The application protocol</td><td>Routing</td></tr>
</table>

<h2>2. Switch vs Router - The Classic Question</h2>

<p>A switch connects things in the <strong>same</strong> network. A router
connects <strong>different</strong> networks. That is the entire difference.</p>

<table>
<tr><th>Aspect</th><th>Switch, layer 2</th><th>Router, layer 3</th></tr>
<tr><td>Uses</td><td>MAC addresses</td><td>IP addresses</td></tr>
<tr><td>Keeps a table of</td><td>MAC address table</td><td>Routing table</td></tr>
<tr><td>Connects</td><td>Devices on one subnet</td><td>Different subnets or networks</td></tr>
<tr><td>Broadcasts</td><td>Floods within the VLAN, never routed</td><td>Does not forward them by default</td></tr>
<tr><td>Typical device</td><td>Access switch in a rack</td><td>Home router, core router, gateway</td></tr>
<tr><td>Analogy</td><td>A corridor inside one building</td><td>The street between two buildings</td></tr>
</table>

<p><strong>Memory trick:</strong> a switch moves data <b>within</b> a street using
house numbers; a router moves it <b>between</b> streets using postcodes.</p>

<h2>3. A Packet's Journey Through a Home Network</h2>

<pre>1. Laptop 192.168.1.10 wants example.com
2. Laptop builds the packet, destination 93.184.216.34
3. Laptop checks its mask: 93.184.216.34 is NOT local
4. Laptop sends the frame to its gateway 192.168.1.1, using the
   gateway's MAC address which it found with ARP
5. Switch forwards that frame to the router port, by MAC lookup
6. Router rewrites the frame header, decrements the TTL and looks
   up the destination in its routing table
7. Router hands the packet to the ISP
8. ISP routers hop by hop until the packet reaches the server
9. The reply returns along the same path in reverse</pre>

<p>Each device rewrites only the part it understands: the switch changes the MAC
header, the router changes the IP TTL and checksum.</p>

<h2>4. How MAC and IP Work Together</h2>

<p>ARP asks "who has 192.168.1.1?" on the local network and the reply carries a MAC
address. ARP works only inside one subnet, because it is a broadcast and
broadcasts do not cross routers.</p>

<table>
<tr><th>Address</th><th>Layer</th><th>Scope</th><th>Changes at</th></tr>
<tr><td>IP</td><td>3</td><td>End to end across the whole internet</td><td>Every router decrements the TTL</td></tr>
<tr><td>MAC</td><td>2</td><td>One local link only</td><td>Every switch and router rewrites it</td></tr>
</table>

<p><strong>Memory trick:</strong> IP is the parcel address and stays the same end
to end. MAC is the label on the van, rewritten at every depot.</p>

<h2>5. VLANs - Virtual LANs</h2>

<p>A VLAN splits one physical switch into several logical ones. Ports in VLAN 10
cannot reach ports in VLAN 20 without a router. That is segmentation without
running extra cables.</p>

<p>A trunk port carries several VLANs at once using 802.1Q tags, which is how
switches connect to each other and to routers.</p>

<h2>6. NAT - Why Private IPs Work</h2>

<p>NAT rewrites the source address on the way out and reverses it on the way
back. Your laptop uses 192.168.1.42, the router owns 203.0.113.7, and everyone
outside sees only the router. Thousands of devices can share one public
address.</p>

<p>The trade-off is that unsolicited inbound traffic has nowhere to go, which is
why inbound servers need port forwarding or a public address.</p>

<h2>7. DHCP - Addresses on Tap</h2>

<p>DHCP hands out addresses automatically in four steps, remembered as
<strong>DORA</strong>:</p>

<table>
<tr><th>Step</th><th>Letter</th><th>Meaning</th></tr>
<tr><td>1</td><td>Discover</td><td>Client broadcasts "is there a DHCP server?"</td></tr>
<tr><td>2</td><td>Offer</td><td>Server offers an address from its pool</td></tr>
<tr><td>3</td><td>Request</td><td>Client asks for that specific address</td></tr>
<tr><td>4</td><td>Acknowledge</td><td>Server confirms and records the lease</td></tr>
</table>

<p><strong>Memory trick:</strong> DORA. Discover, Offer, Request, Acknowledge.</p>

<h2>8. Try It Yourself (15 minutes)</h2>
<ul>
<li>Run <code>ipconfig</code> and find your default gateway.</li>
<li>Run <code>arp -a</code> to see the MAC addresses your machine has learned.</li>
<li>Run <code>tracert 8.8.8.8</code> and notice which hop is your router.</li>
<li>On Windows use <code>ipconfig /release</code> then <code>ipconfig /renew</code> to watch DORA happen.</li>
<li>Log into your home router and list connected devices to see the switch table.</li>
</ul>

<h2>9. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Switching</td><td>One home router doing everything</td><td>Access, distribution and core layers, all redundant</td></tr>
<tr><td>Segmentation</td><td>Probably none at all</td><td>VLANs per environment plus NetworkPolicy in Kubernetes</td></tr>
<tr><td>Routing</td><td>Static routes only</td><td>BGP between sites and clouds, with summarisation</td></tr>
<tr><td>Addressing</td><td>DHCP straight from the router</td><td>Central IPAM with strict ownership per team</td></tr>
<tr><td>Redundancy</td><td>None</td><td>Redundant links, spanning tree or MLAG, dual-homed uplinks</td></tr>
<tr><td>Visibility</td><td>None</td><td>SNMP, streaming telemetry, flow logs</td></tr>
</table>

<h2>10. Key Takeaways</h2>
<ul>
<li>Switch means layer 2 and MAC; router means layer 3 and IP.</li>
<li>MAC addresses are local and rewritten; IP addresses are end to end.</li>
<li>ARP only works inside one subnet because broadcasts do not cross routers.</li>
<li>VLANs give segmentation over a single physical switch.</li>
<li>NAT lets many private devices share one public address.</li>
<li>DHCP is DORA: Discover, Offer, Request, Acknowledge.</li>
</ul>
"""