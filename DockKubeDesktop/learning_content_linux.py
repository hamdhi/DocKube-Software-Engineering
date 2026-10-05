"""Chapter - Linux command line, taught from absolute zero.

Placed before DevOps because everything in DevOps assumes you can move around
a Linux shell and read file permissions.
"""

CHAPTER = """<h2>1. What Linux Is, in One Paragraph</h2>

<p>Linux is an operating system: the layer between your programs and the
hardware. It is built from four ideas you will meet everywhere - users, files,
processes and permissions - and almost everything in this chapter exists to work
with one of them.</p>

<p><strong>The one mental model to keep:</strong> Linux is <strong>one big
folder tree</strong> starting at <code>/</code>. There is no "C drive" and no
"D drive". Everything, including your USB stick and every hard disk, hangs off
that single root.</p>

<pre>/
├── home      your personal files
├── etc       system-wide configuration
├── var       logs and data that grow
├── tmp       temporary files, cleared on reboot
├── usr       programs and libraries
├── bin       essential commands
└── proc      a live view of running processes</pre>

<p><strong>Memory trick:</strong> <code>/etc</code> holds configuration,
<code>/var</code> holds variable data that grows, <code>/usr</code> holds user
programs. They are the three you will visit most.</p>

<h2>2. Getting Around - pwd, cd, ls</h2>

<pre>pwd                 # where am I? prints /home/alice/project
ls                  # list this folder
ls -l               # long format: permissions, owner, size, date
ls -la              # long format plus hidden files
ls -lh              # human readable sizes: 4.0K instead of 4096
cd ..               # go up one level
cd ~                # go home
cd -                # go back to the folder you were just in
cd /etc             # absolute path, from the root
cd ../sibling       # relative: up one, then into sibling</pre>

<h3>Reading ls -l output</h3>
<p>Every line has ten fields. The first is the permission string:</p>

<pre>-rw-r--r--  1 alice alice  4096 Mar  3 10:22 notes.txt
drwxr-xr-x  2 root  root   4096 Mar  3 10:20 project</pre>

<table>
<tr><th>Field</th><th>Example</th><th>Meaning</th></tr>
<tr><td>Type</td><td>- or d</td><td>dash for a file, d for a directory, l for a symlink</td></tr>
<tr><td>Owner</td><td>rw-</td><td>permissions for the file's owner</td></tr>
<tr><td>Group</td><td>r--</td><td>permissions for the file's group</td></tr>
<tr><td>Others</td><td>r--</td><td>permissions for everyone else</td></tr>
<tr><td>Links</td><td>1</td><td>how many hard links point at it</td></tr>
<tr><td>Owner</td><td>alice</td><td>the user that owns it</td></tr>
<tr><td>Group</td><td>alice</td><td>the group that owns it</td></tr>
<tr><td>Size</td><td>4096</td><td>size in bytes</td></tr>
<tr><td>Modified</td><td>Mar 3 10:22</td><td>last change time</td></tr>
<tr><td>Name</td><td>notes.txt</td><td>the file name</td></tr>
</table>

<p><strong>Memory trick:</strong> hidden files start with a dot, like
<code>.bashrc</code>. <code>ls -a</code> reveals them.</p>

<h2>3. Paths: Absolute vs Relative</h2>

<table>
<tr><th>Kind</th><th>Starts with</th><th>Example</th><th>Based on</th></tr>
<tr><td>Absolute</td><td>/</td><td>/etc/nginx/nginx.conf</td><td>Always the root, no matter where you are</td></tr>
<tr><td>Relative</td><td>anything else</td><td>../logs/app.log</td><td>Your current folder</td></tr>
<tr><td>Home</td><td>~</td><td>~/documents</td><td>Your home folder, wherever you are</td></tr>
<tr><td>Current</td><td>.</td><td>./run.sh</td><td>The folder you are in right now</td></tr>
<tr><td>Parent</td><td>..</td><td>../</td><td>One level up from where you are</td></tr>
</table>

<p>Use absolute paths in scripts and configuration, because relative paths break
the moment the script runs from a different folder.</p>

<h2>4. Creating, Copying, Moving, Deleting</h2>

<pre>touch notes.txt              # create an empty file
mkdir project                # create a directory
mkdir -p a/b/c               # create nested folders, no error if they exist
cp notes.txt backup.txt      # copy a file
cp -r source/ destination/   # copy a directory and everything in it
mv old.txt new.txt           # move or rename
rm notes.txt                 # delete a file
rm -r project                # delete a directory and its contents
rm -i bigfile                # ask before each delete
mkdir /tmp/backup &amp;&amp; cp app.log /tmp/backup/   # only if the first worked</pre>

<p><strong>Be careful with <code>rm -rf</code>.</strong> There is no undo and no
recycle bin. Always <code>rm -i</code> until you are confident.</p>

<h2>5. Viewing File Contents</h2>

<pre>cat notes.txt                # print the whole file
less notes.txt               # scroll with arrows, q to quit
head -n 5 notes.txt          # first 5 lines
tail -n 5 notes.txt          # last 5 lines
tail -f /var/log/syslog      # follow new lines as they arrive
wc -l notes.txt              # count lines
grep -c error notes.txt      # count matching lines
sort names.txt | uniq        # sorted unique values
cut -d: -f1 /etc/passwd      # print field 1 using : as the separator</pre>

<p><strong>Memory trick:</strong> <code>tail -f</code> is how you watch a log
file live. Learn <b>f</b>alling for <b>f</b>ollow.</p>

<h2>6. Pipes and Redirection - Where Everybody Gets Stuck</h2>

<p>Every command in Linux writes its result to something called
<strong>standard output</strong>. Redirection decides where that output goes,
and a pipe sends it to another command's input.</p>

<h3>Redirection: changing where output goes</h3>

<table>
<tr><th>Symbol</th><th>Meaning</th><th>Use it to</th></tr>
<tr><td><code>&gt;</code></td><td>Write to a file, replacing it</td><td>Save output, discarding the old file</td></tr>
<tr><td><code>&gt;&gt;</code></td><td>Append to a file</td><td>Add to a log without losing previous lines</td></tr>
<tr><td><code>&lt;</code></td><td>Read input from a file</td><td>Feed a file into a command</td></tr>
<tr><td><code>2&gt;</code></td><td>Redirect errors to a file</td><td>Keep errors separate from results</td></tr>
<tr><td><code>2&gt;&amp;1</code></td><td>Send errors to normal output</td><td>Capture everything in one stream</td></tr>
<tr><td><code>|</code></td><td>Pipe one command into the next</td><td>Chain commands together</td></tr>
</table>

<pre>echo "hello" &gt; file.txt        # file now contains hello
echo "world" &gt;&gt; file.txt       # file now contains hello then world
ls &gt; listing.txt               # save the listing
ls &gt; /dev/null                  # throw the output away
command &lt; input.txt# read input from a file
ls 2&gt; errors.txt               # save errors separately
ls 2&gt;&amp;1 | grep denied# catch errors AND results together</pre>

<p><strong>Why <code>2&gt;&amp;1</code> works:</strong> file descriptors are numbered.
Descriptor <b>1</b> is normal output, <b>2</b> is errors. <code>2&gt;&amp;1</code>
means "take descriptor 2 and send it wherever descriptor 1 is going".</p>

<p><strong>Memory trick:</strong> <b>&gt;</b> points right into a file,
<b>&lt;</b> points left out of one, <b>|</b> is a pipe between two commands.</p>

<h3>Pipes - chaining commands</h3>
<p>The real power of Linux is that each command does one small thing well, and
pipes let you combine them.</p>

<pre>ls -l | grep "Jul" | wc -l          # count files modified in July
cat access.log | grep "404" | wc -l  # count errors in a log
ps aux | grep nginx | grep -v grep # find nginx, hide the grep itself
cat file | sort | uniq | sort -rn | head   # top 10 most common values
find . -name "*.log" -exec du -h {} ";" | sort -rh | head</pre>

<pre># Command substitution: run one command and use its output as an argument
cd "$(dirname /etc/nginx/nginx.conf)"
echo "Today is $(date)"
tar -czf backup-$(date +%Y%m%d).tar.gz /etc
for file in $(ls *.txt); do echo "Found $file"; done</pre>

<h3>Conditionals that chain commands</h3>

<table>
<tr><th>Symbol</th><th>Meaning</th><th>Example</th></tr>
<tr><td><code>&amp;&amp;</code></td><td>Run the second only if the first succeeded</td><td>mkdir x &amp;&amp; cd x</td></tr>
<tr><td><code>||</code></td><td>Run the second only if the first failed</td><td>cd x || echo "no such folder"</td></tr>
<tr><td><code>;</code></td><td>Run the second regardless</td><td>echo a; echo b</td></tr>
</table>

<p><strong>Memory trick:</strong> <code>&amp;&amp;</code> is "success leads to",
<code>||</code> is "failure leads to".</p>

<h2>7. grep - Searching Text</h2>

<pre>grep "error" app.log              # lines containing error
grep -i "error" app.log           # ignore capitalisation
grep -v "error" app.log           # lines NOT containing error
grep -n "error" app.log           # show line numbers
grep -c "error" app.log           # count matching lines
grep -r "apiKey" .                # search a whole directory tree
grep -r -l "apiKey" .             # list only files that match
grep -E "error|warning" app.log   # alternation, like a regex or
grep -r "^root" /etc/passwd       # lines starting with root
grep "user.$" app.log             # end-of-line anchor</pre>

<p><strong>Memory trick:</strong> <b>i</b>nvert case, <b>v</b>erse the match,
<b>n</b>umber the lines, <b>r</b>ecursive, <b>c</b>ount.</p>

<h2>8. File Permissions - The Full Picture</h2>

<p>Linux has no concept of files you cannot see. Every file has an owner, a
group, and three permissions for each of three classes of user. Once you can read
the ten characters of <code>ls -l</code> you can manage any file on the system.</p>

<h3>The three classes</h3>

<table>
<tr><th>Class</th><th>Who it applies to</th><th>Symbol</th></tr>
<tr><td>Owner, the user</td><td>The single user who owns the file</td><td>u</td></tr>
<tr><td>Group</td><td>Everyone in the file's assigned group</td><td>g</td></tr>
<tr><td>Others</td><td>Anybody else on the system</td><td>o</td></tr>
<tr><td>All three</td><td>Owner, group and others together</td><td>a</td></tr>
</table>

<h3>The three permissions</h3>

<table>
<tr><th>Permission</th><th>Letter</th><th>Value</th><th>On a file it means</th><th>On a directory it means</th></tr>
<tr><td>Read</td><td>r</td><td>4</td><td>You can open and view it</td><td>You can list the contents</td></tr>
<tr><td>Write</td><td>w</td><td>2</td><td>You can change the contents</td><td>You can create and delete files inside</td></tr>
<tr><td>Execute</td><td>x</td><td>1</td><td>You can run it as a program</td><td>You can enter it and reach files deeper inside</td></tr>
<tr><td>None</td><td>-</td><td>0</td><td>No access at all</td><td>No access at all</td></tr>
</table>

<p><strong>This is the part that confuses everyone:</strong> the same letter means
different things for a file and a directory. Execute on a <em>file</em> means
"runnable script". Execute on a <em>directory</em> means "you may travel through
it to reach files deeper inside". Without it you can list a folder but not enter
it.</p>

<h3>Reading the permission string</h3>

<pre>-rw-r--r--  1 alice alice 4096 notes.txt
drwxr-xr-x  2 root  root  4096 project
-rwxr-xr-x  1 alice alice 4096 run.sh</pre>

<table>
<tr><th>Example</th><th>Owner</th><th>Group</th><th>Others</th><th>What it is</th></tr>
<tr><td><code>-rw-r--r--</code></td><td>read write</td><td>read</td><td>read</td><td>A normal text file, mode 644</td></tr>
<tr><td><code>drwxr-xr-x</code></td><td>read write execute</td><td>read execute</td><td>read execute</td><td>A normal folder, mode 755</td></tr>
<tr><td><code>-rwxr-xr-x</code></td><td>read write execute</td><td>read execute</td><td>read execute</td><td>A script anyone can run, 755</td></tr>
<tr><td><code>-rw-------</code></td><td>read write</td><td>none</td><td>none</td><td>A private file, 600, such as an SSH key</td></tr>
<tr><td><code>drwx------</code></td><td>read write execute</td><td>none</td><td>none</td><td>A private folder, 700, such as ~/.ssh</td></tr>
</table>

<h2>9. chmod in Numeric Mode</h2>

<p>Numeric mode gives one digit per class. Each digit is the sum of the values you
want: read is 4, write is 2, execute is 1. Read and write without execute is 6,
and all three together is 7.</p>

<table>
<tr><th>Digit</th><th>Letters</th><th>How you get it</th></tr>
<tr><td>0</td><td>---</td><td>Nothing</td></tr>
<tr><td>1</td><td>--x</td><td>Execute only</td></tr>
<tr><td>2</td><td>-w-</td><td>Write only</td></tr>
<tr><td>3</td><td>-wx</td><td>2 + 1, write and execute</td></tr>
<tr><td>4</td><td>r--</td><td>Read only</td></tr>
<tr><td>5</td><td>r-x</td><td>4 + 1, read and execute</td></tr>
<tr><td>6</td><td>rw-</td><td>4 + 2, read and write</td></tr>
<tr><td>7</td><td>rwx</td><td>4 + 2 + 1, everything</td></tr>
</table>

<p><strong>Memory trick for the digits:</strong> <b>4</b>ead, <b>2</b>rite,
e<b>1</b>xecute. Add them up. Learn <b>644</b> and <b>755</b> first, because those
two cover almost everything.</p>

<h3>Why 644 for files and 755 for directories</h3>

<table>
<tr><th>Mode</th><th>Applies to</th><th>Owner</th><th>Group</th><th>Others</th><th>Why</th></tr>
<tr><td>644</td><td>Files</td><td>read write</td><td>read</td><td>read</td><td>Anyone can read it, only the owner edits it</td></tr>
<tr><td>755</td><td>Folders and scripts</td><td>read write execute</td><td>read execute</td><td>read execute</td><td>Everyone can pass through it, only the owner changes it</td></tr>
<tr><td>600</td><td>Private files</td><td>read write</td><td>none</td><td>none</td><td>SSH keys, passwords, tokens</td></tr>
<tr><td>700</td><td>Private folders</td><td>read write execute</td><td>none</td><td>none</td><td>~/.ssh and similar</td></tr>
<tr><td>750</td><td>Team readable</td><td>read write execute</td><td>read execute</td><td>none</td><td>Shared with a group only</td></tr>
<tr><td>775</td><td>Team writable</td><td>read write execute</td><td>read write execute</td><td>read execute</td><td>Group members can edit</td></tr>
</table>

<p>The logic is always the same: give the owner everything, give the group what
they genuinely need, and give everyone else read-only so they can see but not
change.</p>

<h3>chmod in practice</h3>

<pre>chmod 644 notes.txt       # readable by all, writable by owner
chmod 755 run.sh           # anyone can execute it
chmod 600 config.yaml      # only the owner
chmod 700 ~/.ssh           # only the owner
chmod 644 config.yaml      # standard for data and config files
chmod -R 755 public_html/ # -R applies recursively to subfolders</pre>

<p><strong>The habit to build:</strong> start from <b>644</b> for a file or
<b>755</b> for a directory or script, then narrow permissions only where there is
a real reason. Never start from 777.</p>

<h2>10. chmod in Symbolic Mode</h2>

<p>Numeric mode sets all nine permissions at once. Symbolic mode changes one
piece at a time, which is safer when you only want to adjust a single
permission.</p>

<h3>Who - the classes</h3>
<table>
<tr><th>Symbol</th><th>Means</th></tr>
<tr><td><code>u</code></td><td>user, the owner</td></tr>
<tr><td><code>g</code></td><td>group</td></tr>
<tr><td><code>o</code></td><td>others</td></tr>
<tr><td><code>a</code></td><td>all three at once</td></tr>
</table>

<h3>What - the operators</h3>
<table>
<tr><th>Symbol</th><th>Means</th><th>Example</th></tr>
<tr><td><code>+</code></td><td>add a permission</td><td><code>chmod u+x run.sh</code></td></tr>
<tr><td><code>-</code></td><td>remove a permission</td><td><code>chmod g-w notes.txt</code></td></tr>
<tr><td><code>=</code></td><td>set exactly these, clearing the rest</td><td><code>chmod o=rx file</code></td></tr>
</table>

<h3>The permissions being added or removed</h3>
<table>
<tr><th>Letter</th><th>Meaning</th><th>Numeric value</th></tr>
<tr><td><code>r</code></td><td>read</td><td>4</td></tr>
<tr><td><code>w</code></td><td>write</td><td>2</td></tr>
<tr><td><code>x</code></td><td>execute</td><td>1</td></tr>
</table>

<pre>chmod u+x run.sh             # owner can now execute it
chmod g+w report.txt         # group can now write
chmod o-r secrets.txt        # others can no longer read
chmod a+r public.txt         # everyone can read
chmod u=rwx,go=rwx private.txt  # set everything exactly
chmod o= file.txt            # others get no permissions at all
chmod -R u+w folder/         # owner can write, recursively</pre>

<p><strong>Memory trick:</strong> read the symbol as a sentence.
<code>u+x</code> is "add execute to the user". <code>o-r</code> is "remove read
from others". <code>=</code> is the only operator that resets everything it
touches before setting it.</p>

<h2>11. chown, chgrp and umask</h2>

<pre>sudo chown alice notes.txt          # change the owner
sudo chown alice:developers app/    # change owner and group
sudo chgrp developers shared.log    # change just the group
sudo chown -R alice:alice /var/www  # recursively fix a whole tree</pre>

<p>Changing a file's permissions is a lesser risk than changing its owner, but both
are powerful. The rule of least surprise says: prefer adding a user to a group
over making a file world-writable.</p>

<pre>chmod o+w file.txt     # anyone can now change it, avoid this
chmod -R a+w /etc      # dangerous and rarely ever correct
usermod -aG developers alice   # the better answer: join the group instead</pre>

<h3>umask - the default for newly created files</h3>

<p>The umask is subtracted from the maximum. A umask of <code>022</code> turns new
files into 644 and new folders into 755, which is exactly why those modes are so
common on most systems.</p>

<table>
<tr><th>umask</th><th>New files get</th><th>New folders get</th><th>Typical use</th></tr>
<tr><td>022</td><td>644</td><td>755</td><td>The sensible default on most systems</td></tr>
<tr><td>002</td><td>664</td><td>775</td><td>Shared team folders</td></tr>
<tr><td>077</td><td>600</td><td>700</td><td>Private work, keys and secrets</td></tr>
<tr><td>000</td><td>666</td><td>777</td><td>Almost always a mistake</td></tr>
</table>

<pre>umask                                # show the current umask, usually 0022
umask 077                            # make new files private from now on
touch newfile &amp;&amp; ls -l newfile    # verify it is now 600</pre>

<h2>12. Troubleshooting Permission Denied</h2>

<table>
<tr><th>Symptom</th><th>Likely cause</th><th>Correct fix</th></tr>
<tr><td>Permission denied reading a file</td><td>Missing read bit for your class</td><td><code>chmod o+r</code> or better, add the user to the group</td></tr>
<tr><td>Permission denied in a folder</td><td>Missing execute bit on a parent folder</td><td><code>chmod u+x</code> or <code>755</code> on the folder</td></tr>
<tr><td>Permission denied running a script</td><td>File has no execute bit</td><td><code>chmod +x script.sh</code></td></tr>
<tr><td>Not allowed to sudo</td><td>User is not in the sudo group</td><td><code>usermod -aG sudo alice</code> as root</td></tr>
<tr><td>Read-only file system</td><td>Mounted read-only, or immutable flag</td><td>Check with <code>mount</code>, remount or clear the attribute</td></tr>
</table>

<p><strong>Diagnose in this order:</strong> check who you are with
<code>whoami</code> and your groups with <code>id</code>, then read the file with
<code>ls -l</code>, then walk the whole path with <code>namei -l /full/path</code>.
A readable file inside an unreadable folder is still unreachable.</p>

<h2>13. Users, Groups and sudo</h2>

<pre>whoami                     # which user am I
id                         # my user id, group ids and group names
groups                     # which groups I belong to
su - alice                 # switch to another user, - loads their environment
sudo command               # run one command as root
sudo -u postgres command   # run as a specific user
sudo -i                    # start a full root login shell</pre>

<p><strong>Memory trick:</strong> <code>su</code> <b>s</b>witches <b>u</b>ser and
keeps your current directory unless you add <code>-</code>. <code>sudo</code> runs
a single command with elevated rights and leaves you as yourself.</p>

<h3>Group membership gotcha</h3>
<p>Adding yourself to a group does not update your current session. Log out and
back in, or start a new shell, or the change appears to do nothing.</p>

<pre>sudo usermod -aG docker alice   # add alice to the docker group
newgrp docker                   # pick up the new group without logging out</pre>

<h2>14. Processes and Signals</h2>

<pre>ps aux                  # every process on the machine
ps -ef                  # same idea, system-wide format
top                     # live view sorted by CPU, press q to quit
htop                    # prettier version, often not installed by default
pgrep -f nginx          # find a process by name
kill 1234               # ask process 1234 to stop politely
kill -9 1234            # force it, cannot be caught or ignored
jobs                    # background jobs in this shell
command &amp;                # run in background
nohup command &amp;          # keep running after you log out</pre>

<table>
<tr><th>Signal</th><th>Number</th><th>Meaning</th><th>Can the program catch it?</th></tr>
<tr><td>SIGHUP</td><td>1</td><td>Terminal closed</td><td>Yes, usually used to reload config</td></tr>
<tr><td>SIGINT</td><td>2</td><td>Ctrl and C pressed</td><td>Yes, request a clean exit</td></tr>
<tr><td>SIGTERM</td><td>15</td><td>Normal shutdown request</td><td>Yes, this is the polite way</td></tr>
<tr><td>SIGKILL</td><td>9</td><td>Force kill</td><td>No, the kernel ends it immediately</td></tr>
</table>

<p><strong>Always try plain <code>kill</code> before <code>kill -9</code>.</strong>
SIGTERM lets a server finish in-flight requests and close files properly. SIGKILL
gives it no chance, which is how you corrupt databases.</p>

<h2>15. Services with systemd</h2>

<pre>systemctl status nginx            # is it running, and what happened
systemctl start nginx             # start it now
systemctl stop nginx              # stop it now
systemctl restart nginx           # stop then start
systemctl reload nginx            # apply config without dropping connections
sudo systemctl enable nginx       # start automatically at boot
sudo systemctl disable nginx      # do not start at boot
systemctl is-enabled nginx# check whether it starts at boot
systemctl list-units --type=service</pre>

<p><strong>Memory trick:</strong> <code>enable</code> controls <b>boot</b> behaviour,
<code>start</code> controls <b>right now</b>. A service can be running without
being enabled, and enabled without running. This trips everyone up.</p>

<h2>16. Logs and Troubleshooting</h2>

<pre>journalctl -u nginx                # everything from one service
journalctl -u nginx -n 50          # last 50 lines only
journalctl -u nginx -f             # follow live, the equivalent of tail -f
journalctl -u nginx --since "1 hour ago"
journalctl -p err -n 20            # only errors
journalctl -b                       # this boot, useful after a crash
journalctl --disk-usage             # how much space logs are using</pre>

<p>Traditional log files live in <code>/var/log</code>. Common ones worth knowing:
<code>/var/log/syslog</code> for everything,
<code>/var/log/auth.log</code> for logins and sudo attempts, and
<code>/var/log/nginx/</code> for a web server's own logs.</p>

<h2>17. Disk and Storage</h2>

<pre>df -h                 # free space per mounted filesystem
df -h /               # the filesystem holding the current folder
du -sh *              # size of each item in the current folder
du -sh /var/* | sort -rh | head   # what is eating the most space
lsblk                 # block devices as a tree
mount                 # what is mounted where
free -h               # memory and swap
nproc                 # how many CPU cores</pre>

<p><strong>Memory trick:</strong> <code>df</code> is for <b>f</b>ilesystems,
<code>du</code> is for <b>d</b>irectories. They answer different questions and you
will need both when a disk fills up.</p>

<h2>18. sed and awk - Editing Text at Scale</h2>

<p>These two do most of what you would open Notepad for, but across thousands of
files or hundreds of thousands of lines in seconds.</p>

<h3>sed - stream editor, one line at a time</h3>
<pre>sed -n '5p' file.txt              # print line 5
sed -n '1,10p' file.txt           # print lines 1 to 10
sed 's/old/new/g' file.txt        # replace every occurrence
sed 's/old/new/' file.txt         # replace the first occurrence per line
sed -i 's/old/new/g' file.txt     # edit in place, always keep a backup first
sed -i.bak 's/old/new/g' f.txt   # in place, saving f.txt.bak for you
sed '/^#/d' config.ini            # delete every line starting with a hash
sed -n '10,20p' access.log | grep error   # errors between lines 10 and 20</pre>

<table>
<tr><th>Expression</th><th>Meaning</th></tr>
<tr><td><code>s/old/new/g</code></td><td>Substitute every match</td></tr>
<tr><td><code>-i</code></td><td>Edit the file in place</td></tr>
<tr><td><code>-n</code></td><td>Suppress default printing, used with p</td></tr>
<tr><td><code>/pattern/d</code></td><td>Delete matching lines</td></tr>
<tr><td><code>/pattern/p</code></td><td>Print only matching lines</td></tr>
</table>

<h3>awk - columns, like a spreadsheet</h3>
<pre>awk '{print $1}' access.log          # first column
awk '{print $1, $9}' access.log     # first and ninth, separated by a space
awk -F: '{print $1}' /etc/passwd    # use a colon instead of whitespace
awk '$3 &gt; 1000 {print $1}' file   # only rows where column 3 is over 1000
awk -F, 'NR&gt;1 {sum += $2} END {print sum}' sales.csv   # total column 2
awk '{c[$1]++} END {for (ip in c) print ip, c[ip]}' access.log</pre>

<p><strong>Memory trick:</strong> <b>sed</b> changes lines, <b>awk</b> reads
columns. If you are counting or totalling you want awk. If you are replacing text
you want sed.</p>

<h2>19. Archives, Compression and Transfers</h2>

<pre>tar -czf backup.tar.gz /etc        # create a gzipped tar of a folder
tar -xzf backup.tar.gz             # extract it
tar -tf backup.tar.gz              # list contents without extracting
zip -r files.zip folder/            # the Windows-friendly alternative

rsync -avz src/ user@host:/dest/   # copy, transferring only what changed
rsync -avz --delete src/ dest/     # mirror, removing extra files
scp file.txt user@host:/tmp/       # simple copy over SSH
wget https://example.com/file      # download a file
curl -O https://example.com/file   # same job, different tool</pre>

<p><strong>Memory trick:</strong> <b>c</b>reate, <b>x</b>tract, <b>t</b>est,
<b>f</b>ile. <code>tar -czf</code> creates, <code>tar -xzf</code> extracts and
<code>tar -tf</code> lists without extracting.</p>

<h2>20. Package Management</h2>

<pre>apt update                          # refresh the package lists
apt upgrade                         # upgrade everything installed
apt install nginx                   # install a package
apt remove nginx                    # remove it
apt purge nginx                     # remove it and its config files too
apt install --only-upgrade openssl  # security updates only
apt search nginx                    # search the repositories

# Red Hat family
dnf install nginx
dnf update
dnf info nginx</pre>

<p><strong>Never run <code>apt upgrade</code> on a production server without a
plan.</strong> It can pull in a new library version and restart services in the
middle of a working day.</p>

<h2>21. Shell Fundamentals Worth Knowing</h2>

<table>
<tr><th>Topic</th><th>Syntax</th><th>What it does</th></tr>
<tr><td>Single quotes</td><td><code>echo '$HOME'</code></td><td>Literal, nothing is expanded</td></tr>
<tr><td>Double quotes</td><td><code>echo "$HOME"</code></td><td>Variables are expanded</td></tr>
<tr><td>History</td><td><code>history</code>, press Up</td><td>Recall past commands</td></tr>
<tr><td>Tab completion</td><td>press Tab</td><td>Complete paths and command names</td></tr>
<tr><td>Environment variable</td><td><code>export PATH=$PATH:/opt/bin</code></td><td>Set for this shell and its children</td></tr>
<tr><td>Alias</td><td><code>alias ll='ls -la'</code></td><td>A shortcut command</td></tr>
<tr><td>Exit status</td><td><code>echo $?</code></td><td>0 means success, anything else failed</td></tr>
<tr><td>Script header</td><td><code>#!/bin/bash</code></td><td>Tells the kernel which shell to use</td></tr>
</table>

<p><strong>Memory trick:</strong> single quotes are safe, double quotes are
powerful. If unsure about a variable's contents, single-quote it.</p>

<h2>22. A Realistic Shell Session</h2>
<pre># "the site is slow. why?"
ping -c 5 example.com                          # can we even reach it
dig example.com                                # does DNS resolve
curl -o /dev/null -s -w "%{http_code} %{time_total}\n" https://example.com
ss -tulnp | grep 443                           # what is listening on 443
systemctl status nginx                         # is the web server healthy
journalctl -u nginx -n 50 --no-pager          # read the recent logs
free -h &amp;&amp; df -h                           # out of memory, or out of disk?</pre>

<p>This is the order a real sysadmin works in: reachability, then name resolution,
then the application, then logs, then resources. Check from the outside in.</p>

<h2>23. Try It Yourself (30 minutes)</h2>
<ul>
<li>Run <code>ls -l</code> in a folder and decode all ten fields of every line.</li>
<li>Create a file, note its mode, set it to 644 with numeric mode, then add only
the execute bit with <code>chmod u+x</code> and compare.</li>
<li>Compute 777 by hand as 4+2+1 three times, then set it and set it back.</li>
<li>Make a folder, remove its execute bit, and try to <code>cd</code> into it.
Notice what breaks.</li>
<li>Run <code>ls /etc | wc -l</code>, then <code>ls /etc | grep ssh</code>,
then chain both into a single line.</li>
<li>Run <code>ps aux --sort=-%mem | head</code> to find the hungriest process.</li>
</ul>

<h2>24. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Permissions</td><td>chmod 777 until it works</td><td>644 and 755 by default, least privilege everywhere</td></tr>
<tr><td>User accounts</td><td>Everything runs as root</td><td>Every service has its own unprivileged user</td></tr>
<tr><td>Access</td><td>SSH as root with a password</td><td>Key only, no direct root, sudo with logging</td></tr>
<tr><td>Changes</td><td>Typed straight into the server</td><td>Change management, then Ansible, then audit</td></tr>
<tr><td>Config editing</td><td>nano over SSH</td><td>Configuration management or a controlled rollout</td></tr>
<tr><td>Upgrades</td><td>apt upgrade whenever</td><td>Scheduled window, tested in staging first</td></tr>
<tr><td>Disk</td><td>Checked when something breaks</td><td>Alerting at thresholds, capacity planned ahead</td></tr>
<tr><td>Logs</td><td>tail -f on the console</td><td>Centralised, searchable, retained, alerted on</td></tr>
<tr><td>Knowing why</td><td>Reboot and hope</td><td>Documented runbook, then post-incident review</td></tr>
<tr><td>chmod -R on a system path</td><td>Sounds reasonable</td><td>Never. One wrong path can break the whole machine</td></tr>
</table>

<h2>25. Key Takeaways</h2>
<ul>
<li>Linux is one tree starting at <code>/</code>; there are no drive letters.</li>
<li>Permissions are owner, group and others, crossed with read, write and execute.</li>
<li><b>4</b> read, <b>2</b> write, <b>1</b> execute; 644 for files, 755 for folders.</li>
<li>Execute on a folder means you may enter it, not that you may run it.</li>
<li>Combine small commands with pipes before writing scripts.</li>
<li>Try <code>kill</code> before <code>kill -9</code>, and check status before restarting.</li>
<li>In production, least privilege and running as non-root are the whole game.</li>
</ul>
"""