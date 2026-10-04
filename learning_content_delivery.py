"""Chapter - Delivery tooling: CI/CD, GitHub Actions, Jenkins, Terraform, Ansible.

One chapter covering the toolchain that gets code from a commit into running
production, and the two tools that describe the infrastructure and the machines
it runs on.
"""

CHAPTER = """<h2>1. What a CI/CD Pipeline Actually Is</h2>

<p>A pipeline is an automated sequence that takes code from a commit to something
running in production. It replaces the instruction "it builds on my machine" with
"it built successfully, twice, on a clean machine".</p>

<pre>commit -> build -> test -> package -> security scan -> deploy staging
       -> smoke test -> deploy production -> monitor</pre>

<table>
<tr><th>Term</th><th>Means</th><th>Detail</th></tr>
<tr><td>CI, Continuous Integration</td><td>Merge often, build automatically</td><td>Every push is compiled and tested</td></tr>
<tr><td>CD, Continuous Delivery</td><td>Always ready to release</td><td>A human approves the production release</td></tr>
<tr><td>Continuous Deployment</td><td>Releases with no human step</td><td>Green build goes straight to production</td></tr>
<tr><td>Pipeline</td><td>The whole automated process</td><td>Defined as code, usually YAML</td></tr>
<tr><td>Pipeline as code</td><td>The pipeline lives in version control</td><td>Reviewable, versioned, auditable</td></tr>
</table>

<p><strong>Memory trick:</strong> <b>C</b>ontinuous <b>I</b>ntegration is about
code, <b>D</b>elivery is about being ready, <b>D</b>eployment is about actually
doing it.</p>

<h2>2. The Standard Pipeline Stages</h2>

<table>
<tr><th>Stage</th><th>What it does</th><th>Typical gate</th></tr>
<tr><td>Source</td><td>Clone, check out the exact commit</td><td>Fails if the branch is protected</td></tr>
<tr><td>Build</td><td>Compile, bundle, resolve dependencies</td><td>Build errors stop everything</td></tr>
<tr><td>Unit test</td><td>Fast tests, no external services</td><td>Must pass 100 percent</td></tr>
<tr><td>Code quality</td><td>Lint, format, coverage threshold</td><td>Blocks on new violations</td></tr>
<tr><td>Security scan</td><td>Dependency CVEs, secrets, SAST</td><td>Blocks critical findings</td></tr>
<tr><td>Package</td><td>Build a container image, tag it</td><td>Image must be reproducible</td></tr>
<tr><td>Integration test</td><td>Real databases, real services</td><td>Must pass before deploy</td></tr>
<tr><td>Deploy staging</td><td>Automatic, no approval</td><td>Always automatic</td></tr>
<tr><td>Smoke test</td><td>Is the app actually alive?</td><td>Blocks production on failure</td></tr>
<tr><td>Deploy production</td><td>Promotion, canary or blue-green</td><td>Manual or automatic by policy</td></tr>
<tr><td>Verify and monitor</td><td>Health checks and metrics</td><td>Automatic rollback on failure</td></tr>
</table>

<p><strong>Memory trick:</strong> fail fast and cheap. A unit test failure costs
seconds; a production failure costs hours. Put the cheap gates first.</p>

<h2>3. Deployment Strategies</h2>

<table>
<tr><th>Strategy</th><th>How it works</th><th>Rollback</th><th>Downtime</th><th>Cost</th></tr>
<tr><td>Recreate</td><td>Stop the old, start the new</td><td>Redeploy the old version</td><td>Yes</td><td>Cheapest</td></tr>
<tr><td>Rolling</td><td>Replace instances a few at a time</td><td>Redeploy the previous image</td><td>No</td><td>Low</td></tr>
<tr><td>Blue-green</td><td>Run both, then cut traffic over</td><td>Flip traffic back instantly</td><td>No</td><td>Double capacity briefly</td></tr>
<tr><td>Canary</td><td>Send a small percentage of traffic to the new version</td><td>Route 100 percent back to old</td><td>No</td><td>Needs real traffic splitting</td></tr>
<tr><td>Rolling canary</td><td>Canary plus continuous automated analysis</td><td>Automatic on metric regression</td><td>No</td><td>Most tooling and effort</td></tr>
</table>

<p><strong>Memory trick:</strong> <b>R</b>ecreate is <b>R</b>isky, <b>B</b>lue-green
is <b>B</b>ackup, <b>C</b>anary is a small <b>C</b>anary bird that tests the
mine. Rolling sits in between.</p>

<h2>4. Pipeline Security Essentials</h2>

<table>
<tr><th>Practice</th><th>Why it matters</th><th>Where it lives</th></tr>
<tr><td>Least-privilege token permissions</td><td>A leaked token should do minimal damage</td><td><code>permissions:</code> in the workflow</td></tr>
<tr><td>Pin third-party actions to a SHA</td><td>Tags can be moved to malicious code</td><td><code>uses: org/action@sha256:...</code></td></tr>
<tr><td>OIDC instead of stored keys</td><td>No long-lived cloud secrets in GitHub</td><td>Cloud provider role assumption</td></tr>
<tr><td>Protect the main branch</td><td>Nobody should push straight to production</td><td>Branch protection rules</td></tr>
<tr><td>Signed images and commits</td><td>Proves nothing was altered in transit</td><td>Cosign, Sigstore</td></tr>
<tr><td>Never echo secrets</td><td>Logs are readable by everyone with access</td><td>Masked secrets in CI</td></tr>
</table>

<p><strong>Memory trick:</strong> if a credential lives in a config file, assume
it will end up on the internet. Use short-lived, scoped credentials instead.</p>

<h2>5. GitHub Actions - Workflow Anatomy</h2>

<p>A workflow is a YAML file in <code>.github/workflows/</code>. It has triggers
(<code>on:</code>), one or more jobs, and steps inside each job.</p>

<pre>name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pytest -q
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}</pre>

<table>
<tr><th>Key</th><th>Meaning</th><th>Note</th></tr>
<tr><td><code>name</code></td><td>Workflow name shown in the UI</td><td>Your only real documentation</td></tr>
<tr><td><code>on:</code></td><td>When it runs</td><td>push, pull_request, schedule, workflow_dispatch</td></tr>
<tr><td><code>permissions:</code></td><td>The token's allowed actions</td><td>Always set this, even to read-only</td></tr>
<tr><td><code>runs-on:</code></td><td>Which runner</td><td>Pin the version for reproducibility</td></tr>
<tr><td><code>steps:</code></td><td>Ordered commands in the same shell</td><td>The last one determines success</td></tr>
<tr><td><code>uses:</code></td><td>Call an action or repository</td><td>Pin third-party actions to a commit SHA</td></tr>
<tr><td><code>with:</code></td><td>Inputs to an action</td><td>Same idea as function arguments</td></tr>
<tr><td><code>env:</code></td><td>Environment variables</td><td>Use secrets, never literal values</td></tr>
<tr><td><code>secrets.X</code></td><td>A stored secret</td><td>Masked in logs, but still treat carefully</td></tr>
</table>

<p><strong>Memory trick:</strong> the workflow file is the pipeline <b>as code</b>.
Reviewing a change to it is reviewing a change to how you ship.</p>

<h3>Jobs, dependencies and matrices</h3>

<pre>jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python: ["3.11", "3.12", "3.13"]
        os: [ubuntu-latest, windows-latest]
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest -q

  deploy:
    needs: build          # waits for build to succeed
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh</pre>

<table>
<tr><th>Feature</th><th>What it does</th><th>Use when</th></tr>
<tr><td><code>needs</code></td><td>Makes one job wait for another</td><td>Stage ordering: build then deploy</td></tr>
<tr><td><code>if:</code></td><td>Runs the job only when true</td><td>Deploy only from main, or only on failure</td></tr>
<tr><td><code>strategy.matrix</code></td><td>Runs the same job many times in parallel</td><td>Test against many versions or operating systems</td></tr>
<tr><td><code>continue-on-error</code></td><td>Does not fail the job on error</td><td>Optional, non-blocking checks</td></tr>
<tr><td><code>timeout-minutes</code></td><td>Hard limit on a job</td><td>Stops hung builds wasting minutes</td></tr>
</table>

<h3>Useful gh CLI commands</h3>
<pre>gh workflow list
gh workflow run ci.yml
gh run list --limit 10
gh run view 1234567 --log-failed
gh run rerun 1234567 --failed
gh secret set API_KEY
act -l                # list workflow jobs locally
act -j test           # run one job locally with Docker</pre>

<p><strong>Memory trick:</strong> <code>act</code> runs a GitHub Actions workflow
on your own machine before you push. It is the fastest way to debug a pipeline.</p>

<h2>6. Jenkins - The Self-Hosted Automation Server</h2>

<p>Jenkins is a self-hosted automation server. It is older than GitHub Actions and
is still common in companies that need it on their own infrastructure. It is the
reference implementation for the idea of a pipeline.</p>

<table>
<tr><th>Term</th><th>Meaning</th></tr>
<tr><td>Controller</td><td>The Jenkins server itself, with the UI and webhooks on port 8080</td></tr>
<tr><td>Node or agent</td><td>A machine that actually runs the build steps</td></tr>
<tr><td>Job</td><td>A single automated task</td></tr>
<tr><td>Pipeline</td><td>A job whose steps are defined as code in a Jenkinsfile</td></tr>
<tr><td>Freestyle project</td><td>The old click-and-configure job type</td></tr>
<tr><td>Shared library</td><td>Reusable pipeline code stored in a Git repository</td></tr>
<tr><td>Plugin</td><td>Extends Jenkins for most integrations</td></tr>
</table>

<p><strong>Memory trick:</strong> the controller is the <b>manager</b>, agents are
the <b>workers</b>. Scale builds by adding agents, not controllers.</p>

<h3>Jenkinsfile, the declarative way</h3>

<pre>pipeline {
    agent any
    environment {
        IMAGE = 'myapp'
    }
    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Build') {
            steps { sh 'docker build -t $IMAGE .' }
        }
        stage('Test') {
            steps { sh 'docker run --rm $IMAGE pytest -q' }
        }
        stage('Deploy') {
            when { branch 'main' }
            steps { sh 'docker push $IMAGE:latest' }
        }
    }
    post {
        always  { echo 'Finished' }
        failure { mail to: 'team@example.com', subject: 'Build failed' }
    }
}</pre>

<table>
<tr><th>Block</th><th>Purpose</th></tr>
<tr><td><code>pipeline {}</code></td><td>Top level, required</td></tr>
<tr><td><code>agent</code></td><td>Where the build runs: any, none, docker, or a label</td></tr>
<tr><td><code>environment</code></td><td>Variables available to every stage</td></tr>
<tr><td><code>stages</code></td><td>The ordered steps, each visible in the UI</td></tr>
<tr><td><code>steps</code></td><td>The commands, such as sh or bat</td></tr>
<tr><td><code>when</code></td><td>Conditions such as branch or environment</td></tr>
<tr><td><code>post</code></td><td>always, success, failure, unstable, cleanup</td></tr>
<tr><td><code>sh</code> versus <code>bat</code></td><td>Shell command on Linux and Mac, or on Windows</td></tr>
</table>

<p><strong>Memory trick:</strong> Jenkins is <b>J</b>ava-based, runs on port
<b>8080</b>, and its agent inbound port is <b>50000</b>. Those three facts solve
most Jenkins networking problems.</p>

<h3>Running Jenkins locally</h3>
<pre>docker run -d --name jenkins -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home jenkins/jenkins:lts-jdk17
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
docker logs -f jenkins
docker restart jenkins</pre>

<h2>7. Terraform - Infrastructure as Code</h2>

<p>Terraform declares the infrastructure you want in HCL files, then works out
the API calls needed to reach it. It is not configuration management for machines;
it creates cloud resources.</p>

<h3>The four commands that matter</h3>

<table>
<tr><th>Command</th><th>What it does</th><th>Safe?</th></tr>
<tr><td><code>terraform init</code></td><td>Downloads providers, prepares the .terraform folder</td><td>Yes</td></tr>
<tr><td><code>terraform plan</code></td><td>Shows what would change, changing nothing</td><td>Yes, always read it</td></tr>
<tr><td><code>terraform apply</code></td><td>Makes reality match the plan</td><td>It creates and destroys real resources</td></tr>
<tr><td><code>terraform destroy</code></td><td>Removes everything the configuration manages</td><td>Extremely dangerous</td></tr>
</table>

<p><strong>Memory trick:</strong> plan is the rehearsal, apply is the
performance. Never run apply without reading plan first.</p>

<h3>State</h3>
<p>State is Terraform's memory of what exists. It is usually a single JSON file
and it is the most important thing to protect.</p>

<pre>terraform state list
terraform state show aws_instance.web
terraform state rm aws_instance.web
terraform state push backup.tfstate</pre>

<table>
<tr><th>Rule</th><th>Reason</th></tr>
<tr><td>Commit state to a locked remote backend</td><td>A lost state file means orphaned, unmanaged resources</td></tr>
<tr><td>Enable locking on the backend</td><td>Two engineers applying at once corrupts state</td></tr>
<tr><td>Never edit state by hand</td><td>Terraform will not expect it</td></tr>
<tr><td>Split state per environment</td><td>Staging state and production state must never merge</td></tr>
</table>

<h3>Workspaces</h3>
<p>Workspaces let one configuration manage several states: development, staging
and production from the same files.</p>

<pre>terraform workspace list
terraform workspace new staging
terraform workspace select staging
terraform workspace delete staging</pre>

<h2>8. Ansible - Configuration Management</h2>

<p>Ansible connects over SSH and makes machines match a description. There is no
agent to install, which is why it is called agentless. Where Terraform
<em>creates</em> resources, Ansible <em>configures</em> things that already
exist.</p>

<table>
<tr><th>Term</th><th>Meaning</th></tr>
<tr><td>Inventory</td><td>The list of machines and groups you manage</td></tr>
<tr><td>Playbook</td><td>A YAML file of plays, listing tasks to run against groups</td></tr>
<tr><td>Play</td><td>A group of hosts with a set of tasks</td></tr>
<tr><td>Task</td><td>One action using one module</td></tr>
<tr><td>Module</td><td>The unit of work: copy, apt, service, template, lineinfile</td></tr>
<tr><td>Role</td><td>A reusable directory of tasks, variables, handlers and templates</td></tr>
<tr><td>Collection</td><td>A package of roles, such as community.general</td></tr>
<tr><td>Handler</td><td>A task that runs only when notified, usually a service restart</td></tr>
</table>

<p><strong>Memory trick:</strong> <b>I</b>nventory says <b>where</b>,
playbook says <b>what</b>, module says <b>how</b>.</p>

<h3>Idempotency - the whole point</h3>
<p>Running a playbook twice must leave the system in the same state as running it
once. A playbook that installs a package when missing is idempotent; one that
appends a line to a config file every run is not, and will eventually break
something.</p>

<pre>ansible all -m ping
ansible webservers -m ping
ansible all -m setup | grep ansible_distribution</pre>

<h3>A simple playbook</h3>

<pre>- name: Configure web servers
  hosts: webservers
  become: true
  vars:
    http_port: 80
  tasks:
    - name: Update apt cache
      ansible.builtin.apt:
        update_cache: true
      tags: [always]

    - name: Install nginx
      ansible.builtin.apt:
        name: nginx
        state: present
      notify: Restart nginx
      tags: [install]

    - name: Ensure nginx is running
      ansible.builtin.service:
        name: nginx
        state: started
        enabled: true

  handlers:
    - name: Restart nginx
      ansible.builtin.service:
        name: nginx
        state: restarted</pre>

<table>
<tr><th>Keyword</th><th>Meaning</th></tr>
<tr><td><code>hosts</code></td><td>Which group from the inventory this play targets</td></tr>
<tr><td><code>become</code></td><td>Run with sudo</td></tr>
<tr><td><code>vars</code></td><td>Variables for this play</td></tr>
<tr><td><code>tasks</code></td><td>The ordered actions</td></tr>
<tr><td><code>notify</code></td><td>Trigger a handler when this task changes something</td></tr>
<tr><td><code>handlers</code></td><td>Runs once at the end, only if notified</td></tr>
<tr><td><code>tags</code></td><td>Run only some tasks with --tags</td></tr>
<tr><td><code>state: present</code></td><td>Ensure installed, without upgrading if already there</td></tr>
</table>

<h3>The commands worth memorising</h3>
<pre>ansible all -m ping
ansible-playbook site.yml --check --diff    # show what would change
ansible-playbook site.yml --syntax-check    # validate before running
ansible-playbook site.yml --limit webservers
ansible-playbook site.yml --tags deploy
ansible-playbook site.yml --start-at-task "Install nginx"
ansible-inventory --graph
ansible-vault create secrets.yml
ansible-galaxy collection install community.general</pre>

<p><strong>Memory trick:</strong> always run with <b>--check</b> first. It reports
what would change without changing anything, which is exactly what you want before
touching production.</p>

<h2>9. The Four Tools Side by Side</h2>

<table>
<tr><th>Tool</th><th>Purpose</th><th>Describes</th><th>Runs where</th><th>Idempotent</th></tr>
<tr><td>GitHub Actions</td><td>CI/CD pipeline</td><td>Steps to build, test, deploy</td><td>GitHub or self-hosted runners</td><td>Yes, if written well</td></tr>
<tr><td>Jenkins</td><td>CI/CD pipeline</td><td>A Jenkinsfile in the repo</td><td>Your own controller and agents</td><td>Yes, if written well</td></tr>
<tr><td>Terraform</td><td>Provision infrastructure</td><td>Cloud resources in HCL</td><td>Against the cloud API</td><td>Yes, by design</td></tr>
<tr><td>Ansible</td><td>Configure machines</td><td>Tasks and modules in YAML</td><td>Over SSH to existing hosts</td><td>Yes, by design</td></tr>
</table>

<p><strong>Memory trick:</strong> GitHub Actions and Jenkins move
<b>c</b>ode, Terraform creates <b>i</b>nfrastructure, Ansible configures
<b>m</b>achines.</p>

<h2>10. Try It Yourself (60 minutes)</h2>
<ul>
<li>Create a repository and add a GitHub Actions workflow with a build job, a
test job and a <code>needs</code> dependency between them.</li>
<li>Add a matrix so the test job runs on three Python versions.</li>
<li>Install the <code>gh</code> CLI, run <code>gh auth login</code> and
<code>gh workflow list</code>.</li>
<li>Run a Jenkins container in Docker, unlock it with the printed admin password,
and create a pipeline job using the Jenkinsfile above.</li>
<li>Install Terraform and run <code>init</code>, <code>validate</code> and
<code>plan</code> on the <code>main.tf</code> template in this app.</li>
<li>Install Ansible, write a playbook that creates a user and installs a package,
then run it with <code>--check</code> before running it for real.</li>
<li>Wire them together: have Terraform output the server IP, and feed it into the
Ansible inventory.</li>
</ul>

<h2>11. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Pipeline definition</td><td>One workflow file, edited freely</td><td>Reviewed, versioned, with required status checks</td></tr>
<tr><td>Runner</td><td>GitHub-hosted, ubuntu-latest</td><td>Pinned image, or self-hosted for network access</td></tr>
<tr><td>Deployments</td><td>Manual button press</td><td>Progressive rollout with automatic rollback</td></tr>
<tr><td>Secrets</td><td>Repository secrets</td><td>Environment-scoped, rotated, short-lived OIDC</td></tr>
<tr><td>Terraform state</td><td>Local terraform.tfstate</td><td>Remote, locked backend, per environment</td></tr>
<tr><td>Terraform apply</td><td>From your laptop</td><td>From the pipeline, after plan review</td></tr>
<tr><td>Ansible inventory</td><td>A few IPs in a text file</td><td>Dynamic inventory from the cloud provider</td></tr>
<tr><td>Ansible runs</td><td>Straight to production</td><td>Staging first, then a limited canary group</td></tr>
<tr><td>Jenkins</td><td>Latest image tag</td><td>Pinned version, patched, with a shared library</td></tr>
<tr><td>Failures</td><td>Fix it and push again</td><td>Alerted, with a runbook and a post-mortem</td></tr>
</table>

<h2>12. Key Takeaways</h2>
<ul>
<li>A pipeline replaces "it works on my machine" with reproducible verification.</li>
<li>Put the cheap, fast checks first, and fail early.</li>
<li>Recreate is risky, blue-green is backup, canary is a small test.</li>
<li>Pin third-party actions to a SHA and set token permissions explicitly.</li>
<li>Jenkins runs on 8080 with agents inbound on 50000.</li>
<li>Terraform plan is a rehearsal; state is the memory and must be locked and
remote.</li>
<li>Ansible is agentless and idempotent, so always run --check first.</li>
<li>Actions and Jenkins move code, Terraform creates infrastructure, Ansible
configures machines.</li>
</ul>
"""