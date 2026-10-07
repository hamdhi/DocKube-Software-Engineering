"""Documentation content and highlighting rules for the DocKube categories.

This module is pure data so that `app.py` stays focused on UI wiring.
Doc strings use a tiny convention understood by ``App.display_documentation``:

* ``Heading:``             -> rendered as a bold section heading
* ``- item``               -> rendered as a bullet
* ``    indented command`` -> rendered with the command colour
* anything else           -> rendered as body text
"""

# Prefixes that mark a line as a shell command for colouring purposes.
COMMAND_PREFIXES = (
    "kubectl ", "docker ", "minikube ", "kind ", "git ", "gh ", "helm ",
    "terraform ", "tofu ", "ansible", "jenkins", "mysql ", "psql ", "mongosh ",
    "mongo ", "npm ", "npx ", "yarn ", "make ", "curl ", "wget ", "python ",
    "pip ", "aws ", "gcloud ", "az ", "systemctl ", "service ", "netstat ",
    "tasklist ", "taskkill ", "echo ", "cd ", "ls ", "cat ", "mkdir ", "cp ",
    "rm ", "act ", "export ", "source ", "find ", "grep ",
)

MYSQL_DOC = """MySQL on Kubernetes

MySQL is a stateful, transactional database. In Kubernetes it must run as a
StatefulSet so each replica gets a stable identity and its own persistent
volume. A stateless Deployment would lose data every time a pod is rescheduled.

Key concepts:
- StatefulSet gives pods stable hostnames (mysql-0, mysql-1) tied to PVCs
- headless Service (clusterIP: None) provides per-pod DNS resolution
- PersistentVolumeClaim keeps data across pod restarts and rescheduling
- Secret stores the root password; never bake it into an image or a manifest
- mysqldump is the backup tool, mysql is the interactive client

Getting started:
1. Click 'Write MySQL Manifest' to drop a ready-to-apply YAML file into the
   working directory, then edit it in the built-in YAML editor.
2. Apply it, then check the pods with the Pods list button.
3. Use 'Exec Shell' to open the mysql client inside the container.
4. Port-forward to connect from your machine with any SQL GUI.

Key commands:
    kubectl apply -f mysql.yaml
    kubectl get statefulset mysql
    kubectl get pods -l app=mysql
    kubectl exec -it mysql-0 -- mysql -u root -p
    kubectl logs mysql-0 -f
    kubectl port-forward svc/mysql 3306:3306
    kubectl scale statefulset mysql --replicas=3
    kubectl delete statefulset mysql

Connect from your machine:
- Port-forward first, then use host 127.0.0.1 port 3306 in DBeaver or Navicat
- From another machine use the NodePort and the node IP

Important notes:
- mysqld is the server, mysql is the client - they are different binaries
- Deleting a StatefulSet leaves the PVCs behind; remove them explicitly with
  'Delete PVCs' when you really want the data gone
- Back up with mysqldump before any destructive operation"""
POSTGRES_DOC = """PostgreSQL on Kubernetes

Postgres follows the same pattern as MySQL - a StatefulSet, a headless Service
and persistent volumes. What differs is the tooling: the server is 'postgres',
the client is 'psql', and backups are taken with pg_dump and pg_dumpall.

Key concepts:
- Init containers or an init script create databases and roles on first boot
- PGDATA must live on the PVC, never on the container filesystem
- pg_dump is logical and portable, pg_basebackup is physical and faster
- Postgres listens on 5432 and uses the pg_hba.conf ruleset for auth
- Connection strings look like postgres://user:pass@host:5432/dbname

Getting started:
1. Click 'Write Postgres Manifest' to create a StatefulSet with a PVC.
2. Apply it and watch the pods come up.
3. Exec into the pod and run psql.
4. Port-forward to reach it from pgAdmin or DBeaver.

Key commands:
    kubectl apply -f postgres.yaml
    kubectl get statefulset postgres
    kubectl exec -it postgres-0 -- psql -U postgres
    kubectl port-forward svc/postgres 5432:5432
    kubectl logs postgres-0 -f
    kubectl scale statefulset postgres --replicas=2

Backup and restore:
    kubectl exec postgres-0 -- pg_dump -U postgres dbname > backup.sql
    kubectl cp postgres-0:/tmp/backup.sql ./backup.sql
    kubectl exec -i postgres-0 -- psql -U postgres dbname < backup.sql

Important notes:
- A single-writer database means one replica unless you add a replication
  tool such as Patroni or CloudNativePG
- Quote the database name when it contains upper case characters
- Never store the password in plain text; use a Secret and envFrom"""

MONGODB_DOC = """MongoDB on Kubernetes

MongoDB is a document database. It is usually deployed as a StatefulSet and
scaled with a replica set so reads can be distributed and failover is fast.
Unlike MySQL and Postgres, MongoDB has no schema and no fixed table layout.

Key concepts:
- Replica set = one primary and N secondaries; writes only hit the primary
- WiredTiger is the default storage engine with journaling
- mongosh is the modern shell; mongo was the legacy shell
- mongod is the server, mongos is the sharding router
- Connection strings look like mongodb://host:27017/?replicaSet=rs0

Getting started:
1. Click 'Write MongoDB Manifest' to create a single-node replica set.
2. Apply it and confirm the pod is Running.
3. Exec into the pod and open mongosh.
4. Port-forward 27017 for Compass or Atlas tooling.

Key commands:
    kubectl apply -f mongodb.yaml
    kubectl get statefulset mongodb
    kubectl exec -it mongodb-0 -- mongosh --quiet
    kubectl port-forward svc/mongodb 27017:27017
    kubectl logs mongodb-0 -f

Data operations inside mongosh:
    show dbs
    use mydatabase
    db.collectionName.find().pretty()
    db.collectionName.insertMany([{a:1},{a:2}])
    db.collectionName.createIndex({field:1})
    db.collectionName.dropIndexes()

Important notes:
- A single-node replica set is fine for development, never for production
- Authentication is off by default in the plain image - enable it before
  exposing the pod outside the cluster"""
CICD_DOC = """CI/CD and GitHub Actions

CI/CD is the pipeline that turns a commit into a running artifact. In a
Kubernetes context the pipeline builds an image, pushes it to a registry,
then applies it to a cluster and verifies the rollout.

Key concepts:
- Workflow lives at .github/workflows/<name>.yml and triggers on events
- steps run on a runner; each step is a shell command in a container
- Secrets are stored in GitHub and injected as environment variables
- needs defines job dependencies; jobs without it run in parallel
- act runs a workflow locally before you push it

Pipeline stages:
1. Lint and unit test on every pull request
2. Build the Docker image and tag it with the commit SHA
3. Push the image to a registry
4. Deploy to the cluster with kubectl apply or a Helm upgrade
5. Verify with kubectl rollout status and smoke tests

Key commands:
    gh workflow list
    gh workflow run deploy.yml --ref main
    gh run list --limit 10
    gh run view 123456789 --log-failed
    gh run rerun 123456789 --failed
    gh secret set DOCKER_PASSWORD
    act -l
    act -j build
    docker build -t myapp:1.0 .
    docker push myregistry/myapp:1.0
    kubectl apply -f k8s/deploy.yaml
    kubectl rollout status deployment/myapp
    kubectl rollout undo deployment/myapp

Important notes:
- Never put secrets in the workflow file - use secrets or environments
- Pin runner versions such as ubuntu-22.04 for reproducible builds
- A pipeline that cannot be re-run from a clean checkout is not a pipeline"""

GITHUB_DOC = """GitHub and Git

Git is a distributed version control system: every clone is a full repository
with history. GitHub is a hosted platform around it that adds pull requests,
issues, Actions and releases. The commands below cover the everyday workflow
plus the GitHub CLI.

Setup and configuration:
    git config --global user.name "Your Name"
    git config --global user.email "you@example.com"
    git config --global init.defaultBranch main
    git config --list --show-origin

Repository lifecycle:
    git init
    git clone https://github.com/user/repo.git
    git clone git@github.com:user/repo.git
    git remote -v
    git remote add origin https://github.com/user/repo.git
    git remote set-url origin https://github.com/user/repo.git
    git remote remove origin
    git remote prune origin

Everyday work:
    git status
    git status -sb
    git add .
    git add -p
    git commit -m "message"
    git commit -am "message"
    git commit --amend --no-edit
    git diff
    git diff --staged
    git restore file.txt
    git restore --staged file.txt
    git mv old.txt new.txt
    git rm file.txt
    git pull --rebase
    git push -u origin main

Branching:
    git branch
    git branch -a
    git branch -d feature
    git branch -D feature
    git switch -c feature
    git switch main
    git checkout -b hotfix
    git merge feature
    git rebase main
    git rebase --continue
    git rebase --abort

History and inspection:
    git log
    git log --oneline --graph --decorate --all
    git log -p file.txt
    git show abc1234
    git blame file.txt
    git shortlog -s
    git reflog
    git describe --tags
    git tag
    git tag -a v1.0 -m "release"
    git push --tags

Undo and recovery:
    git restore --staged .
    git reset --soft HEAD~1
    git reset --mixed HEAD~1
    git reset --hard HEAD~1
    git revert abc1234
    git cherry-pick abc1234
    git stash
    git stash push -m "wip"
    git stash list
    git stash pop
    git stash drop
    git clean -n
    git clean -fd

Advanced:
    git bisect start
    git bisect bad
    git bisect good abc1234
git bisect reset
    git worktree add ../hotfix hotfix
    git gc --prune=now
    git fsck

GitHub CLI:
    gh auth login
    gh auth status
    gh repo view
    gh repo create myrepo --private --push
    gh repo clone user/repo
    gh pr create --fill
    gh pr list
    gh pr checkout 42
    gh pr merge 42 --squash
    gh issue list
    gh issue create --title "bug" --body "details"
    gh release create v1.0 --generate-notes
    gh api /repos/user/repo
    gh browse

Important notes:
- git reset --hard and git clean -fd destroy uncommitted work irrecoverably
- Use git reflog to recover anything you reset away
- Never commit directly to main on a shared repository; use a feature branch"""

JENKINS_DOC = """Jenkins

Jenkins is a self-hosted automation server. It runs pipelines defined in a
Jenkinsfile, triggered by webhooks, timers or manual builds. Running it in
Docker is the fastest way to get a working controller locally.

Key concepts:
- Controller runs the UI, executor and agent orchestration on port 8080
- Agent (node) executes the actual build steps
- Jenkinsfile declares stages, each with steps that run shell commands
- The initial admin password is generated on first start
- Plugins extend everything: GitHub, Kubernetes, Docker Pipeline, Credentials

Getting started:
1. Click 'Start Jenkins Container' to launch a detached container.
2. Click 'Get Initial Admin Password' and paste it into the unlock screen.
3. Choose 'Install suggested plugins', then create your first job.
4. Click 'Open Jenkins UI' to reach http://localhost:8080

Key commands:
    docker run -d --name jenkins -p 8080:8080 -p 50000:50000 -v jenkins_home:/var/jenkins_home jenkins/jenkins:lts-jdk17
    docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
    docker logs -f jenkins
    docker restart jenkins
    docker stop jenkins
    docker rm jenkins
    docker exec -it jenkins bash
    docker inspect jenkins
    curl -s http://localhost:8080/api/json

Important notes:
- Mount a volume or you lose every job on container removal
- Port 50000 is the inbound agent port; keep it open for agents
- Pin the image tag rather than using 'latest'"""

TERRAFORM_DOC = """Terraform

Terraform manages infrastructure as code. You describe the desired state in
HCL files and Terraform works out the exact API calls needed to reach it,
recording everything it creates in state.

Key concepts:
- init downloads providers and prepares the .terraform directory
- plan shows what would change without changing anything
- apply executes the plan; destroy tears resources back down
- state is the memory of what exists - back it up and never edit by hand
- workspaces let you manage several states (dev, staging, prod) separately

Core workflow:
    terraform init
    terraform validate
    terraform plan
    terraform plan -out=tfplan
    terraform apply tfplan
    terraform destroy
    terraform fmt
    terraform fmt -recursive
    terraform show
    terraform providers
    terraform version

State management:
    terraform state list
    terraform state show aws_instance.web
    terraform state rm aws_instance.web
    terraform refresh
    terraform force-unlock LOCK_ID
    terraform workspace list
    terraform workspace new staging
    terraform workspace select staging

Importing and debugging:
    terraform import aws_instance.web i-0123456789
    terraform graph -type=plan
    terraform console
    terraform output
    terraform output -json
    terraform taint aws_instance.web
    terraform untaint aws_instance.web
    terraform apply -auto-approve
    terraform apply -target=aws_instance.web

Important notes:
- Commit the lock file .terraform.lock.hcl, ignore the .terraform directory
- Never run terraform apply without reviewing the plan first
- Keep state in a remote backend for any real team"""

ANSIBLE_DOC = """Ansible

Ansible is agentless configuration management. It connects over SSH, reads an
inventory of hosts, and applies playbooks that describe the desired state of
those machines. No agent to install, no daemon to maintain.

Key concepts:
- inventory lists the hosts and groups you manage
- playbook is a YAML file of plays, each with tasks and handlers
- module is the unit of work: copy, apt, service, template, lineinfile
- --check (or --dry-run) reports changes without applying them
- --diff shows the exact before/after for file modules
- handlers run once at the end of a play, triggered by notifications

Common commands:
    ansible all -m ping
    ansible webservers -m ping
    ansible-playbook site.yml
    ansible-playbook site.yml --check --diff
    ansible-playbook site.yml --syntax-check
    ansible-playbook site.yml --limit webservers
    ansible-playbook site.yml --tags deploy
    ansible all -m shell -a "uptime"
    ansible all -m command -a "df -h"
    ansible webservers -b -m apt -a "nginx"

Inventory and configuration:
    ansible-inventory --graph
    ansible-inventory --list
    ansible-inventory --host web1
    ansible -i production.ini all -m ping
    ansible-config dump
    ansible-config list
    ansible --version

Vault and collections:
    ansible-vault create secrets.yml
    ansible-vault edit secrets.yml
    ansible-vault decrypt secrets.yml
    ansible-galaxy collection install community.general
    ansible-galaxy role init myrole
    ansible-doc -l
    ansible-doc user.add

Important notes:
- Keep inventory in source control but secrets in ansible-vault
- Always run --syntax-check in CI before a real run
- Use --check --diff in pull requests to preview infrastructure changes"""

PORT_MANAGER_DOC = """Port Manager

Port Manager lists every TCP and UDP port currently in use on this PC, maps
each one to the owning process, and lets you terminate that process.

Key concepts:
- netstat -ano shows the connections plus the owning PID for each one
- tasklist resolves those PIDs into readable process names
- LISTENING means the process accepts inbound connections on that port
- taskkill /F force-kills a process; /T also kills its children
- PID 0 and PID 4 are kernel-owned and can never be terminated

Common ports you will recognise:
- 135 RPC, 445 SMB, 3389 RDP, 53 DNS, 8080 Jenkins, 5432 Postgres
- 3306 MySQL, 27017 MongoDB, 6379 Redis, 9090 many dashboards
- 6443 Kubernetes API server, 3000 Grafana

Key commands:
    netstat -ano
    netstat -ano | findstr LISTENING
    netstat -ano | findstr :8080
    netstat -ano -p TCP
    tasklist /FI "PID eq 1234"
    tasklist /FO CSV /NH
    taskkill /PID 1234 /F
    taskkill /PID 1234 /F /T
    taskkill /IM node.exe /F

How to use it:
1. Press Refresh to load the live table.
2. Filter by protocol or search a port number to narrow the list.
3. Select a row and press Kill Port.
4. Confirm the dialog; the table refreshes automatically afterwards.

Important notes:
- Killing a system service can trigger a reboot or lose unsaved work
- The Kill button blocks PID 0, PID 4 and core Windows services
- Admin rights are required to terminate protected processes"""

DOCKER_DOC = """Docker - the Complete CLI

Docker packages applications into lightweight containers. An image is a
read-only template of filesystem layers; a container is a running instance
of an image. This panel covers the whole CLI the way it is actually used.

Key concepts:
- Image is read-only, container adds a writable layer on top
- Build with docker build, run with docker run, clean with prune
- Bind mounts share host folders, named volumes persist data
- Networks isolate containers; user-defined networks give DNS names

Common commands:
    docker version
    docker info
    docker system df
    docker run -d --name web -p 8080:80 nginx:alpine
    docker ps -a
    docker logs -f web
    docker exec -it web sh
    docker build -t app:dev .
    docker build -t app:dev . && docker image prune -f
    docker compose up -d --build
    docker system prune

Starter files:
- Write Dockerfile for a multi-stage, non-root Python image
- Write docker-compose.yml for a web plus Postgres stack
- Write .dockerignore to keep the build context small

Important notes:
- Read docker system df before any prune
- docker volume prune DELETES DATA - confirm the volume first
- Never use latest in production; pin the tag"""

SECURITY_DOC = """Security Testing

Security testing finds the vulnerabilities before someone else does. Only
ever scan systems you own or have written permission to test.

Key concepts:
- Recon maps the target: DNS, ports, services, technology
- Scanning finds known vulnerabilities: Nikto, Nuclei, sqlmap
- SAST reads the code: Bandit, Semgrep, Gitleaks for secrets
- CI/CD gates fail the build when a check fails
- OWASP Top 10 is the starting vocabulary

Common commands:
    nmap -sV target
    nikto -h http://target
    nuclei -u http://target
    sqlmap -u http://target/page?id=1 --batch
    bandit -r src
    semgrep --config auto
    gitleaks detect
    bandit -r src && semgrep --config auto && gitleaks detect

Important notes:
- Unauthorised scanning is illegal in most jurisdictions
- Gate the build: SAST plus secret scanning on every pull request
- Start with the OWASP Top 10, then read the Security Testing chapter"""

DATABASES_DOC = """Database Administration

Designing and querying a database properly is most of what separates a
working application from a fast one. This panel administers a database you
already have a client for - distinct from the MySQL, Postgres and MongoDB
categories, which deploy each engine on Kubernetes.

Key concepts:
- psql is the Postgres client, mysql the MySQL client, mongosh the Mongo one
- pg_dump and mysqldump take logical backups; restore with psql or mysql
- EXPLAIN shows the query plan before the query hurts production
- Indexes speed reads and slow writes; unused ones are pure cost

Common commands:
    psql -U postgres -c '\\l'
    mysql -u root -p -e 'SHOW DATABASES;'
    mongosh --eval 'db.adminCommand({listDatabases:1})'
    pg_dump -d mydb > dump.sql
    mysqldump mydb > dump.sql

Important notes:
- Back up with a dump before any destructive operation
- Deleting a StatefulSet leaves the PVCs behind by design
- Parameterise every query; never interpolate input into raw SQL"""

WINDOWS_DIAG_DOC = """Windows Diagnostics

The classic toolkit for working out why a Windows machine is misbehaving.
Every command here runs in the shared prompt below; the ones that need an
argument take it from the box above the buttons.

Key concepts:
- systeminfo and msinfo32 are the one-shot summary when you know nothing yet
- wmic is the legacy query language; PowerShell cmdlets are its replacement
- ipconfig /all plus ping of the gateway isolates network faults in two steps
- netstat -ano ties a listening port to the PID owning it
- wevtutil reads event logs from the command line; eventvwr does it graphically
- sfc repairs system files, DISM repairs the image sfc repairs from

Common commands:
    systeminfo | findstr /C:\"Boot Time\"
    ipconfig /all
    netstat -ano | findstr LISTENING
    wevtutil qe System /c:20 /rd:true /f:text
    sfc /scannow
    DISM /Online /Cleanup-Image /RestoreHealth

Important notes:
- Run sfc, DISM and chkdsk from an elevated prompt or they refuse to work
- chkdsk /f on C: schedules the scan for the next reboot
- The Diagnostics chapter walks the triage order these commands fit into"""

EXTRA_DOCS = {
    "Docker": DOCKER_DOC,
    "MySQL": MYSQL_DOC,
    "Postgres": POSTGRES_DOC,
    "MongoDB": MONGODB_DOC,
    "CI/CD & GitHub Actions": CICD_DOC,
    "GitHub": GITHUB_DOC,
    "Jenkins": JENKINS_DOC,
    "Terraform": TERRAFORM_DOC,
    "Ansible": ANSIBLE_DOC,
    "Port Manager": PORT_MANAGER_DOC,
    "Security Testing": SECURITY_DOC,
    "Databases": DATABASES_DOC,
    "Windows Diagnostics": WINDOWS_DIAG_DOC,
}