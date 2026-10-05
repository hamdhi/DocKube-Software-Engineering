"""Chapter - System administration for both Linux and Windows, side by side.

Learning both together is far more effective than learning them separately,
because the concepts are identical and only the command names differ.
"""

CHAPTER = """<h2>1. What a Sysadmin Actually Does</h2>

<p>A system administrator keeps other people's machines working. Concretely, that
means five things all day:</p>

<table>
<tr><th>Job</th><th>What it means in practice</th><th>How you know it is going wrong</th></tr>
<tr><td>Availability</td><td>Services stay up and users can work</td><td>Alerts when a service or host goes down</td></tr>
<tr><td>Security</td><td>Patching, accounts, least privilege</td><td>Failed logins, unexpected privilege changes</td></tr>
<tr><td>Capacity</td><td>Disk, memory and CPU will not run out</td><td>Thresholds reached before they are full</td></tr>
<tr><td>Backup</td><td>Restorable copies of everything important</td><td>Restores tested on a schedule</td></tr>
<tr><td>Change</td><td>Updates and config applied safely</td><td>Change records and rollback plans</td></tr>
</table>

<p><strong>Memory trick for the priorities:</strong> restore <b>first</b>, then
<u>u</u>pdate, then patch. A backup you have never restored is not a backup.</p>

<h2>2. Users and Groups, Side by Side</h2>

<table>
<tr><th>Task</th><th>Linux</th><th>Windows</th></tr>
<tr><td>Create a user</td><td><code>sudo useradd -m alice</code></td><td><code>New-LocalUser alice</code></td></tr>
<tr><td>Delete a user</td><td><code>sudo userdel -r alice</code></td><td><code>Remove-LocalUser alice</code></td></tr>
<tr><td>Set a password</td><td><code>sudo passwd alice</code></td><td><code>net user alice *</code></td></tr>
<tr><td>Lock the account</td><td><code>sudo usermod -L alice</code></td><td><code>net user alice /active:no</code></td></tr>
<tr><td>Add to a group</td><td><code>sudo usermod -aG sudo alice</code></td><td><code>Add-LocalGroupMember Administrators alice</code></td></tr>
<tr><td>See a user's groups</td><td><code>id alice</code></td><td><code>net user alice</code></td></tr>
<tr><td>Who am I</td><td><code>whoami</code></td><td><code>whoami</code></td></tr>
<tr><td>List all users</td><td><code>cat /etc/passwd</code></td><td><code>Get-LocalUser</code></td></tr>
<tr><td>Raise privileges</td><td><code>sudo</code></td><td>Run PowerShell as Administrator</td></tr>
</table>

<p><strong>Memory trick:</strong> Linux stores users in <code>/etc/passwd</code>
and hashed passwords in <code>/etc/shadow</code>. Windows keeps them in the
registry and the SAM database. Both use the idea of a local account plus
group membership for permissions.</p>

<h3>The sudoers file on Linux</h3>
<p>On Linux, which commands a user may run as root is defined in
<code>/etc/sudoers</code>, edited with <code>visudo</code> so syntax errors are
caught. Never grant <code>ALL</code> casually; grant the specific binary.</p>

<pre>alice ALL=(ALL) /usr/bin/systemctl restart nginx   # good, narrow
alice ALL=(ALL) NOPASSWD: ALL                # bad, defeats the purpose</pre>

<h2>3. Services, Side by Side</h2>

<table>
<tr><th>Task</th><th>Linux, systemd</th><th>Windows, PowerShell</th></tr>
<tr><td>Is it running?</td><td><code>systemctl status nginx</code></td><td><code>Get-Service W3SVC</code></td></tr>
<tr><td>Start</td><td><code>sudo systemctl start nginx</code></td><td><code>Start-Service W3SVC</code></td></tr>
<tr><td>Stop</td><td><code>sudo systemctl stop nginx</code></td><td><code>Stop-Service W3SVC</code></td></tr>
<tr><td>Restart</td><td><code>sudo systemctl restart nginx</code></td><td><code>Restart-Service W3SVC</code></td></tr>
<tr><td>Start at boot</td><td><code>sudo systemctl enable nginx</code></td><td><code>Set-Service -StartupType Automatic</code></td></tr>
<tr><td>Do not start at boot</td><td><code>sudo systemctl disable nginx</code></td><td><code>Set-Service -StartupType Disabled</code></td></tr>
<tr><td>List everything</td><td><code>systemctl list-units</code></td><td><code>Get-Service</code></td></tr>
<tr><td>Apply config without dropping connections</td><td><code>systemctl reload nginx</code></td><td><code>iisreset</code></td></tr>
</table>

<p><strong>Memory trick:</strong> on Linux, <code>enable</code> means "start at
boot" and <code>start</code> means "right now". On Windows the equivalent of
enable is <code>Set-Service -StartupType</code>. These are genuinely different
concepts and getting them confused causes outages.</p>

<h2>4. File Permissions, Side by Side</h2>

<p>Both systems answer the same question, "who may do what to this file", with
the same three classes: owner, group, everyone else. Only the notation differs.</p>

<table>
<tr><th>Task</th><th>Linux</th><th>Windows</th></tr>
<tr><td>See permissions</td><td><code>ls -l file</code></td><td><code>icacls file</code></td></tr>
<tr><td>Add read for everyone</td><td><code>chmod a+r file</code></td><td><code>icacls file /grant *S-1-1-0:(R)</code></td></tr>
<tr><td>Change owner</td><td><code>sudo chown alice file</code></td><td><code>takeown /f file</code></td></tr>
<tr><td>Change group</td><td><code>sudo chgrp admins file</code></td><td><code>icacls file /setgroup "Domain Admins"</code></td></tr>
<tr><td>Remove permissions</td><td><code>chmod o-r file</code></td><td><code>icacls file /remove:g Everyone</code></td></tr>
<tr><td>Apply to subfolders too</td><td><code>chmod -R</code></td><td><code>icacls folder /t</code></td></tr>
<tr><td>Copy permissions onto a file</td><td><code>getfacl / setfacl</code></td><td><code>icacls file /save acl.txt</code></td></tr>
</table>

<h3>The key difference</h3>

<table>
<tr><th>Aspect</th><th>Linux</th><th>Windows</th></tr>
<tr><td>Built-in groups</td><td>root, sudo, and groups you create</td><td>Administrators, Users, Guests, SYSTEM</td></tr>
<tr><td>Everyone</td><td><code>others</code>, written as <code>o</code> or <code>a</code></td><td>The "Everyone" principal, usually represented by a SID</td></tr>
<tr><td>Inheritance</td><td>Optional, via ACLs</td><td>On by default and deeply baked in</td></tr>
<tr><td>Typical default</td><td>644 files, 755 folders</td><td>Inherited from the parent folder</td></tr>
<tr><td>Getting it wrong</td><td>"Permission denied"</td><td>"Access is denied", and inheritance fights you</td></tr>
</table>

<p><strong>Memory trick:</strong> Linux gives the owner everything and others the
minimum. Windows inherits permissions down from the parent folder, so the answer
to "why can I not delete this" is usually "the parent folder will not let you",
and you must take ownership first with <code>takeown</code>.</p>

<h2>5. Host Networking, Side by Side</h2>

<table>
<tr><th>Task</th><th>Linux</th><th>Windows</th></tr>
<tr><td>Show IP configuration</td><td><code>ip addr show</code></td><td><code>ipconfig /all</code></td></tr>
<tr><td>Show the routes</td><td><code>ip route</code></td><td><code>route print</code></td></tr>
<tr><td>Listening ports</td><td><code>ss -tulnp</code></td><td><code>netstat -ano</code></td></tr>
<tr><td>Who owns a port</td><td><code>lsof -i :8080</code></td><td><code>tasklist /FI "PID eq 1234"</code></td></tr>
<tr><td>DNS lookup</td><td><code>dig example.com</code></td><td><code>nslookup example.com</code></td></tr>
<tr><td>Test reachability</td><td><code>ping -c 4 host</code></td><td><code>ping host</code></td></tr>
<tr><td>Trace the route</td><td><code>traceroute host</code></td><td><code>tracert host</code></td></tr>
<tr><td>Test a TCP port</td><td><code>nc -vz host 443</code></td><td><code>Test-NetConnection -Port 443</code></td></tr>
<tr><td>Firewall, view rules</td><td><code>sudo ufw status</code></td><td><code>Get-NetFirewallRule</code></td></tr>
<tr><td>Firewall, allow a port</td><td><code>sudo ufw allow 443/tcp</code></td><td><code>New-NetFirewallRule -DisplayName HTTPS -Direction Inbound -LocalPort 443 -Protocol TCP -Action Allow</code></td></tr>
<tr><td>Active firewall</td><td><code>sudo ufw enable</code></td><td><code>Set-NetFirewallProfile -Profile Public -Enabled True</code></td></tr>
</table>

<p>The Port Manager in this app uses <code>netstat -ano</code> and
<code>tasklist</code>, which is exactly this Windows column, so you can practise
it on your own machine right now.</p>

<h2>6. Processes, Side by Side</h2>

<table>
<tr><th>Task</th><th>Linux</th><th>Windows</th></tr>
<tr><td>List processes</td><td><code>ps aux</code> or <code>top</code></td><td><code>Get-Process</code></td></tr>
<tr><td>Live view by CPU</td><td><code>top</code></td><td><code>Get-Process | Sort-Object CPU -Desc</code></td></tr>
<tr><td>Find by name</td><td><code>pgrep -f nginx</code></td><td><code>Get-Process nginx</code></td></tr>
<tr><td>Stop politely</td><td><code>kill 1234</code></td><td><code>Stop-Process -Id 1234</code></td></tr>
<tr><td>Force stop</td><td><code>kill -9 1234</code></td><td><code>taskkill /PID 1234 /F /T</code></td></tr>
<tr><td>System load</td><td><code>top</code>, <code>uptime</code></td><td><code>Get-Counter</code></td></tr>
<tr><td>Memory</td><td><code>free -h</code></td><td><code>Get-CimInstance Win32_OperatingSystem</code></td></tr>
</table>

<p><strong>Memory trick:</strong> on both platforms the polite stop lets the
program clean up, and the force stop does not. Prefer the polite one.</p>

<h2>7. Disk and Storage, Side by Side</h2>

<table>
<tr><th>Task</th><th>Linux</th><th>Windows</th></tr>
<tr><td>Free space per filesystem</td><td><code>df -h</code></td><td><code>Get-Volume</code></td></tr>
<tr><td>Size of a folder</td><td><code>du -sh /var/log</code></td><td><code>Get-ChildItem -Recurse | Measure-Object</code></td></tr>
<tr><td>List disks and partitions</td><td><code>lsblk</code></td><td><code>Get-Disk</code>, <code>Get-Partition</code></td></tr>
<tr><td>What is mounted where</td><td><code>mount</code>, <code>df -h</code></td><td><code>Get-Volume</code></td></tr>
<tr><td>Partition a disk</td><td><code>fdisk /dev/sdb</code>, <code>parted</code></td><td><code>diskpart</code></td></tr>
<tr><td>Filesystem type</td><td><code>mkfs.ext4 /dev/sdb1</code></td><td><code>Format-Volume -FileSystem NTFS</code></td></tr>
<tr><td>Mount a filesystem</td><td><code>mount /dev/sdb1 /mnt/data</code></td><td><code>Mount-DiskImage</code>, or assign a drive letter</td></tr>
<tr><td>Mount at boot</td><td>edit <code>/etc/fstab</code></td><td><code>Set-Partition -NewDriveLetter</code></td></tr>
<tr><td>Check disk health</td><td><code>smartctl -a /dev/sda</code></td><td><code>Get-PhysicalDisk</code></td></tr>
</table>

<p><strong>Warning:</strong> partitioning and formatting destroy data. In
production nobody does this interactively; a storage system manages it.</p>

<h2>8. Logs and Troubleshooting, Side by Side</h2>

<table>
<tr><th>Task</th><th>Linux</th><th>Windows</th></tr>
<tr><td>Where logs live</td><td><code>/var/log</code>, the journal</td><td>C:\\Windows\\System32\\LogFiles, Event Viewer</td></tr>
<tr><td>Logs for one service</td><td><code>journalctl -u nginx</code></td><td><code>Get-WinEvent -LogName Application</code></td></tr>
<tr><td>Follow live</td><td><code>journalctl -u nginx -f</code></td><td><code>Get-Content -Wait log.txt</code></td></tr>
<tr><td>Recent errors only</td><td><code>journalctl -p err -n 50</code></td><td><code>Get-WinEvent -FilterHashtable @{Level=2}</code></td></tr>
<tr><td>Search a log file</td><td><code>grep -i error /var/log/syslog</code></td><td><code>Select-String -Path log.txt -Pattern error</code></td></tr>
<tr><td>Boot log</td><td><code>journalctl -b</code></td><td><code>Get-WinEvent -LogName System</code></td></tr>
<tr><td>Rotate old logs</td><td><code>logrotate</code></td><td>Built in, configured per application</td></tr>
</table>

<h3>A troubleshooting order that works on both</h3>
<ul>
<li><strong>Is the machine up?</strong> Check <code>uptime</code> or Task Manager.</li>
<li><strong>Is the service running?</strong> <code>systemctl status</code> or
<code>Get-Service</code>.</li>
<li><strong>Is it listening on the right port?</strong> <code>ss -tulnp</code> or
<code>netstat -ano</code>.</li>
<li><strong>What do the logs say?</strong> <code>journalctl</code> or Event Viewer.</li>
<li><strong>Are resources fine?</strong> <code>df -h</code>, <code>free -h</code>,
or the Task Manager performance tab.</li>
<li><strong>Did anything change?</strong> Recent updates, config edits, deploys.</li>
</ul>

<h2>9. Scheduling, Side by Side</h2>

<table>
<tr><th>Task</th><th>Linux</th><th>Windows</th></tr>
<tr><td>Run daily at 2am</td><td><code>0 2 * * *</code> in crontab</td><td>Task Scheduler with a daily trigger</td></tr>
<tr><td>Edit the schedule</td><td><code>crontab -e</code></td><td><code>schtasks /create /tn "Task" /tr cmd /sc daily /st 02:00</code></td></tr>
<tr><td>List scheduled jobs</td><td><code>crontab -l</code>, <code>ls /etc/cron.d</code></td><td><code>Get-ScheduledTask</code></td></tr>
<tr><td>Long-running schedule</td><td>systemd timers</td><td>Task Scheduler, or a service</td></tr>
<tr><td>Run once, detached</td><td><code>nohup cmd &amp;</code></td><td><code>Start-Process cmd -WindowStyle Hidden</code></td></tr>
</table>

<p><strong>Memory trick for cron:</strong> five fields in the order minute, hour,
day of month, month, day of week. A <code>*</code> means "every", so
<code>0 2 * * *</code> reads "at minute 0 of hour 2, every day".</p>

<h2>10. Package Management, Side by Side</h2>

<table>
<tr><th>Task</th><th>Linux, Debian</th><th>Linux, Red Hat</th><th>Windows</th></tr>
<tr><td>Refresh lists</td><td><code>apt update</code></td><td><code>dnf check-update</code></td><td><code>winget update</code></td></tr>
<tr><td>Install</td><td><code>apt install nginx</code></td><td><code>dnf install nginx</code></td><td><code>winget install nginx</code></td></tr>
<tr><td>Remove</td><td><code>apt remove nginx</code></td><td><code>dnf remove nginx</code></td><td><code>winget uninstall nginx</code></td></tr>
<tr><td>Security patches</td><td><code>unattended-upgrades</code></td><td><code>dnf update --security</code></td><td>Windows Update, or a patching tool</td></tr>
<tr><td>Other repositories</td><td><code>add-apt-repository</code></td><td><code>dnf config-manager</code></td><td><code>choco</code>, or a company feed</td></tr>
</table>

<h2>11. Backup and Transfer, Side by Side</h2>

<table>
<tr><th>Task</th><th>Linux</th><th>Windows</th></tr>
<tr><td>Copy preserving timestamps</td><td><code>rsync -avz src/ dest/</code></td><td><code>robocopy src dest /E /Z</code></td></tr>
<tr><td>Archive a folder</td><td><code>tar -czf backup.tar.gz /etc</code></td><td><code>Compress-Archive -Path data -DestinationPath data.zip</code></td></tr>
<tr><td>System backup</td><td><code>rsnapshot</code>, or Bacula</td><td><code>wbadmin</code>, or Veeam</td></tr>
<tr><td>Secure copy</td><td><code>rsync -e ssh</code>, <code>scp</code></td><td><code>scp</code>, available via OpenSSH</td></tr>
<tr><td>Verify the backup</td><td><code>tar -tzf backup.tar.gz</code></td><td><code>Get-FileHash backup.zip</code></td></tr>
</table>

<p><strong>The rule that matters:</strong> a backup is only real once you have
restored it. Schedule a restore test, not just a backup.</p>

<h2>12. Command Equivalence Cheat Sheet</h2>

<table>
<tr><th>What you want</th><th>Linux</th><th>Windows</th></tr>
<tr><td>Where am I</td><td><code>pwd</code></td><td><code>cd</code></td></tr>
<tr><td>List files</td><td><code>ls -la</code></td><td><code>dir /a</code></td></tr>
<tr><td>Change folder</td><td><code>cd /etc</code></td><td><code>cd C:\\Windows</code></td></tr>
<tr><td>Copy a file</td><td><code>cp a.txt b.txt</code></td><td><code>copy a.txt b.txt</code></td></tr>
<tr><td>Move or rename</td><td><code>mv a b</code></td><td><code>move a b</code></td></tr>
<tr><td>Delete</td><td><code>rm a.txt</code></td><td><code>del a.txt</code></td></tr>
<tr><td>Create a folder</td><td><code>mkdir new</code></td><td><code>mkdir new</code></td></tr>
<tr><td>View a file</td><td><code>cat a.txt</code></td><td><code>type a.txt</code></td></tr>
<tr><td>Search text</td><td><code>grep -r "x" .</code></td><td><code>findstr /s "x" *.*</code></td></tr>
<tr><td>Count lines</td><td><code>wc -l a.txt</code></td><td><code>(Get-Content a.txt).Count</code></td></tr>
<tr><td>Set permissions</td><td><code>chmod 644 f</code></td><td><code>icacls f /grant *S-1-1-0:(R)</code></td></tr>
<tr><td>Disk space</td><td><code>df -h</code></td><td><code>Get-Volume</code></td></tr>
<tr><td>Free memory</td><td><code>free -h</code></td><td><code>systeminfo</code></td></tr>
<tr><td>List processes</td><td><code>ps aux</code></td><td><code>Get-Process</code></td></tr>
<tr><td>Kill a process</td><td><code>kill 1234</code></td><td><code>taskkill /PID 1234 /F</code></td></tr>
<tr><td>IP address</td><td><code>ip addr</code></td><td><code>ipconfig</code></td></tr>
<tr><td>Ports in use</td><td><code>ss -tulnp</code></td><td><code>netstat -ano</code></td></tr>
<tr><td>Ping</td><td><code>ping -c 4 host</code></td><td><code>ping host</code></td></tr>
<tr><td>DNS lookup</td><td><code>dig host</code></td><td><code>nslookup host</code></td></tr>
<tr><td>Trace route</td><td><code>traceroute host</code></td><td><code>tracert host</code></td></tr>
<tr><td>Download a file</td><td><code>curl -O url</code></td><td><code>curl.exe -O url</code></td></tr>
<tr><td>Archive</td><td><code>tar -czf f.tar.gz dir</code></td><td><code>Compress-Archive</code></td></tr>
<tr><td>Who am I</td><td><code>whoami</code></td><td><code>whoami</code></td></tr>
<tr><td>Uptime</td><td><code>uptime</code></td><td><code>Get-CimInstance Win32_OperatingSystem</code></td></tr>
</table>

<h2>13. Remote Access and SSH</h2>

<table>
<tr><th>Task</th><th>Linux</th><th>Windows</th></tr>
<tr><td>Connect to a server</td><td><code>ssh user@10.0.0.5</code></td><td><code>ssh user@10.0.0.5</code>, or OpenSSH client</td></tr>
<tr><td>Use a key</td><td><code>ssh -i ~/.ssh/id_ed25519 user@host</code></td><td><code>ssh -i C:\\keys\\id_ed25519 user@host</code></td></tr>
<tr><td>Non-standard port</td><td><code>ssh -p 2222 user@host</code></td><td><code>ssh -p 2222 user@host</code></td></tr>
<tr><td>Copy files securely</td><td><code>scp f user@host:/tmp/</code></td><td><code>scp f user@host:C:/tmp/</code></td></tr>
<tr><td>Tunnel a local port</td><td><code>ssh -L 5432:db:5432 user@host</code></td><td>Same command works</td></tr>
<tr><td>Server config</td><td><code>/etc/ssh/sshd_config</code></td><td><code>C:\\ProgramData\\ssh\\sshd_config</code></td></tr>
<tr><td>Reload the SSH service</td><td><code>sudo systemctl reload sshd</code></td><td><code>Restart-Service sshd</code></td></tr>
</table>

<p>SSH is identical on both platforms, which makes it the easiest bridge when
moving between a Linux server and a Windows workstation.</p>

<h2>14. Try It Yourself (30 minutes, Windows)</h2>
<p>You can practise most of the Windows side immediately, without installing
anything:</p>
<ul>
<li>Open the Port Manager in this app and compare it with
<code>netstat -ano | findstr LISTENING</code>.</li>
<li>Run <code>Get-Service | Where-Object {$_.Status -eq 'Running'}</code>.</li>
<li>Run <code>Get-LocalUser</code> and <code>whoami /groups</code>.</li>
<li>Run <code>Get-NetFirewallProfile</code> and see which profiles are on.</li>
<li>Run <code>Get-WinEvent -LogName System -MaxEvents 10</code> to see the
Windows equivalent of <code>journalctl</code>.</li>
</ul>

<h2>15. Try It Yourself (45 minutes, Linux)</h2>
<p>Use WSL, a VM, or a free cloud instance:</p>
<ul>
<li>Run <code>ls -l</code> in <code>/etc</code> and decode five lines fully.</li>
<li>Create a file and set it to 644, then 600, checking with <code>ls -l</code>
each time.</li>
<li>Create a folder, <code>chmod 644</code> it, and prove you cannot
<code>cd</code> into it. Explain why.</li>
<li>Run <code>ls -l /etc | head</code> and work out why some files are 644 and
some are 777 or 600.</li>
<li>Run <code>systemctl list-units --type=service --state=running | head</code>.</li>
</ul>

<h2>16. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Accounts</td><td>One admin account for everything</td><td>Named accounts per person, shared credentials banned</td></tr>
<tr><td>Access</td><td>Password over SSH or RDP</td><td>Keys or VPN, MFA, no direct root</td></tr>
<tr><td>Permissions</td><td>Whatever makes it work</td><td>Least privilege, reviewed quarterly</td></tr>
<tr><td>Changes</td><td>Typed directly on the machine</td><td>Change request, tested, automated, audited</td></tr>
<tr><td>Config</td><td>Edited by hand in place</td><td>Managed as code, rolled out by tooling</td></tr>
<tr><td>Patching</td><td>When you remember</td><td>Scheduled, prioritised by severity, with a window</td></tr>
<tr><td>Backups</td><td>Occasional manual copy</td><td>Automated, monitored, restore-tested</td></tr>
<tr><td>Logs</td><td>Read after the user complains</td><td>Centralised and alerted on before users notice</td></tr>
<tr><td>Inventory</td><td>Remembered or a spreadsheet</td><td>Automated discovery, reconciled regularly</td></tr>
<tr><td>Linux</td><td>Learn on one distribution</td><td>Standardise on one, know the differences</td></tr>
</table>

<h2>17. Key Takeaways</h2>
<ul>
<li>The concepts are identical on Linux and Windows; only the commands differ.</li>
<li><code>enable</code> means start at boot, <code>start</code> means right now.</li>
<li>Windows inherits permissions from the parent folder, which explains most
"Access is denied" problems.</li>
<li>Work from the outside in: reachability, service, port, logs, resources.</li>
<li>A backup you have never restored is not a backup.</li>
<li>Standardise. Fewer operating system variants means fewer surprises.</li>
</ul>
"""