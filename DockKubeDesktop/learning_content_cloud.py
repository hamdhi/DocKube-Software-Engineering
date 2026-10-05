"""Chapter - Cloud Engineer core concepts across AWS, Azure and GCP."""

CHAPTER = """<h2>1. What Does A Cloud Engineer Actually Do?</h2>

<p>A cloud engineer designs and runs the infrastructure a company lives on:
compute, storage, networking and identity, in a public cloud, so that it scales
globally and survives failure.</p>

<p>Four areas cover almost all of it, and they are the four parts of this
chapter: architecture and services, networking and security, availability and
disaster recovery, and cost.</p>

<p><strong>Memory trick:</strong> a cloud engineer is judged on two things that
pull against each other. Make it never go down, and make it cheap. Both numbers
are measured, and both show up on the same invoice and the same dashboard.</p>

<h2>2. The Shared Vocabulary Across AWS, Azure And GCP</h2>

<p>Every provider invented its own names, which is the main reason cloud
learning feels harder than it is. Underneath, the ideas are the same:</p>

<table>
<tr><th>Concept</th><th>AWS</th><th>Azure</th><th>GCP</th></tr>
<tr><td>Virtual private network</td><td>VPC</td><td>Virtual Network</td><td>VPC</td></tr>
<tr><td>Subnetwork</td><td>Subnet</td><td>Subnet</td><td>Subnet</td></tr>
<tr><td>Virtual machine</td><td>EC2</td><td>Virtual Machines</td><td>Compute Engine</td></tr>
<tr><td>Managed containers</td><td>ECS / EKS</td><td>AKS</td><td>GKE</td></tr>
<tr><td>Serverless functions</td><td>Lambda</td><td>Azure Functions</td><td>Cloud Functions</td></tr>
<tr><td>Object storage</td><td>S3</td><td>Blob Storage</td><td>Cloud Storage</td></tr>
<tr><td>Block storage</td><td>EBS</td><td>Managed Disks</td><td>Persistent Disk</td></tr>
<tr><td>Managed relational database</td><td>RDS</td><td>Azure SQL</td><td>Cloud SQL</td></tr>
<tr><td>Load balancer</td><td>ELB / ALB</td><td>Load Balancer</td><td>Cloud Load Balancing</td></tr>
<tr><td>Identity and access</td><td>IAM</td><td>Entra ID / RBAC</td><td>IAM</td></tr>
<tr><td>Secret management</td><td>Secrets Manager</td><td>Key Vault</td><td>Secret Manager</td></tr>
</table>

<p>Learn the concepts and the mapping, rather than memorising one vendor's
product names. The names change; the concepts move very slowly.</p>

<h2>3. Compute - Choosing What To Run On</h2>

<table>
<tr><th>Option</th><th>You manage</th><th>Use when</th><th>Cost shape</th></tr>
<tr><td>Virtual machine</td><td>OS, patching, everything</td><td>You need specific software or full control</td><td>Pay per hour, always on</td></tr>
<tr><td>Containers</td><td>Your app and its config</td><td>Consistent packaging across environments</td><td>Pay per node</td></tr>
<tr><td>Serverless functions</td><td>Nothing but the code</td><td>Event-driven, spiky, short-lived</td><td>Pay per invocation</td></tr>
<tr><td>Managed platform</td><td>Your code and its config</td><td>A web service without managing servers</td><td>Pay per use, with a floor</td></tr>
</table>

<p><strong>Memory trick:</strong> every step up this table gives away control and
takes away toil. Choose how far up to climb deliberately, not by default.</p>

<p>Serverless is genuinely cheaper for spiky, event-driven work and genuinely
more expensive for steady, always-on load. A service running flat out 24 hours a
day is usually cheaper on a small VM or container than on a per-invocation
function.</p>

<h2>4. Storage - Three Kinds, Three Trade-offs</h2>

<table>
<tr><th>Type</th><th>Shape</th><th>Access</th><th>Good for</th></tr>
<tr><td>Object</td><td>Files and blobs with a key</td><td>Over HTTP</td><td>Backups, static sites, data lakes</td></tr>
<tr><td>Block</td><td>Raw disks formatted by you</td><td>Mounted like a drive</td><td>Databases, anything needing a filesystem</td></tr>
<tr><td>File</td><td>Shared folders</td><td>Mounted over the network</td><td>Legacy shared storage, shared app files</td></tr>
</table>

<p>Object storage is cheap and effectively unlimited, but you cannot run SQL
against it. That single limitation is why data lakes and object storage coexist
rather than one replacing the other.</p>

<p>One decision worth getting right early: object storage should have versioning
and a lifecycle rule from day one. Retrofitting them means finding every object
that was ever written.</p>

<h2>5. Networking - VPC, Subnets And Routing</h2>

<p>A <strong>VPC</strong> is your private network in the cloud. Nothing inside is
reachable from the internet unless you explicitly open it.</p>

<p><strong>Subnets</strong> divide that network, and you split them across
availability zones so one failure does not take everything:</p>

<ul>
<li><strong>Public subnet</strong> - has a route to the internet. Load balancers,
NAT gateways and anything directly exposed.</li>
<li><strong>Private subnet</strong> - no direct internet route. Databases and
internal services. Reaches the internet only through a NAT gateway.</li>
</ul>

<p><strong>Memory trick:</strong> public things in public subnets, private things
in private subnets, and never put a database in a public subnet because it was
quick to deploy.</p>

<pre>Route table decides:      Network ACL decides:    Security group decides:
where traffic goes next   who may enter the subnet  what may talk to this resource
at the subnet level       at the subnet boundary    on the resource itself</pre>

<p>These three are constantly confused. A route table directs traffic between
subnets, a network access control list filters at the subnet boundary, and a
security group filters per resource. All three can block you, and all three have
their own rules pages.</p>

<h2>6. Identity And Access Management</h2>

<p>IAM is the control over who or what may do what, and it is the most important
security surface in a cloud account.</p>

<table>
<tr><th>Concept</th><th>What it is</th><th>Why it matters</th></tr>
<tr><td>User</td><td>A person</td><td>Prefer federation over creating users</td></tr>
<tr><td>Role</td><td>A set of permissions</td><td>Assign roles, never individual permissions</td></tr>
<tr><td>Policy</td><td>A document defining permissions</td><td>Least privilege, and auditable</td></tr>
<tr><td>Service role</td><td>A role one service assumes to act for you</td><td>How a function reads from object storage</td></tr>
<tr><td>Federation</td><td>Using your existing identity provider</td><td>Removes password storage entirely</td></tr>
</table>

<pre># Too broad - never do this
"Action": "s3:*", "Resource": "*"

# Least privilege - read one specific bucket
"Action": "s3:GetObject", "Resource": "arn:aws:s3:::my-bucket/reports/*"</pre>

<p><strong>Memory trick:</strong> least privilege is the whole principle. Give the
narrowest role that works, because you cannot revoke access you never granted
to a service you forgot about.</p>

<p>Enable MFA for everyone and make privileged actions require it. Cloud
credentials bypass every password policy your company has ever written.</p>

<h2>7. Security Groups In The Cloud</h2>

<p>Cloud security groups are the cloud form of the host firewall, and one
difference in behaviour catches people out: <strong>in most clouds a security
group rule that denies traffic does not exist.</strong></p>

<p>You describe what is allowed, and everything not described is refused. There
is no explicit deny rule to add, and no ordering to worry about.</p>

<pre>Ingress: allow TCP 443 from 0.0.0.0/0        # the internet
Ingress: allow TCP 22  from 203.0.113.10/32  # one office IP only
Egress:  allow all                          # consider narrowing this</pre>

<p>Restricting SSH to a single office IP is the single highest-value change most
people can make to a cloud account, because a public SSH port is under automated
attack continuously from the moment a machine is created.</p>

<h2>8. High Availability</h2>

<p>High availability means staying up when something breaks. In practice it is
built from three habits: never run one copy of anything important, spread the
copies apart, and fail over automatically.</p>

<table>
<tr><th>Technique</th><th>What it does</th><th>Protects against</th></tr>
<tr><td>Load balancer</td><td>Spreads traffic across healthy instances</td><td>One instance dying, uneven load</td></tr>
<tr><td>Auto-scaling group</td><td>Adds instances when load rises, removes them when it falls</td><td>Traffic spikes, and wasted spend afterwards</td></tr>
<tr><td>Multi-AZ</td><td>Runs copies in separate availability zones</td><td>A whole data centre failing</td></tr>
<tr><td>Health checks</td><td>Removes an unhealthy instance from rotation</td><td>A broken instance still receiving traffic</td></tr>
</table>

<p><strong>Memory trick:</strong> redundancy removes the single point of failure.
Scaling adds capacity. They are different problems and people confuse them
constantly.</p>

<h3>Setting real targets</h3>
<p>Availability is a number with an implied time window, so decide yours before
architecture work begins. It changes everything about how much you have to
build.</p>

<table>
<tr><th>Target</th><th>Downtime per year</th><th>What it demands</th></tr>
<tr><td>99.9%</td><td>8.8 hours</td><td>Multi-AZ, auto-scaling, tested failover</td></tr>
<tr><td>99.99%</td><td>53 minutes</td><td>Multi-region, no single point of failure anywhere</td></tr>
<tr><td>99.999%</td><td>5.3 minutes</td><td>Active-active, plus rehearsed regional failover</td></tr>
</table>

<h2>9. Disaster Recovery</h2>

<p>Disaster recovery is what you do when a region is gone. Availability keeps you
up during a component failure; disaster recovery is about surviving an event big
enough to take a whole location with it.</p>

<table>
<tr><th>Strategy</th><th>What it costs</th><th>Recovery time</th><th>Data lost</th></tr>
<tr><td>Backup and restore</td><td>Cheapest</td><td>Hours</td><td>Since last backup</td></tr>
<tr><td>Backup and replicate</td><td>Low</td><td>Minutes</td><td>Replication lag</td></tr>
<tr><td>Pilot light</td><td>Medium</td><td>Minutes</td><td>Replication lag</td></tr>
<tr><td>Active-passive</td><td>Expensive</td><td>Minutes</td><td>Replication lag</td></tr>
<tr><td>Active-active</td><td>Most expensive</td><td>Seconds</td><td>Almost none</td></tr>
</table>

<p>Two numbers come out of every DR plan and they are not the same thing:
<strong>RPO</strong>, how much data you can afford to lose, and <strong>RTO</strong>,
how long you can afford to be down. Cost is decided by those two numbers and by
nothing else.</p>

<p><strong>Memory trick:</strong> RPO is data, RTO is time. Backups protect the
first. Warm infrastructure protects the second.</p>

<h2>10. Backups And Lifecycle</h2>

<p>A backup you have never restored is a hope, not a backup. Test restores on a
schedule and record how long they took.</p>

<table>
<tr><th>Rule</th><th>Why</th></tr>
<tr><td>Follow the 3-2-1 rule</td><td>3 copies, on 2 media types, 1 off site. Still the best advice.</td></tr>
<tr><td>Enable versioning</td><td>Protects against deletion and ransomware, which backups alone do not</td></tr>
<tr><td>Set a lifecycle policy</td><td>Moves cold data to cheap storage, then expires it automatically</td></tr>
<tr><td>Encrypt with your own key</td><td>Protects against anyone who obtains the storage credentials</td></tr>
<tr><td>Rehearse a restore</td><td>The only way to know the recovery time is real</td></tr>
</table>

<h2>11. FinOps - Cost Is A Design Constraint</h2>

<p>FinOps is the practice of treating cloud spend as something you actively
manage rather than something you discover on an invoice. Most waste is
structural, not accidental.</p>

<table>
<tr><th>Technique</th><th>What it does</th><th>Typical saving</th></tr>
<tr><td>Rightsizing</td><td>Match instance size to actual measured use</td><td>20 to 40 percent</td></tr>
<tr><td>Auto-scaling</td><td>Remove capacity when demand falls</td><td>Large if load is variable</td></tr>
<tr><td>Storage classes</td><td>Move cold data to cheaper tiers automatically</td><td>60 to 90 percent on cold data</td></tr>
<tr><td>Spot instances</td><td>Buy spare capacity at a discount, interruptible</td><td>60 to 90 percent</td></tr>
<tr><td>Reserved or savings plans</td><td>Commit for a term, pay less for steady load</td><td>20 to 40 percent</td></tr>
<tr><td>Idle resource removal</td><td>Delete forgotten volumes, snapshots and IPs</td><td>Small but free</td></tr>
</table>

<p><strong>Memory trick:</strong> the cheapest resource is the one you are not
paying for. Delete first, downsize second, then optimise the architecture.</p>

<h3>Spot and reserved pricing</h3>
<table>
<tr><th>Model</th><th>Commitment</th><th>Discount</th><th>Risk</th></tr>
<tr><td>On-demand</td><td>None</td><td>None</td><td>None</td></tr>
<tr><td>Reserved</td><td>One or three years</td><td>20 to 40 percent</td><td>Paying for unused capacity</td></tr>
<tr><td>Spot</td><td>None</td><td>60 to 90 percent</td><td>The machine can vanish mid-run</td></tr>
</table>

<p>Spot is excellent for batch jobs, CI runners and stateless work that can
restart. It is dangerous for a single database with no replica.</p>

<h2>12. Putting It Together</h2>

<p>A typical well-built cloud application looks like this, and every element
above appears in it:</p>

<pre>Users
  |
CDN and web application firewall      (the cloud firewall layer)
  |
Application load balancer             (spreads traffic, drops unhealthy nodes)
  |
Auto-scaling group, 2+ instances     (capacity follows demand)
  across 2 or more availability zones
  |
Containers on a managed platform      (serverless or Kubernetes)
  |
Private subnets only                  (the database never sees the internet)
  |
Managed database, multi-AZ            (survives a zone failure)
  |
Object storage for backups            (versioned, lifecycle policy)
  |
IAM roles, least privilege           (nothing more than it needs)</pre>

<p><strong>Try it yourself:</strong> build one small thing end to end. A static
site in object storage behind a CDN, plus one function with a role that may read
exactly one bucket. It is about an hour, and you will touch more cloud concepts
than a month of reading.</p>

<p><strong>Learning vs production:</strong> a tutorial builds one machine in one
region with a shared admin login. Production means multi-region, immutable
infrastructure defined in code, no human passwords, a rehearsed failover, and a
bill somebody is accountable for every month.</p>"""
