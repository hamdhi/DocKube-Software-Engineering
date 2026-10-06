r"""Chapter 36 - Linux sysadmin deep dive: systemd, storage, networking, logs and automation."""

CHAPTER = r"""<h2>1. systemd - The Init System Everything Hangs Off</h2>

<pre># Unit lifecycle
systemctl status nginx
systemctl start|stop|restart|reload nginx
systemctl enable --now nginx          # start now AND at boot
systemctl disable nginx
systemctl daemon-reload               # after editing any unit file
systemctl list-units --failed         # THE health check
systemctl list-unit-files --state=enabled

# Journal and logs
journalctl -u nginx -f                # follow one unit
journalctl -b -p err                  # this boot, errors only
journalctl --since "1 hour ago" --until now
journalctl -u nginx --since "2026-01-01" --no-pager -o json-pretty   # machine-readable
journalctl --disk-usage                # how big the log store got

# Write your own service
# /etc/systemd/system/backup.service
[Unit]
Description=Nightly backup
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=backup
ExecStart=/usr/local/bin/backup.sh
Nice=10

[Install]
WantedBy=multi-user.target

# Matching timer (systemd's cron replacement - see the logs in journalctl)
# /etc/systemd/system/backup.timer
[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

systemctl enable --now backup.timer
timerlist=$(systemctl list-timers --all)   # what is scheduled and when
</pre>

<table>
<tr><th>Task</th><th>cron</th><th>systemd timer</th></tr>
<tr><td>Define</td><td>/etc/crontab, /etc/cron.d, crontab -e</td><td>.timer unit</td></tr>
<tr><td>See the schedule</td><td>crontab -l (per user only)</td><td>systemctl list-timers</td></tr>
<tr><td>Logs</td><td>MAILTO / syslog, easy to lose</td><td>journalctl -u backup.service</td></tr>
<tr><td>Missed runs</td><td>Skipped if machine was off</td><td>Persistent=true catches up</td></tr>
<tr><td>Dependencies</td><td>None - chain with &amp;&amp;</td><td>After=/Wants= honoured</td></tr>
</table>

<h2>2. Users, Groups, sudoers And Permissions</h2>

<pre># Accounts
useradd -m -s /bin/bash -G docker,sysops alice
gpasswd -a alice sudo
passwd -l root                      # lock root password login (SSH keys remain)
chage -l alice                      # password ageing: expires, last change, warn
getent passwd alice                 # LDAP/SSSD-aware lookup
id alice &amp;&amp; groups alice

# sudoers - NEVER edit with vi directly in a hurry; use visudo (syntax-checks)
# visudo -f /etc/sudoers.d/sysops
sysops ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx
# Syntax errors in sudoers can lock you out of sudo entirely.

# Permissions in the real world
chmod 640 app.conf                  # rw-r----- owner+group only
chmod 750 /srv/app                  # rwxr-x--- executable dir for the team
chown -R app:app /srv/app
setfacl -m u:alice:rX /srv/app      # per-user ACL without changing groups
umask 027                           # new files: group read, nothing for others

# Special bits (know these for exams and audits)
setuid 4755 /usr/bin/passwd          # run as file owner (root)
setgid 2755 /srv/shared              # new files inherit the directory group
sticky bit 1777 /tmp                 # only the owner can delete their files
find / -perm -4000 -type f 2&gt;/dev/null   # audit setuid files weekly
</pre>

<p><strong>Memory trick:</strong> r=4 w=2 x=1; add the three digits per
position (owner group other). 750 = rwx for owner, r-x for group, nothing
for others. When access breaks, check order: permissions, ownership, ACL,
then SELinux.</p>

<h2>3. Packages And Repositories</h2>

<pre># Debian / Ubuntu (apt)
apt update                          # refresh indexes - NOT an upgrade
apt upgrade -y &amp;&amp; apt autoremove -y
apt install -y nginx
apt list --upgradable
apt search &lt;term&gt; &amp;&amp; apt show nginx
dpkg -l | grep nginx                # low-level installed list
apt-mark hold nginx                 # freeze a version during an incident

# RHEL / Rocky / Fedora (dnf / yum)
dnf install -y nginx
dnf update &amp;&amp; dnf repolist
dnf info nginx &amp;&amp; dnf history        # undo a bad transaction: dnf history undo ID

# Both: where did this file come from?
dpkg -S /usr/sbin/nginx || rpm -qf /usr/sbin/nginx
</pre>

<h2>4. Storage - Filesystems, LVM And fstab</h2>

<pre># Inspect
lsblk -f                            # devices, filesystems, UUIDs, mountpoints
df -hT                              # space by filesystem (add -i for inodes!)
blkid /dev/sdb1
findmnt                             # the real mount table

# Partition + filesystem (non-destructive order)
parted /dev/sdb mklabel gpt mkpart primary ext4 0% 100%
mkfs.ext4 -L data /dev/sdb1

# LVM - growable storage
pvcreate /dev/sdb1                  # physical volume
vgcreate vg0 /dev/sdb1              # volume group
lvcreate -L 20G -n lv_data vg0      # logical volume
mkfs.ext4 /dev/vg0/lv_data
mount /dev/vg0/lv_data /srv/data

# Grow a live filesystem:
lvextend -L +10G /dev/vg0/lv_data
resize2fs /dev/vg0/lv_data          # ext4, online is fine

# fstab - mount at boot, by UUID (never by /dev/sdb1, names move)
# UUID=abcd-1234  /srv/data  ext4  defaults,noatime  0  2
systemctl daemon-reload &amp;&amp; mount -a   # test fstab BEFORE rebooting
findmnt --verify

# Swap
fallocate -l 4G /swapfile &amp;&amp; chmod 600 /swapfile
mkswap /swapfile &amp;&amp; swapon /swapfile
echo '/swapfile none swap sw 0 0' &gt;&gt; /etc/fstab
</pre>

<p><strong>Memory trick:</strong> a server "suddenly" full is almost always
inodes (<code>df -i</code>) or logs, not blocks. Check both in the first
minute of any disk incident.</p>
<h2>5. Networking - nmcli, ip And ss</h2>

<pre># The ip suite replaced ifconfig/route/netstat (still found in old docs)
ip addr show &amp;&amp; ip -br a              # addresses, brief
ip route show &amp;&amp; ip rule
ip link set eth0 up &amp;&amp; ip addr add 10.0.5.20/24 dev eth0
ip neigh                             # ARP/ND cache

ss -tulpn                           # listening sockets + owning process (replaces netstat)
ss -s                               # socket summary

# Connection debugging in order:
ping -c3 10.0.5.1                   # L3 reachability
ip route get 1.1.1.1                # which source/exit will be used
curl -v --connect-timeout 5 https://example.com   # DNS + TCP + TLS in one
journalctl -u NetworkManager --since -10min
nmcli device status                 # is the device even managed?

# NetworkManager on servers/desktops (RHEL family, Ubuntu Desktop)
nmcli con show
nmcli con mod "eth0" ipv4.addresses 10.0.5.20/24 ipv4.gateway 10.0.5.1 \
              ipv4.dns 1.1.1.1 ipv4.method manual
nmcli con up "eth0"

# Persistent firewall (nftables is the engine; ufw/firewalld the front-ends)
nft list ruleset
ufw allow 22/tcp &amp;&amp; ufw enable &amp;&amp; ufw status verbose   # Ubuntu
firewall-cmd --permanent --add-service=ssh &amp;&amp; firewall-cmd --reload   # RHEL
# NEVER enable a firewall remotely without allowing your access port first.
</pre>

<h2>6. Processes And Performance</h2>

<pre>top -o %CPU                         # or htop (friendlier)
ps aux --sort=-%mem | head          # memory ranking
ps -eo pid,ppid,%cpu,%mem,etime,cmd --sort=-%cpu | head
kill -15 PID &amp;&amp; sleep 10 || kill -9 PID    # graceful, then force
pkill -u nobody -f "old-worker"     # by user + full command line

# Why is it slow? Five commands, in order:
uptime                              # load average vs cores: load 4 on 4 cores = saturated
vmstat 1 5                          # us/sy/id, wa (iowait), run queue
iostat -xz 1 5                      # %util and await per disk
df -h &amp;&amp; df -i                      # space and inodes
ss -tulpn                           # something listening where it should not

# Deeper
pidstat -u 1 3                      # per-process CPU
strace -p PID -c                   # syscalls summary (finds stuck I/O)
lsof -i :8080                       # who owns the port
cat /proc/PID/limits &amp;&amp; cat /proc/meminfo | head
timeout 5 strace -p PID             # attach when you suspect a hang

# cgroup view on modern systems
cat /sys/fs/cgroup/system.slice/nginx.service/memory.current
</pre>

<h2>7. SSH Hardening And Remote Admin</h2>

<pre># /etc/ssh/sshd_config - the six lines that matter
PermitRootLogin no
PasswordAuthentication no           # keys only
AllowGroups sysops
Port 2222                            # move off 22 to cut scanner noise
ClientAliveInterval 300 &amp;&amp; ClientAliveCountMax 2   # drop dead sessions
MaxAuthTries 3

# Then:
sshd -t                              # CONFIG SYNTAX CHECK before reload
systemctl reload sshd

# Keys
ssh-keygen -t ed25519 -C "laptop-$(date +%Y)"
ssh-copy-id -i ~/.ssh/id_ed25519.pub alice@server
ssh -J bastion.corp internal-box     # jump through a bastion in one command
# ~/.ssh/config: Host internal-box -&gt; User alice, ProxyJump bastion

# Automation
ssh alice@server 'systemctl is-active nginx'
rsync -avz --delete /srv/data/ backup@nas:/data/    # checksum-based mirroring
</pre>

<h2>8. Backups, SELinux And Shell Patterns</h2>

<pre># 3-2-1: 3 copies, 2 media, 1 offsite - and a restore you have tested
tar czf /backup/app-$(date +%F).tar.gz /srv/app
rsync -aHAX --delete /srv/ /mnt/backup/              # preserves perms/xattrs/ACLs
restic -r /mnt/backup init repo &amp;&amp; restic -r /mnt/backup backup /srv  # dedup + encryption
# Verify monthly:  restore to /tmp, checksum a sample, then document it.

# SELinux: the reason "permissions are correct but it still 500s"
getenforce &amp;&amp; sestatus
ls -Z /var/www/html/index.html     # context must match: httpd_sys_content_t
restorecon -Rv /var/www/html       # relabel after moving files
setsebool -P httpd_can_network_connect on   # allow app to make outbound calls
type -a httpd_t 2&gt;/dev/null | head  # what domain is allowed here?
ausearch -m avc -ts recent         # the audit log line that explains the denial

# Patterns every admin script needs
set -euo pipefail                  # fail fast on errors, unset vars, pipe failures
trap 'echo "failed at line $LINENO" &gt;&gt; /var/log/deploy.log' ERR
tmp=$(mktemp) &amp;&amp; trap 'rm -f "$tmp"' EXIT          # always clean up
retry() { for i in 1 2 3; do "$@" &amp;&amp; return 0; sleep 5; done; return 1; }
# Log everything:  mycmd 2&gt;&gt;&amp;1 | tee -a /var/log/job.log
</pre>

<h2>9. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Access</td><td>root all the time</td><td>Named users + sudo scope + SSH keys, root login disabled</td></tr>
<tr><td>Services</td><td>Start it and hope</td><td>Unit files, enable --now, failed-unit alerting</td></tr>
<tr><td>Storage</td><td>One big partition</td><td>LVM, separate /var/log, quotas, capacity alerts, fstab by UUID</td></tr>
<tr><td>Networking</td><td>ifconfig from an old tutorial</td><td>ip/nmcli, declarative netplan/NetworkManager, config in git</td></tr>
<tr><td>Logs</td><td>tail -f in a terminal</td><td>journald persistence + central syslog/SIEM, time sync</td></tr>
<tr><td>Patching</td><td>apt upgrade when you remember</td><td>Staging first, maintenance window, rollback path</td></tr>
<tr><td>Changes</td><td>vi directly on the server</td><td>Ansible/git - the server is a build artefact, not a pet</td></tr>
</table>

<h2>10. Key Takeaways</h2>
<ul>
<li>systemctl status, systemctl list-units --failed, journalctl -p err -
the three-command health check.</li>
<li>Timers beat cron when you want logs, dependencies and missed-run
recovery.</li>
<li>Visudo for sudoers, ACLs for fine-grained files, and audit setuid
binaries.</li>
<li>df -i as often as df -h; fstab by UUID; test with mount -a before any
reboot.</li>
<li>ip and ss replaced ifconfig and netstat; nftables underlies every modern
firewall front-end.</li>
<li>set -euo pipefail and a trap are the two lines that turn a script into a
tool.</li>
<li>SELinux denials show up in ausearch - restorecon fixes the common
case.</li>
</ul>

<p><strong>Exercise:</strong> build a systemd service + timer that appends
disk and memory stats to /var/log/health.log every 15 minutes, then prove it
ran with journalctl.</p>
"""