r"""Chapter 43 - Docker: the complete command reference, from run to swarm."""

CHAPTER = r"""<h2>1. The Mental Model</h2>

<pre>Registry (Docker Hub, GHCR, ECR)   store of IMAGES
   image  = immutable template: OS libs + app + config, layered
   container = RUNNING instance of an image (writable layer on top)
   Dockerfile = build instructions for an image
   volume = data that outlives the container
   network = private bridge so containers can find each other

   Dockerfile --docker build--&gt; IMAGE --docker run--&gt; CONTAINER
                                      ^                  |
                                      +--docker commit---+  (discouraged)
</pre>

<table>
<tr><th>Concept</th><th>Rule of thumb</th></tr>
<tr><td>Layers</td><td>Each instruction = one cached layer; order matters - put rarely changing steps (deps) before frequently changing (source)</td></tr>
<tr><td>Container</td><td>One concern per container; stateless by default; stoppable and replaceable</td></tr>
<tr><td>Image tag vs digest</td><td>Tags move (latest lies); pin :sha256-... in production</td></tr>
<tr><td>Writable layer</td><td>Everything written to the container rootfs dies with it - use volumes</td></tr>
</table>

<h2>2. Daemon, Contexts And Info</h2>

<pre>docker version                      # client + server versions
 docker info                        # storage driver, runtime, registry mirrors, containers
 docker context ls                  # local vs remote daemons
docker context use remote-prod      # point the CLI at another daemon
docker system df                    # space used by images, containers, volumes
 docker system df -v                # per-image layer breakdown + who uses what
 DOCKER_BUILDKIT=1 docker build .   # BuildKit (default since 23.x)
docker context inspect
systemctl status docker             # Linux daemon
Get-Service docker                  # Windows
journalctl -u docker -e            # daemon log
</pre>

<h2>3. Running Containers - The run Flag Encyclopedia</h2>

<pre># The flags you will use every day
docker run -d --name web -p 8080:80 --restart unless-stopped nginx:1.27
           ^   ^        ^        ^          ^
     detached  name  host:container  restart policy

# Full catalogue
docker run -it --rm ubuntu:24.04 bash        # interactive shell, delete on exit
docker run -d -e API_KEY=abc -e MODE=prod myapp            # environment vars
docker run -d --env-file .env myapp                        # env from file
docker run -d -v /host/data:/var/data myapp                # bind mount
docker run -d -v dbdata:/var/lib/postgresql/data postgres   # named volume
docker run -d --mount type=bind,src=/h,dst=/r,readonly myapp
docker run --network app-net --add-host db:10.0.0.5 myapp  # custom DNS entry
docker run -d --memory 512m --cpus 1.5 myapp               # hard limits
docker run -d --read-only --tmpfs /tmp myapp               # immutable rootfs
docker run --user 1000:1000 myapp                          # non-root
docker run -d --health-cmd "curl -f localhost/" --health-interval 30s myapp
docker run -d --log-driver json-file --log-opt max-size=10m --log-opt max-file=3 myapp
docker run -p 127.0.0.1:5432:5432 postgres                  # localhost only
docker run -d --pull always myapp                          # never trust local tag

# Lifecycle (equivalents in order)
docker create --name x myapp        # allocated, not started
docker start x | stop x | restart x
 docker pause x / unpause x         # freeze the cgroup (SIGSTOP)
docker kill x                       # SIGKILL
 docker rm x                         # remove stopped container
 docker rm -f x                      # force remove
 docker rename old new
docker wait x                       # block until it exits (exit code)
docker update --memory 1g x         # resize a running container
</pre>

<h2>4. Inspecting And Debugging Running Containers</h2>

<pre>docker ps                 # running;  docker ps -a  # all (incl. exited)
docker ps -q --filter status=exited            # just the dead ones
docker ps --filter name=web --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

docker logs -f --tail 100 --since 10m web      # follow with context
 docker logs -f --timestamps web 2&gt;&amp;1 | grep -i error

docker exec -it web sh                        # shell (sh exists everywhere)
docker exec -it web bash                      # bash if the image has it
docker exec -u root web id                    # who am I, which uid
docker exec web env                           # environment actually set
docker exec web cat /etc/resolv.conf          # DNS the container sees

 docker inspect web                           # everything: IPs, mounts, env, health
 docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' web
docker inspect -f '{{json .State.Health}}' web | python -m json.tool
 docker top web                               # host processes inside it
docker stats                                  # live CPU/mem/net (all containers)
 docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

docker diff web                               # what changed in the filesystem
 docker port web                              # port mappings
docker cp web:/var/log/app.log ./local.log    # copy out
 docker cp ./fixture.json web:/tmp/           # copy in
 docker export web -o snapshot.tar            # filesystem snapshot (no history)
</pre>

<table>
<tr><th>Field</th><th>Where it lives</th></tr>
<tr><td>Entrypoint / Cmd</td><td>docker inspect web -&gt; Config.Entrypoint / Config.Cmd</td></tr>
<tr><td>Exit code</td><td>State.ExitCode - the number your restart loop is hiding</td></tr>
<tr><td>Health</td><td>State.Health.Status: starting / healthy / unhealthy</td></tr>
<tr><td>Mounts</td><td>Mounts[] - Source, Destination, RW</td></tr>
<tr><td>Logs driver</td><td>HostConfig.LogConfig</td></tr>
</table>
<h2>5. Building Images</h2>

<pre>docker build -t myapp:1.0 .                    # from Dockerfile in cwd
docker build --no-cache -t myapp:1.0 .         # ignore cache (flaky builds)
docker build --pull -t myapp:1.0 .             # fresh base image
docker build -f Dockerfile.prod -t myapp:prod .
docker build --target dev -t myapp:dev .       # multi-stage: stop at a stage
docker build --build-arg VERSION=1.2 -t myapp .
docker build -t myapp . &amp;&amp; docker image prune -f  # remove dangling after build

# BuildKit extras (faster, more powerful)
docker buildx build --platform linux/amd64,linux/arm64 -t myapp:1.0 --push .
docker buildx ls                              # builders and their platforms
docker buildx build --push --cache-from type=gha --cache-to type=gha,mode=max .
# Cache mounts survive across builds (huge for apt/pip):
#   RUN --mount=type=cache,target=/var/cache/apt apt-get install -y build-essential

# The Dockerfile that production deserves
FROM python:3.12-slim AS build
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

FROM python:3.12-slim
RUN useradd -r appuser
WORKDIR /srv
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /app .
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
</pre>

<table>
<tr><th>Instruction</th><th>Purpose</th><th>Tip</th></tr>
<tr><td>FROM</td><td>Base image</td><td>Pin minor version, prefer slim/distroless</td></tr>
<tr><td>COPY / ADD</td><td>Files in (ADD also handles URLs/tar - prefer COPY)</td><td>COPY requirements first for cache</td></tr>
<tr><td>RUN</td><td>Execute at build</td><td>Combine with &amp;&amp;, clean apt lists in the same layer</td></tr>
<tr><td>ENV / ARG</td><td>ENV baked into image, ARG build-only</td><td>Never ARG a secret - it leaks into layers</td></tr>
<tr><td>EXPOSE</td><td>Documentation only</td><td>-p still required at run time</td></tr>
<tr><td>CMD / ENTRYPOINT</td><td>CMD = default args (overridable), ENTRYPOINT = the executable</td><td>ENTRYPOINT ["app"] + CMD ["--port","80"] is the combo</td></tr>
<tr><td>WORKDIR</td><td>cd for everything after</td><td>Absolute path; never cd in a RUN then forget</td></tr>
<tr><td>USER</td><td>Run as non-root</td><td>Security baseline - always set it</td></tr>
<tr><td>VOLUME</td><td>Declare a mount point</td><td>Anonymous volumes leak - name them</td></tr>
<tr><td>HEALTHCHECK</td><td>Container health probe</td><td>Docker restarts nothing; orchestration acts on it</td></tr>
<tr><td>.dockerignore</td><td>Exclude .git, venv, node_modules, secrets from context</td><td>Cuts build time and accidental secret leaks</td></tr>
</table>

<pre>docker history myapp:1.0                       # layer sizes - find the bloat
docker image inspect myapp:1.0 --format '{{json .Config.Env}}'
docker image save myapp:1.0 -o myapp.tar       # offline transfer
docker image load -i myapp.tar
docker image tag myapp:1.0 registry.example.com/team/myapp:1.0
docker image rm myapp:1.0                      # fails if a container uses it
docker image prune                             # dangling images only
docker image prune -a                          # EVERY unused image (careful)
docker search nginx                            # hub search (rarely useful)
docker pull nginx@sha256:ab...                 # digest-pinned pull
</pre>

<h2>6. Networks</h2>

<pre>docker network ls
docker network create app-net                  # bridge (the default kind)
docker network create --driver bridge --subnet 10.10.0.0/24 --gateway 10.10.0.1 net1
docker network inspect app-net                 # containers + IPs + options

docker run -d --name api --network app-net myapi
docker run -d --name db  --network app-net postgres
docker network connect app-net legacy          # attach a running container
docker network disconnect app-net legacy
docker network rm app-net &amp;&amp; docker network prune -f

# Containers on the same user-defined network resolve each other BY NAME:
psql -h db -U app        # "db" is the container name - built-in DNS
</pre>

<table>
<tr><th>Driver</th><th>Scope</th><th>Use for</th></tr>
<tr><td>bridge (default)</td><td>Host</td><td>Containers on one host talking by name</td></tr>
<tr><td>host</td><td>Host</td><td>No isolation - max performance, no port mapping</td></tr>
<tr><td>none</td><td>-</td><td>Air-gapped jobs</td></tr>
<tr><td>overlay</td><td>Cluster</td><td>Swarm services across hosts</td></tr>
<tr><td>macvlan</td><td>Host</td><td>Container gets its own MAC on the physical LAN</td></tr>
<tr><td>custom (CNI/Calico)</td><td>Cluster</td><td>Kubernetes - Docker\'s network is bypassed there</td></tr>
</table>

<p><strong>Memory trick:</strong> the default bridge does NOT do name
resolution - user-defined networks do. If "cannot connect to mysql", first
question: same user-defined network?</p>

<h2>7. Volumes And Data</h2>

<pre>docker volume ls
docker volume create --driver local --opt type=nfs --opt o=addr=10.0.0.5 --opt device=/shares/data nfs-data
docker run -d -v pgdata:/var/lib/postgresql/data --name db postgres
docker volume inspect pgdata                    # find the real host path
 docker volume rm pgdata                        # fails while in use
 docker volume prune -f                         # ALL unused volumes - data loss if wrong

# Back up a volume the right way (stop writer first, or use pg_dump)
docker run --rm -v pgdata:/data -v $(pwd):/backup alpine \
  tar czf /backup/pgdata-$(date +%F).tar.gz -C /data .

# Bind mount vs named volume
bind mount:  -v /host/path:/container/path     host path, absolute, host FS semantics
named volume: -v name:/container/path          Docker-managed, portable, backup-able
read-only:    -v name:/path:ro
</pre>
<h2>8. Registries, Login And Distribution</h2>

<pre>docker login                                  # Docker Hub (or docker login ghcr.io)
docker login registry.example.com -u ci --password-stdin   # CI: never on the argv
docker logout --all
docker pull nginx:1.27
 docker push registry.example.com/team/app:1.27
docker search --limit 10 flask
docker tag app:1.27 myname/app:latest          # retag before push
 docker manifest inspect nginx:1.27            # what platforms does it have?

# Version discipline:
#   :1.27        immutable release tag
#   :1.27-alpine variant
#   :latest       convenience ONLY on your laptop
#   @sha256:...  what production deploys

# Private registry in a pinch:
docker run -d -p 5000:5000 --name registry -v regdata:/var/lib/registry registry:2
docker tag app:1.0 localhost:5000/app:1.0 &amp;&amp; docker push localhost:5000/app:1.0
</pre>

<h2>9. Docker Compose - Multi-Container In One File</h2>

<pre>docker compose up -d                           # create + start detached
docker compose up -d --build                   # rebuild changed images first
docker compose up -d --force-recreate          # recreate from scratch
docker compose ps                              # status of this project
docker compose logs -f --tail 100 api          # follow one service
docker compose exec db psql -U app             # shell/command in a service
docker compose run --rm web pytest             # one-off task (no deps sharing)
docker compose restart api
 docker compose stop web / start web
 docker compose pause api / unpause api
docker compose pull &amp;&amp; docker compose build --no-cache
docker compose config                          # rendered, validated YAML (secrets resolved)
docker compose top                             # processes per service
docker compose down                            # stop + remove containers + network
docker compose down -v                         # ALSO deletes volumes - DATA LOSS
docker compose down --rmi all --volumes         # nuclear cleanup
docker compose -f base.yml -f prod.yml up -d   # layered files
COMPOSE_PROJECT_NAME=shop docker compose up -d # isolate parallel copies
</pre>

<pre># docker-compose.yml reference (Compose specification)
services:
  web:
    build: .                          # or image: ghcr.io/me/web:1.0
    ports: ["8080:80"]
    environment: {NODE_ENV: production}
    env_file: [.env]
    depends_on:                       # startup ORDER + health gating
      db: {condition: service_healthy}
    volumes: ["./src:/app:ro"]
    networks: [frontend]
    deploy:                           # swarm/stack semantics
      replicas: 2
      resources: {limits: {cpus: "0.50", memory: 512M}}
      restart_policy: {condition: on-failure}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      retries: 3
    restart: unless-stopped

  db:
    image: postgres:16
    volumes: [pgdata:/var/lib/postgresql/data]
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD:?set DB_PASSWORD}   # fail fast if unset

volumes:
  pgdata:
networks:
  frontend:
</pre>

<table>
<tr><th>Gotcha</th><th>Fix</th></tr>
<tr><td>depends_on does not wait for readiness</td><td>condition: service_healthy + a healthcheck</td></tr>
<tr><td>Secrets in environment</td><td>Compose secrets / env_file outside git; never in the image</td></tr>
<tr><td>Stale images after branch switch</td><td>compose up -d --build, or --pull always</td></tr>
<tr><td>Two checkouts collide on ports</td><td>COMPOSE_PROJECT_NAME or different host ports</td></tr>
</table>

<h2>10. Swarm - Built-In Orchestration</h2>

<pre>docker swarm init                               # manager token printed
docker swarm join --token SWARM-WORKER ...      # run on workers
docker node ls                                  # membership and status

docker service create --name web --replicas 3 --publish 80:80 myapp:1.0
docker service ls / docker service ps web
 docker service scale web=5
docker service update --image myapp:1.1 web     # rolling update
docker service logs web
docker stack deploy -c compose.yml shop         # compose-driven swarm
docker stack ls / services / docker stack rm shop

# Swarm vs Kubernetes: Swarm is batteries-included and simple; Kubernetes
# won the ecosystem (operators, autoscalers, ecosystem). Learn Swarm to
# understand the concepts cheaply, invest in Kubernetes for production.
</pre>

<h2>11. System And Cleanup</h2>

<pre>docker system df
 docker system df -v
 docker system events --since 10m               # live daemon activity stream
docker system prune                             # stopped containers + dangling images + unused networks
docker system prune -a --volumes                # EVERYTHING unused - read df first!
docker container prune -f                       # stopped containers only
docker image prune -a -f                        # all unused images
docker network prune -f                         # unused networks
 docker volume prune -f                          # unused volumes (DATA)
docker builder prune -a -f                      # build cache (speeds vs space)
docker trust inspect myapp:1.0                  # content trust signatures
</pre>

<p><strong>Memory trick:</strong> cleanup order of safety: container prune
-&gt; image prune -f -&gt; builder prune -&gt; network prune -&gt; volume prune LAST
and never with -a on a host you do not know. <code>system df -v</code>
before ANY prune.</p>

<h2>12. Security Hardening</h2>

<pre>Never:            Run as root. Bake secrets into images. Expose the docker
                  socket (/var/run/docker.sock) to app containers. Use :latest.
Always:           USER in Dockerfile. --read-only where possible. Resource
                  limits. Signed images (cosign), scanned (trivy). Private
                  registry + pull secrets. seccomp/apparmor defaults. Drop
                  capabilities: --cap-drop ALL --cap-add NET_BIND_SERVICE.

scan as early as CI:    trivy image myapp:1.0
secrets at runtime:     docker secret create db_pass ./pass.txt  (swarm)
                        or --env-file from a mounted secret file (compose)
daemon config:          limit exposure: hosts = [unix:///var/run/docker.sock]
lock the socket:        restrict to root group; never -v /var/run/docker.sock:/var/run/docker.sock in an app
</pre>

<h2>13. Troubleshooting Cookbook</h2>

<table>
<tr><th>Symptom</th><th>Check</th><th>Usual cause</th></tr>
<tr><td>Container exits immediately</td><td>docker logs x; docker inspect -f \u0027{{.State.ExitCode}}\u0027 x</td><td>App crash, wrong CMD, missing env</td></tr>
<tr><td>Restart loop</td><td>logs + exit code; healthcheck output</td><td>Missing dependency (db not ready), bad config</td></tr>
<tr><td>Port already allocated</td><td>docker ps -a + netstat -ano / ss -tulpn</td><td>Old container still bound; host process on the port</td></tr>
<tr><td>Cannot reach service by name</td><td>docker network inspect; docker exec x getent hosts db</td><td>Different networks, or default bridge (no DNS)</td></tr>
<tr><td>Permission denied writing volume</td><td>docker exec x id; ls -l on host path</td><td>UID mismatch - match user in Dockerfile to host owner</td></tr>
<tr><td>Disk full</td><td>docker system df -v</td><td>Log driver never rotated; build cache; dangling images</td></tr>
<tr><td>Build picks stale code</td><td>docker history; .dockerignore</td><td>COPY . . cached, or .git/venv in context</td></tr>
<tr><td>Slow I/O</td><td>bind mount vs named volume; docker stats</td><td>Windows/macOS bind mounts across OS boundary</td></tr>
<tr><td>Daemon will not start</td><td>journalctl -u docker -e</td><td>Corrupt json daemon config, storage driver clash, full disk</td></tr>
</table>

<h2>14. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Images</td><td>latest on Docker Hub</td><td>Pinned tags + digests, signed, scanned in CI</td></tr>
<tr><td>Compose</td><td>One file on a laptop</td><td>Compose files in git; real deployments on orchestrators</td></tr>
<tr><td>State</td><td>Anonymous volumes</td><td>External managed databases; volumes backed up and restore-tested</td></tr>
<tr><td>Networks</td><td>Default bridge, -p everywhere</td><td>User-defined networks, internal-only where possible, mesh/ingress in front</td></tr>
<tr><td>Cleanup</td><td>docker system prune -a blindly</td><td>Log rotation policies, registry GC, disk alerts on the daemon</td></tr>
<tr><td>Root</td><td>Everything as root</td><td>Non-root USER, read-only rootfs, dropped caps, no docker.sock</td></tr>
</table>

<h2>15. Key Takeaways</h2>
<ul>
<li>Image = layered recipe, container = running meal; volumes carry data,
networks carry names.</li>
<li>Order Dockerfile steps for cache: deps before source, and multi-stage
keeps the final image slim.</li>
<li>User-defined networks give built-in DNS - containers connect by
name.</li>
<li>Compose: depends_on needs service_healthy; down -v deletes data;
config validates your YAML.</li>
<li>Prune in safety order and always read system df -v first.</li>
<li>Non-root, pinned digests, scanned and signed images are the production
baseline.</li>
</ul>

<p><strong>Exercise:</strong> dockerize a small app you own: multi-stage
Dockerfile, non-root user, healthcheck, named volume for its data, two
services in compose with a health-gated depends_on - then break each piece
on purpose and fix it with the cookbook.</p>
"""