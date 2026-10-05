"""Chapter - Amazon Web Services, taught current (2026).

Deliberately assumes no prior cloud knowledge. Every service table carries a
Learning vs Production comparison because the console defaults are unsafe for
real workloads.
"""

CHAPTER = """<h2>1. What AWS Actually Is</h2>

<p>AWS is the largest cloud provider: you rent servers, storage and databases
over the internet instead of buying hardware. You pay for what you use and turn
things off when you stop using them.</p>

<p><strong>The mental model that makes AWS click:</strong> everything you create
is a <em>resource</em>. Resources live inside a <em>region</em>, and access to
them is controlled by <em>IAM</em>. Nearly every AWS question is really one of
these three.</p>

<table>
<tr><th>Pillar</th><th>What it is</th><th>Why it matters</th></tr>
<tr><td>Regions</td><td>Isolated geographic areas, for example eu-west-1</td><td>Where your data physically lives</td></tr>
<tr><td>Availability Zones</td><td>Separate datacentres inside a region</td><td>Survive a single-site failure</td></tr>
<tr><td>Resources</td><td>EC2 instances, S3 buckets, RDS databases</td><td>The things you actually build</td></tr>
<tr><td>IAM</td><td>Identity and Access Management</td><td>Who may do what, the single biggest security lever</td></tr>
<tr><td>Shared responsibility</td><td>AWS secures the cloud, you secure your data</td><td>Explains why misconfiguration is the top breach cause</td></tr>
</table>

<p><strong>Memory trick:</strong> a <b>Region</b> is a city, an <b>Availability
Zone</b> is a separate data centre in that city. Two AZs means one data centre
can burn down without taking you offline.</p>

<h2>2. Regions, Availability Zones and Naming</h2>

<table>
<tr><th>Code</th><th>Region</th><th>Location</th></tr>
<tr><td>us-east-1</td><td>US East, N. Virginia</td><td>USA</td></tr>
<tr><td>eu-west-1</td><td>Europe, Ireland</td><td>Ireland</td></tr>
<tr><td>ap-south-1</td><td>Asia Pacific, Mumbai</td><td>India</td></tr>
<tr><td>us-east-2</td><td>US East, Ohio</td><td>USA</td></tr>
</table>

<p><strong>Read a region code right to left:</strong> the continent, then the
direction, then a number. <code>eu-west-1</code> is Europe, west, first region.</p>

<h3>The three availability zone types</h3>
<table>
<tr><th>Type</th><th>What you get</th><th>Use it when</th></tr>
<tr><td>Availability Zones</td><td>Independent datacentres, low latency between them</td><td>Almost always; this is the default choice</td></tr>
<tr><td>Local Zones</td><td>One zone, big cities, low latency from users</td><td>Media, gaming, need city-level closeness</td></tr>
<tr><td>Wavelength Zones</td><td>Inside 5G/mobile networks</td><td>Processing right at the mobile edge</td></tr>
</table>

<h2>3. The AWS Console and Naming Rules</h2>

<p>Almost every AWS service uses the same naming pattern. Learn it once and you
can predict resource names before you ever open the console.</p>

<pre>abbreviation-environment-account          e.g. dockeybe-prod-483920
myapp-prod-iam-role
dockeybe-prod-1-subnet-public</pre>

<h3>Shared responsibility in one line each</h3>
<table>
<tr><th>AWS is responsible for</th><th>You are responsible for</th></tr>
<tr><td>Security of the physical datacentres</td><td>Your IAM permissions</td></tr>
<tr><td>The hypervisor and host OS patches</td><td>The guest OS and its packages</td></tr>
<tr><td>Storage durability of the disks</td><td>Your bucket policies and encryption</td></tr>
<tr><td>Managed service patching</td><td>Your application code and its secrets</td></tr>
</table>

<p><strong>Memory trick:</strong> the biggest cause of cloud breaches is not AWS
failing, it is a customer leaving a bucket public. That is your job.</p>

<h2>4. IAM - The Most Important Service</h2>

<p>IAM controls who can do what to which resources, and when. Get this right and
most security problems disappear.</p>

<h3>The building blocks</h3>

<table>
<tr><th>Building block</th><th>Is it a person or a thing?</th><th>What it holds</th></tr>
<tr><td>User</td><td>A human</td><td>Long-term credentials, which you should almost never create</td></tr>
<tr><td>Role</td><td>A service, an app or a third party</td><td>Short-lived credentials</td></tr>
<tr><td>Group</td><td>A set of users</td><td>Attach policies to many people at once</td></tr>
<tr><td>Policy</td><td>Neither</td><td>The permissions themselves, as JSON</td></tr>
</table>

<p><strong>Memory trick:</strong> users and groups are for <b>people</b>. Roles
are for <b>software</b>. If a machine has an identity, it should be a role.</p>

<h3>Policy anatomy</h3>

<pre>{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::my-bucket/reports/*",
    "Condition": {
      "IpAddress": { "aws:SourceIp": "203.0.113.0/24" }
    }
  }]
}</pre>

<table>
<tr><th>Element</th><th>Meaning</th></tr>
<tr><td>Effect</td><td>Allow or Deny. An explicit Deny always wins</td></tr>
<tr><td>Action</td><td>What is permitted, such as s3:GetObject, or * for everything</td></tr>
<tr><td>Resource</td><td>Which thing, written as an ARN</td></tr>
<tr><td>Condition</td><td>Extra rules such as source IP, time or MFA</td></tr>
</table>

<h3>The rules that keep you safe</h3>
<ul>
<li><strong>Never use * for Action.</strong> Grant the specific call you need.</li>
<li><strong>Scope every resource.</strong> A role that can do anything anywhere
is a role that will eventually do anything somewhere.</li>
<li><strong>No long-lived users.</strong> Use IAM Identity Centre and temporary
credentials.</li>
<li><strong>Deny by default.</strong> An identity with no policy can do nothing.</li>
<li><strong>Rotate and audit.</strong> Use CloudTrail and Access Analyzer.</li>
</ul>

<pre># The single most useful IAM commands
aws iam list-users
aws iam list-roles
aws sts get-caller-identity
aws iam get-policy --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess</pre>

<h2>5. Networking - VPC, Subnet, Security Group</h2>

<p>A VPC is your private network inside AWS. Everything you launch lives in one.</p>

<table>
<tr><th>Concept</th><th>What it is</th><th>Analogy</th></tr>
<tr><td>VPC</td><td>Your private network</td><td>The whole city</td></tr>
<tr><td>Subnet</td><td>A smaller slice of the VPC</td><td>A street</td></tr>
<tr><td>Route table</td><td>Where traffic from a subnet goes</td><td>Signposts</td></tr>
<tr><td>Internet Gateway</td><td>The door to the internet</td><td>The city gate</td></tr>
<tr><td>NAT Gateway</td><td>Allows outbound only</td><td>A one-way exit</td></tr>
<tr><td>Security Group</td><td>Firewall attached to a resource</td><td>A guard on each door</td></tr>
<tr><td>Network ACL</td><td>Firewall attached to a subnet</td><td>A checkpoint at the street entrance</td></tr>
</table>

<h3>Public vs private subnets - the key decision</h3>

<table>
<tr><th>Aspect</th><th>Public subnet</th><th>Private subnet</th></tr>
<tr><td>Route to the internet</td><td>Direct via an Internet Gateway</td><td>Only outbound, via a NAT Gateway</td></tr>
<tr><td>Reachable from the internet</td><td>Yes, if a security group allows it</td><td>No, ever</td></tr>
<tr><td>Holds</td><td>Load balancers</td><td>Databases, internal apps, workers</td></tr>
<tr><td>Why</td><td>Needs to accept inbound traffic</td><td>Must not be exposed to attackers</td></tr>
</table>

<p><strong>Memory trick:</strong> a database never goes in a public subnet. This
one rule prevents a large share of real-world data breaches.</p>

<h3>Security groups vs network ACLs</h3>
<table>
<tr><th>Aspect</th><th>Security Group</th><th>Network ACL</th></tr>
<tr><td>Applies to</td><td>Individual resources</td><td>Whole subnet</td></tr>
<tr><td>Stateful</td><td>Yes, return traffic is automatic</td><td>No, you must allow both directions</td></tr>
<tr><td>Order</td><td>No rules, just allow and deny</td><td>Evaluated in numbered order</td></tr>
<tr><td>Change effect</td><td>Only affects new connections</td><td>Can kill live traffic instantly</td></tr>
</table>

<h3>CIDR blocks to remember</h3>
<table>
<tr><th>CIDR</th><th>Means</th><th>Is it safe?</th></tr>
<tr><td>0.0.0.0/0</td><td>Everywhere on the internet</td><td>Only for public resources such as a load balancer</td></tr>
<tr><td>10.0.0.0/8</td><td>All private 10.x addresses</td><td>Acceptable for internal traffic</td></tr>
<tr><td>203.0.113.0/24</td><td>One small public office network</td><td>Yes, this is scoped</td></tr>
</table>

<p><strong>Warning:</strong> opening port 22 or 3389 to 0.0.0.0/0 is scanned
within minutes of being created. Never do it.</p>

<pre># AWS CLI network commands
aws ec2 describe-vpcs
aws ec2 describe-subnets
aws ec2 describe-security-groups
aws ec2 create-vpc --cidr-block 10.0.0.0/16</pre>

<h2>6. S3 - Object Storage</h2>

<p>S3 stores files as objects in buckets. You can think of it as an infinitely
large hard drive you access over the web, though it behaves nothing like a
filesystem.</p>

<h3>Storage classes - pick by how often you read</h3>

<table>
<tr><th>Class</th><th>Built for</th><th>Retrieval cost</th><th>Typical use</th></tr>
<tr><td>Standard</td><td>Frequent access</td><td>None</td><td>Active application data</td></tr>
<tr><td>Standard-IA</td><td>Infrequent but quick</td><td>Small</td><td>Data lake, analytics</td></tr>
<tr><td>Intelligent-Tiering</td><td>Unknown or changing pattern</td><td>None</td><td>When you cannot predict usage</td></tr>
<tr><td>Glacier Instant</td><td>Rarely, needs minutes</td><td>Small</td><td>Versioned backups</td></tr>
<tr><td>Glacier Flexible</td><td>Rarely, needs hours</td><td>Moderate</td><td>Quarterly archives</td></tr>
<tr><td>Deep Archive</td><td>Almost never</td><td>Higher</td><td>Compliance, 7 to 10 year retention</td></tr>
</table>

<p><strong>Memory trick:</strong> colder storage is cheaper to keep and more
expensive to fetch. Move data down tiers as it ages.</p>

<h3>Lifecycle rules</h3>
<p>Transition objects automatically: to Standard-IA at 30 days, to Glacier at
90, and delete at 365. This is how real buckets stay affordable.</p>

<h3>Block Public Access</h3>
<p>Four settings, all of which should be ON for almost every bucket. This is the
single most effective S3 security control.</p>

<ul>
<li>Block all public access</li>
<li>Ignore public ACLs</li>
<li>Block public bucket policies</li>
<li>Restrict public bucket ACLs</li>
</ul>

<pre># Useful S3 commands
aws s3 ls
aws s3 cp report.csv s3://my-bucket/
aws s3 sync ./dist s3://my-bucket/ --delete
aws s3api get-bucket-versioning --bucket my-bucket
aws s3 presign "s3://my-bucket/report.pdf" --expires-in 3600</pre>

<h3>S3 Learning vs Production</h3>
<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Public access</td><td>Bucket left public so you can read it</td><td>Block Public Access on, signed URLs or CloudFront</td></tr>
<tr><td>Encryption</td><td>Default only</td><td>SSE-KMS with a customer-managed key</td></tr>
<tr><td>Versioning</td><td>Off</td><td>On, with a lifecycle policy to expire old versions</td></tr>
<tr><td>Deleting</td><td>console delete</td><td>Never; rely on versioning and lifecycle rules</td></tr>
<tr><td>Access</td><td>Access keys on your laptop</td><td>IAM roles, ideally temporary credentials</td></tr>
</table>

<h2>7. Compute - EC2 and Beyond</h2>

<table>
<tr><th>Service</th><th>You manage</th><th>AWS manages</th><th>Start time</th><th>Use when</th></tr>
<tr><td>EC2</td><td>The whole OS and its patches</td><td>The physical host</td><td>Minutes</td><td>You need full control or unusual software</td></tr>
<tr><td>ECS</td><td>Containers and scaling</td><td>The servers</td><td>Minutes</td><td>You already run Docker</td></tr>
<tr><td>EKS</td><td>Kubernetes</td><td>The control plane</td><td>About 10 minutes</td><td>You already run Kubernetes</td></tr>
<tr><td>Fargate</td><td>Nothing but the container</td><td>Servers and containers</td><td>Seconds</td><td>Spiky or unpredictable load</td></tr>
<tr><td>Lambda</td><td>Only the function</td><td>Everything else</td><td>Under a second</td><td>Event-driven, short tasks</td></tr>
</table>

<p><strong>Memory trick:</strong> each step up the table removes one more thing
you must patch and monitor. Choose the highest level you can comfortably
operate.</p>

<h3>EC2 things to know</h3>
<ul>
<li><strong>AMI</strong> - the template for an instance. Never use
<code>latest</code>, because it changes under you.</li>
<li><strong>Instance types</strong> - <code>t3.micro</code> is cheap and burstable,
<code>m7g.large</code> is general purpose, <code>c7g.xlarge</code> is compute
optimised, <code>r7g.large</code> is memory optimised.</li>
<li><strong>Key pairs</strong> - SSH keys for Linux, not for Windows.</li>
<li><strong>Placement groups</strong> - how instances are spread across AZs.</li>
</ul>

<h3>Serverless - Lambda</h3>
<p>You upload a function, AWS runs it per request and you pay per invocation.
Watch three limits:</p>
<table>
<tr><th>Limit</th><th>Typical value</th><th>What it means</th></tr>
<tr><td>Timeout</td><td>Up to 15 minutes</td><td>Longer work needs Step Functions or ECS</td></tr>
<tr><td>Memory</td><td>128 MB to 10 GB</td><td>Power scales with memory, not CPU</td></tr>
<tr><td>Package size</td><td>250 MB zipped</td><td>Large dependencies must sit in a layer</td></tr>
<tr><td>Cold start</td><td>Under a second usually</td><td>First call on a new container is slower</td></tr>
</table>

<h2>8. Databases</h2>

<table>
<tr><th>Service</th><th>Model</th><th>Managed by AWS</th><th>Scales by</th><th>Use when</th></tr>
<tr><td>RDS MySQL or Postgres</td><td>Relational, SQL</td><td>Yes, including patching</td><td>Vertically, with read replicas</td><td>Your data has relationships</td></tr>
<tr><td>Aurora</td><td>Relational, MySQL or Postgres compatible</td><td>Yes, with 6 copies across 3 AZs</td><td>Storage separates from compute</td><td>You need high availability by default</td></tr>
<tr><td>DynamoDB</td><td>Key-value, NoSQL</td><td>Fully serverless</td><td>Automatically, on partition key</td><td>Traffic is spiky and unpredictable</td></tr>
<tr><td>ElastiCache</td><td>In-memory cache</td><td>Yes</td><td>Node size and shard count</td><td>To remove a database bottleneck</td></tr>
<tr><td>Redshift</td><td>Data warehouse, columnar</td><td>Yes</td><td>Node count and concurrency</td><td>Reporting and analytics over huge data</td></tr>
</table>

<p><strong>Memory trick:</strong> relational and fixed-shape data is RDS. Spiky,
key-value and enormous traffic is DynamoDB.</p>

<h3>RDS decisions that matter</h3>
<ul>
<li><strong>Multi-AZ</strong> is standby replication for failure, not for speed.</li>
<li><strong>Read replicas</strong> are for read-heavy load.</li>
<li><strong>Backups</strong> are automatic and kept for a window you set.</li>
<li><strong>Never put a database in a public subnet.</strong></li>
</ul>

<h2>9. DNS, Load Balancing and Scaling</h2>

<h3>Route 53</h3>
<p>Route 53 is AWS's DNS. Beyond simple records it is a full traffic router,
which makes failover surprisingly simple.</p>

<table>
<tr><th>Record type</th><th>Points to</th><th>Typical use</th></tr>
<tr><td>A</td><td>An IPv4 address</td><td>Normal web traffic</td></tr>
<tr><td>AAAA</td><td>An IPv6 address</td><td>Modern clients</td></tr>
<tr><td>CNAME</td><td>Another hostname</td><td>www pointing to example.com</td></tr>
<tr><td>ALIAS</td><td>An AWS resource such as an S3 bucket</td><td>Apex domains, with no extra charge</td></tr>
<tr><td>Weighted</td><td>Several records split by weight</td><td>Blue and green, or a 10 percent canary</td></tr>
<tr><td>Failover</td><td>Primary with a health-checked backup</td><td>Automatic disaster recovery</td></tr>
<tr><td>Latency</td><td>The fastest healthy region</td><td>Users spread around the world</td></tr>
</table>

<h3>Load balancers</h3>
<table>
<tr><th>Type</th><th>Layer</th><th>Routes on</th><th>Example</th></tr>
<tr><td>Application LB</td><td>7, HTTP</td><td>Path, host, headers</td><td>example.com to /api or /web</td></tr>
<tr><td>Network LB</td><td>4, TCP</td><td>Port and IP only</td><td>Ultra low latency, gaming, TLS offload</td></tr>
<tr><td>Gateway LB</td><td>3</td><td>IP and port across many servers</td><td>Firewalls and intrusion detection appliances</td></tr>
</table>

<p><strong>Memory trick:</strong> ALB for HTTP rules, NLB for raw TCP speed,
GWLB for appliances. ALB is the default choice for web applications.</p>

<h3>Auto Scaling</h3>
<p>Auto Scaling keeps a minimum instance count, adds instances when CPU or a
custom metric rises, and removes them when load falls. Always pair it with a load
balancer and health checks, or it will cheerfully scale to zero healthy nodes.</p>

<h2>10. The Well-Architected Pillars</h2>

<table>
<tr><th>Pillar</th><th>One-line summary</th><th>The question it asks</th></tr>
<tr><td>Operational excellence</td><td>Run and monitor systems continuously</td><td>Will we learn from every change?</td></tr>
<tr><td>Security</td><td>Protect data, systems and assets</td><td>Who can do what, and did we audit it?</td></tr>
<tr><td>Reliability</td><td>Recover from failure and meet demand</td><td>What happens when this component dies?</td></tr>
<tr><td>Performance efficiency</td><td>Use resources efficiently</td><td>Are we using the right size or shape?</td></tr>
<tr><td>Cost optimisation</td><td>Deliver value at the lowest price</td><td>What are we paying for and not using?</td></tr>
<tr><td>Sustainability</td><td>Minimise environmental impact</td><td>Are we burning more compute than the task needs?</td></tr>
</table>

<p><strong>Memory trick:</strong> <b>O</b>perational excellence,
<b>S</b>ecurity, <b>R</b>eliability, <b>P</b>erformance, <b>C</b>ost,
<b>S</b>ustainability. Every AWS certification exam maps onto these.</p>

<h2>11. Cost Control - Where Money Is Lost</h2>

<table>
<tr><th>Common mistake</th><th>How to spot it</th><th>The fix</th></tr>
<tr><td>An idle EC2 left running</td><td>Cost Explorer, grouped by service</td><td>Stop it, or schedule it for the hours it is used</td></tr>
<tr><td>Unassociated Elastic IPs</td><td>They are billed even with nothing attached</td><td>Release them</td></tr>
<tr><td>Forgotten test environments</td><td>Cost by tag or by account</td><td>Tag everything and automate teardown</td></tr>
<tr><td>Cold S3 data in Standard</td><td>Large buckets that are rarely read</td><td>Lifecycle rules moving data to Glacier</td></tr>
<tr><td>Data transfer out of AWS</td><td>A surprising NAT Gateway or S3 bill</td><td>Cache with CloudFront, or keep traffic inside AWS</td></tr>
<tr><td>Oversized databases</td><td>Low CPU on a large instance class</td><td>Downsize and enable storage autoscaling</td></tr>
</table>

<pre># Cost and audit commands
aws ce get-cost-and-usage --time-period Start=2026-01-01,End=2026-02-01 --granularity MONTHLY
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running"
aws budget create-budget --budget-name Monthly --budget-type COST --limit Amount=100,Unit=USD
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=DeleteTrail</pre>

<p><strong>Memory trick:</strong> a bill spike is almost always an unused
resource. Tag everything, set budget alerts, and review Cost Explorer monthly.</p>

<h2>12. What Is New in 2026</h2>

<table>
<tr><th>Area</th><th>What changed</th><th>Why it matters</th></tr>
<tr><td>Generative AI</td><td>Amazon Bedrock offers managed access to many models with no vendor lock-in</td><td>Build AI features without training or hosting a model</td></tr>
<tr><td>EKS Auto Mode</td><td>A fully managed Kubernetes node lifecycle</td><td>No more hand-built node groups</td></tr>
<tr><td>Elastic disaster recovery</td><td>Cross-region recovery as a managed service</td><td>A regional failure becomes a non-event</td></tr>
<tr><td>S3 Express One Zone</td><td>Single-zone storage at very high throughput</td><td>For data processing, not long-term storage</td></tr>
<tr><td>OpenTelemetry in AWS</td><td>OTel-native in CloudWatch, X-Ray and ECS</td><td>Vendor-neutral observability</td></tr>
<tr><td>Savings Plans and Graviton</td><td>Commit to usage, and use ARM chips for up to 40 percent less</td><td>The two biggest levers on monthly cost</td></tr>
<tr><td>IPv6 by default</td><td>New VPCs and services now prefer IPv6</td><td>Plan for dual stack from the start</td></tr>
</table>

<h2>13. Try It Yourself (60 minutes)</h2>
<ul>
<li>Create an AWS account and set up a second factor. Do not skip this even on
the free tier.</li>
<li>In IAM, create a role for EC2 that may only read one S3 bucket. Attach no
wildcards.</li>
<li>Create a VPC with two subnets in different availability zones, one public
and one private.</li>
<li>Create a security group allowing SSH only from your own IP, never
0.0.0.0/0.</li>
<li>Launch an EC2 instance with a pinned AMI and a key pair. Terminate it when
done.</li>
<li>Create an S3 bucket, upload a file, and confirm Block Public Access is on.</li>
<li>Run <code>aws sts get-caller-identity</code> and
<code>aws ce get-cost-and-usage</code>.</li>
<li>Set a monthly budget with an alert at 50 percent.</li>
</ul>

<h2>14. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Access keys</td><td>Long-lived keys on your laptop</td><td>IAM roles and Identity Centre, never stored keys</td></tr>
<tr><td>AMIs</td><td>The latest Amazon Linux</td><td>Pinned version, patched by a scheduled pipeline</td></tr>
<tr><td>Regions</td><td>us-east-1 only</td><td>At least two, with tested failover</td></tr>
<tr><td>Availability</td><td>A single instance</td><td>Multi-AZ behind an autoscaling group</td></tr>
<tr><td>Infrastructure</td><td>Clicking in the console</td><td>All of it in code, reviewed and applied by pipeline</td></tr>
<tr><td>Secrets</td><td>Plaintext in a config file</td><td>Secrets Manager or SSM Parameter Store, encrypted</td></tr>
<tr><td>Tagging</td><td>None</td><td>Environment, owner and cost centre on everything</td></tr>
<tr><td>Teardown</td><td>Deleting in the console</td><td>Automated destruction of ephemeral environments</td></tr>
<tr><td>Logging</td><td>Default only</td><td>CloudTrail everywhere, centralised and alerted</td></tr>
<tr><td>Guardrails</td><td>Your own discipline</td><td>SCPs, Config rules and Control Tower accounts</td></tr>
</table>

<h2>15. Key Takeaways</h2>
<ul>
<li>Everything is a resource, in a region, governed by IAM. That is the model.</li>
<li>A region is a city; an availability zone is a separate data centre in it.</li>
<li>Users are for people, roles are for software.</li>
<li>Never put a database in a public subnet, and never open 22 or 3389 to the
world.</li>
<li>Block Public Access on every S3 bucket.</li>
<li>A bill spike is almost always an idle resource. Tag, budget, review.</li>
<li>Infrastructure should live in code, not in console clicks.</li>
</ul>
"""