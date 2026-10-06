r"""Chapter 37 - The Linux kernel: boot, modules, memory, scheduling, namespaces and eBPF."""

CHAPTER = r"""<h2>1. What The Kernel Actually Is</h2>

<p>The kernel is the one program always running in the most privileged mode
(CPU ring 0). Everything else - shells, browsers, containers - asks it for
everything: memory, CPU time, files, sockets, devices. Linux is
<strong>monolithic</strong>: drivers and filesystems live inside kernel space
for speed, loaded as modules so they can be added without rebooting.</p>

<pre>User space   |  shell   app   systemd   nginx   your Python code
             |  syscalls: open, read, write, mmap, socket, ioctl, fork
-------------+----------------------------------------------------
Kernel space |  VFS  |  VM + page cache  |  scheduler  |  TCP/IP  |  drivers
             |  (files look the same)   |  (CFS)      |  netfilter|  (modules)
-------------+----------------------------------------------------
Hardware     |  CPU   memory   disk   NIC   GPU   USB
</pre>

<table>
<tr><th>Job</th><th>Subsystem</th><th>What you see</th></tr>
<tr><td>Arbitrate hardware</td><td>System calls, interrupts, drivers</td><td>strace output, /dev nodes</td></tr>
<tr><td>Memory</td><td>Virtual memory, page cache, swap, OOM killer</td><td>free -h, /proc/meminfo</td></tr>
<tr><td>CPU</td><td>Scheduler (CFS/EEVDF), cgroups</td><td>top load average, taskset</td></tr>
<tr><td>Storage</td><td>VFS, ext4/xfs, block layer</td><td>mount, iostat</td></tr>
<tr><td>Networking</td><td>Socket layer, TCP/IP stack, netfilter</td><td>ss, nft, /proc/net</td></tr>
</table>

<p><strong>Memory trick:</strong> the kernel is a librarian, not a
workhorse: every request from user space is a <em>syscall</em>. Run
<code>strace -c ls</code> and you are literally listing the librarian calls
a program makes.</p>

<h2>2. Boot Process And The Filesystems Behind It</h2>

<pre>Power on
  -&gt; firmware (BIOS/UEFI)      POST, finds the boot loader
  -&gt; GRUB                      menu, loads vmlinuz + initramfs
  -&gt; initramfs                 transient root: loads modules to find the real disk
  -&gt; kernel starts             decompresses, sets up memory, starts PID 1
  -&gt; systemd (PID 1)           mounts filesystems (fstab), starts targets
  -&gt; multi-user.target         network, sshd, your services
  -&gt; login

Where to look when it will not boot:
  journalctl -b -1              # the PREVIOUS boot's log
  journalctl -b -p err
  dmesg | head -50              # early kernel messages (also journalctl -k)
  systemctl isolate rescue.target   # minimal shell with root mounted
  cat /boot/grub/grub.cfg | grep menuentry
  lsinitrd /boot/initramfs-$(uname -r).img | head   # what is in the initramfs
</pre>

<table>
<tr><th>Filesystem</th><th>Purpose</th></tr>
<tr><td>/proc</td><td>Kernel and process state AS FILES - /proc/cpuinfo, /proc/PID/maps</td></tr>
<tr><td>/sys</td><td>Devices and their attributes (sysfs), udev feeds from it</td></tr>
<tr><td>/dev</td><td>Device nodes; udev creates them dynamically</td></tr>
<tr><td>/run</td><td>Runtime state (PID files, sockets), wiped on reboot</td></tr>
<tr><td>/etc/fstab</td><td>What to mount at boot</td></tr>
</table>

<h2>3. Kernel Modules</h2>

<pre>lsmod                             # loaded modules + use counts
modinfo ext4                      # parameters, license, vermagic
sudo modprobe br_netfilter        # load (resolves dependencies)
sudo modprobe -r dummy            # unload (fails if in use)
lspci -k                          # device + the driver it is using
lsusb -v | head
journalctl -k | grep -i error     # driver probe failures

# Persistent: /etc/modules-load.d/docker.conf
br_netfilter
overlay

# Tunables: /etc/sysctl.d/99-kernel.conf
net.bridge.bridge-nf-call-iptables = 1   # Kubernetes requirement
net.ipv4.ip_forward = 1                  # routing / containers
vm.swappiness = 10                       # prefer RAM over swap
fs.file-max = 2097152
kernel.panic = 10                        # reboot 10s after a kernel panic

sysctl --system                          # apply everything now
sysctl net.ipv4.ip_forward               # read one value
</pre>

<h2>4. Memory Management Internals</h2>

<pre>User virtual memory: each process gets its own 64-bit address space
  text (code) | data | heap (grows up via malloc/brk) | ... | stack (grows down)
  Physical RAM is shared underneath via page tables; the MMU translates.

Page cache: reads and writes land in RAM first - that is why repeat file
  access is instant and why "used" memory looks high (it is cache, not waste).
free -h:
              total  used  free  shared  buff/cache  available
              (available is the number that matters)

Swap: cold pages move to disk. Swapping hard = the box is out of memory.
OOM killer: when memory truly runs out the kernel picks the fattest process
  and SIGKILLs it - dmesg | grep -i "out of memory" tells you who and when.

# Memory forensics
cat /proc/meminfo | head -20
cat /proc/PID/status | grep -E "VmRSS|VmSize"
smem -t -k -s pss            # proportional set size: who REALLY uses memory
valgrind --leak-check=full ./app        # user-space leaks
perf stat -e page-faults -p PID         # fault rate of a running process
</pre>

<h2>5. Scheduling And CPU</h2>

<table>
<tr><th>Concept</th><th>Detail</th></tr>
<tr><td>CFS / EEVDF</td><td>The Linux scheduler: fair-share by virtual runtime; "nice" values tilt the share</td></tr>
<tr><td>Load average</td><td>Run queue length + blocked tasks, 1/5/15 min - load 8 on 4 cores means saturated</td></tr>
<tr><td>Nice / priority</td><td>nice -n 10 ./heavy; renice -n -20 -p PID (root only)</td></tr>
<tr><td>Affinity</td><td>taskset -c 0-3 app pins work to specific cores</td></tr>
<tr><td>cgroups v2</td><td>Hard limits per group: memory.max, cpu.max - what containers use</td></tr>
<tr><td>Interrupts</td><td>Hardware events deferred by softirqs; cat /proc/interrupts shows who fires</td></tr>
</table>

<pre># See cgroups v2 in action (a container is just these knobs + a namespace)
cat /sys/fs/cgroup/system.slice/nginx.service/memory.max
echo 512M &gt; /sys/fs/cgroup/test/memory.max
systemd-cgtop                      # live resource use per cgroup
cat /proc/PID/cgroup               # which cgroup is this process in?
</pre>

<h2>6. Namespaces, Containers And eBPF</h2>

<pre>Namespaces isolate VIEWS:    cgroups limit USAGE:
  mnt   - private mount tree     memory / cpu / io / pids limits
  pid   - PID 1 inside           (what "docker run --memory" sets)
  net   - own interfaces/ports
  uts   - own hostname
  user  - mapped root (rootless containers)
  ipc, cgroup, time

# Docker container = namespace + cgroups + union filesystem (overlayfs)
unshare --mount --pid --fork --uts bash   # hand-made "container"
lsns                                  # list namespaces on the system
cat /proc/PID/ns/                     # which namespace each process has

eBPF: safe sandbox programs attached to kernel hooks - observability
  without agents or kernel mods:
bcc-tools:  execsnoop, opensnoop, tcpconnect, bitesize
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("%s %s\n", comm, str(args.filename)); }'
bpftool prog list &amp;&amp; bpftool map show
# Cilium (Kubernetes networking) and most modern security tooling is eBPF.
</pre>

<h2>7. Tracing And Debugging The Kernel</h2>

<pre>dmesg -T --level=err,warn           # kernel ring buffer, human timestamps
journalctl -k --since today         # same messages via journald
ftrace:   echo function &gt; /sys/kernel/tracing/current_tracer
          cat /sys/kernel/tracing/trace_pipe
perf top                           # live hot functions (kernel + user)
perf record -g -p PID &amp;&amp; perf report # call-graph profiling
crash /proc/kcore /boot/vmlinux-$(uname -r)   # post-mortem of a crash dump
pstore:    journalctl -b -1 survives reboots if pstore is enabled

# Build your own kernel (know the steps even if you never ship one)
sudo apt build-dep linux            # deps
make olddefconfig                   # start from the running config
make menuconfig                     # the TUI - enable/disable subsystems
make -j$(nproc) &amp;&amp; make modules_install &amp;&amp; make install
# New kernels appear in GRUB; keep the previous entry for rollback.
</pre>

<h2>8. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Modules</td><td>modprobe anything interesting</td><td>Locked set, load-on-boot file, change-controlled</td></tr>
<tr><td>sysctl</td><td>Default values</td><td>Versioned in /etc/sysctl.d, tuned to workload, diffed after change</td></tr>
<tr><td>Memory</td><td>Watch free</td><td>Alert on available, OOM events, swap-in rate</td></tr>
<tr><td>Boot</td><td>It just works</td><td>serial console + pstore + previous-boot logs for headless boxes</td></tr>
<tr><td>Kernel version</td><td>Latest from tutorial</td><td>Distribution kernel + vendor backports; upgrade in staging</td></tr>
<tr><td>Tracing</td><td>print statements</td><td>perf/eBPF in production - near-zero overhead, full visibility</td></tr>
</table>

<h2>9. Key Takeaways</h2>
<ul>
<li>Monolithic + loadable modules: drivers live in kernel space but can be
added at runtime.</li>
<li>Everything is a syscall - strace -c shows your program's real
vocabulary.</li>
<li>Boot: firmware -&gt; GRUB -&gt; initramfs -&gt; kernel -&gt; systemd; debug with
journalctl -b -1 and dmesg.</li>
<li>Page cache explains "used" memory; available is the metric; the OOM
killer is the last resort.</li>
<li>cgroups limit, namespaces isolate - together they ARE a container.</li>
<li>eBPF lets you instrument the kernel safely - the basis of modern
Kubernetes networking and security tooling.</li>
</ul>

<p><strong>Exercise:</strong> run strace -c ls &gt; /dev/null, count the
syscalls, then write the same list from memory - that list is your map of
the kernel API.</p>
"""