r"""Chapter 35 - Windows sysadmin: every command you need to run a Windows estate."""

CHAPTER = r"""<h2>1. PowerShell Is The Real Interface</h2>

<p>cmd shows text; PowerShell pipes <em>objects</em> with properties. Every
Windows admin task below exists twice - once as a cmdlet (preferred) and
once as the legacy CLI - so both are listed.</p>

<pre># Run as Administrator once:
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser   # scripts allowed, downloads blocked
Get-Command *process*        # discovery beats memorisation
Get-Service | Where-Object Status -eq 'Stopped' | Select-Object -First 10
Get-Process | Sort-Object CPU -Descending | Format-Table -AutoSize
Get-Help Get-Service -Full    # examples included

# Piping is the whole point:
Get-EventLog -LogName System -EntryType Error -Newest 50 |
    Group-Object Source |
    Sort-Object Count -Descending |
    Format-Table Count, Name
</pre>

<table>
<tr><th>Task</th><th>PowerShell</th><th>Legacy CLI</th></tr>
<tr><td>List processes</td><td>Get-Process</td><td>tasklist</td></tr>
<tr><td>Kill process</td><td>Stop-Process -Id 1234 -Force</td><td>taskkill /PID 1234 /F</td></tr>
<tr><td>List services</td><td>Get-Service</td><td>sc query / net start</td></tr>
<tr><td>Restart service</td><td>Restart-Service Spooler</td><td>sc stop &amp; sc start / net stop Spooler</td></tr>
<tr><td>Remote machine</td><td>Invoke-Command -ComputerName SRV01 -ScriptBlock {hostname}</td><td>powershell -ComputerName (PS remoting)</td></tr>
</table>

<h2>2. Users, Groups And Domain Identity</h2>

<pre># Local accounts
net user administrator /active:yes          # enable (use carefully)
net user svc_deploy P@ssw0rd! /add /expires:never
net localgroup Administrators svc_deploy /add
net user                                       # list local users

# PowerShell equivalents (richer)
New-LocalUser -Name svc_deploy -Password (Read-Host -AsSecureString) `
              -Description "deployment service account"
Add-LocalGroupMember -Group Administrators -Member svc_deploy
Get-LocalGroupMember Administrators
Disable-LocalUser -Name guest

# Active Directory (RSAT: AD module)
Get-ADUser -Filter {Enabled -eq $true} -Properties LastLogonDate |
    Where-Object LastLogonDate -lt (Get-Date).AddDays(-90)
New-ADUser -Name "Jane Doe" -SamAccountName jdoe `
           -Path "OU=Staff,DC=corp,DC=local" -ChangePasswordAtLogon $true
Add-ADGroupMember -Identity "VPN-Users" -Members jdoe
Get-ADGroupMember "Domain Admins" -Recursive
# Offboarding in one sweep:
Disable-ADAccount jdoe; Remove-ADGroupMember -Identity VPN-Users -Members jdoe -Confirm:$false
</pre>

<p><strong>Memory trick:</strong> the three things that bite during audits:
local admin drift (everyone in Administrators), service accounts with
non-expiring passwords, and disabled users left in privileged groups.
Command: check those three weekly.</p>

<h2>3. Services, Processes And Scheduled Tasks</h2>

<pre># Services
Get-Service | Where-Object StartType -eq 'Automatic' |
    Where-Object Status -eq 'Stopped'        # failed auto-starts
Set-Service -Name Spooler -StartupType Disabled
sc.exe qc Spooler                           # classic view: start type, account
sc.exe queryex Spooler                      # PID + flags

# Process memory top-list
Get-Process | Group-Object Name |
    Sort-Object {($_.Group | Measure-Object WorkingSet -Sum).Sum} -Descending |
    Select-Object -First 10 Name, @{n='MB';e={[int]($_.Group | Measure-Object WorkingSet -Sum).Sum / 1MB}}

# Scheduled tasks
schtasks /Create /TN "NightlyBackup" /TR "D:\scripts\backup.ps1" `
         /SC DAILY /ST 02:00 /RU SYSTEM
schtasks /Query /TN NightlyBackup /V /FO LIST
schtasks /Run NightlyBackup                  # trigger it now
Get-ScheduledTask | Where-Object State -ne 'Ready'   # broken tasks

# Through PowerShell (module ScheduledTasks)
$action  = New-ScheduledTaskAction -Execute powershell.exe -Argument "-File D:\scripts\backup.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -TaskName NightlyBackup -Action $action -Trigger $trigger -RunLevel Highest
</pre>

<h2>4. Event Logs And Audit Trails</h2>

<pre># Modern (recommended)
Get-WinEvent -FilterHashtable @{LogName='System'; Level=1,2; StartTime=(Get-Date).AddHours(-24)} |
    Group-Object ProviderName | Sort-Object Count -Descending

# Failed logons - the first thing any security review asks for
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625} -MaxEvents 50 |
    Format-Table TimeCreated, @{n='User';e={$_.Properties[5].Value}}

# Classic cmdlet
Get-EventLog -LogName Application -EntryType Error -Newest 20

# wevtutil CLI
wevtutil epl System C:\logs\system.evtx               # export for support\wevtutil qe Security /c:20 /rd:true /f:text            # quick query
wevtutil sl Security /ms:1073741824                    # grow log to 1 GB

# Enable PowerShell script-block logging (audit what scripts ran):
# HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging -&gt; EnableScriptBlockLogging = 1
</pre>

<table>rh
<tr><th>Event ID</th><th>Meaning - memorise these five</th></tr>
<tr><td>4624 / 4625</td><td>Logon success / failure</td></tr>
<tr><td>4720</td><td>User account created</td></tr>
<tr><td>4728 / 4732</td><td>Member added to a global / local group</td></tr>
<tr><td>7045</td><td>New service installed (persistence marker)</td></tr>
<tr><td>1102</td><td>Security log cleared (red alert)</td></tr>
</table>

<h2>5. WMI/CIM - Querying The Machine</h2>

<pre>Get-CimInstance Win32_OperatingSystem | Select-Object Caption, LastBootUpTime
Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, LoadPercentage
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" |
    Select-Object DeviceID, @{n='FreeGB';e={[math]::Round($_.FreeSpace/1GB)}}, @{n='SizeGB';e={[math]::Round($_.Size/1GB)}}
Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object IPEnabled |
    Select-Object Description, IPAddress, DefaultIPGateway
Get-CimInstance Win32_ComputerSystem | Select-Object Name, Domain, TotalPhysicalMemory
Get-CimInstance Win32_Product | Where-Object Name -like "*7-Zip*"   # slow - use registry for inventory

# Remote query
Get-CimInstance -ComputerName SRV01 Win32_Service -Filter "State='Stopped'"
# Classic WMI still appears in old scripts:
wmic process get name,processid /format:list
</pre>

<p><strong>Memory trick:</strong> CIM is the modern, WS-Management (WinRM)
transport WMI; <code>wmic</code> is deprecated - learn Get-CimInstance and
replace wmic when you meet it.</p>

<h2>6. The Registry</h2>

<pre># HKLM = machine-wide, HKCU = current user
Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' |
    Select-Object ProductName, DisplayVersion      # Windows version + build

Set-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender' `
                 -Name DisableAntiSpyware -Value 0   # never do this to disable AV!

# Classic CLI
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v BuildNumber
reg export HKLM\SOFTWARE backup.reg                # ALWAYS export before editing
reg import new-settings.reg

# Golden rules:
# 1. reg export first, every time.
# 2. Edit HKCU when the setting is per-user; HKLM changes everyone.
# 3. Group Policy beats direct registry edits - GPO re-applies, drift does not.
</pre>
<h2>7. Disk, Storage And Files</h2>

<pre># PowerShell Storage module (modern)
Get-Disk | Format-Table Number, FriendlyName, OperationalStatus, Size
Get-Volume | Sort-Object SizeRemaining -Descending |
    Format-Table DriveLetter, FileSystemLabel, @{n='FreeGB';e={[math]::Round($_.SizeRemaining/1GB)}}, @{n='SizeGB';e={[math]::Round($_.Size/1GB)}}
Initialize-Disk -Number 1 -PartitionStyle GPT
New-Partition -DiskNumber 1 -UseMaximumSize -DriveLetter D
Format-Volume -DriveLetter D -FileSystem NTFS -NewFileSystemLabel Data -Confirm:$false
Get-Partition -DiskNumber 0 | Resize-Partition -Size 100GB   # shrink C:

# diskpart (scriptable, works where cmdlets do not)
list disk
select disk 1
clean
create partition primary
format fs=ntfs quick label=Data
assign letter=D

# Repair / health
chkdsk C: /f /r            # fix + recover bad sectors (needs reboot for C:)
Repair-Volume -DriveLetter C -Scan    # modern, online scan
sfc /scannow                # protected system files
DISM /Online /Cleanup-Image /RestoreHealth   # component store repair first
fsutil dirty query C:        # is a chkdsk pending?

# Files and ACLs
icacls D:\data /grant DomainAdmins:(OI)(CI)F /T
icacls D:\data /remove Users                          # least privilege
robocopy D:\data E:\backup /MIR /R:3 /W:5 /LOG:backup.log   # mirrors with a real log
Get-ChildItem C:\ -Recurse -File -ErrorAction SilentlyContinue |
    Group-Object Extension | Sort-Object Count -Descending | Select-Object -First 10
</pre>

<h2>8. Networking On Windows</h2>

<pre># ip config, modern
Get-NetIPConfiguration | Format-Table InterfaceAlias, @{n='IPv4';e={$_.IPv4Address.IPAddress}}, IPv4DefaultGateway
Get-NetIPAddress -AddressFamily IPv4 | Select-Object InterfaceAlias, IPAddress, PrefixLength
New-NetIPAddress -InterfaceAlias Ethernet -IPAddress 10.0.5.20 -PrefixLength 24 -DefaultGateway 10.0.5.1
Set-DnsClientServerAddress -InterfaceAlias Ethernet -ServerAddresses 1.1.1.1, 8.8.8.8
Get-NetRoute -DestinationPrefix 0.0.0.0/0
New-NetRoute -DestinationPrefix 10.9.0.0/16 -NextHop 10.0.5.1 -InterfaceAlias Ethernet
Test-NetConnection host -Port 443             # TCP reachability + trace
Resolve-DnsName example.com -Type MX

# Legacy but everywhere
ipconfig /all &amp;&amp; ipconfig /flushdns &amp;&amp; ipconfig /renew
netsh interface ip show config
netsh advfirewall show allprofiles
nslookup -type=any example.com
pathping example.com &amp;&amp; tracert example.com

# Shares
New-SmbShare -Name Finance -Path D:\finance -FullAccess 'CORP\Finance' -ChangeAccess 'CORP\Finance-Readers'
Get-SmbShare | Get-SmbShareAccess
net share                         # classic view
</pre>

<h2>9. Firewall And Windows Update</h2>

<pre># Defender Firewall via netsh (and PowerShell equivalents below)
netsh advfirewall set allprofiles state on
netsh advfirewall firewall add rule name="Allow HTTPS" dir=in action=allow protocol=TCP localport=443
netsh advfirewall firewall show rule name=all | findstr /i "rule name"

New-NetFirewallRule -DisplayName "Allow HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow
Get-NetFirewallRule | Where-Object Enabled -eq True | Measure-Object   # count live rules

# Windows Update automation
Install-Module PSWindowsUpdate -Scope CurrentUser -Force
Get-WindowsUpdate                       # what is pending
Install-WindowsUpdate -AcceptAll -AutoReboot
# Servers: wsuscmd / intune / MECM instead - never let servers auto-reboot.

# Patch level in one line:
Get-CimInstance Win32_QuickFixing | Sort-Object InstalledOn -Descending | Select-Object -First 10 HotFixID, InstalledOn
</pre>

<h2>10. IIS And Performance</h2>

<pre># IIS
Import-Module WebAdministration
Get-Website | Format-Table Name, State, PhysicalPath
New-Website -Name app -PhysicalPath C:\inetpub\app -Port 8080 -ApplicationPool DefaultAppPool
iisreset /start &amp;&amp; iisreset /status
appcmd list app /apppool.name:                         # classic CLI

# Performance: the four counters that answer "what is wrong"
typeperf "\\$(hostname)\Processor(_Total)\% Processor Time" `
         "\\$(hostname)\Memory\Available MBytes" `
         "\\$(hostname)\PhysicalDisk(_Total)\% Disk Time" `
         "\\$(hostname)\Network Interface(*)\Bytes Total/sec" -sc 10

Get-Counter '\Processor(_Total)\% Processor Time','\Memory\Available MBytes' -SampleInterval 5 -MaxSamples 6
# Data collector sets for longer capture:
logman create counter CPUBURST -f bsl -c "\Processor(_Total)\% Processor Time" si 5 -o C:\logs\perf.blg
logman start CPUBURST &amp;&amp; logman stop CPUBURST

# Battery report / power (laptops)
powercfg /batteryreport /output battery.html
powercfg /sleepstudy
</pre>

<h2>11. Backup, Recovery And Hardening Checklist</h2>

<pre>Backup:   wbadmin start backup -backupTarget:E: -include:C: -quiet   # legacy
          or Veeam / Azure Recovery Services in the real world
Restore:  system restore points (rstrui.exe), wbadmin get versions
BCD:      bcdedit /set {default} safeboot minimal   # boot to safe mode
          bcdedit /deletevalue {default} safeboot
Reset:    dism /online /cleanup-image /checkhealth

Hardening baseline (audit this list monthly):
[ ] Local Administrators: named individuals + one managed break account
[ ] Guest disabled, shared local accounts eliminated
[ ] BitLocker on all laptops; firewall on all profiles
[ ] Windows Defender ON, real-time on, signatures current
[ ] Auto-login disabled; screen lock policy enforced
[ ] Only approved software; inventory compared against allow-list
[ ] RDP: NLA required, restricted to jump host subnet
[ ] Logging: 4625/4720/7045 alerts wired to your inbox
[ ] Backups: nightly + restore tested THIS month
[ ] Patches: current within your patch window; reboot verified
</pre>

<h2>12. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Access</td><td>Your own admin account</td><td>Separate admin identities (LAPS), MFA, jump host, no daily-driver admin</td></tr>
<tr><td>Changes</td><td>GUI clicks, one machine</td><td>DSC/Intune/Ansible desired state across the fleet</td></tr>
<tr><td>Logging</td><td>Event Viewer when something breaks</td><td>Central SIEM, retention policy, alerts on the five key event IDs</td></tr>
<tr><td>Backups</td><td>Copied files to D:</td><td>3-2-1 rule, encrypted, restore TESTED monthly</td></tr>
<tr><td>Patching</td><td>Manual update button</td><td>Pilot ring -&gt; broad ring, maintenance windows, verified reboot</td></tr>
<tr><td>Registry</td><td>Edited by hand</td><td>GPO/Intune policy with documented rationale</td></tr>
</table>

<h2>13. Key Takeaways</h2>
<ul>
<li>PowerShell objects beat cmd text: Get-Command, Get-Help, pipes.</li>
<li>Weekly health sweep: stopped auto-start services, low disk, event log errors, failed logons, pending patches.</li>
<li>CIM replaces wmic; Group Policy replaces hand-edited registry keys;
robocopy replaces xcopy.</li>
<li>Event IDs 4624/4625/4720/7045/1102 are the audit core.</li>
<li>Backups you have never restored are wishes, not backups.</li>
</ul>

<p><strong>Exercise:</strong> write one PowerShell script that reports disk
space, stopped automatic services and the last 24 hours of system errors,
then schedule it with schtasks to email you every morning.</p>
"""