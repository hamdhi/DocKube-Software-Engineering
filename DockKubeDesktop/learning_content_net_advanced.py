r"""Chapter 32 - Network engineering advanced: SDN, multi-cloud, BGP, zero trust, service meshes."""

CHAPTER = r"""<h2>1. Software-Defined Networking (SDN)</h2>

<p>Classically you configure each box by hand (CLI into switch A, switch B,
switch C). SDN splits the device into two planes and centralises one of
them:</p>

<pre>Traditional                          SDN
+--------+  +--------+              +---------------------------+
| switch |  | switch |              |  SDN CONTROLLER           |
| rules  |  | rules  |              |  one global view, a program|
| per-box|  | per-box|              |  writes rules everywhere  |
+--------++--------+              +-------------+-------------+
                                          | southbound API
   control + data fused in each box       | (OpenFlow, gRPC, REST)
                                +----------+----------+
                                | switch | switch | switch |
                                | forward only     |       |
                                +---------------------------+
</pre>

<table>
<tr><th>Plane</th><th>Job</th><th>Where it lives (SDN)</th></tr>
<tr><td>Data (forwarding)</td><td>Move the packets</td><td>The switches, dumbly following flow entries</td></tr>
<tr><td>Control</td><td>Decide where packets go</td><td>The controller - software, centrally, programmable</td></tr>
<tr><td>Management</td><td>Monitor, configure, alarm</td><td>Controller + orchestrator (OpenDaylight, ONOS, cloud consoles)</td></tr>
</table>

<p><strong>Memory trick:</strong> SDN turns network gear into a printer: the
hardware prints packets, the driver (controller) decides what it prints.
Variants: OpenFlow (classic), SD-WAN (site-to-site overlays), and every
cloud VPC - they are all SDN.</p>

<h2>2. Hybrid And Multi-Cloud Connectivity</h2>

<table>
<tr><th>Path</th><th>What it is</th><th>Latency / bandwidth</th><th>Cost</th></tr>
<tr><td>Site-to-site IPsec VPN</td><td>Encrypted tunnel over the public internet</td><td>Jitter, variable</td><td>Lowest</td></tr>
<tr><td>AWS Direct Connect</td><td>Physical dedicated circuit into AWS</td><td>Consistent, 1-100 Gbps</td><td>High + port fee</td></tr>
<tr><td>Azure ExpressRoute</td><td>Same idea for Azure (Equinix/Megaport fabric)</td><td>Consistent</td><td>High</td></tr>
<tr><td>Cloud interconnect</td><td>Equinix Fabric / Megaport elastic links between clouds and DCs</td><td>Sub-ms metro</td><td>Per port + egress</td></tr>
<tr><td>Transit gateway</td><td>Managed hub (AWS TGW, Azure vWAN) replacing a full mesh of VPC peering</td><td>In-region, fast</td><td>Per attachment + GB</td></tr>
<tr><td>VPC peering</td><td>Private L3 link between two networks, non-transitive</td><td>Very fast</td><td>Per GB both directions</td></tr>
</table>

<pre>On-prem DC ----[IPsec VPN]---\
                              +--- [Transit Gateway] --- app VPC
Branch A  ----[SD-WAN]-------/                           \__ data VPC
Branch B  ----[IPsec VPN]---  (BGP advertises on-prem      \__ SaaS endpoints
                               prefixes over each tunnel)

Rules of thumb:
- VPN for backup and small sites, dedicated interconnect for the main path
- One hub (transit gateway) beats a mesh once you have 3+ networks
- Always two tunnels: a single VPN is a single point of failure
</pre>

<h2>3. Advanced Routing And BGP</h2>

<p><strong>BGP</strong> is the routing protocol of the internet: it exchanges
<strong>prefixes</strong> between Autonomous Systems (AS numbers, e.g. AS15169
= Google) and picks paths by attribute, not by speed.</p>

<table>
<tr><th>Attribute</th><th>Effect</th><th>Manipulated to...</th></tr>
<tr><td>AS_PATH</td><td>Every AS the prefix crossed</td><td>Prepend your AS to look longer = less preferred (outbound traffic engineering)</td></tr>
<tr><td>LOCAL_PREF</td><td>Preferred within an AS (higher wins)</td><td>Choose which ISP carries your outbound traffic</td></tr>
<tr><td>MED</td><td>Hint to the neighbour which entry path to use</td><td>Influence where inbound traffic enters your network</td></tr>
<tr><td>Origin (IGP/EGP/incomplete)</td><td>How the prefix was originated</td><td>Minor preference</td></tr>
<tr><td>Weight (Cisco local)</td><td>Local-only, highest wins</td><td>Router-local first choice</td></tr>
</table>

<pre>router bgp 65001
 bgp router-id 10.0.0.1
 neighbor 203.0.113.1 remote-as 65002
 address-family ipv4 unicast
  network 192.0.2.0/24 route-map SET-MED
  neighbor 203.0.113.1 activate
  neighbor 203.0.113.1 prefix-list PL-DEFAULTS out
 route-map SET-MED permit 10
  set med 50
! Verification
show ip bgp summary          ! neighbour state = Established?
show ip bgp                 ! paths, next hops, best flag
traceroute to a remote host  ! which exit is actually used

Anycast: the SAME /32 announced from many locations - BGP sends each user
to the nearest instance (DNS root servers, CDNs, public DNS like 1.1.1.1).
</pre>

<p><strong>Memory trick:</strong> iBGP inside your AS (full mesh or route
reflectors), eBGP between ASes. BGP never chooses by latency - it chooses by
attributes, then shortest AS_PATH. That is why traffic engineering is
attribute manipulation.</p>

<h2>4. Network Security And Zero Trust</h2>

<table>
<tr><th>Concept</th><th>What it is</th><th>Replaces</th></tr>
<tr><td>Zero Trust (ZTNA)</td><td>Never trust the network; verify every request, every time, least privilege, per-session</td><td>The old castle-and-moat VPN that put you flat on the LAN</td></tr>
<tr><td>Micro-segmentation</td><td>Every workload in its own zone; east-west traffic allowed only by explicit policy</td><td>One big trusted internal network</td></tr>
<tr><td>NGFW</td><td>Firewall that understands apps, users, TLS inspection, IDS/IPS - not just ports</td><td>Port/protocol ACLs alone</td></tr>
<tr><td>ACL</td><td>Ordered permit/deny rules; first match wins, implicit deny at the end</td><td>-</td></tr>
<tr><td>mTLS</td><td>Both sides present certificates - workload identity</td><td>Shared API keys inside the datacenter</td></tr>
</table>

<pre>Zero trust checklist:
1. Identity is the perimeter   - SSO + MFA for humans, SPIFFE/mTLS for services
2. Device health is checked    - posture before access
3. Least privilege per request - short-lived tokens, not standing VPN access
4. Assume breach               - encrypt, log, segment, detect east-west
5. Continuous verification     - re-evaluate on every hop, not once at login
</pre>

<h2>5. Service Meshes</h2>

<p>A <strong>service mesh</strong> (Istio, Linkerd) puts a sidecar proxy
(Envoy) next to every pod and takes over service-to-service traffic. Your
code changes by zero lines; the platform gains discovery, encryption and
traffic control.</p>

<table>
<tr><th>Feature</th><th>What it does</th><th>Tooling example</th></tr>
<tr><td>Service discovery</td><td>Find healthy instances without hard-coded IPs</td><td>VirtualService + DestinationRule</td></tr>
<tr><td>mTLS</td><td>Encrypt and authenticate every pod-to-pod call</td><td>Istio PeerAuthentication STRICT</td></tr>
<tr><td>Traffic splitting</td><td>90/10 canary between two versions</td><td>weight: 90 / weight: 10 routes</td></tr>
<tr><td>Retries, timeouts, circuit breaking</td><td>Stop cascading failure</td><td>outlierDetection, http2MaxRequests</td></tr>
<tr><td>Observability</td><td>Per-request metrics, tracing, access logs</td><td>Kiali, Jaeger, Prometheus</td></tr>
<tr><td>Authorization</td><td>"payments may call ledger, nothing else"</td><td>Istio AuthorizationPolicy</td></tr>
</table>

<pre>client --&gt; [Envoy sidecar] ==mTLS==&gt; [Envoy sidecar] --&gt; service
              |                                |
              +---- telemetry to Istiod ------+

When NOT to mesh: a handful of services (a reverse proxy is enough), or
clusters where the sidecar CPU cost outweighs the benefits.
</pre>

<h2>6. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>SDN</td><td>One vSwitch</td><td>Controller HA, intent-based policies, drift alerts</td></tr>
<tr><td>Cloud links</td><td>Single VPN, single AZ</td><td>Two tunnels, two carriers, two transit zones</td></tr>
<tr><td>BGP</td><td>Read the defaults</td><td>Prefix filters, RPKI ROAs, route monitoring (RIPE RIS), change windows</td></tr>
<tr><td>Zero trust</td><td>Flat network, trust LAN</td><td>Identity-aware proxy, micro-segmented east-west, deny by default</td></tr>
<tr><td>Mesh</td><td>demo cluster</td><td>mTLS STRICT, quota, gradual rollout policies, SLO alerts</td></tr>
</table>

<h2>7. Key Takeaways</h2>
<ul>
<li>SDN separates the control plane (the decision) from the data plane (the
forwarding) and makes the network programmable.</li>
<li>Direct Connect / ExpressRoute for the main path, IPsec VPN for backup
and branches; one transit hub beats a mesh.</li>
<li>BGP picks paths by attributes - AS_PATH, LOCAL_PREF, MED - never by
speed; manipulating them IS traffic engineering.</li>
<li>Zero trust = verify every request, least privilege, assume breach;
micro-segmentation and mTLS are how it is built.</li>
<li>A service mesh gives discovery, mTLS, canaries and telemetry without
touching application code.</li>
</ul>

<p><strong>Exercise:</strong> draw your home network as an SDN diagram: one
control point (your router), data plane (switch ports), and write the
"flow entries" (port forwards, firewall rules) it programs.</p>
"""