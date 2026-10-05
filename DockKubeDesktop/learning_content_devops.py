"""Chapter 9 - DevOps, cloud and the tooling in this app."""

CHAPTER = """<h2>1. What Is DevOps?</h2>

<p>DevOps removes the wall between writing software and running it. Developers own
their code in production, and operations teams write code. The goal is small,
frequent, reversible changes.</p>

<p><strong>Memory trick for the golden signals:</strong> latency, traffic, errors
and saturation. Monitor those four and you know whether your service is
healthy.</p>

<h2>2. Containers - Docker</h2>

<p>A container packages your application with its dependencies into a single image
that runs identically everywhere. That removes the classic "works on my
machine" problem.</p>

<pre>docker build -t myapp:1.0 .
docker run -d -p 8080:80 --name web myapp:1.0
docker ps
docker logs -f web
docker exec -it web sh
docker stop web &amp;&amp; docker rm web</pre>

<table>
<tr><th>Concept</th><th>Meaning</th><th>Analogy</th></tr>
<tr><td>Image</td><td>An immutable template with the app and its dependencies</td><td>A recipe</td></tr>
<tr><td>Container</td><td>A running instance of an image</td><td>A cooked meal from the recipe</td></tr>
<tr><td>Dockerfile</td><td>The build instructions for an image</td><td>The written recipe</td></tr>
<tr><td>Volume</td><td>Storage that survives container deletion</td><td>A hard drive, not RAM</td></tr>
<tr><td>Registry</td><td>Where images are stored and shared</td><td>A library</td></tr>
</table>

<p><strong>Containers versus virtual machines:</strong> a VM emulates hardware and
ships a full OS kernel, so it is large and slow to boot. A container shares the
host kernel, so it is small and starts almost instantly.</p>

<h2>3. Kubernetes - Scheduling Containers</h2>

<p>Kubernetes keeps a desired number of containers running. If one dies it is
replaced; if traffic rises it scales out. You describe the desired state and the
controller makes it happen.</p>

<table>
<tr><th>Object</th><th>What it does</th><th>Use it for</th></tr>
<tr><td>Pod</td><td>The smallest runnable unit</td><td>Anything, but rarely created by hand</td></tr>
<tr><td>Deployment</td><td>Manages a stateless replicated workload</td><td>Web servers, APIs, workers</td></tr>
<tr><td>StatefulSet</td><td>Stable identity and storage per replica</td><td>Databases, anything needing a fixed disk</td></tr>
<tr><td>Service</td><td>A stable virtual IP in front of changing pods</td><td>Networking, always</td></tr>
<tr><td>Ingress</td><td>Routes outside HTTP traffic by path or host</td><td>One entry point for many services</td></tr>
<tr><td>ConfigMap</td><td>Non-secret configuration</td><td>Environment specific settings</td></tr>
<tr><td>Secret</td><td>Sensitive values such as passwords</td><td>Credentials and tokens</td></tr>
<tr><td>PVC</td><td>A request for persistent storage</td><td>Anything that must keep data</td></tr>
</table>

<p><strong>Memory trick:</strong> Deployment for things that can be thrown away,
StatefulSet for things that cannot.</p>

<pre>kubectl apply -f app.yaml
kubectl get pods
kubectl describe pod &lt;name&gt;
kubectl logs -f deployment/myapp
kubectl exec -it &lt;pod&gt; -- sh
kubectl port-forward svc/myapp 8080:80
kubectl scale deployment/myapp --replicas=3
kubectl rollout status deployment/myapp
kubectl rollout undo deployment/myapp
kubectl delete -f app.yaml</pre>

<h2>4. Containers versus Virtual Machines</h2>

<table>
<tr><th>Aspect</th><th>Virtual machine</th><th>Container</th></tr>
<tr><td>Contains</td><td>A full OS with its own kernel</td><td>Just the app and its libraries</td></tr>
<tr><td>Size</td><td>Gigabytes</td><td>Megabytes</td></tr>
<tr><td>Start time</td><td>Minutes</td><td>Milliseconds</td></tr>
<tr><td>Isolation</td><td>Strong, separate kernel</td><td>Weaker, shares the host kernel</td></tr>
<tr><td>Density</td><td>Dozens per host</td><td>Hundreds per host</td></tr>
<tr><td>Best for</td><td>Full OS, strong isolation, legacy apps</td><td>Microservices, scale out, fast deploys</td></tr>
</table>

<h2>5. Where to Go Deeper</h2>

<p>The tool mechanics live in their own chapters so this chapter stays about
mindset. Use these pointers when you need the detail.</p>

<table>
<tr><th>Topic</th><th>Go to</th><th>Why it is separate</th></tr>
<tr><td>CI/CD pipelines, GitHub Actions</td><td>Chapter 13, Delivery Tooling</td><td>Workflow syntax, matrices, caching and runners need room</td></tr>
<tr><td>Jenkins pipelines</td><td>Chapter 13, Delivery Tooling</td><td>Jenkinsfile, agents and plugins are a large topic</td></tr>
<tr><td>Terraform and Ansible</td><td>Chapter 13, Delivery Tooling</td><td>State, backends, modules and roles need proper explanation</td></tr>
<tr><td>Scrum, Agile and the SDLC</td><td>Chapter 11, SDLC, Agile and Scrum</td><td>Roles, events and artefacts deserve their own treatment</td></tr>
<tr><td>AWS services in depth</td><td>Chapter 12, AWS</td><td>Regions, IAM, VPC, S3, EC2 and cost control</td></tr>
<tr><td>Linux and Windows commands</td><td>Chapters 8 and 10</td><td>Full command references with permissions and services</td></tr>
</table>

<p><strong>Memory trick:</strong> this chapter answers <b>what</b> DevOps is and
<b>why</b> it exists. Chapter 13 answers <b>how</b> to run the delivery
pipeline.</p>

<pre>gh workflow list
gh run list --limit 10
gh run view &lt;id&gt; --log-failed
gh workflow run deploy.yml --ref main
act -l              # run workflows locally before pushing</pre>

<h2>6. Version Control with Git</h2>

<p>Git tracks changes so you can experiment safely and undo anything.</p>

<pre>git init
git add .
git commit -m "message"
git branch feature
git switch feature
git merge main
git push -u origin feature</pre>

<p>A file lives in one of three places: the working directory, the staging area,
and the repository. <code>git add</code> moves it to staging,
<code>git commit</code> saves it.</p>

<h2>7. Observability</h2>

<table>
<tr><th>Pillar</th><th>Question it answers</th><th>Examples</th></tr>
<tr><td>Logs</td><td>What happened in this event?</td><td>Structured JSON logs in Loki or ELK</td></tr>
<tr><td>Metrics</td><td>How is the system doing overall?</td><td>Prometheus and Grafana</td></tr>
<tr><td>Traces</td><td>Where did this request spend its time?</td><td>OpenTelemetry, Jaeger, Tempo</td></tr>
</table>

<p><strong>Memory trick:</strong> logs tell you <b>what</b>, metrics tell you
<b>whether to worry</b>, traces tell you <b>where</b>. You need all three.</p>

<h2>8. Learning vs Production</h2>

<p>Linux command line skills are covered in full in the Linux Command Line chapter.
The habits that matter most when applying them to infrastructure are below.</p>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Containers</td><td>docker-compose up on one machine</td><td>Orchestrated, autoscaled, patched automatically</td></tr>
<tr><td>Images</td><td>The latest tag</td><td>Pinned digests, signed and scanned</td></tr>
<tr><td>Kubernetes</td><td>minikube or kind</td><td>Managed clusters with multi-AZ node pools</td></tr>
<tr><td>Secrets</td><td>Plain ConfigMaps</td><td>External secret managers with automatic rotation</td></tr>
<tr><td>Deploys</td><td>Applying the YAML by hand</td><td>GitOps, progressive rollout, automatic rollback</td></tr>
<tr><td>Logs</td><td>docker logs</td><td>Centralised, searchable, retained</td></tr>
<tr><td>Infrastructure</td><td>Terraform state on your laptop</td><td>Remote state with locking in a shared bucket</td></tr>
<tr><td>Access</td><td>root, all the time</td><td>Least privilege, SSO, audited, just-in-time</td></tr>
<tr><td>Monitoring</td><td>Staring at a terminal</td><td>Dashboards, alerts, and someone paged</td></tr>
</table>

<h2>9. Key Takeaways</h2>
<ul>
<li>DevOps means developers own their code in production.</li>
<li>An image is a template; a container is a running instance of it.</li>
<li>Deployment for disposable workloads, StatefulSet for things with data.</li>
<li>Terraform plan is a rehearsal and apply is the performance; always read it.</li>
<li>Ansible with --check shows what would change without changing it.</li>
<li>Logs say what, metrics say whether to worry, traces say where.</li>
</ul>
"""