r"""Chapter 33 - CCNA: the exam blueprint, the core skills, and how to study it."""

CHAPTER = r"""<h2>1. What CCNA Actually Is</h2>

<p>The CCNA (200-301) is Cisco's associate-level networking exam. One test,
~100 questions in 120 minutes, mix of multiple choice, drag-and-drop, and
simulated CLI tasks (simlets). It certifies you can configure, operate and
troubleshoot a small to medium network - the same skills every NOC, field
engineer and cloud engineer uses daily.</p>

<table>
<tr><th>Exam domain</th><th>Weight</th><th>What is inside</th></tr>
<tr><td>Network fundamentals</td><td>20%</td><td>OSI/TCP models, cables, IPv4 addressing, subnetting, DHCP, DNS, ARP, routing concepts</td></tr>
<tr><td>Network access</td><td>20%</td><td>VLANs, trunking (80.1Q), STP, EtherChannel, wireless, port security, SPAN</td></tr>
<tr><td>IP connectivity</td><td>25%</td><td>Static routes, OSPF single/multi-area, FHRP, NAT</td></tr>
<tr><td>IP services</td><td>10%</td><td>NTP, NAT/PAT, DHCP, QoS, SNMP, syslog, SSH, HSRP</td></tr>
<tr><td>Security fundamentals</td><td>15%</td><td>ACLs (std/ext/extended), port security, DHCP snooping, AAA, wireless auth, VPN</td></tr>
<tr><td>Automation and programmability</td><td>10%</td><td>SDN vs traditional, RESTCONF/YANG, controllers, Ansible, Python REST APIs</td></tr>
</table>

<p><strong>Memory trick for the weights:</strong> routing (IP connectivity)
is the biggest slice at 25% - if you cannot subnet and configure OSPF in
your sleep, nothing else matters.</p>

<h2>2. The OSI Model As You Meet It On The Job</h2>

<table>
<tr><th>Layer</th><th>Name</th><th>Unit</th><th>Devices</th><th>Failure you will see</th></tr>
<tr><td>7</td><td>Application</td><td>Data</td><td>-</td><td>404s, API errors</td></tr>
<tr><td>6</td><td>Presentation</td><td>Data</td><td>-</td><td>TLS/cipher mismatch</td></tr>
<tr><td>5</td><td>Session</td><td>Data</td><td>-</td><td>Dropped sessions</td></tr>
<tr><td>4</td><td>Transport</td><td>Segment</td><td>Firewall (L4)</td><td>Port blocked, RST, retransmits</td></tr>
<tr><td>3</td><td>Network</td><td>Packet</td><td>Router, L3 switch</td><td>Wrong gateway, routing loop, no route</td></tr>
<tr><td>2</td><td>Data link</td><td>Frame</td><td>Switch, bridge, AP</td><td>Duplex mismatch, STP flap, VLAN missing on trunk</td></tr>
<tr><td>1</td><td>Physical</td><td>Bits</td><td>Cable, SFP, hub</td><td>Link light off, CRC errors</td></tr>
</table>

<pre>Encapsulation:  data --&gt; segment (TCP) --&gt; packet (IP) --&gt; frame (Ethernet) --&gt; bits
De-encapsulation is the reverse on the far side.
Memory: "Please Do Not Throw Sausage Pizza Away" (7 to 1)
</pre>

<h2>3. Subnetting - The Skill The Exam Tests Fastest</h2>

<pre>CIDR /24 = 255.255.255.0 = 254 hosts (2^8 - 2)
Borrow bits to go shorter: /26 = 64-address blocks, 62 hosts each

Step 1: block size = 256 - interesting octet (/26 -&gt; 256-192? no: 2^(32-26)=64)
Step 2: boundaries at 0, 64, 128, 192
Step 3: first host = network+1, last = broadcast-1, broadcast = next boundary-1

Host 10.0.0.100/26:
  mask 255.255.255.192, block 64 -&gt; network 10.0.0.64
  range 10.0.0.65 - 10.0.0.126, broadcast .127

Shortcut table to memorise:
 /25 = 128 addrs /126 hosts    /28 = 16 addrs /14 hosts
 /26 = 64  addrs /62  hosts    /29 = 8  addrs /6  hosts
 /27 = 32  addrs /30  hosts    /30 = 4  addrs /2  hosts (serial links)
</pre>

<h2>4. VLANs, Trunks And Spanning Tree</h2>

<pre>! Create a VLAN and put a port in it
Switch(config)# vlan 20
Switch(config-vlan)# name USERS
Switch(config)# interface gi0/1
Switch(config-if)# switchport mode access
Switch(config-if)# switchport access vlan 20

! Trunk to the router/switch: carries every VLAN with tags
Switch(config)# interface gi0/24
Switch(config-if)# switchport mode trunk
Switch(config-if)# switchport trunk allowed vlan 10,20,30
Switch(config-if)# switchport trunk native vlan 99   ! match both ends!

! Inter-VLAN routing - router on a stick
Router(config)# interface gi0/0.10
Router(config-subif)# encapsulation dot1Q 10
Router(config-subif)# ip address 10.0.10.1 255.255.255.0

! Port security: only one MAC, shut on violation
Switch(config)# interface gi0/1
Switch(config-if)# switchport port-security
Switch(config-if)# switchport port-security maximum 1
Switch(config-if)# switchport port-security violation shutdown
</pre>

<table>
<tr><th>Problem</th><th>Usual cause on the exam and at work</th></tr>
<tr><td>Same VLAN cannot talk across switches</td><td>Trunk missing, wrong native VLAN, allowed-vlan list excludes it</td></tr>
<tr><td>Two switches keep flapping</td><td>STP sees a loop - one side is mis-trunked or a cable is doubled back</td></tr>
<tr><td>Intermittent connectivity, slow</td><td>Duplex mismatch (one auto, one hard-set)</td></tr>
<tr><td>Ping gateway works, internet does not</td><td>Default route missing on the router or host</td></tr>
</table>

<p><strong>STP in one line:</strong> root bridge election by lowest bridge
ID, all other switches pick the best path to it, redundant links get
blocked. Use PortFast on access ports, BPDU guard to kill rogue switches,
RSTP (802.1w) for fast convergence.</p>

<h2>5. IP Connectivity - Static And OSPF</h2>

<pre>! Static default route (the "gateway of last resort")
Router(config)# ip route 0.0.0.0 0.0.0.0 203.0.113.1

! OSPF single area - the workhorse of the exam
Router(config)# router ospf 1
Router(config-router)# router-id 1.1.1.1
Router(config-router)# network 10.0.0.0 0.0.0.255 area 0
Router(config-router)# network 192.0.2.0 0.0.0.3 area 0

! Verification
show ip ospf neighbor        ! FULL with 2-WAY/DROTHER is healthy
show ip route ospf           ! O routes present?
show ip protocols

! OSPF multi-area: area 0 is the backbone; areas 1 and 2 MUST touch it.
! Cost = reference-bandwidth / interface-bandwidth (default ref 100 Mbps).
</pre>

<table>
<tr><th>OSPF state</th><th>Meaning</th></tr>
<tr><td>DOWN / INIT</td><td>Hello seen one way only</td></tr>
<tr><td>2-WAY</td><td>Neighbors established (DR/BDR election done)</td></tr>
<tr><td>EXSTART / EXCHANGE</td><td>LSDB database description in progress</td></tr>
<tr><td>FULL</td><td>Adjacency complete - the only healthy end state</td></tr>
</table>

<p><strong>Memory trick:</strong> adjacency will not form when areas differ,
authentication differs, MTU mismatches, or hello/dead timers disagree. In
the exam, check those four first.</p>
<h2>6. ACLs, NAT And DHCP - The Services Layer</h2>

<pre>! Standard ACL (by source IP) - place it CLOSE to the destination
R1(config)# access-list 10 permit 192.168.10.0 0.0.0.255
R1(config)# access-list 10 deny any
R1(config)# interface g0/1
R1(config-if)# ip access-group 10 in

! Extended ACL (source, dest, protocol, port) - CLOSE to the source
R1(config)# access-list 101 deny tcp host 192.168.1.20 host 10.0.0.5 eq 23
R1(config)# access-list 101 permit ip any any        ! implicit deny is at the end

! NAT overload (PAT) - how a whole office shares one public IP
R1(config)# ip nat inside source list 1 interface g0/0 overload
R1(config)# interface g0/0   -&gt; ip nat inside
R1(config)# interface g0/1   -&gt; ip nat outside

! DHCP server on the router
R1(config)# ip dhcp excluded-address 192.168.1.1 192.168.1.10
R1(config)# ip dhcp pool LAN
R1(dhcp-config)# network 192.168.1.0 255.255.255.0
R1(dhcp-config)# default-router 192.168.1.1
R1(dhcp-config)# dns-server 1.1.1.1

! SSH instead of telnet
R1(config)# ip domain-name lab.local
R1(config)# crypto key generate rsa modulus 2048
R1(config)# username admin privilege 15 secret Str0ngPass!
R1(config)# line vty 0 4
R1(config-line)# transport input ssh
R1(config-line)# login local
</pre>

<table>
<tr><th>Rule</th><th>Detail</th></tr>
<tr><td>ACL order</td><td>Top-down, first match wins - the permit any you meant to put first must be LAST</td></tr>
<tr><td>Implicit deny</td><td>Every ACL ends with deny any, invisible in the config</td></tr>
<tr><td>Standard vs extended</td><td>Standard: source only, numbers 1-99. Extended: src+dst+port+protocol, 100-199</td></tr>
<tr><td>NAT direction</td><td>inside interfaces facing your LAN, outside facing the ISP - swap them and nothing translates</td></tr>
<tr><td>One ACL per interface per direction</td><td>ip access-group ... in | out</td></tr>
</table>

<h2>7. Security And Troubleshooting On The Exam</h2>

<pre>Standard troubleshooting order (follow it top-down, do not guess):
1. Layer 1  - link lights, cable type, show ip int brief (up/up?)
2. Layer 2  - VLAN, trunk allowed list, native VLAN, STP, duplex
3. Layer 3  - ip address/subnet, default gateway, route present, ACL hit counters
4. Services - DHCP pool, DNS reachability, NAT inside/outside
5. Host     - static IP vs DHCP, firewall on the PC

show access-lists           ! hit counters tell you if an ACL is matching
show ip nat translations     ! is traffic translating?
show interfaces counters    ! CRC, input errors = physical problem
debug ip ospf adjacency      ! last resort, noisy - only in labs
</pre>

<table>
<tr><th>Security feature</th><th>Protects against</th></tr>
<tr><td>Port security</td><td>Unknown MACs plugged into access ports (hub attack)</td></tr>
<tr><td>DHCP snooping</td><td>Rogue DHCP server handing out gateways</td></tr>
<tr><td>Dynamic ARP inspection</td><td>ARP poisoning (uses snooping binding table)</td></tr>
<tr><td>BPDU guard</td><td>Rogue switch causing STP changes</td></tr>
<tr><td>802.1X</td><td>Unauthorized devices - authenticate before the port carries data</td></tr>
<tr><td>AAA + RADIUS/TACACS+</td><td>Shared logins; per-user auth, authorisation, accounting</td></tr>
<tr><td>VPN (IPsec / SSL)</td><td>Eavesdropping across public networks</td></tr>
</table>

<h2>8. Automation And Programmability (10% - Do Not Skip It)</h2>

<table>
<tr><th>Concept</th><th>Exam-ready definition</th></tr>
<tr><td>SDN</td><td>Control plane separated from forwarding, central controller programs the devices</td></tr>
<tr><td>REST API</td><td>HTTP verbs (GET/POST/PUT/DELETE) on resource URLs, JSON bodies - what controllers and cloud gear speak</td></tr>
<tr><td>YANG + RESTCONF/NETCONF</td><td>YANG = data model language, RESTCONF = HTTP/JSON over that model, NETCONF = SSH/XML</td></tr>
<tr><td>Controller</td><td>vManage, DNA Center, APIC, ONOS - the central brain that renders intent into device config</td></tr>
<tr><td>Configuration drift</td><td>Device config no longer matches the intended source of truth</td></tr>
<tr><td>Push vs pull</td><td>Controller pushes config; Ansible/Chef pull agent-based or push agentless over SSH</td></tr>
<tr><td>IaC</td><td>Network described in code (Terraform, Ansible) - versioned, reviewed, repeatable</td></tr>
</table>

<pre># What a REST call to a controller looks like:
curl -k -u admin:pass -H "Content-Type: application/json" \
     -X POST https://sandboxapicem.cisco.com/intent/api/v1/config/ -d '{...}'

# Ansible playbook shape for a switch:
# - hosts: switches
#   gather_facts: no
#   tasks:
#     - ios_vlans: [{name: USERS, vlan_id: 20}]
#     - ios_config:
#         lines: ["switchport access vlan 20"]
#         parents: interface gi0/1
</pre>

<h2>9. A 12-Week Study Plan</h2>

<table>
<tr><th>Weeks</th><th>Focus</th><th>Output</th></tr>
<tr><td>1-2</td><td>OSI, TCP/IP, subnetting daily (15 min), cables, DHCP/DNS/ARP</td><td>Subnet in under 30 seconds, every time</td></tr>
<tr><td>3-4</td><td>VLANs, trunks, STP, EtherChannel, wireless - Packet Tracer labs 1-4</td><td>Two-switch multi-VLAN build from memory</td></tr>
<tr><td>5-7</td><td>Static routes, OSPF (single then multi-area), NAT, ACLs - labs 5-8</td><td>3-router topology, FULL neighbours, ACL verified with hit counters</td></tr>
<tr><td>8-9</td><td>Security features, SSH, AAA, VPN concepts</td><td>Hardened switch/router config template</td></tr>
<tr><td>10</td><td>Automation: APIs, YANG/RESTCONF, Ansible, SDN</td><td>One API call and one playbook against a lab</td></tr>
<tr><td>11</td><td> Boson/MeasureUp practice exams, review every wrong answer</td><td>Consistently 850+ (scaled)</td></tr>
<tr><td>12</td><td> Weakest-domain drilling + final mock under timed conditions</td><td>Exam booked and passed</td></tr>
</table>

<p><strong>Memory trick:</strong> 70% of the score is built from three habits:
daily subnetting, weekly Packet Tracer builds, and reading the explanation
for EVERY wrong practice-answer - not just the ones you guessed.</p>

<h2>10. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning (labs)</th><th>In production</th></tr>
<tr><td>Access</td><td>Console to everything</td><td>Jump host, TACACS+, MFA, session recording</td></tr>
<tr><td>Changes</td><td>Type directly into running-config</td><td>Version-controlled templates, peer review, change window</td></tr>
<tr><td>Routing</td><td>OSPF area 0 demo</td><td>Route filters, prefix-lists, logging, capacity alerts</td></tr>
<tr><td>Security</td><td>One ACL to prove the concept</td><td>Layered: ACL + 802.1X + DHCP snooping + monitoring + audits</td></tr>
<tr><td>Documentation</td><td>In your head</td><td>IPAM record, diagrams, runbooks - updated in the same change</td></tr>
</table>

<h2>11. Key Takeaways</h2>
<ul>
<li>CCNA = fundamentals 20 + access 20 + connectivity 25 + services 10 +
security 15 + automation 10.</li>
<li>Subnetting speed and OSPF verification carry the most marks.</li>
<li>ACLs: first match wins, implicit deny at the end, standard near
destination, extended near source.</li>
<li>Troubleshoot in layer order: physical, data link, network, services,
host.</li>
<li>Automation is examinable: know what a controller, REST API, YANG model
and configuration drift are.</li>
<li>Practice exams plus Packet Tracer repetition beat more video watching.</li>
</ul>

<p><strong>Exercise:</strong> take the three-router topology from lab 5,
delete the OSPF config, and rebuild it using only the verification commands
in section 5 until every neighbour reads FULL.</p>
"""