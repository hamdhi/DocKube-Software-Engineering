"""Chapter - Firewalls: what they decide, and the four you will actually use."""

CHAPTER = """<h2>1. What Is A Firewall?</h2>

<p>A firewall is a rulebook. It sits at a network boundary, looks at every packet
passing through, and decides one of three things: <strong>allow</strong> it,
<strong>block</strong> it, or <strong>drop</strong> it silently.</p>

<p>Allow and block are not the same. A blocked packet gets a rejection the sender
can see. A dropped packet vanishes with no reply at all. Dropping is the stronger
option, because a rejection tells an attacker that a port exists and only that
you are not answering.</p>

<p><strong>Memory trick:</strong> a bouncer at a club. Allow is someone with an
invite, block is turned away loudly, drop is the person simply not on the list
who will never be told why.</p>

<h2>2. The Main Job Of A Firewall</h2>

<p>Almost every real firewall has one reason for existing, and knowing which one
tells you the right rules:</p>

<table>
<tr><th>Purpose</th><th>What it stops</th><th>Typical rules</th></tr>
<tr><td>Host firewall</td><td>Anything reaching this machine directly</td><td>Allow port 22 from one admin IP, drop everything else</td></tr>
<tr><td>Network firewall</td><td>Traffic crossing between network segments</td><td>Web tier may talk to the database tier, nothing else can</td></tr>
<tr><td>Cloud security group</td><td>Traffic reaching a cloud resource</td><td>Allow 443 from anywhere, allow 22 from your office only</td></tr>
<tr><td>Web application firewall</td><td>Malicious HTTP requests</td><td>Block SQL injection strings and known bad patterns</td></tr>
</table>

<p>These four are not the same thing wearing different names. A security group
cannot see an HTTP body, and a web application firewall cannot see an IP packet.
You need all four to cover what a firewall is meant to cover, and understanding
which layer does what is the actual skill.</p>

<h2>3. Packet Filtering - The Basic Rules</h2>

<p>Filtering decides using the fields every packet carries in its header, without
looking inside:</p>

<table>
<tr><th>Field</th><th>Example</th><th>What it lets you do</th></tr>
<tr><td>Source IP</td><td>203.0.113.10</td><td>Allow one machine, block the rest of the internet</td></tr>
<tr><td>Destination IP</td><td>10.0.0.5</td><td>Send traffic to a specific server</td></tr>
<tr><td>Source port</td><td>51000</td><td>Return traffic for a known connection</td></tr>
<tr><td>Destination port</td><td>443</td><td>Allow web traffic only</td></tr>
<tr><td>Protocol</td><td>TCP, UDP, ICMP</td><td>Allow ping, or refuse it</td></tr>
<tr><td>State</td><td>ESTABLISHED</td><td>Let replies through for connections you started</td></tr>
</table>

<p>The last row is the important one. Without stateful inspection, allowing a
connection out means also having to allow anything back in, which lets an
attacker start a connection <em>inwards</em> that you never permitted.</p>

<h2>4. The Default Stance</h2>

<p>Two philosophies, and picking the wrong one causes outages:</p>

<p><strong>Deny by default.</strong> Nothing is allowed until you say so. This is
the secure choice and the one every security guide recommends.</p>

<p><strong>Allow by default.</strong> Everything is allowed unless blocked. Easier
to start, and it means one forgotten rule is a breach.</p>

<p>Deny by default has a sharp edge: deny by default inbound and you will lock
yourself out of your own server over SSH the first time you enable it. The safe
order is always enable, allow SSH, <em>then</em> set the default to deny.</p>

<p><strong>Memory trick:</strong> lock the building first, then give people their
keys. Locking everyone out and handing out keys afterwards is the sequence that
works.</p>

<h2>5. The Four You Will Actually Use</h2>

<h3>ufw - Ubuntu's simple front end</h3>
<p>A readable wrapper around nftables. Use this on Ubuntu and Debian.</p>
<pre>sudo ufw status verbose
sudo ufw default deny incoming
sudo ufw allow 22/tcp
sudo ufw allow 80,443/tcp
sudo ufw allow from 203.0.113.10 to any port 22
sudo ufw enable
sudo ufw delete allow 3306/tcp</pre>

<h3>firewalld - zones, on RHEL and CentOS</h3>
<p>Groups rules by <em>zone</em>. A network interface belongs to a zone, and the
zone decides the rules, so moving a cable between interfaces changes the policy.</p>
<pre>sudo firewall-cmd --list-all
sudo firewall-cmd --get-active-zones
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
sudo firewall-cmd --zone=public --list-all</pre>

<h3>nftables - the modern engine</h3>
<p>The kernel rule system ufw and firewalld both write to. You configure it
directly when you need logic the wrappers cannot express.</p>
<pre>sudo nft list ruleset
sudo nft list table inet filter
sudo nft -j list ruleset        # JSON, for scripts and diffing</pre>

<h3>Windows Defender Firewall</h3>
<p>The same idea, configured through netsh. Profiles matter: Domain, Private and
Public have separate rule sets.</p>
<pre>netsh advfirewall show allprofiles
netsh advfirewall set allprofiles state on
netsh advfirewall firewall add rule name="Allow 443" dir=in action=allow protocol=TCP localport=443
netsh advfirewall firewall show rule name=all</pre>

<h2>6. Ingress, Egress, And Why Egress Matters</h2>

<p>Most people only think about <strong>ingress</strong>, traffic coming in. But
egress filtering stops data leaving when it should not:</p>

<table>
<tr><th>Direction</th><th>Blocks</th><th>Why you want it</th></tr>
<tr><td>Inbound</td><td>Hackers reaching services you never meant to expose</td><td>The reason firewalls were invented</td></tr>
<tr><td>East-west</td><td>One compromised server attacking the rest of the data centre</td><td>Stops a single breach spreading sideways</td></tr>
<tr><td>Outbound</td><td>Data exfiltration, and command-and-control traffic to known bad addresses</td><td>Ransomware cannot phone home if you block it</td></tr>
</table>

<p>Egress filtering is the least used and most valuable control. A compromised
server that cannot reach anything outside your network is a far smaller problem
than one that can.</p>

<h2>7. Reading And Changing Rules Safely</h2>

<p>Every command here is safe to run, because reading rules changes nothing.
Learn to read before you write.</p>

<pre># What is allowed right now?
sudo ufw status numbered
sudo firewall-cmd --list-all
netsh advfirewall show allprofiles

# What is actually listening on this machine?
netstat -ano | findstr LISTENING
ss -tulnp

# Has the firewall ever blocked me?
sudo tail -n 50 /var/log/ufw.log</pre>

<p>The last one is the one people skip. When something will not connect, the
answer is usually sitting in the log, and the block is often a rule someone added
months earlier without telling anyone.</p>

<h2>8. Common Mistakes</h2>

<table>
<tr><th>Mistake</th><th>Consequence</th></tr>
<tr><td>Enabling deny-by-default before allowing SSH</td><td>Locked out of your own server</td></tr>
<tr><td>Allowing 22 to the whole internet</td><td>Your SSH server is being brute-forced every second of every day</td></tr>
<tr><td>Allowing 3306 or 5432 to anywhere</td><td>The database is on the internet. This is how breaches start.</td></tr>
<tr><td>Never reading the rules again</td><td>Rules accumulate until nobody dares touch them</td></tr>
<tr><td>Assuming a firewall makes you safe</td><td>It stops network attacks only. Application flaws walk straight through it.</td></tr>
<tr><td>Disabling it to make something work</td><td>The bug is still there, now without a safety net</td></tr>
</table>

<p><strong>Try it yourself:</strong> on a Linux virtual machine or a WSL instance,
run <code>sudo ufw status verbose</code>, then add a rule for a port nobody uses,
read it back, and delete it. Reading the state before and after is the whole
skill; the commands are incidental.</p>

<p><strong>Learning vs production:</strong> a home firewall on one machine is one
rule set. Production means cloud security groups, a network firewall, host
firewalls, a WAF and an egress policy, and they must agree with each other.
Change one layer and traffic that used to flow silently stops, which is why
firewall changes need the same care as any other production change.</p>"""
