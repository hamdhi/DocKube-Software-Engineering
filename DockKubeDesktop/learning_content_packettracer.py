r"""Chapter 34 - Cisco Packet Tracer: building, testing and troubleshooting networks on screen."""

CHAPTER = r"""<h2>1. What Packet Tracer Is</h2>

<p>Packet Tracer is Cisco's free network simulator: you drag routers,
switches, PCs and servers onto a canvas, cable them together, type the real
IOS commands into them, and watch packets travel. It is the official lab
environment for the CCNA and the fastest way to make networking concrete
without buying gear.</p>

<table>
<tr><th>Where</th><th>How</th></tr>
<tr><td>Download</td><td>netacad.com - free with the "Getting Started with Packet Tracer" course (a Cisco account is enough)</td></tr>
<tr><td>Platforms</td><td>Windows, macOS, Linux; tablet versions are view-only</td></tr>
<tr><td>File</td><td>Save as .pka (single) or .joinpka (multi-user class activity)</td></tr>
<tr><td>Licence</td><td>Free for learning; no payment details</td></tr>
</table>

<h2>2. The Workspace</h2>

<pre>+--------------------------------------------------------------+
| File  Edit  Options  Extras  Help                             |
+--------------------------------------------------------------+
|            |                                                  |
| component  |                 CANVAS                          |
| palette    |      [Router0]----[Switch0]----[PC0]              |
| (routers,  |              |                                   |
|  switches, |          [Server0]                               |
|  cables,   |                                                  |
|  end dev)  |                                                  |
|            |                                                  |
+--------------------------------------------------------------+
| Realtime | Simulation   |  realtime clock / event list        |
+--------------------------------------------------------------+

Two modes:
Realtime  - everything behaves live, like real gear
Simulation - time freezes; step through packet-by-packet, see PDUs
            (ARP, ICMP, TCP), open the PDU envelope to inspect headers
</pre>

<ol>
<li><strong>Place devices</strong> - bottom-left palette: Routers
(1941, 4321), Switches (2960), End devices (PC, laptop, server, phone),
Connections (the lightning bolt = automatic cable selection).</li>
<li><strong>Cable correctly</strong> - copper straight-through for
different layers (PC to switch), crossover for same layer (switch to
switch, PC to PC) - though modern gear auto-MDIXs, the exam still tests the
classification.</li>
<li><strong>Configure</strong> - click a device: Physical tab (power, modules
like WIC-2T), Config tab (GUI form), CLI tab (real IOS).</li>
</ol>

<h2>3. First Lab - PC To Server Across Two Switches</h2>

<pre>1. Drag 2960 switch x2, PC x2, server x1, cable with auto tool.
2. PC0: Config &gt; FastEthernet0 &gt; IPv4: 192.168.1.10 /24, gateway 192.168.1.1
   PC1: 192.168.1.11 /24    Server0: 192.168.1.100 /24
3. Switch0 CLI:
   Switch&gt; enable
   Switch# configure terminal
   Switch(config)# hostname SW1
   SW1(config)# vlan 10
   SW1(config)# interface range fastEthernet 0/1 - 5
   SW1(config-if-range)# switchport mode access
   SW1(config-if-range)# switchport access vlan 10
   SW1(config)# interface gigabitEthernet 0/1
   SW1(config-if)# switchport mode trunk
4. Repeat on SW2. Set the PCs into VLAN 10 as well.
5. Ping PC0 -&gt; Server0: works. Then Simulation mode and watch ARP first,
   then ICMP echo and reply - the exact handshake from Chapter 1.
</pre>

<h2>4. Router CLI In The Simulator</h2>

<pre>Router&gt; enable
Router# configure terminal
Router(config)# hostname R1
R1(config)# interface gigabitEthernet 0/0
R1(config-if)# ip address 192.168.1.1 255.255.255.0
R1(config-if)# no shutdown          ! ports start administratively down
R1(config-if)# exit
R1(config)# interface serial 0/0/0
R1(config-if)# ip address 10.0.0.1 255.255.255.252
R1(config-if)# clock rate 64000     ! DCE side of the serial cable
R1(config-if)# no shutdown
R1(config)# ip route 0.0.0.0 0.0.0.0 10.0.0.2

# Verification commands worth muscle-memory:
show ip interface brief     ! up/up at a glance
show ip route               ! connected (C), static (S), OSPF (O)
show running-config         ! what is really configured
show interfaces counters    ! errors, CRC, drops
ping 192.168.1.100          ! ! means success in IOS
traceroute 10.0.0.2
</pre>

<h2>5. Simulation Mode - Where You Actually Learn</h2>

<table>
<tr><th>Step</th><th>What to look at</th></tr>
<tr><td>Open Simulation (bottom tab)</td><td>Time pauses; an event list appears</td></tr>
<tr><td>Press Play / Capture Forward</td><td>The coloured ball walks each hop</td></tr>
<tr><td>Click the ball (PDU)</td><td>OSI model view: which layer produced what on each device</td></tr>
<tr><td>Filter the event list</td><td>Show only ICMP to strip ARP noise</td></tr>
<tr><td>Deliberately break something</td><td>Wrong subnet, missing route, shut port - then watch exactly where the packet stops and why</td></tr>
</table>

<p><strong>Memory trick:</strong> the ball stops at the device that first
says "I do not know what to do with this" - no ARP reply means L2 problem,
no reply from gateway means L3, reply but no server means server config.</p>

<h2>6. Ten Progressive Labs</h2>

<table>
<tr><th>#</th><th>Lab</th><th>Pass condition</th></tr>
<tr><td>1</td><td>Single switch LAN</td><td>3 PCs ping each other</td></tr>
<tr><td>2</td><td>VLANs</td><td>Same-VLAN pings work, cross-VLAN blocked</td></tr>
<tr><td>3</td><td>Trunk between switches</td><td>VLAN 10 spans both switches</td></tr>
<tr><td>4</td><td>Router on a stick</td><td>VLAN 10 pings VLAN 20</td></tr>
<tr><td>5</td><td>Static routing, 3 routers</td><td>End-to-end ping across all three LANs</td></tr>
<tr><td>6</td><td>OSPF single area</td><td>show ip ospf neighbor = FULL on every link</td></tr>
<tr><td>7</td><td>ACL</td><td>PC-A can telnet to R2, PC-B cannot</td></tr>
<tr><td>8</td><td>NAT + DHCP</td><td>Private PCs reach the simulated internet server</td></tr>
<tr><td>9</td><td>SSH hardening</td><td>Console-only access replaced by SSH login</td></tr>
<tr><td>10</td><td>Troubleshoot a broken .pka</td><td>Given 5 faults, find each with show commands</td></tr>
</table>

<pre>Classic fault checklist for labs:
- "no shutdown" missing (interface administratively down)
- Clock rate missing on the DCE serial side
- IP on the wrong subnet / mask typo
- Default gateway missing on PCs
- Trunk native VLAN mismatch
- ACL ordered wrong (deny before permit) or applied in the wrong direction
</pre>

<h2>7. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>Packet Tracer</th><th>Real gear / GNS3-EVE-NG</th></tr>
<tr><td>Coverage</td><td>Core IOS features; no vendor quirks, limited protocols</td><td>Full behaviour: real ASICs, crashes, weird defaults</td></tr>
<tr><td>Timing</td><td>Simulation - deterministic</td><td>Real timers, real convergence races</td></tr>
<tr><td>Scale</td><td>Dozens of devices</td><td>Hundreds on EVE-NG/GNS3 with real IOS images</td></tr>
<tr><td>Where it fits</td><td>Learning commands and protocol behaviour</td><td>Career proof, job interviews, production change practice</td></tr>
</table>

<h2>8. Key Takeaways</h2>
<ul>
<li>Packet Tracer is free, official and enough for the CCNA - build the
topology before you read the theory.</li>
<li>Simulation mode is the learning engine: step the packet, open the PDU,
see which layer failed.</li>
<li>Every CLI lab is finished with verification commands - configure only
what you can prove with show ip route, show ip ospf neighbor, ping.</li>
<li>Break things on purpose; a network you have never broken is a network
you cannot fix at 3am.</li>
</ul>

<p><strong>Exercise:</strong> build lab 4 end to end (two switches, one
router, two VLANs) without following the steps - only from memory - then
save the .pka as your revision template.</p>
"""