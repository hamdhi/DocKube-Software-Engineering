r"""Chapter 38 - PC diagnostics for technical support: every test, Windows and Linux, in triage order."""

CHAPTER = r"""<h2>1. The Triage Order (Never Deviate)</h2>

<pre>0. Reproduce it.   What exactly, which user, which app, when did it start?
1. Power           lights, fans, POST beeps, does it reach the boot menu?
2. Software crash  event/log first - most "hardware" faults are software
3. Boot            OS loads? Safe mode / recovery environment?
4. Connectivity    link light, ip addr, ping gateway, DNS, then app
5. Storage         SMART + space + inodes + chkdsk/fsck
6. Memory          memtest overnight if crashes persist
7. Heat / power    throttling, PSU, battery health
8. Peripherals     swap the cable/device before blaming the board

Golden rule: change ONE variable, retest, record the result.
Ticket hygiene: symptom, reproduction steps, what you already tried, fix.
</pre>

<h2>2. Windows Diagnostics</h2>

<pre># --- System health ---
systeminfo | findstr /C:"Boot Time" /C:"OS Name" /C:"Total Physical Memory"
wmic os get lastbootuptime                      # uptime: patch or hang?
msinfo32                                        # the one-shot GUI summary
Get-ComputerInfo | Select-Object OsName, OsBuildNumber, CsManufacturer

# --- Memory ---
mdsched.exe                                     # Windows Memory Diagnostic: reboot test
Get-PhysicalMemory | Select Manufacturer, Capacity, Speed, Status   # STATUS must be OK
wmic memorychip get devicelocator, capacity, speed   # is a stick missing?
resmon                                           # Resource Monitor: RAM per process

# --- Disk ---
Get-PhysicalDisk | Format-Table FriendlyName, MediaType, HealthStatus, Size
Get-Volume C | Format-Table HealthStatus, SizeRemaining, Size
chkdsk C: /f /r                                 # schedule on reboot if C:
sfc /scannow &amp;&amp; DISM /Online /Cleanup-Image /RestoreHealth
perfmon /rel                                    # Reliability Monitor: when did it degrade?
# CrystalDiskMark / smartmontools (smartctl on Windows) for benchmark + SMART

# --- Event logs (find the FIRST error, not the last) ---
Get-WinEvent -FilterHashtable @{LogName='System'; Level=1,2; StartTime=(Get-Date).AddDays(-3)} |
    Sort-Object TimeCreated | Format-Table TimeCreated, Id, ProviderName, Message -AutoSize
eventvwr.msc                                    # GUI equivalent
dxdiag                                          # DirectX + GPU + drivers (games, display)
driverquery /v &amp; pnputil /enum-drivers           # driver inventory
verifier /standard /all                         # stress drivers (boot-safe mode to clear)

# --- CPU and heat ---
typeperf "\\$env:COMPUTERNAME\Processor(_Total)\% Processor Time" -sc 10
powercfg /thermal                               # thermal throttling events
powercfg /batteryreport /output battery.html    # laptops: design vs full charge capacity
wmic cpu get loadpercentage, name

# --- Network ---
ipconfig /all &amp; ipconfig /flushdns
Test-NetConnection gateway -Port 443            # + built-in trace
netsh wlan show interfaces                      # WiFi signal quality (dBm)
netsh int tcp show global                       # TCP tuning state
</pre>

<h2>3. Linux Diagnostics</h2>

<pre># --- System health ---
uname -a &amp;&amp; uptime &amp;&amp; hostnamectl
cat /etc/os-release
journalctl -b -p err --no-pager                 # errors since this boot
dmesg -T | tail -100 &amp;&amp; dmesg -T | grep -i -E "error|fail|warn"
systemctl --failed                              # failed units in one line

# --- Hardware discovery ---
lspci -nnk                                      # devices + bound driver
lsusb -t                                        # USB tree
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE
lshw -short &amp;&amp; dmidecode -t system               # model, serial, BIOS
inxi -Fxz                                       # all-in-one (install inxi)
sensors                                         # temperatures (lm-sensors)

# --- Memory ---
free -h &amp;&amp; cat /proc/meminfo | head
journalctl -k | grep -i -E "oom|out of memory"   # OOM killer victims
memtest86+ (boot from USB)                      # the definitive RAM test

# --- Disk and filesystem ---
df -hT &amp;&amp; df -i                                 # blocks AND inodes
smartctl -a /dev/sda                            # SMART: Reallocated_Sector_Ct, Power_On_Hours
smartctl -t short /dev/sda                      # run a self-test
fsck -n /dev/sdb1                               # dry-run check (unmounted only!)
e2fsck -f /dev/sdb1
badblocks -sv /dev/sdb                          # surface scan (slow)
iostat -xz 1 5                                  # disk saturation
hdparm -t /dev/sda                              # raw read speed

# --- Network ---
ip -br a &amp;&amp; ip r
ss -tulpn                                       # listeners
ping -c3 1.1.1.1 &amp;&amp; dig example.com +short
ethtool eth0                                    # link speed/duplex (half-duplex = classic)
mtr -rw example.com                             # ping + traceroute combined
journalctl -u NetworkManager -n 50
speedtest-cli                                    # actual throughput

# --- CPU / thermals / power ---
watch -n1 "cat /proc/loadavg; uptime"
mpstat -P ALL 1 5
stress-ng --cpu 4 --timeout 60s                 # deliberate load test
cat /sys/class/thermal/thermal_zone0/temp        # millidegrees C
</pre>

<h2>4. The Symptom-To-Test Map</h2>

<table>
<tr><th>Symptom</th><th>First three tests</th><th>Usual culprits</th></tr>
<tr><td>Won't power on</td><td>Outlet/cable/PSU test, listen for fans, POST codes</td><td>PSU, front-panel switch, dead outlet</td></tr>
<tr><td>Boots to black screen</td><td>Monitor/cable swap, safe mode, boot repair disk</td><td>GPU driver, GRUB, display output order</td></tr>
<tr><td>Random freeze / BSOD / kernel panic</td><td>Event log / journalctl -p err, memtest, temp</td><td>RAM, overheating, failing disk, bad driver</td></tr>
<tr><td>Very slow</td><td>resmon/iostat (CPU, RAM, disk 100%), df -h / df -i, startup items</td><td>Dying disk (100% active), RAM exhaustion, update thrash</td></tr>
<tr><td>No internet, others work</td><td>link light, ip addr, ping gateway then 8.8.8.8 then DNS</td><td>Wrong DHCP, DNS server, NIC driver</td></tr>
<tr><td>App crashes on open</td><td>Event ID 1000, dependency versions, clean profile test</td><td>Missing runtime (.NET/VC++), corrupt profile</td></tr>
<tr><td>Slow boot</td><td>boot duration (eventvwr / systemd-analyze), enabled services</td><td>Too many startup items, disk at 100%</td></tr>
<tr><td>Overheating / fan noise</td><td>powercfg /thermal or sensors, dust, airflow</td><td>Blocked vents, dried thermal paste, fan failure</td></tr>
<tr><td>Battery dies fast</td><td>powercfg /batteryreport (design vs full charge)</td><td>Cell wear &gt; 30%, background tasks, screen brightness</td></tr>
</table>

<h2>5. Benchmarks And Stress Tests (Prove The Fix)</h2>

<pre>Windows:   winsat disk -drive C          # built-in disk score
           CrystalDiskMark               # sequentials + 4K random (SSD health)
           CPU-Z / HWiNFO                # clock, throttle, VRM temps
Linux:     dd if=/dev/zero of=test bs=1M count=1024 oflag=dsync   # rough write
           fio --name=randread --rw=randread --bs=4k --numjobs=4   # proper I/O test
           sysbench cpu --threads=4      # CPU
           stress-ng --vm 2 --vm-bytes 1G --timeout 300s          # memory pressure
Both:      iperf3 -s / -c server         # LAN throughput between two machines
</pre>

<p><strong>Memory trick:</strong> a fix is not a fix until you have run the
same test that failed before - on the same conditions. "It seems fine now"
is how tickets come back three days later.</p>

<h2>6. Working A Support Ticket Professionally</h2>

<ol>
<li><strong>Intake:</strong> exact error text (screenshot), when it started,
what changed, who is affected, deadline impact.</li>
<li><strong>Reproduce:</strong> if you cannot reproduce it, ask what you are
missing - do not guess-fix.</li>
<li><strong>Isolate:</strong> one variable at a time; note every result in
the ticket as you go.</li>
<li><strong>Fix:</strong> smallest change that addresses the cause, not the
symptom.</li>
<li><strong>Verify:</strong> original test passes, plus a regression check
that nothing else broke.</li>
<li><strong>Document:</strong> root cause, what you changed, prevention
action - that note becomes the knowledge base article.</li>
</ol>

<table>
<tr><th>Escalate when...</th><th>To whom</th></tr>
<tr><td>Out of warranty hardware fault confirmed</td><td>Vendor support with diagnostics attached</td></tr>
<tr><td>Data loss or suspected compromise</td><td>Immediate - security + backup team, stop touching the machine</td></tr>
<tr><td>Affects the whole site/network</td><td>NOC / network team, with mtr + traceroute + timestamps</td></tr>
<tr><td>Same issue hits 3+ users</td><td>Change/release team - likely a deployment problem</td></tr>
</table>

<h2>7. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Fix style</td><td>Reinstall and start over</td><td>Diagnose to root cause - reinstalling hides the bug for the next person</td></tr>
<tr><td>Logs</td><td>Glance at the last error</td><td>First error in the sequence, correlated across machines by time</td></tr>
<tr><td>Tooling</td><td>Task Manager, top</td><td>Baseline first (you know what "normal" looks like), then compare</td></tr>
<tr><td>Tickets</td><td>Chat message</td><td>Full trail: symptom, tests, changes, verification, prevention</td></tr>
<tr><td>Prevention</td><td>Restart and forget</td><td>Alert on the metric that predicted it; recurring tickets get a project</td></tr>
</table>

<h2>8. Key Takeaways</h2>
<ul>
<li>Triage in fixed order: power -&gt; logs -&gt; boot -&gt; network -&gt; storage -
&gt; memory -&gt; heat.</li>
<li>Windows: eventvwr, resmon, sfc/DISM, mdsched, powercfg.
Linux: journalctl -p err, dmesg, smartctl, df -i, memtest86+.</li>
<li>Never skip the first error in the log; the last one is just the
symptom.</li>
<li>One variable per test, everything in the ticket, verify the original
failure is gone.</li>
<li>A recurring ticket without a prevention action is a failure, not a
fix.</li>
</ul>

<p><strong>Exercise:</strong> take a machine you can break, disable its DNS
resolver, and run the network row of the symptom map top to bottom until you
can name the fault from the tests alone, without guessing.</p>
"""