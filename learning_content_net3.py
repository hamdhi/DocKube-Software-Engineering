"""Chapter 3 - Subnetting, with the shortcuts that make it stick."""

CHAPTER = """<h2>1. Why Subnet at All?</h2>

<p>One flat network is simple until it breaks. In a single subnet every device
sees every other device, broadcast traffic floods everywhere, and you cannot apply
different rules to different teams. Subnetting slices one big network into
smaller logical networks.</p>

<p><strong>Analogy:</strong> one giant open-plan floor versus a building divided
into departments. They share the same postal address, but each has its own
internal number range and its own secured door.</p>

<p>Subnets give you:</p>
<ul>
<li><strong>Segmentation</strong> - a breach in one subnet does not expose all.</li>
<li><strong>Efficiency</strong> - smaller broadcast domains, less wasted space.</li>
<li><strong>Organisation</strong> - engineering, finance and guests look different.</li>
<li><strong>Flexibility</strong> - separate policies, routes and DHCP scopes.</li>
</ul>

<h2>2. CIDR Notation</h2>

<p>CIDR is an address followed by a slash and the prefix length, for example
<code>10.0.0.0/16</code>. The number after the slash says how many of the 32 bits
belong to the network. A /24 means 24 network bits and 8 host bits, and those 8
host bits decide how many addresses exist.</p>

<h2>3. The Magic Number Table - Memorise This</h2>

<p>This single table answers almost every subnetting question.</p>

<table>
<tr><th>Prefix</th><th>Mask</th><th>Host bits</th><th>Total</th><th>Usable hosts</th></tr>
<tr><td>/24</td><td>255.255.255.0</td><td>8</td><td>256</td><td>254</td></tr>
<tr><td>/25</td><td>255.255.255.128</td><td>7</td><td>128</td><td>126</td></tr>
<tr><td>/26</td><td>255.255.255.192</td><td>6</td><td>64</td><td>62</td></tr>
<tr><td>/27</td><td>255.255.255.224</td><td>5</td><td>32</td><td>30</td></tr>
<tr><td>/28</td><td>255.255.255.240</td><td>4</td><td>16</td><td>14</td></tr>
<tr><td>/29</td><td>255.255.255.248</td><td>3</td><td>8</td><td>6</td></tr>
<tr><td>/30</td><td>255.255.255.252</td><td>2</td><td>4</td><td>2</td></tr>
<tr><td>/31</td><td>255.255.255.254</td><td>1</td><td>2</td><td>2 point to point</td></tr>
<tr><td>/32</td><td>255.255.255.255</td><td>0</td><td>1</td><td>1 single host</td></tr>
</table>

<p><strong>Memory trick:</strong> <b>255.255.255.0 is /24</b>. Every step down
halves it: 254, 126, 62, 30, 14, 6, 2. Learn that sequence and you can answer
instantly.</p>

<h2>4. Usable Hosts = 2 to the power n, minus 2</h2>

<p>Two addresses are always wasted: the network address and the broadcast
address.</p>

<pre>Hosts needed: 50
Smallest power of two above 50 is 64  ->  2^6
Add 2 back for network and broadcast  ->  64 + 2 = 66
Next power of two above 66 is 128      ->  2^7
So we need 7 host bits -> prefix = 32 - 7 = /25</pre>

<p><strong>Why minus 2?</strong> .0 is the name of the street itself and .255 means
"everyone on this street". Neither can be a real house.</p>

<h2>5. Subnetting Step by Step - A Worked Example</h2>

<p>You own <code>192.168.0.0/24</code> and need to split it into four /26 subnets.</p>

<table>
<tr><th>Subnet</th><th>Network address</th><th>Usable range</th><th>Broadcast</th></tr>
<tr><td>1</td><td>192.168.0.0/26</td><td>192.168.0.1 - 192.168.0.62</td><td>192.168.0.63</td></tr>
<tr><td>2</td><td>192.168.0.64/26</td><td>192.168.0.65 - 192.168.0.126</td><td>192.168.0.127</td></tr>
<tr><td>3</td><td>192.168.0.128/26</td><td>192.168.0.129 - 192.168.0.190</td><td>192.168.0.191</td></tr>
<tr><td>4</td><td>192.168.0.192/26</td><td>192.168.0.193 - 192.168.0.254</td><td>192.168.0.255</td></tr>
</table>

<p><strong>Memory trick:</strong> start at .0 and add the block size each time. For
/26 the block size is 64, so: 0, 64, 128, 192.</p>

<h2>6. The Borrow 2^n Trick</h2>

<p>For a /26 you borrow 6 bits, so the block size is 2 to the power 6, which is 64.
You never need to look it up.</p>

<table>
<tr><th>Bits borrowed</th><th>1</th><th>2</th><th>3</th><th>4</th><th>5</th><th>6</th><th>7</th></tr>
<tr><th>Block size</th><th>2</th><th>4</th><th>8</th><th>16</th><th>32</th><th>64</th><th>128</th></tr>
</table>

<p>Equivalently, the block size is 256 minus the last octet of the mask. For
255.255.255.192 that is 256 minus 192, which is 64.</p>

<h2>7. VLSM - Variable Length Subnet Masking</h2>

<p>Old subnetting gave every subnet the same size and wasted enormous address
space. VLSM gives each subnet only what it needs, largest first.</p>

<table>
<tr><th>Department</th><th>Hosts needed</th><th>Prefix</th><th>Usable</th><th>Wasted</th></tr>
<tr><td>Engineering</td><td>500</td><td>/22</td><td>1022</td><td>522</td></tr>
<tr><td>Marketing</td><td>100</td><td>/25</td><td>126</td><td>26</td></tr>
<tr><td>Support</td><td>50</td><td>/26</td><td>62</td><td>12</td></tr>
<tr><td>Router link</td><td>2</td><td>/31</td><td>2</td><td>0</td></tr>
</table>

<p><strong>Why biggest first:</strong> if you allocate the small subnets first, the
large one no longer fits into what is left. Always work downwards from the
largest requirement.</p>

<h2>8. Scenarios Worth Memorising</h2>

<table>
<tr><th>Scenario</th><th>What to do</th><th>Answer</th></tr>
<tr><td>Give a PC and a router addresses on 192.168.1.0/24</td><td>Never use .0 or .255</td><td>PC 192.168.1.10, router 192.168.1.1</td></tr>
<tr><td>Usable hosts on 10.0.0.0/27</td><td>2^5 = 32, minus 2</td><td>30 hosts, .1 to .30</td></tr>
<tr><td>Split 172.16.0.0/24 into two</td><td>Borrow 1 bit</td><td>/25 and /25, 126 hosts each</td></tr>
<tr><td>Link between two routers</td><td>Smallest useful subnet</td><td>/30, 4 addresses, 2 usable</td></tr>
<tr><td>One address on a loopback</td><td>Zero host bits</td><td>/32, for example 10.0.0.1/32</td></tr>
<tr><td>Kubernetes Service CIDR</td><td>Services are virtual IPs</td><td>Commonly 10.96.0.0/12</td></tr>
</table>

<h2>9. Commands</h2>
<pre># Windows
ipconfig /all
route print
netsh interface ip show address

# Linux
ip addr show
ip route</pre>

<h2>10. Try It Yourself (20 minutes)</h2>
<ul>
<li>You need subnets for 100, 50 and 10 hosts. Find the prefix for each.</li>
<li>Split 10.0.0.0/24 into four equal subnets and write out the ranges.</li>
<li>Why is 192.168.1.255 unusable on a /24? Because it is the broadcast address.</li>
<li>Write /24, /25, /26, /27 and their usable counts from memory.</li>
<li>Drill the row <b>254, 126, 62, 30, 14, 6, 2</b> until it is automatic.</li>
</ul>

<h2>11. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Example</td><td>A tidy 10.0.0.0/24 split into four /26</td><td>Whole /16 blocks carved across many VPCs</td></tr>
<tr><td>Overlaps</td><td>Overlapping home causes no visible problem</td><td>Break VPN tunnels and on-prem routing</td></tr>
<tr><td>Routing</td><td>One flat table and the default route</td><td>Dynamic protocols with summarisation and BGP</td></tr>
<tr><td>Allocation</td><td>Done by hand in a terminal</td><td>Terraform, VPC CNI, IPAM with strict tagging</td></tr>
<tr><td>Waste</td><td>Not a concern</td><td>Some clouds bill per allocated address</td></tr>
<tr><td>Documentation</td><td>You remember it</td><td>IPAM plus a network diagram reviewed in pull requests</td></tr>
<tr><td>Errors</td><td>Redo the table</td><td>Cause outages, so changes need review and rollback</td></tr>
</table>

<h2>12. Key Takeaways</h2>
<ul>
<li>The CIDR number equals the count of 1s in the mask.</li>
<li>Usable hosts is 2 to the power n, minus 2 for network and broadcast.</li>
<li>Block size is 2 to the power the bits borrowed, or 256 minus the last mask octet.</li>
<li>/24 gives 254 hosts and every step down halves it.</li>
<li>In VLSM always allocate the largest subnet first.</li>
<li>In production a subnet mistake is not homework; it is an outage.</li>
</ul>
"""