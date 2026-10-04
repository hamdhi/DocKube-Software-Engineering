import customtkinter as ctk
import subprocess
import threading
import os
import tkinter as tk
from tkinter import messagebox, ttk
import re
import webbrowser
import csv
import io

import devops_tools
from docs_content import COMMAND_PREFIXES, EXTRA_DOCS

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class TerminalFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.label = ctk.CTkLabel(self, text="Terminal Output", font=ctk.CTkFont(size=14, weight="bold"))
        self.label.grid(row=0, column=0, padx=10, pady=(10,0), sticky="w")
        self.output_button = ctk.CTkButton(self, text="Hide Output", width=100, command=self.toggle_output)
        self.output_button.grid(row=0, column=1, padx=10, pady=(8, 0), sticky="e")
        self.grid_columnconfigure(1, weight=0)
        # VS Code dark theme styled Text widget
        # Use a clear monospaced font for better readability
        self.textbox = tk.Text(
            self,
            font=ctk.CTkFont(family="Courier New", size=12),
            wrap="none",
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#d4d4d4",
            relief="flat",
        )
        self.textbox.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.output_collapsed = False
        # Configure tags for colored output (VS Code‑like theme)
        self.textbox.tag_configure("error", foreground="#f44747")   # red
        self.textbox.tag_configure("warning", foreground="#ff8800") # orange
        self.textbox.tag_configure("info", foreground="#9cdcfe")    # light blue
        self.textbox.tag_configure("keyword", foreground="#c586c0") # purple

    def append_output(self, text, tag=None):
        self.textbox.configure(state="normal")
        # Determine tag for coloring; default to provided or infer from content
        if tag:
            self.textbox.insert("end", text, tag)
        else:
            # Simple heuristic based on prefixes
            for line in text.splitlines(keepends=True):
                if line.lower().startswith("error") or "error" in line.lower():
                    self.textbox.insert("end", line, "error")
                elif line.lower().startswith("warning") or "warn" in line.lower():
                    self.textbox.insert("end", line, "warning")
                else:
                    self.textbox.insert("end", line, "info")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def clear(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")

    def set_output_collapsed(self, collapsed):
        self.output_collapsed = collapsed
        if collapsed:
            self.textbox.grid_remove()
            self.label.configure(text="Terminal Output (collapsed)")
            self.output_button.configure(text="Show Output")
            self.configure(height=42)
            self.grid_propagate(False)
        else:
            self.textbox.grid()
            self.label.configure(text="Terminal Output")
            self.output_button.configure(text="Hide Output")
            self.configure(height=290)
            self.grid_propagate(False)
        if callable(getattr(self, "on_output_visibility_changed", None)):
            self.on_output_visibility_changed(collapsed)

    def toggle_output(self):
        self.set_output_collapsed(not self.output_collapsed)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DocKube Software Engineer")
        self.geometry("1100x720")
        self.minsize(360, 540)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.categories = [
            "Dashboard", "Docker", "Minikube/Kind", "Pods", "Deployments",
            "Services", "ReplicaSets", "StatefulSets", "Volumes & PVC",
            "MySQL", "Postgres", "MongoDB", "CI/CD & GitHub Actions",
            "GitHub", "Jenkins", "Terraform", "Ansible", "Port Manager",
            "Custom", "Networking Masterclass"
        ]
        # Push the spacer below every button so the last one keeps its height.
        self.sidebar.grid_rowconfigure(len(self.categories) + 1, weight=1)
        ctk.CTkLabel(self.sidebar, text="DocKube", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(20,10))
        self.sidebar_buttons = {}
        for i, cat in enumerate(self.categories):
            btn = ctk.CTkButton(self.sidebar, text=cat, fg_color="transparent",
                                text_color=("gray10","gray90"), hover_color=("gray70","gray30"),
                                anchor="w", command=lambda c=cat: self.select_category(c))
            btn.grid(row=i+1, column=0, padx=20, pady=5, sticky="ew")
            self.sidebar_buttons[cat] = btn
        # Main area
        self.main = ctk.CTkFrame(self)
        self.main.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main.grid_rowconfigure(5, weight=1)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_columnconfigure(1, weight=1)
        self.doc_text = tk.Text(self.main, wrap="word", height=7, bg="#161b22", fg="#d4d4d4", insertbackground="#d4d4d4", relief="flat", padx=16, pady=12, font=("Segoe UI", 12))
        self.doc_text.tag_configure("title", foreground="#58a6ff", font=("Segoe UI", 19, "bold"), spacing3=8)
        self.doc_text.tag_configure("heading", foreground="#79c0ff", font=("Segoe UI", 14, "bold"), spacing1=8, spacing3=3)
        self.doc_text.tag_configure("bullet", foreground="#c9d1d9", lmargin1=12, lmargin2=24, spacing1=2)
        self.doc_text.tag_configure("command", foreground="#7ee787", font=("Cascadia Mono", 11, "bold"), lmargin1=16, lmargin2=16)
        self.doc_text.tag_configure("emphasis", foreground="#ffa657", font=("Segoe UI", 12, "bold"))
        self.table_style = ttk.Style(self)
        self.table_style.configure("DocKube.Treeview", background="#161b22", fieldbackground="#161b22", foreground="#d4d4d4", rowheight=24, borderwidth=0)
        self.table_style.configure("DocKube.Treeview.Heading", background="#238636", foreground="#ffffff", font=("Segoe UI", 10, "bold"), relief="flat")
        self.doc_text.configure(state="disabled")
        self.doc_text.grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="nsew")
        self.cmd_preview = ctk.CTkEntry(self.main, placeholder_text="Generated command appears here", width=800)
        self.cmd_preview.grid(row=2, column=0, padx=20, pady=5, sticky="w")
        # Header label for selected category
        self.header = ctk.CTkLabel(self.main, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.header.grid(row=0, column=0, sticky="w", padx=20, pady=(10,0))
        self.category_picker = ctk.CTkComboBox(self.main, values=self.categories, command=self.select_category, width=190)
        self.category_picker.grid(row=0, column=1, sticky="e", padx=20, pady=(10,0))
        # Working directory input
        self.work_dir_label = ctk.CTkLabel(self.main, text="Working Directory:")
        self.work_dir_label.grid(row=3, column=0, padx=20, pady=2, sticky="w")
        self.work_dir_entry = ctk.CTkEntry(self.main, width=600)
        self.work_dir_entry.insert(0, os.getcwd())
        self.work_dir_entry.grid(row=3, column=1, padx=20, pady=2, sticky="ew")
        # External terminal button
        self.ext_btn = ctk.CTkButton(self.main, text="Run in External Terminal", command=lambda: self.run_in_external_terminal(self.cmd_preview.get()))
        self.ext_btn.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        self.actions = ctk.CTkScrollableFrame(self.main)
        self.actions.grid(row=4, column=0, columnspan=2, padx=20, pady=5, sticky="nsew")
        self.actions.grid_columnconfigure(0, weight=1)
        self.terminal = TerminalFrame(self.main)
        self.terminal.grid(row=5, column=0, columnspan=2, padx=20, pady=5, sticky="nsew")
        self.terminal.set_output_collapsed(True)
        self.terminal.on_output_visibility_changed = self.configure_content_rows
        self.main.grid_rowconfigure(4, weight=1)
        # State helpers
        self.last_items = []   # list of (namespace, name)
        self.last_kind = ""
        self.manifest_combo = None
        self.yaml_file_combos = []
        self.service_combo = None
        self.service_options = []
        self.ports_tree = None
        self.ports_frame = None
        self.port_records = {}
        self.compact_layout = False
        self.configure_content_rows(True)
        # Detailed documentation snippets for DevOps concepts and YAML field guidance
        self.docs = {
            "Docker": "Docker packages applications into lightweight containers.\nKey concepts:\n- Image: read‑only template containing filesystem layers.\n- Container: a running instance of an image.\nCommon commands:\n    docker ps            – list running containers\n    docker ps -a        – list all containers\n    docker images       – list local images\n    docker run IMAGE    – start a new container from IMAGE\n    docker exec -it CONTAINER /bin/bash – open an interactive shell inside a running container.",
            "Minikube/Kind": "Minikube and Kind provide local Kubernetes clusters for development.\n- Minikube uses a VM or Docker driver to run a single‑node K8s cluster.\n- Kind runs Kubernetes inside Docker containers (great for CI).\nTypical commands:\n    minikube start      – start the cluster\n    kind create cluster – spin up a cluster with default config.",
            "Pods": "Pods are the smallest deployable unit in Kubernetes. They encapsulate one or more containers that share the same network namespace and storage volumes.\nImportant fields in a pod YAML:\n- `metadata.name`: unique pod name.\n- `spec.containers`: list of container specs (image, ports, env).\n- `spec.restartPolicy`: `Always`, `OnFailure`, or `Never`.",
            "Deployments": "Deployments manage stateless workloads, ensuring a desired number of pod replicas. They provide declarative updates and roll‑backs.\nKey YAML fields:\n- `spec.replicas`: number of desired pod replicas.\n- `spec.selector.matchLabels`: label selector matching the pods.\n- `spec.template`: pod template used for new pods.\n- `spec.strategy.type`: `RollingUpdate` (default) or `Recreate`.",
            "Services": "Services expose a set of Pods via a stable network endpoint.\nTypes:\n- **ClusterIP** (default): internal cluster‑only IP. Use when pods talk to each other.\n- **NodePort**: exposes the service on each node’s IP at a static port (30000‑32767).\n- **LoadBalancer**: provisions an external load balancer (cloud providers).\nKey fields:\n- `spec.type`: `ClusterIP`|`NodePort`|`LoadBalancer`.\n- `spec.ports`: list of ports (port, targetPort, nodePort).",
            "ReplicaSets": "ReplicaSets ensure that a specified number of pod replicas are running at any time. They are usually managed by Deployments, but can be used directly for simple scaling.\nKey fields:\n- `spec.replicas`: desired replica count.\n- `spec.selector`: label selector.\n- `spec.template`: pod template.",
            "StatefulSets": "StatefulSets manage stateful workloads that require stable network IDs and persistent storage. Ideal for databases.\nKey concepts:\n- Stable pod names (ordinal index).\n- Ordered, graceful deployment and scaling.\nImportant fields:\n- `spec.serviceName`: headless service governing DNS.\n- `spec.volumeClaimTemplates`: template for PersistentVolumeClaims per pod.",
            "Volumes & PVC": "A **PersistentVolume (PV)** represents a piece of storage in the cluster (NFS, cloud disk, etc.). A **PersistentVolumeClaim (PVC)** is a request for storage by a pod.\nCommon PVC fields:\n- `spec.accessModes`: `ReadWriteOnce`, `ReadOnlyMany`, `ReadWriteMany`.\n- `spec.resources.requests.storage`: size (e.g., `5Gi`).\n- `spec.storageClassName`: optional storage class.",
            "MySQL": "Typical MySQL deployment uses a StatefulSet for the database pod, a headless Service for stable DNS, and a PVC for data persistence. Sample YAML includes `apiVersion: apps/v1`, `kind: StatefulSet`, and a `volumeClaimTemplates` section.\nYou can edit the generated YAML with the built‑in editor before applying.",
            "Postgres": "Postgres follows the same pattern as MySQL – StatefulSet + PVC + Service. Helm charts also provide a ready‑made deployment with many configurable values.",
            "MongoDB": "MongoDB is often deployed as a StatefulSet with a headless Service. Operators can automate replica set configuration and backups.",
            "CI/CD & GitHub Actions": "GitHub Actions run workflow files located in `.github/workflows/*.yml`.\nKey steps for Docker/K8s CI/CD:\n1. `actions/checkout` – fetch source.\n2. Build Docker image and push to registry.\n3. Use `kubectl` (with a kubeconfig secret) to `apply -f` your YAML manifests.\nYou can author these YAML files directly in the app’s editor.",
            "Jenkins": "Jenkins is an automation server for building, testing, and deploying software.\nCore workflow:\n1. Define a pipeline in a `Jenkinsfile`.\n2. Check out source code.\n3. Build and test the application.\n4. Publish artifacts or deploy to Kubernetes.\nCommon pipeline stages:\n- Build: compile or build a container image.\n- Test: run unit, integration, and security tests.\n- Deploy: apply a reviewed release to an environment.",
            "Terraform": "Terraform manages infrastructure as code using `.tf` files.\nTypical workflow:\n1. `terraform init` downloads providers and prepares state.\n2. `terraform plan` previews infrastructure changes.\n3. `terraform apply` executes an approved plan.\n4. `terraform destroy` removes managed infrastructure.\nKeep state files secure and review plans before applying.",
            "Ansible": "Ansible automates configuration through inventories and YAML playbooks.\nCore workflow:\n1. Define hosts in an inventory file.\n2. Verify connectivity with the ping module.\n3. Describe desired state in a playbook.\n4. Run with `ansible-playbook`.\nUse `--check` to preview safe changes before applying them.",
            "Port Manager": "See the local TCP and UDP ports currently listening on this computer. Select a row to identify the owning process, then stop that exact process only when you are sure it is safe to do so.",
            "YAML Editor": "Create Kubernetes manifest files without leaving DocKube. The editor saves `.yaml` or `.yml` files directly into the Working Directory shown above. Choose a starter template, give the file a name, then save it.",
            "Manifest Files": "DocKube automatically finds YAML manifests in the Working Directory. Select one to open it in the editor or apply it to the active Kubernetes cluster—no filename entry required.",
            "Custom": "Enter any free‑form command you want to run – useful for resources not covered by the built‑in shortcuts, such as `ReplicationController` or custom `kubectl` plugins.",
            "Networking Masterclass": """            <h1 style="font-size:24px;color:#2b6cb0;font-weight:bold;">Networking Masterclass - From the Ground Up</h1>
<h2 style="font-size:20px;color:#2b6cb0;">Table of Contents</h2>
<ul>
<li>What Is an IP Address?</li>
<li>Binary Anatomy of IPv4 &amp; IPv6</li>
<li>Subnetting - Theory, Math, and Mnemonics</li>
<li>CIDR Notation &amp; /23, /24, ... Explained</li>
<li>Ports, Sockets, and the Transport Layer</li>
<li>Firewalls, ACLs, and Statefulness</li>
<li>The OSI Model - Layer-by-Layer Deep Dive</li>
<li>Domain Names, DNS, and Resolution Mechanics</li>
<li>TLS/SSL, SSH, and Packet-Level Handshakes</li>
<li>Subnetting in Everyday Scenarios - "How to Easily Remember"</li>
</ul>
<hr/>
<h2 style="font-size:20px;">IP Address Basics</h2>
<p>There are <strong>two versions</strong> of the protocol, each with its own address format and semantics.</p>
The IP address table has been disabled to avoid syntax errors.
(You may re-enable it later if needed.)
<p><em>Why 32 vs. 128 bits?</em> The original designers of IPv4 could not foresee the explosion of devices, so they chose a compact 32-bit space (~4 billion addresses). IPv6 expands the space by <strong>96 additional bits</strong>, giving you enough addresses to assign <strong>every grain of sand on Earth</strong> a unique IP, with room to spare.</p>
<h3 style="font-size:18px;">Binary Anatomy of IPv4 &amp; IPv6</h3>
<p><strong>IPv4 Example - 192.168.10.25</strong></p>
<table style="border-collapse:collapse; width:60%; margin:auto;">
<tr><th>Octet</th><th>Decimal</th><th>Binary (8 bits)</th></tr>
<tr><td>192</td><td>192</td><td>11000000</td></tr>
<tr><td>168</td><td>168</td><td>10101000</td></tr>
<tr><td>10</td><td>10</td><td>00001010</td></tr>
<tr><td>25</td><td>25</td><td>00011001</td></tr>
</table>
<p>Combined binary: <code>110000001010100000001010000110012</code>. With a <code>/24</code> prefix, the first 24 bits are the network ID and the last 8 bits are the host ID.</p>
<p><strong>IPv6 Example - 2001:db8::1</strong></p>
<p>Expanded: <code>2001:0db8:0000:0000:0000:0000:0000:0001</code>. Each block is 16 bits.</p>
<table style="border-collapse:collapse; width:80%; margin:auto;">
<tr><th>Block</th><th>Hex</th><th>Binary (16 bits)</th></tr>
<tr><td>2001</td><td>0010 0000 0000 0001</td><td>0010000000000001</td></tr>
<tr><td>0db8</td><td>0000 1101 1011 1000</td><td>0000110110111000</td></tr>
<tr><td>...</td><td>all zeros</td><td>0000000000000000</td></tr>
<tr><td>0001</td><td>0000 0000 0000 0001</td><td>0000000000000001</td></tr>
</table>
<h3 style="font-size:18px;">Subnetting - Theory, Math, and Mnemonics</h3>
<p>Subnetting splits a larger network into smaller logical sub-networks.</p>
<table style="width:100%;border-collapse:collapse;">
<tr style="background:#f0f0f0;"><th style="border:1px solid #ccc;padding:4px;">Step</th><th style="border:1px solid #ccc;padding:4px;">Calculation</th><th style="border:1px solid #ccc;padding:4px;">Result</th></tr>
<tr><td style="border:1px solid #ccc;padding:4px;">Needed hosts</td><td style="border:1px solid #ccc;padding:4px;">300</td><td style="border:1px solid #ccc;padding:4px;">-</td></tr>
<tr><td style="border:1px solid #ccc;padding:4px;">Add 2 (net+broadcast)</td><td style="border:1px solid #ccc;padding:4px;">302</td><td style="border:1px solid #ccc;padding:4px;">-</td></tr>
<tr><td style="border:1px solid #ccc;padding:4px;">Next power of 2 >= 302</td><td style="border:1px solid #ccc;padding:4px;">512 (2^9)</td><td style="border:1px solid #ccc;padding:4px;">-</td></tr>
<tr><td style="border:1px solid #ccc;padding:4px;">Host bits</td><td style="border:1px solid #ccc;padding:4px;">9</td><td style="border:1px solid #ccc;padding:4px;">-</td></tr>
<tr><td style="border:1px solid #ccc;padding:4px;">CIDR prefix</td><td style="border:1px solid #ccc;padding:4px;">/23</td><td style="border:1px solid #ccc;padding:4px;">512 total, 510 usable</td></tr>
</table>
<p><strong>Mnemonic Aids</strong></p>
<ul>
<li>Slash-N gives you <code>2^(32-N)</code> total addresses.</li>
<li>/24 = "A-class-C house with 256 rooms (254 live-in)."</li>
<li>/16 = "A-class-B block - 65,536 rooms."</li>
<li>/8 = "A-class-A planet - 16,777,216 rooms."</li>
<li>Port ranges: 0-1023 well-known, 1024-49151 registered, 49152-65535 ephemeral.</li>
</ul>
<h3 style=\\"font-size:18px;\\">CIDR Notation &amp; /23, /24, ... Explained</h3>
<p>Modern networking uses CIDR to allocate any prefix length from <code>/0</code> to <code>/32</code>. The prefix length determines how many bits belong to the network versus the host.</p>
<h3 style=\\"font-size:18px;\\">Ports, Sockets, and the Transport Layer</h3>
<p>Ports are 16-bit numbers that identify a specific process on a host. Common well-known ports:</p>
<ul>
<li>80 - HTTP</li>
<li>443 - HTTPS</li>
<li>22 - SSH</li>
<li>53 - DNS</li>
</ul>
<h3 style=\\"font-size:18px;\\">Firewalls, ACLs, and Statefulness</h3>
<p>Firewalls enforce security policies. A stateful firewall tracks connection state (NEW, ESTABLISHED, RELATED) to allow return traffic without explicit rules.</p>
<h3 style=\\"font-size:18px;\\">The OSI Model - Layer-by-Layer Deep Dive</h3>
<p>Seven layers, each with specific responsibilities:</p>
<ol>
<li>Physical - bits on the wire.</li>
<li>Port ranges: 0-1023 well-known, 1024-49151 registered, 49152-65535 ephemeral.</li>
</ul>
<h3 style=\\"font-size:18px;\\">CIDR Notation &amp; /23, /24, ... Explained</h3>
<p>Modern networking uses CIDR to allocate any prefix length from <code>/0</code> to <code>/32</code>. The prefix length determines how many bits belong to the network versus the host.</p>
<h3 style=\\"font-size:18px;\\">Ports, Sockets, and the Transport Layer</h3>
<p>Ports are 16-bit numbers that identify a specific process on a host. Common well-known ports:</p>
<ul>
<li>80 - HTTP</li>
<li>443 - HTTPS</li>
<li>22 - SSH</li>
<li>53 - DNS</li>
</ul>
<h3 style=\\"font-size:18px;\\">Firewalls, ACLs, and Statefulness</h3>
<p>Firewalls enforce security policies. A stateful firewall tracks connection state (NEW, ESTABLISHED, RELATED) to allow return traffic without explicit rules.</p>
<h3 style=\\"font-size:18px;\\">The OSI Model - Layer-by-Layer Deep Dive</h3>
<p>Seven layers, each with specific responsibilities:</p>
<ol>
<li>Physical - bits on the wire.</li>
</ul>
<h3 style="font-size:18px;">CIDR Notation &amp; /23, ... Explained</h3>
<p>Modern networking uses CIDR to allocate any prefix length from <code>/0</code> to <code>/32</code>. The prefix length determines how many bits belong to the network versus the host.</p>
<h3 style="font-size:18px;">Ports, Sockets, and the Transport Layer</h3>
<p>Ports are 16-bit numbers that identify a specific process on a host. Common well-known ports:</p>
<ul>
<li>80 - HTTP</li>
<li>443 - HTTPS</li>
<li>22 - SSH</li>
<li>53 - DNS</li>
</ul>
<h3 style="font-size:18px;">Firewalls, ACLs, and Statefulness</h3>
<p>Firewalls enforce security policies. A stateful firewall tracks connection state (NEW, ESTABLISHED, RELATED) to allow return traffic without explicit rules.</p>
<h3 style="font-size:18px;">The OSI Model - Layer-by-Layer Deep Dive</h3>
<p>Seven layers, each with specific responsibilities:</p>
<ol>
<li>Physical - bits on the wire.</li>
<li>Data Link - MAC addresses, Ethernet frames.</li>
<li>Network - IP routing, subnets.</li>
<li>Transport - TCP/UDP, ports.</li>
<li>Session - Dialog control.</li>
<li>Presentation - Encryption, compression.</li>
<li>Application - End-user protocols (HTTP, DNS).</li>
</ol>
<h3 style="font-size:18px;">Domain Names, DNS, and Resolution Mechanics</h3>
<p>DNS translates human-readable names into IP addresses using a hierarchy of authoritative servers.</p>
<h3 style="font-size:18px;">TLS/SSL, SSH, and Packet-Level Handshakes</h3>
<p>Secure protocols perform a handshake to establish encrypted channels.</p>
<ul>
<li>TLS - exchange of certificates, then symmetric key.</li>
<li>SSH - Diffie-Hellman key exchange, host verification.</li>
</ul>
<h3 style="font-size:18px;">Subnetting in Everyday Scenarios - "How to Easily Remember"</h3>
<p>Use the "network-first" rule: start allocating the smallest subnet that fits the requirement, then move to the next block.</p>
<hr/>
<h2 style="font-size:20px;">Appendix - Diagrams &amp; Image Sources</h2>
<table style="width:100%;border-collapse:collapse;">
<tr style="background:#f0f0f0;"><th style="border:1px solid #ccc;padding:4px;">Diagram</th><th style="border:1px solid #ccc;padding:4px;">Description</th><th style="border:1px solid #ccc;padding:4px;">Suggested URL (download &amp; place in `assets/`)</th></tr>
<tr><td style="border:1px solid #ccc;padding:4px;">k8s_network.png</td><td style="border:1px solid #ccc;padding:4px;">Flat Kubernetes pod network with Service CIDR, kube-proxy, CNI.</td><td style="border:1px solid #ccc;padding:4px;">https://raw.githubusercontent.com/kubernetes/website/main/content/en/images/docs/concepts/cluster/networking.png</td></tr>
<tr><td style="border:1px solid #ccc;padding:4px;">dns_flow.png</td><td style="border:1px solid #ccc;padding:4px;">Full DNS resolution flow (root -> TLD -> authoritative).</td><td style="border:1px solid #ccc;padding:4px;">https://www.cloudflare.com/img/learning/dns/dns-overview/dns-overview-diagram.svg</td></tr>
<tr><td style="border:1px solid #ccc;padding:4px;">cidr_chart.png</td><td style="border:1px solid #ccc;padding:4px;">Visual table of CIDR prefixes and host counts.</td><td style="border:1px solid #ccc;padding:4px;">https://www.ipcalc.net/images/cidr-table.png</td></tr>
<tr><td style="border:1px solid #ccc;padding:4px;">osi_layers.png</td><td style="border:1px solid #ccc;padding:4px;">Classic OSI 7-layer diagram.</td><td style="border:1px solid #ccc;padding:4px;">https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/OSI_Model.png/800px-OSI_Model.png</td></tr>
<tr><td style="border:1px solid #ccc;padding:4px;">subnet_example.png</td><td style="border:1px solid #ccc;padding:4px;">Example of dividing a /16 into /24 subnets with a diagram.</td><td style="border:1px solid #ccc;padding:4px;">https://i.stack.imgur.com/5xqZb.png</td></tr>
<tr><td style="border:1px solid #ccc;padding:4px;">firewall_stateful.png</td><td style="border:1px solid #ccc;padding:4px;">Stateful firewall flow diagram (NEW -> ESTABLISHED).</td><td style="border:1px solid #ccc;padding:4px;">https://www.cisco.com/c/en/us/td/docs/security/firepower/630/firepower-system-management/configuration/guide/fpm-630-sys-mgmt-config/figures/fpm_stateful_firewall.png</td></tr>
<tr><td style="border:1px solid #ccc;padding:4px;">ssh_handshake.png</td><td style="border:1px solid #ccc;padding:4px;">SSH key-exchange and authentication steps.</td><td style="border:1px solid #ccc;padding:4px;">https://i.stack.imgur.com/l3P2N.png</td></tr>
<tr><td style="border:1px solid #ccc;padding:4px;">tls_handshake.png</td><td style="border:1px solid #ccc;padding:4px;">TLS 1.2 handshake message diagram.</td><td style="border:1px solid #ccc;padding:4px;">https://tls13.ulfheim.net/tls13_handshake.png</td></tr>
<tr><td style="border:1px solid #ccc;padding:4px;">router_vs_switch.png</td><td style="border:1px solid #ccc;padding:4px;">Router vs. switch responsibilities (Layer 3 vs. Layer 2).</td><td style="border:1px solid #ccc;padding:4px;">https://www.networkworld.com/wp-content/uploads/2020/05/router-switch-800x450.png</td></tr>
<tr><td style="border:1px solid #ccc;padding:4px;">vm_vs_container.png</td><td style="border:1px solid #ccc;padding:4px;">Comparison table graphic (VM vs. Container).</td><td style="border:1px solid #ccc;padding:4px;">https://i.stack.imgur.com/aB9Xy.png</td></tr>
</table>

 Table of Contents
1. [What Is an IP Address?](#what-is-an-ip-address)  
2. [Binary Anatomy of IPv4 & IPv6](#binary-anatomy)  
3. [Subnetting - Theory, Math, and Mnemonics](#subnetting)  
4. [CIDR Notation & /23, /24, ... Explained](#cidr)  
5. [Ports, Sockets, and the Transport Layer](#ports)  
6. [Firewalls, ACLs, and Statefulness](#firewalls)  
7. [The OSI Model - Layer-by-Layer Deep Dive](#osi)  
8. [Domain Names, DNS, and Resolution Mechanics](#dns)  
9. [TLS/SSL, SSH, and Packet-Level Handshakes](#tls-ssh)  
10. [Subnetting in Everyday Scenarios - "How to Easily Remember"](#subnet-mnemonics)  

---





* **Street name** -> **Network prefix** (identifies the *subnet* or *network*).
* **House number** -> **Host identifier** (identifies the *individual device* within that network).

<p>There are <strong>two versions</strong> of the protocol, each with its own address format and semantics.</p>
<table style="width:100%; border-collapse:collapse;">
  <tr style="background:#f0f0f0;">
    <th style="border:1px solid #ccc; padding:4px;">Version</th>
  <th style="border:1px solid #ccc; padding:4px;">Bit-length</th>
  <th style="border:1px solid #ccc; padding:4px;">Human-readable format</th>
    <th style="border:1px solid #ccc; padding:4px;">Total address space</th>
    <th style="border:1px solid #ccc; padding:4px;">Typical usage</th>
</tr>
  <tr>
    <td style="border:1px solid #ccc; padding:4px;">IPv4</td>
    <td style="border:1px solid #ccc; padding:4px;">32 bits</td>
    <td style="border:1px solid #ccc; padding:4px;">Dotted decimal: a.b.c.d (0-255 each) -> e.g., 192.168.10.25</td>
    <td style="border:1px solid #ccc; padding:4px;">2^32 ~= 4.29 billion</td>
    <td style="border:1px solid #ccc; padding:4px;">Still dominant on the public Internet; private networks use RFC 1918 ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16).</td>
  </tr>
  <tr>
    <td style="border:1px solid #ccc; padding:4px;">IPv6</td>
    <td style="border:1px solid #ccc; padding:4px;">128 bits</td>
    <td style="border:1px solid #ccc; padding:4px;">Hexadecimal groups: xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx -> e.g., 2001:0db8:85a3:0000:0000:8a2e:0370:7334</td>
    <td style="border:1px solid #ccc; padding:4px;">2^128 ~= 3.4 * 10^38</td>
    <td style="border:1px solid #ccc; padding:4px;">Designed to replace IPv4; already mandatory for many cloud providers, mobile networks, and emerging IoT.</td>
  </tr>
</table>

*Why 32 vs. 128 bits?* The original designers of IPv4 could not foresee the explosion of devices, so they chose a compact 32-bit space (~=4 billion addresses). IPv6 expands the space by **96 additional bits**, giving you enough addresses to assign **every grain of sand on Earth** a unique IP, with room to spare.

 IPv4 Address Class vs. CIDR


An **Internet Protocol (IP) address** is the numeric identifier that a network-layer device uses to locate *exactly one* network interface on a given network. It is analogous to a **postal address** for a house.






* **Street name** -> **Network prefix** (identifies the *subnet* or *network*).  
* **House number** -> **Host identifier** (identifies the *individual device* within that network).

There are **two versions** of the protocol, each with its own address format and semantics.

| Version | Bit-length | Human-readable format | Total address space | Typical usage |
|---------|------------|-----------------------|---------------------|---------------|
| **IPv4** | 32 bits | Dotted decimal: `a.b.c.d` (0-255 each) -> e.g., `192.168.10.25` | 2^3^2 ~= 4.29 billion | Still dominant on the public Internet; private networks use RFC 1918 ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`). |
| **IPv6** | 128 bits | Hexadecimal groups: `xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx` -> e.g., `2001:0db8:85a3:0000:0000:8a2e:0370:7334` | 2^1^2^8 ~= 3.4 x 10^3^8 | Designed to replace IPv4; already mandatory for many cloud providers, mobile networks, and emerging IoT. |

*Why 32 vs. 128 bits?* The original designers of IPv4 could not foresee the explosion of devices, so they chose a compact 32-bit space (~=4 billion addresses). IPv6 expands the space by **96 additional bits**, giving you enough addresses to assign **every grain of sand on Earth** a unique IP, with room to spare.

 IPv4 Address Class vs. CIDR

Early IPv4 design used *classful* networks (Class A, B, C) with fixed subnet masks (e.g., Class C = `/24`). Modern networking abandoned this in favor of **CIDR (Classless Inter-Domain Routing)**, allowing any prefix length from `/0` to `/32` to suit the required number of hosts.

---

 2️⃣ Binary Anatomy of IPv4 & IPv6 <a name="binary-anatomy"></a>

 IPv4 Example - `192.168.10.25`

| Octet | Decimal | Binary (8 bits) |
|-------|---------|-----------------|
| 192   | 192     | `11000000` |
| 168   | 168     | `10101000` |
| 10    | 10      | `00001010` |
| 25    | 25      | `00011001` |

*Combined*: `11000000 10101000 00001010 00011001` -> `11000000101010000000101000011001_2`.  
You can count **network bits** from the left. If the network prefix is `/24`, the first 24 bits (`110000001010100000001010`) represent the **network ID**, and the remaining 8 bits (`00011001`) represent the **host ID**.

 IPv6 Example - `2001:db8::1`

* Expanded notation: `2001:0db8:0000:0000:0000:0000:0000:0001`.  
* Each block = 16 bits (4 hex digits).

| Block | Hex | Binary (16 bits) |
|-------|-----|------------------|
| 2001 | `0010 0000 0000 0001` |
| 0db8 | `0000 1101 1011 1000` |
| ...   | all zeros |
| 0001 | `0000 0000 0000 0001` |

IPv6 also introduces **special address types**:

* **Link-Local** (`fe80::/10`) - only usable on the same Ethernet segment.
* **Unique Local** (`fc00::/7`) - private-address equivalent to IPv4 RFC 1918.
* **Multicast**, **Anycast**, and **Global Unicast** - all identified by distinct prefix ranges.

---

 3️⃣ Subnetting - Theory, Math, and Mnemonics <a name="subnetting"></a>

Subnetting is the process of **splitting a larger IP network into smaller, logical sub-networks**, each with its own broadcast domain. It serves three primary goals:

1. **Conserve address space** (especially in IPv4).  
2. **Contain broadcast traffic** to its own subnet.  
3. **Apply security policies** (different subnets can have different firewall rules).

 3.1. The Core Math

Given a **network prefix length** `/N` (where `0 <= N <= 32` for IPv4):

* **Network bits** = N  
* **Host bits** = 32 - N  
* **Number of possible host addresses** = `2^(32-N)`  
* **Usable hosts** = `2^(32-N) - 2` (subtract network address and broadcast address).

**Example - `/24`**  
* Host bits = 8 -> `2^8 = 256` total addresses -> 254 usable (`0` is network, `255` is broadcast).

 3.2. Determining the Right Subnet Size

1. **Count needed hosts** (including routers, servers, future growth).  
2. **Find the smallest power of two** >= needed hosts + 2 (network + broadcast).  
3. **Compute** `Host bits = log2(needed_total)`.  
4. **CIDR prefix** = `32 - Host bits`.

**Worked Example - Need 300 hosts**

| Step | Calculation | Result |
|------|-------------|--------|
| 1. Needed hosts | 300 | |
| 2. Add 2 (net+broadcast) | 302 | |
| 3. Next power of 2 >= 302 | 512 | (`2^9`) |
| 4. Host bits | 9 | |
| 5. CIDR prefix | `32-9 = 23` | -> **`/23`** (512 total, 510 usable) |

 3.3. Mnemonic Aids

| Concept | Mnemonic |
|---------|----------|
| **Slash-N** | "*Slash N* gives you **2^(32-N)** total addresses." |
| **/24** | "*A-class-C* house with 256 rooms (254 live-in)." |
| **/16** | "*A-class-B* block - 65 536 rooms." |
| **/8**  | "*A-class-A* planet - 16 777 216 rooms." |
| **Port range** | "*0-1023* = **well-known doors**, *1024-49151* = **registered doors**, *49152-65535* = **ephemeral doors** you open temporarily." |
| **Subnet mask trick** | Write the mask in binary, count continuous 1's from the left - that's the CIDR prefix. E.g., `255.255.254.0` -> `11111111.11111111.11111110.00000000` -> 23 ones -> **/23**. |

 3.4. Subnetting Example - Real-World Scenario

*You own a 10.0.0.0/16 private block and need the following sub-nets:*  

| Purpose | Required hosts | Chosen CIDR | Network address | Broadcast address |
|---------|----------------|------------|-----------------|-------------------|
| Management VLAN (routers, NOC) | 30 | `/27` (32 total) | `10.0.0.0/27` | `10.0.0.31` |
| Server farm | 200 | `/24` (256 total) | `10.0.1.0/24` | `10.0.1.255` |
| Guest Wi-Fi | 150 | `/24` (256 total) | `10.0.2.0/24` | `10.0.2.255` |
| IoT sensors | 4000 | `/20` (4096 total) | `10.0.16.0/20` | `10.0.31.255` |

*Note*: Sub-nets are **contiguous** and allocated from low to high addresses to simplify routing tables.

---

 4️⃣ CIDR Notation & /23, /24, ... Explained <a name="cidr"></a>

**CIDR (Classless Inter-Domain Routing)** expresses an IP network as `address/prefix_length`. The *prefix length* tells how many **most-significant bits** belong to the network portion.

| CIDR | Netmask (dotted decimal) | Usable hosts |
|------|--------------------------|--------------|
| `/32` | `255.255.255.255` | 1 (single host, used for loopback or point-to-point) |
| `/31` | `255.255.255.254` | 2 (RFC 3021 - used for point-to-point links, no broadcast) |
| `/30` | `255.255.255.252` | 2 (common for router-to-router links) |
| `/29` | `255.255.255.248` | 6 |
| `/28` | `255.255.255.240` | 14 |
| `/27` | `255.255.255.224` | 30 |
| `/26` | `255.255.255.192` | 62 |
| `/25` | `255.255.255.128` | 126 |
| `/24` | `255.255.255.0`   | **254** (classic "class C") |
| `/23` | `255.255.254.0`   | **510** |
| `/22` | `255.255.252.0`   | 1 022 |
| `/16` | `255.255.0.0`     | 65 534 |
| `/8`  | `255.0.0.0`       | 16 777 214 |

**Why `/23` vs `/24` matters**  
A `/23` merges two adjacent `/24` blocks, giving you **double the hosts** (510 usable). The trade-off is a **larger broadcast domain** and a **longer mask** (less granularity for routing).

 Visualising CIDR

```
/24 (255.255.255.0)
11111111.11111111.11111111.00000000   <- network part = 24 bits
^^^^^^^^ ^^^^^^^^ ^^^^^^^^
|          |          |
|          |          +--- Host part: 8 bits -> 0-255
|          +------------- Network part: first three octets (192.168.1)
+------------------------ Fixed network identifier
```

When you move to **/23**, the third octet's last bit becomes part of the host portion, giving you the range `192.168.0.0 - 192.168.1.255`.

---

 5️⃣ Ports, Sockets, and the Transport Layer <a name="ports"></a>

A **socket** is identified by a **4-tuple**:

```
(source IP, source port, destination IP, destination port)
```

* **Port**: a 16-bit unsigned integer (0-65535) the OS uses to multiplex/demultiplex traffic.  
* **Well-known ports** (0-1023) are assigned by IANA (e.g., 22 -> SSH, 80 -> HTTP, 443 -> HTTPS).  
* **Registered ports** (1024-49151) are documented for specific services.  
* **Dynamic/ephemeral ports** (49152-65535) are chosen by clients for outbound connections.

 How a TCP connection is established (three-way handshake)

1. **SYN** - client -> server: `seq = X`.  
2. **SYN-ACK** - server -> client: `seq = Y`, `ack = X+1`.  
3. **ACK** - client -> server: `ack = Y+1`.  

After this, both sides know each other's initial sequence numbers and can reliably transmit data.

**UDP** skips the handshake - it's **connectionless**, just sends datagrams to a destination IP : port. No guarantee of delivery, ordering, or duplication protection.

 Port-Based Security

* **Firewalls** filter by source/destination IP, protocol, and port.  
* **ACLs (Access Control Lists)** on routers/switches can also restrict ports.  
* **Stateful inspection** tracks the flow's state (e.g., only allow traffic that belongs to an existing TCP connection).

**Mnemonic:** "*Ports are doors; firewalls are security guards checking who may walk through which door.*"

---

 6️⃣ Firewalls, ACLs, and Statefulness <a name="firewalls"></a>

| Concept | Definition | Typical Layer(s) | Example Rule |
|----------|------------|------------------|--------------|
| **Stateless firewall** | Examines each packet in isolation (no memory of prior packets). | Network/Transport | `deny ip any any` (drops everything regardless of connection state). |
| **Stateful firewall** | Tracks connection state (e.g., SYN->SYN-ACK->ACK) and allows return traffic automatically. | Network/Transport | `allow tcp any any established` (permits packets belonging to established connections). |
| **ACL (Access Control List)** | Ordered list of permit/deny statements applied to interfaces. | Usually Layer 3 (IP) and Layer 4 (TCP/UDP). | `permit ip 10.0.0.0 0.0.255.255 any` - allows whole 10.0.0.0/16 subnet. |
| **Application-layer firewall** | Inspects payload, can block based on URL, HTTP method, etc. | Layer 7 (Application) | `deny http uri "/admin"` - blocks access to web admin pages. |

 Modern "Next-Gen" Firewalls
* Combine **deep-packet inspection**, **intrusion-prevention**, **URL filtering**, and **sandboxing** in a single appliance.  
* Frequently integrated into **cloud security groups** (AWS SG, Azure NSG) and **Kubernetes NetworkPolicy** objects.

---

 7️⃣ OSI Model - Layer-by-Layer Deep Dive <a name="osi"></a>

```
+---+-----------------------+-----------------------------------+
| 7 | Application           | HTTP, SMTP, DNS, SSH, TLS         |
| 6 | Presentation          | Data representation, encryption   |
| 5 | Session               | Dialog control, synchronization   |
| 4 | Transport             | TCP (reliable), UDP (unreliable)  |
| 3 | Network               | IP addressing, routing, subnetting|
| 2 | Data Link             | Ethernet frames, MAC addresses    |
| 1 | Physical              | Cables, fiber, radio, voltage     |
+---+-----------------------+-----------------------------------+
```

 Real-World Mapping

| OSI Layer | Common Protocol | Typical Device |
|-----------|----------------|----------------|
| 7 - Application | `HTTP`, `SSH`, `DNS`, `SMTP` | Web server, mail server |
| 6 - Presentation | `TLS`, `SSL` (encryption) | Load balancer, reverse proxy |
| 5 - Session | `NetBIOS`, RPC | Windows Server, SMB |
| 4 - Transport | `TCP`, `UDP` (ports) | OS networking stack |
| 3 - Network | `IP`, `ICMP`, `IPv6` | Router, L3 switch |
| 2 - Data Link | `Ethernet`, `802.1Q` (VLAN) | Switch, bridge |
| 1 - Physical | `RJ-45`, `Fiber`, `Wi-Fi` | NIC, transceiver |

Understanding the OSI stack is the key to **troubleshooting**: you isolate the problem to a layer (e.g., "I can ping (ICMP) but HTTP fails -> issue in Layer 7 or 4").

---

 8️⃣ Domain Names, DNS, and Resolution Mechanics <a name="dns"></a>

 8.1. Anatomy of a Fully-Qualified Domain Name (FQDN)

```
www.example.com.
│   │        │
│   │        └─ Top-Level Domain (TLD) - .com, .org, .net, country codes (.uk, .jp)
│   └─ Second-Level Domain - the "example" part, usually the brand
└─ Sub-domain - "www", "mail", "api", etc.
```

*The trailing dot `.` is the DNS root, rarely typed but part of the formal name.*

 8.2. DNS Resolution Process (step-by-step)

1. **Stub Resolver** (part of OS) receives the domain to resolve.  
2. It queries the **Recursive Resolver** (usually your ISP's DNS server).  
3. Recursive resolver checks its **cache**; if miss, it queries the **Root Server** (`a.root-servers.net`).  
4. Root server returns the **TLD name-server** for `.com`.  
5. TLD server returns the **Authoritative name-server** for `example.com`.  
6. Authoritative server returns the record(s) - typically an **A (IPv4) or AAAA (IPv6)** record.  
7. Recursive resolver caches the answer and sends it back to the stub resolver.

```
Client -> Recursive DNS -> Root -> .com TLD -> example.com Authoritative -> IP
```

 8.3. Record Types You'll See

| Type | Meaning | Example |
|------|---------|---------|
| **A** | IPv4 address | `example.com A 93.184.216.34` |
| **AAAA** | IPv6 address | `example.com AAAA 2606:2800:220:1:248:1893:25c8:1946` |
| **CNAME** | Alias (canonical name) | `www.example.com CNAME example.com` |
| **MX** | Mail Exchange - points to mail server | `example.com MX 10 mail.example.com` |
| **TXT** | Arbitrary text (often SPF/DKIM) | `example.com TXT "v=spf1 -all"` |
| **NS** | Name-server for a zone | `example.com NS ns1.provider.com` |
| **SRV** | Service location (used by SIP, LDAP) | `_sip._tcp.example.com SRV 10 60 5060 sipserver.example.com` |

 8.4. DNS Security Extensions (DNSSEC)
*Adds digital signatures to DNS records, preventing **cache poisoning** and **man-in-the-middle** attacks.*  
Deployments require signing zones with **private keys** and publishing **public keys** in the **parent zone** (e.g., `.com`).

---

 9️⃣ TLS/SSL, SSH, and Packet-Level Handshakes <a name="tls-ssh"></a>

 9.1. TLS Handshake (HTTPS)

```
ClientHello -> ServerHello -> Certificate -> ServerKeyExchange (optional)
-> CertificateRequest (optional) -> ServerHelloDone
<- ClientCertificate (optional) <- ClientKeyExchange <- CertificateVerify
<- ChangeCipherSpec <- Finished
-> ChangeCipherSpec -> Finished
```

* **Key exchange**: Usually **ECDHE** (Elliptic-Curve Diffie-Hellman) - provides *forward secrecy* (compromise of a long-term key does not reveal past sessions).  
* **Certificates**: X.509; signed by a **Certificate Authority (CA)**.  
* **Cipher suite**: Negotiates symmetric cipher (AES-GCM, ChaCha20-Poly1305), hash (SHA-256), and key-exchange method.

 9.2. SSH Handshake

1. **Version exchange** - both sides announce protocol version.  
2. **Key exchange** (Diffie-Hellman, Curve25519, ECDH) - derive a shared secret.  
3. **Host key verification** - client verifies the server's public key (`known_hosts`).  
4. **User authentication** - password, public-key, GSSAPI, or keyboard-interactive.  
5. **Channel request** - open a "session" channel, then execute commands or allocate a PTY.

*SSH encrypts *all* traffic (including X11 forwarding, SFTP, port forwarding).*

 9.3. Comparing TLS vs SSH

| Aspect | TLS (HTTPS) | SSH |
|--------|-------------|-----|
| Primary use | Secure web traffic, API endpoints. | Secure remote shell, admin tasks, tunneling. |
| Port | 443 (default) | 22 (default) |
| Authentication | X.509 certificates (server) + optionally client certs. | Host key + user credentials (password/key). |
| Forward secrecy | Mandatory with modern cipher suites. | Mandatory - always uses DH/ECDH. |

---

 🔟 Subnetting in Everyday Scenarios - "How to Easily Remember" <a name="subnet-mnemonics"></a>

| Subnet | Binary Mask (first octet) | Decimal Mask | Hosts | Mnemonic |
|--------|---------------------------|--------------|-------|----------|
| `/30` | `11111111.11111111.11111111.11111100` | `255.255.255.252` | 2 | "**Point-to-Point** - two ends, no broadcast." |
| `/29` | `...11111000` | `255.255.255.248` | 6 | "**Six** = small office." |
| `/28` | `...11110000` | `255.255.255.240` | 14 | "**Fourteen** = fourteen-person team." |
| `/27` | `...11100000` | `255.255.255.224` | 30 | "**Thirty** = 30-person lab." |
| `/26` | `...11000000` | `255.255.255.192` | 62 | "**Sixty-two** ~= 2 x 31 (two labs)." |
| `/25` | `...10000000` | `255.255.255.128` | 126 | "**One-hundred-twenty-six** -> half of a /24." |
| `/24` | `...00000000` | `255.255.255.0`   | 254 | "**Standard class C** - 254 host seats." |
| `/23` | `11111110.00000000` | `255.255.254.0`   | 510 | "**Double-size** - two /24s merged." |

**Quick mental cue**: *"The more zeros you see at the end of the mask, the more hosts you have."*  
E.g., `255.255.254.0` -> `00000000` (8 zeros) -> `2^8 = 256` per half-segment -> total `512` addresses (`510` usable).

**Subnet-calculator formula**:  
```
hosts_per_subnet = 2^(32 - prefix) - 2
netmask = (2^32 - 1) << (32 - prefix)  # binary left-shift, then convert to dotted decimal
```

---

 1️⃣1️⃣ Ports, Firewalls, and "Handshakes" - The Big Picture <a name="handshakes"></a>

| Concept | Where it Happens | Typical Port(s) | Handshake / State |
|---------|------------------|-----------------|-------------------|
| **HTTP** | Application Layer (7) - Web browsers, servers | 80 (HTTP), 443 (HTTPS) | TCP 3-way -> TLS handshake (if HTTPS). |
| **SSH** | Application Layer (7) - Remote admin | 22 | TCP 3-way -> SSH key exchange -> user auth. |
| **DNS** | Application Layer (7) - Name resolution | 53 (UDP, sometimes TCP) | UDP query/response (no handshake). |
| **SMTP** | Mail Transfer | 25 (plain), 465/587 (TLS) | TCP 3-way -> optional STARTTLS (cryptographic upgrade). |
| **TLS** | Transport (4) - Encryption wrapper | 443 (HTTPS), 22 (SSH uses its own), 993 (IMAPS) | TLS handshake (client-hello ... server-finished). |
| **RDP** | Remote Desktop | 3389 | TCP 3-way -> TLS (or CredSSP) handshake. |
| **IPsec** | Network (3) - VPN | 500, 4500 | IKE (Internet Key Exchange) handshake, then ESP/AH encapsulation. |

 How a **firewall rule** interacts with a handshake
1. **Inbound SYN** to port 22 -> firewall **accepts** (state = NEW).  
2. **Outbound SYN-ACK** -> firewall marks connection as **ESTABLISHED**.  
3. **Further packets** (ACK, data) -> automatically allowed because they belong to an ESTABLISHED flow (stateful inspection).  
If the firewall *denies* the SYN, the handshake never proceeds -> the client sees "connection timed out".

---

 1️⃣2️⃣ Networking Devices - Deep Dive <a name="devices"></a>

| Device | Core Function | OSI Layers | Modern Evolution |
|--------|---------------|------------|-------------------|
| **Router** | Routes IP packets between **different logical networks** (subnets). | 3 (Network) + 4 (Transport for ACLs) | Often includes built-in **firewall**, **NAT**, **VPN**, **DHCP** server. |
| **Layer-2 Switch** | Forwards Ethernet frames based on **MAC address** within a **single broadcast domain**. | 2 (Data Link) | Many support **VLANs** (802.1Q) to create *multiple* logical Layer-2 segments on a single physical device. |
| **Layer-3 Switch** (multilayer switch) | Performs **routing** between VLANs, still functions as a fast switching fabric. | 2 + 3 | Common in data-center spine-leaf designs. |
| **Bridge** | Connects two network segments, learns MAC addresses to avoid loops. | 2 | Deprecated in favor of switches. |
| **Access Point (AP)** | Provides **wireless (Wi-Fi)** connectivity, translates 802.11 frames to Ethernet. | 1-2 | Integrated into routers (home Wi-Fi) or stand-alone for enterprise. |
| **Load Balancer** | Distributes inbound connections across a pool of **backend servers** using algorithms (round-robin, least-connections, etc.). | 4-7 (Transport to Application) | Can be **L4 (TCP)** or **L7 (HTTP)**; popular software: HAProxy, NGINX, Envoy. |
| **Firewall (NGFW)** | Deep-packet inspection, intrusion detection/prevention, application awareness. | 3-7 | Often a **virtual appliance** running in the cloud. |
| **Proxy** | Intermediary that terminates client connections, forwards to server (caching, filtering). | 7 | Transparent vs. explicit proxies; used for web filtering or content acceleration. |
| **IDS/IPS** | Detects (and optionally blocks) malicious traffic. | 4-7 | Signature-based or behavior-based; often built into NGFWs. |
| **Router-Firewall Combo** | The **home router** you buy off the shelf: one device handling NAT, DHCP, WIFI, and a basic stateful firewall. | 1-4 (plus optional 7) | Shows the *convergence* trend: many formerly separate appliances now live on a single chassis. |

**Historical note**: In the early 1990s, you needed **four separate boxes** (router, switch, firewall, IDS) to build a secure corporate network. Today, a single *virtual* appliance in a cloud VPC can provide routing, firewalling, load balancing, and IDS in one place.

---

 1️⃣3️⃣ Kubernetes Networking - The Full Picture <a name="k8s"></a>

| Component | Role | IP Range (typical) | Interaction |
|-----------|------|-------------------|-------------|
| **Pod CIDR** | Allocates a unique IP to every Pod. | `10.244.0.0/16` (Flannel) or `192.168.0.0/16` (Calico) | Pods talk to each other directly (no NAT). |
| **Service CIDR** | Virtual IPs (`ClusterIP`) that expose a Service to the cluster. | `10.96.0.0/12` (default) | kube-proxy rewrites `ClusterIP` -> one of the Service's backing Pod IPs. |
| **kube-proxy** | Installs **iptables** (or **IPVS**) rules on each node to implement Service load-balancing. | N/A | Translates incoming Service traffic to the appropriate Pod endpoint. |
| **CNI plugins** | (Calico, Flannel, Cilium...) provide the underlying network fabric. | Varies per plugin (Calico uses BGP, Flannel uses overlay). | Provides the *flat* networking model Kubernetes expects. |
| **NetworkPolicy** | Declarative *firewall* at the Pod level. | N/A | Enforces which Pods can talk to which, based on namespaces, labels, ports. |
| **Ingress Controller** | Exposes HTTP(S) Services outside the cluster, often with a **LoadBalancer** service. | Typically uses `NodePort` or external LB IP. | Handles TLS termination, path-based routing. |

 Packet Flow Example - Pod -> External Service
1. **Pod** sends packet to `8.8.8.8:53` (DNS).  
2. Packet leaves Pod with its own Pod IP as source, passes through the **veth** pair into the node's **bridge**.  
3. **iptables NAT MASQUERADE** rewrites source IP to the node's external IP.  
4. Packet travels out through the node's **router** (or cloud VPC router) to the internet.  
5. Return traffic is NAT-translated back to the Pod IP and delivered via the same bridge.

 "Why no NAT between Pods?"
Kubernetes promises **pod-to-pod** connectivity without NAT to keep latency low and simplify network policies. All Pods share a common routing table that knows how to reach any other Pod CIDR.

---

 1️⃣4️⃣ Virtual Machines vs. Containers - IP Allocation & Access <a name="vm-container"></a>

| Feature | Virtual Machine (VM) | Docker Container |
|---------|----------------------|------------------|
| **Isolation level** | Full hardware virtualisation (hypervisor) -> separate kernel. | OS-level namespaces + cgroups -> shared kernel. |
| **IP address** | Usually assigned a **virtual NIC**; appears as a distinct host on the LAN (e.g., `192.168.1.101`). | By default uses **Docker bridge** (`172.17.0.0/16`). Can be placed on the **host network** (`--network=host`) to share the host's IP. |
| **SSH access** | `ssh user@<VM-IP>` on port 22 (or custom). | Not typical; you `docker exec -it <container> /bin/bash` or expose SSH inside the container (`-p 2222:22`). |
| **Port mapping** | NAT (port forwarding) on the host, or direct bridging. | `docker run -p <hostPort>:<containerPort>` maps host port to container port. |
| **Boot time** | Seconds to minutes (kernel boot). | Milliseconds (just start a process). |
| **Use-case** | Run multiple OSes, strong isolation. | Micro-service workloads, fast dev cycles. |

**Accessing a VM**: Usually via **SSH (port 22)** or **RDP (port 3389)** if it's a Windows VM. The VM's network interface can be **bridged** (gets its own IP on the physical LAN) or **NATed** (shares host IP, uses port forwarding).

**Accessing a container**: Through **exposed ports** (e.g., `-p 8080:80`) or **Docker network overlay** (Swarm/K8s) that assigns a unique IP inside the overlay network.

---

 1️⃣5️⃣ How This All Fits Into a DevOps Engineer's Toolbox <a name="devops"></a>

| Skill | Why It Matters | Typical Tool |
|-------|----------------|--------------|
| **IP planning & subnetting** | Enables efficient address use, reduces broadcast storms, prepares for scaling. | `ipcalc`, `subnetcalc`, AWS VPC CIDR calculators. |
| **DNS management** | Controls service discovery, SSL certificate issuance (via ACME DNS-01), routing of traffic. | `bind9`, `CoreDNS`, `Route53`, `kubectl edit configmap coredns`. |
| **TLS/SSL automation** | Secures traffic, enables zero-trust pipelines. | `certbot`, `letsencrypt`, `HashiCorp Vault PKI`. |
| **SSH key management** | Provides secure, password-less access to VMs, containers, and bastion hosts. | `ssh-keygen`, `ssh-agent`, `ansible` *SSH* module, `ssh-config`. |
| **Infrastructure as Code (IaC)** | Declares networking (VPCs, subnets, security groups) in version-controlled files. | `Terraform`, `AWS CloudFormation`, `Azure ARM`, `Pulumi`. |
| **Container orchestration** | Handles service discovery, overlay networking, load balancing. | `Kubernetes` (CNI plugins, Service CIDR, NetworkPolicy), `Docker Swarm`. |
| **CI/CD pipelines** | Must trigger builds, push images, and apply Kubernetes manifests. | `GitHub Actions`, `GitLab CI`, `Jenkins`, `Argo CD`. |
| **Monitoring & Observability** | Captures network latency, packet loss, firewall hits. | `Prometheus` + `node_exporter` (network metrics), `Grafana`, `ELK` stack, `Jaeger` (tracing). |
| **Security scanning** | Detects open ports, mis-configured firewalls, vulnerable services. | `nmap`, `OpenVAS`, `tfsec`, `kube-audit`, `AWS Inspector`. |

A **DevOps engineer** constantly flips between **infrastructure provisioning**, **application deployment**, **security hardening**, and **observability**--all of which rely heavily on the networking concepts covered above.

---

 1️⃣6️⃣ Appendix - Diagrams & Image Sources <a name="appendix"></a>

| Diagram | Description | Suggested URL (download & place in `assets/`) |
|--------|-------------|----------------------------------------------|
| `k8s_network.png` | Flat Kubernetes pod network with Service CIDR, kube-proxy, CNI. | https://raw.githubusercontent.com/kubernetes/website/main/content/en/images/docs/concepts/cluster/networking.png |
| `dns_flow.png` | Full DNS resolution flow (root -> TLD -> authoritative). | https://www.cloudflare.com/img/learning/dns/dns-overview/dns-overview-diagram.svg |
| `cidr_chart.png` | Visual table of CIDR prefixes and host counts. | https://www.ipcalc.net/images/cidr-table.png |
| `osi_layers.png` | Classic OSI 7-layer diagram. | https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/OSI_Model.png/800px-OSI_Model.png |
| `subnet_example.png` | Example of dividing a /16 into /24 subnets with a diagram. | https://i.stack.imgur.com/5xqZb.png |
| `firewall_stateful.png` | Stateful firewall flow diagram (NEW -> ESTABLISHED). | https://www.cisco.com/c/en/us/td/docs/security/firepower/630/firepower-system-management/configuration/guide/fpm-630-sys-mgmt-config/figures/fpm_stateful_firewall.png |
| `ssh_handshake.png` | SSH key-exchange and authentication steps. | https://i.stack.imgur.com/l3P2N.png |
| `tls_handshake.png` | TLS 1.2 handshake message diagram. | https://tls13.ulfheim.net/tls13_handshake.png |
| `router_vs_switch.png` | Router vs. switch responsibilities (Layer 3 vs. Layer 2). | https://www.networkworld.com/wp-content/uploads/2020/05/router-switch-800x450.png |
| `vm_vs_container.png` | Comparison table graphic (VM vs. Container). | https://i.stack.imgur.com/aB9Xy.png |

\"\"\" ,
""" ,
           "hi": """<h2 style=\"font-size:20px;color:#2b6cb0;\">Software Engineering Concepts</h2>

<h3 style=\"font-size:18px;\">N+1 Query Problem</h3>
<p>The N+1 problem occurs when an application executes one query to retrieve a list of items (N) and then, for each item, executes an additional query (1) to fetch related data. This results in N+1 queries, causing performance degradation.</p>
<p><strong>Why it matters</strong></p>
<ul>
<li>Extra round-trips to the database.</li>
<li>High latency, especially over networked DBs.</li>
<li>Exhausts connection pools.</li>
</ul>
<p><strong>How to fix it</strong></p>
<ol>
<li>Eager loading - join related tables in a single query (<code>SELECT ... FROM parent JOIN child ...</code>).</li>
<li>Batch fetching - retrieve all related records in one additional query using <code>WHERE parent_id IN (...) </code>.</li>
<li>Use ORM helpers - e.g., Django's <code>select_related</code>/<code>prefetch_related</code>, SQLAlchemy's <code>joinedload</code>.</li>
<li>Cache results - memoize repeated look-ups when data is immutable.</li>
</ol>
<pre><code># Example with SQLAlchemy eager loading
session.query(User).options(joinedload(User.posts)).all()
</code></pre>

<h3 style=\"font-size:18px;\">Design Patterns</h3>
<h4 style=\"font-size:16px;\">MVC (Model-View-Controller)</h4>
<ul>
<li><strong>Model</strong> - business data and rules.</li>
<li><strong>View</strong> - UI representation.</li>
<li><strong>Controller</strong> - handles input, updates model, selects view.</li>
</ul>
<h4 style=\"font-size:16px;\">MVC2 (Model-View-Presenter)</h4>
<ul>
<li><strong>Presenter</strong> replaces Controller, pulls data from Model and formats for View.</li>
<li>View is passive; Presenter updates it.</li>
</ul>
<h4 style=\"font-size:16px;\">DAO (Data Access Object)</h4>
<ul>
<li>Abstracts persistence layer.</li>
<li>Provides CRUD methods (<code>create</code>, <code>read</code>, <code>update</code>, <code>delete</code>).</li>
</ul>
<h4 style=\"font-size:16px;\">Service Layer</h4>
<ul><li>Encapsulates business logic, calls DAOs.</li></ul>
<h4 style=\"font-size:16px;\">Repository</h4>
<ul><li>Collection-oriented facade over DAOs, supports domain-driven design.</li></ul>
<h4 style=\"font-size:16px;\">Factory &amp; Abstract Factory</h4>
<ul><li>Centralises object creation, hides concrete classes.</li></ul>
<h4 style=\"font-size:16px;\">Singleton</h4>
<ul><li>One-instance global access (use sparingly).</li></ul>

<h3 style=\"font-size:18px;\">Layered Architecture</h3>
<pre><code>Presentation (UI) -> Service -> Repository/DAO -> Domain -> Persistence (DB)
</code></pre>

<h3 style=\"font-size:18px;\">Best Practices</h3>
<ul>
<li><strong>Folder layout</strong>: <code>src/</code>, <code>tests/</code>, <code>configs/</code>, <code>scripts/</code>, <code>docs/</code>.</li>
<li><strong>Environment files</strong>: store secrets in <code>.env</code>, load with <code>python-dotenv</code>.</li>
<li><strong>Config separation</strong>: <code>config/dev.py</code>, <code>config/prod.py</code>.</li>
<li><strong>Logging</strong>: use <code>logging</code> module with rotating file handlers.</li>
<li><strong>Typing</strong>: annotate functions for clarity.</li>
<li><strong>Dependency injection</strong>: pass collaborators via constructor.</li>
</ul>

<h3 style=\"font-size:18px;\">HTTP Status Codes (complete list)</h3>
<pre><code>1xx - Informational: 100 Continue, 101 Switching Protocols
2xx - Success: 200 OK, 201 Created, 202 Accepted, 204 No Content
3xx - Redirection: 301 Moved Permanently, 302 Found, 304 Not Modified
4xx - Client Error: 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 429 Too Many Requests
5xx - Server Error: 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout
</code></pre>

<h3 style=\"font-size:18px;\">REST API</h3>
<ul>
<li><strong>Stateless</strong> HTTP verbs (<code>GET</code>, <code>POST</code>, <code>PUT</code>, <code>PATCH</code>, <code>DELETE</code>).</li>
<li><strong>Resources</strong> identified by URLs.</li>
<li><strong>Representations</strong> usually JSON.</li>
</ul>
<pre><code>import flask
app = flask.Flask(__name__)

@app.route("/users", methods=["GET"])
def list_users():
    return flask.jsonify([...])
</code></pre>

<h3 style=\"font-size:18px;\">GraphQL</h3>
<ul>
<li>Single endpoint, client-specified queries.</li>
<li>Allows fetching exactly what is needed.</li>
</ul>
<pre><code>import graphene

class Query(graphene.ObjectType):
    hello = graphene.String(name=graphene.String(default_value="World"))
    def resolve_hello(root, info, name):
        return f"Hello {name}"

schema = graphene.Schema(query=Query)
</code></pre>
"""


# The N+1 problem occurs when an application executes one query to retrieve a list of items (N) and then, for each item, executes an additional query (1) to fetch related data. This results in N+1 queries, causing performance degradation.

# **Why it matters**
# - Extra round‑trips to the database.
# - High latency, especially over networked DBs.
# - Exhausts connection pools.

# **How to fix it**
# 1. **Eager loading** – join related tables in a single query (`SELECT … FROM parent JOIN child …`).
# 2. **Batch fetching** – retrieve all related records in one additional query using `WHERE parent_id IN (…)`.
# 3. **Use ORM helpers** – e.g., Django’s `select_related` / `prefetch_related`, SQLAlchemy’s `joinedload`.
# 4. **Cache results** – memoize repeated look‑ups when data is immutable.

# ```python
# Example with SQLAlchemy eager loading
# session.query(User).options(joinedload(User.posts)).all()
# ```

## 🏗️ Design Patterns

### MVC (Model‑View‑Controller)
# - **Model** – business data and rules.
# - **View** – UI representation.
# - **Controller** – handles input, updates model, selects view.

### MVC2 (Model‑View‑Presenter)
# - **Presenter** replaces Controller, pulls data from Model and formats for View.
# - View is passive; Presenter updates it.

### DAO (Data Access Object)
# - Abstracts persistence layer.
# - Provides CRUD methods (`create`, `read`, `update`, `delete`).

### Service Layer
# - Encapsulates business logic, calls DAOs.

### Repository
# - Collection‑oriented façade over DAOs, supports domain‑driven design.

### Factory & Abstract Factory
# - Centralises object creation, hides concrete classes.

### Singleton
# - One‑instance global access (use sparingly).

## 📂 Layered Architecture
# ```
# Presentation (UI) → Service → Repository/DAO → Domain → Persistence (DB)
# ```
# - Each layer only talks to the layer directly beneath it.
# - Improves testability and separation of concerns.

## 🛠️ Best Practices
# - **Folder layout**: `src/`, `tests/`, `configs/`, `scripts/`, `docs/`.
# - **Environment files**: store secrets in `.env`, load with `python-dotenv`.
# - **Config separation**: `config/dev.py`, `config/prod.py`.
# - **Logging**: use `logging` module with rotating file handlers.
# - **Typing**: annotate functions for clarity.
# - **Dependency injection**: pass collaborators via constructor.

## 🌐 HTTP Status Codes (complete list)
# ```
# 1xx – Informational: 100 Continue, 101 Switching Protocols
# 2xx – Success: 200 OK, 201 Created, 202 Accepted, 204 No Content
# 3xx – Redirection: 301 Moved Permanently, 302 Found, 304 Not Modified
# 4xx – Client Error: 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 429 Too Many Requests
# 5xx – Server Error: 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout
# ```

## 📡 REST API
# - **Stateless** HTTP verbs (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`).
# - **Resources** identified by URLs.
# - **Representations** usually JSON.

# ```python
# import flask
# app = flask.Flask(__name__)

# @app.route("/users", methods=["GET"])
# def list_users():
#     return flask.jsonify([...])
# ```

## 🧩 GraphQL (instead of “respul and gorc”)
# - Single endpoint, client‑specified queries.
# - Allows fetching exactly what is needed.

# ```python
# import graphene

# class Query(graphene.ObjectType):
#     hello = graphene.String(name=graphene.String(default_value="World"))
#     def resolve_hello(root, info, name):
#         return f"Hello {name}"

# schema = graphene.Schema(query=Query)
# ```
# """
        }
        # Replace the short placeholder entries with the full guides.
        self.docs.update(EXTRA_DOCS)
        self.bind("<Configure>", self.update_responsive_layout)
        self.select_category("Dashboard")
    # ------------------------------------------------------------------
    def select_category(self, cat):
        self.header.configure(text=cat)
        self.manifest_combo = None
        self.yaml_file_combos = []
        self.service_combo = None
        self.service_options = []
        if self.category_picker.get() != cat:
            self.category_picker.set(cat)
        for w in self.actions.winfo_children():
            # PortManagerFrame.destroy cancels its auto-refresh timer first.
            w.destroy()
        self.ports_tree = None
        self.ports_frame = None
        self.display_documentation(cat, self.docs.get(cat, f"Details for {cat} will appear here."))
        self.cmd_preview.delete(0, ctk.END)
        if cat == "Dashboard":
            self.display_documentation("Dashboard", "Welcome! Use the shortcuts below to inspect your Kubernetes cluster, including complete and wide resource views.")
            self.add_cmd_button("Cluster Info", "kubectl cluster-info")
            self.add_cmd_button("Get All Resources", "kubectl get all")
            self.add_cmd_button("Get All Resources (Wide)", "kubectl get all -o wide")
            self.add_cmd_button("Get All Namespaces", "kubectl get all --all-namespaces")
            self.add_cmd_button("Get All Namespaces (Wide)", "kubectl get all --all-namespaces -o wide")
# Removed duplicate Dashboard handling (self.doc was undefined)
# self.doc reference removed (was undefined)
        elif cat == "Docker":
            self.add_cmd_button("List Containers", "docker ps -a")
            self.add_cmd_button("List Images", "docker images")
            self.add_custom_input()
        elif cat == "Minikube/Kind":
            self.add_cmd_button("Start Minikube", "minikube start")
            self.add_cmd_button("Start Kind", "kind create cluster")
            self.add_cmd_button("Cluster Info", "kubectl cluster-info")
            self.add_service_url_tools()
        elif cat == "Pods":
            self.add_yaml_apply()
            self.add_list_ui("kubectl get pods -A", "Pod")
        elif cat == "Deployments":
            self.add_yaml_apply()
            self.add_list_ui("kubectl get deployments -A", "Deployment")
        elif cat == "Services":
            self.add_yaml_apply()
            self.add_list_ui("kubectl get services -A", "Service")
        elif cat == "ReplicaSets":
            self.add_yaml_apply()
            self.add_list_ui("kubectl get rs -A", "ReplicaSet")
        elif cat == "StatefulSets":
            self.add_yaml_apply()
            self.add_list_ui("kubectl get statefulsets -A", "StatefulSet")
        elif cat == "Volumes & PVC":
            self.add_yaml_apply()
            self.add_list_ui("kubectl get pvc -A", "PVC")
        elif cat in ["MySQL", "Postgres", "MongoDB"]:
            devops_tools.add_database_tools(self, cat)
        elif cat == "CI/CD & GitHub Actions":
            devops_tools.add_cicd_tools(self)
        elif cat == "GitHub":
            devops_tools.add_github_tools(self)
        elif cat == "Jenkins":
            devops_tools.add_jenkins_tools(self)
        elif cat == "Terraform":
            devops_tools.add_terraform_tools(self)
        elif cat == "Ansible":
            devops_tools.add_ansible_tools(self)
        elif cat == "Port Manager":
            devops_tools.add_port_manager(self)
        elif cat == "Custom":
            self.add_custom_input()
        else:
            self.add_yaml_apply()
    # ------------------------------------------------------------------
    def display_documentation(self, title, content):
        """Render lessons as a readable, syntax-coloured in-app guide."""
        self.doc_text.configure(state="normal")
        self.doc_text.delete("1.0", "end")
        self.doc_text.insert("end", f"{title}\n", "title")
        for raw_line in content.splitlines():
            line = re.sub(r"<[^>]+>", "", raw_line).strip()
            line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
            # Measure indentation before stripping, otherwise indented
            # commands such as "    terraform init" lose their colour.
            indented = len(raw_line) - len(raw_line.lstrip()) >= 4
            if not line:
                self.doc_text.insert("end", "\n")
            elif line.startswith(("Key ", "Important ", "Common ", "Typical ", "Types:", "Key concepts:", "Key fields:")) or line.endswith(":"):
                self.doc_text.insert("end", f"{line}\n", "heading")
            elif line.startswith(("- ", "• ")):
                self.doc_text.insert("end", f"• {line[2:]}\n", "bullet")
            elif line.startswith(COMMAND_PREFIXES) or indented:
                self.doc_text.insert("end", f"{line}\n", "command")
            else:
                self.doc_text.insert("end", f"{line}\n")
        self.doc_text.configure(state="disabled")

    def update_responsive_layout(self, event):
        """Keep navigation available when the app is used in a narrow window."""
        if event.widget is not self:
            return
        use_compact = event.width < 900
        if use_compact == self.compact_layout:
            self.resize_terminal(event.height)
            return
        self.compact_layout = use_compact
        if use_compact:
            self.sidebar.grid_remove()
            self.main.grid_configure(column=0, padx=8, pady=8)
            self.category_picker.configure(width=145)
            self.cmd_preview.configure(width=280)
            self.work_dir_entry.configure(width=280)
            self.doc_text.configure(height=4)
            self.cmd_preview.grid_configure(row=2, column=0, columnspan=2, padx=12, sticky="ew")
            self.ext_btn.grid_configure(row=3, column=0, columnspan=2, padx=12, sticky="w")
            self.work_dir_label.grid_configure(row=4, column=0, columnspan=2, padx=12, sticky="w")
            self.work_dir_entry.grid_configure(row=5, column=0, columnspan=2, padx=12, sticky="ew")
            self.actions.grid_configure(row=6, column=0, columnspan=2, padx=12, sticky="nsew")
            self.terminal.grid_configure(row=7, column=0, columnspan=2, padx=12, sticky="nsew")
            self.terminal.set_output_collapsed(True)
        else:
            self.sidebar.grid()
            self.main.grid_configure(column=1, padx=20, pady=20)
            self.category_picker.configure(width=190)
            self.cmd_preview.configure(width=800)
            self.work_dir_entry.configure(width=600)
            self.doc_text.configure(height=7)
            self.cmd_preview.grid_configure(row=2, column=0, columnspan=1, padx=20, sticky="w")
            self.ext_btn.grid_configure(row=2, column=1, columnspan=1, padx=10, sticky="w")
            self.work_dir_label.grid_configure(row=3, column=0, columnspan=1, padx=20, sticky="w")
            self.work_dir_entry.grid_configure(row=3, column=1, columnspan=1, padx=20, sticky="ew")
            self.actions.grid_configure(row=4, column=0, columnspan=2, padx=20, sticky="nsew")
            self.terminal.grid_configure(row=5, column=0, columnspan=2, padx=20, sticky="nsew")
        self.configure_content_rows(self.terminal.output_collapsed)
        self.resize_terminal(event.height)
        active_category = self.header.cget("text")
        if active_category:
            self.after_idle(lambda category=active_category: self.select_category(category))

    def configure_content_rows(self, output_collapsed):
        """Give section controls the remaining space and scroll them when needed."""
        actions_row = 6 if self.compact_layout else 4
        for row in range(8):
            self.main.grid_rowconfigure(row, weight=0)
        self.main.grid_rowconfigure(actions_row, weight=1)
        if not output_collapsed:
            self.resize_terminal(self.winfo_height())

    def resize_terminal(self, window_height):
        """Scale visible output without allowing it to crowd out section controls."""
        if self.terminal.output_collapsed:
            return
        height = max(150, min(290, int(window_height * 0.40)))
        self.terminal.configure(height=height)

    def run_cmd(self, cmd, callback=None, open_external=True):
        self.terminal.clear()
        print(f"> {cmd}")
        self.terminal.append_output(f"> {cmd}\n")
        self.cmd_preview.delete(0, ctk.END)
        self.cmd_preview.insert(0, cmd)
        if open_external:
            self.run_in_external_terminal(cmd)
        def task():
            try:
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=self.work_dir_entry.get())
                out = []
                for line in proc.stdout:
                    self.after(0, self.terminal.append_output, line)
                    out.append(line)
                proc.wait()
                if callback:
                    self.after(0, callback, "".join(out))
            except Exception as e:
                self.after(0, self.terminal.append_output, f"\nError: {e}\n")
        threading.Thread(target=task, daemon=True).start()
    # ------------------------------------------------------------------
    def run_in_external_terminal(self, cmd):
        """Launch the command in a new interactive Windows terminal."""
        try:
            # /k keeps the result visible; cwd avoids fragile cmd.exe quote handling.
            directory = os.path.abspath(os.path.expanduser(self.work_dir_entry.get().strip()))
            subprocess.Popen(["cmd.exe", "/k", cmd], cwd=directory)
        except Exception as e:
            self.terminal.append_output(f"\nError launching external terminal: {e}\n")
    def add_cmd_button(self, label, cmd):
        btn = ctk.CTkButton(self.actions, text=label, command=lambda: self.run_cmd(cmd))
        btn.pack(pady=4, anchor="w", padx=5)
    def add_custom_input(self):
        frm = ctk.CTkFrame(self.actions, fg_color="transparent")
        frm.pack(pady=8, fill="x", anchor="w", padx=5)
        ctk.CTkLabel(frm, text="Custom command:").pack(side="left", padx=5)
        entry = ctk.CTkEntry(frm, placeholder_text="e.g. docker inspect <container>", width=400)
        entry.pack(side="left", padx=5)
        ctk.CTkButton(frm, text="Run", command=lambda: self.run_cmd(entry.get())).pack(side="left", padx=5)

    def add_service_url_tools(self):
        """Offer service URLs without requiring users to type service or port names."""
        frm = ctk.CTkFrame(self.actions)
        frm.pack(pady=8, fill="x", anchor="w", padx=5)
        ctk.CTkLabel(frm, text="Service launcher:").grid(row=0, column=0, columnspan=2, padx=8, pady=(6, 2), sticky="w")
        self.service_combo = ctk.CTkComboBox(frm, values=["(fetching services...)"], width=360)
        self.service_combo.grid(row=1, column=0, columnspan=2, padx=8, pady=2, sticky="ew")
        refresh = ctk.CTkButton(frm, text="Refresh Services", command=lambda: self.fetch_service_options(True))
        minikube = ctk.CTkButton(frm, text="Open with Minikube", command=self.open_minikube_service)
        kind = ctk.CTkButton(frm, text="Open Kind NodePort", command=self.open_kind_nodeport)
        if self.compact_layout:
            refresh.grid(row=2, column=0, columnspan=2, padx=8, pady=2, sticky="ew")
            minikube.grid(row=3, column=0, columnspan=2, padx=8, pady=2, sticky="ew")
            kind.grid(row=4, column=0, columnspan=2, padx=8, pady=(2, 8), sticky="ew")
        else:
            refresh.grid(row=2, column=0, padx=(8, 4), pady=(2, 8), sticky="ew")
            minikube.grid(row=2, column=1, padx=(4, 8), pady=(2, 8), sticky="ew")
            kind.grid(row=3, column=0, columnspan=2, padx=8, pady=(0, 8), sticky="ew")
        frm.grid_columnconfigure(0, weight=1)
        frm.grid_columnconfigure(1, weight=1)
        self.after_idle(self.fetch_service_options)

    def fetch_service_options(self, open_external=False):
        if not self.service_combo:
            return

        def on_done(output):
            services = []
            for line in output.strip().splitlines():
                parts = line.split()
                if len(parts) < 7 or parts[0] == "NAMESPACE":
                    continue
                namespace, name, service_type, ports = parts[0], parts[1], parts[2], parts[-2]
                node_port = next(iter(re.findall(r":(\d+)/(?:TCP|UDP|SCTP)", ports)), None)
                display = f"{namespace}/{name}  |  {service_type}  |  {ports}"
                services.append({"display": display, "namespace": namespace, "name": name, "node_port": node_port})
            self.service_options = services
            values = [service["display"] for service in services] or ["(no services found)"]
            self.service_combo.configure(values=values)
            self.service_combo.set(values[0])

        self.run_cmd("kubectl get services --all-namespaces --no-headers", on_done, open_external=open_external)

    def selected_service(self):
        if not self.service_combo:
            return None
        selected = self.service_combo.get()
        for service in self.service_options:
            if service["display"] == selected:
                return service
        self.terminal.append_output("\nChoose a service from the dropdown first.\n", tag="warning")
        return None

    def open_minikube_service(self):
        service = self.selected_service()
        if not service:
            return

        def open_url(output):
            match = re.search(r"https?://[^\s]+", output)
            if not match:
                self.terminal.append_output("\nMinikube did not return a service URL.\n", tag="warning")
                return
            url = match.group(0)
            self.terminal.append_output(f"\nOpening {url} in your default browser.\n", tag="info")
            webbrowser.open(url)

        self.run_cmd(f'minikube service "{service["name"]}" --namespace "{service["namespace"]}" --url', open_url)

    def open_kind_nodeport(self):
        service = self.selected_service()
        if not service:
            return
        if not service["node_port"]:
            self.terminal.append_output("\nThis service has no NodePort. Choose a service whose type is NodePort.\n", tag="warning")
            return
        url = f'http://localhost:{service["node_port"]}'

        def open_url(_output):
            self.terminal.append_output(f"\nOpening {url} in your default browser.\n", tag="info")
            webbrowser.open(url)

        self.run_cmd(f'kubectl get service "{service["name"]}" --namespace "{service["namespace"]}"', open_url)
    def add_yaml_apply(self):
        frm = ctk.CTkFrame(self.actions)
        frm.pack(pady=8, fill="x", anchor="w", padx=5)
        ctk.CTkLabel(frm, text="YAML files in the Working Directory:").grid(row=0, column=0, columnspan=2, padx=8, pady=(6, 2), sticky="w")
        file_combo = ctk.CTkComboBox(frm, values=["(loading files...)"], width=340)
        file_combo.grid(row=1, column=0, columnspan=2, padx=8, pady=2, sticky="ew")
        refresh = ctk.CTkButton(frm, text="Refresh YAML Files", command=self.refresh_manifest_files)
        create = ctk.CTkButton(frm, text="Create New YAML", command=self.open_yaml_editor)
        edit = ctk.CTkButton(frm, text="Edit Selected YAML", command=lambda: self.edit_yaml_from_combo(file_combo))
        delete = ctk.CTkButton(frm, text="Delete Selected YAML", fg_color="#a93226", hover_color="#7b241c", command=lambda: self.delete_yaml_from_combo(file_combo))
        apply = ctk.CTkButton(frm, text="Apply Selected YAML", command=lambda: self.apply_yaml_from_combo(file_combo))
        if self.compact_layout:
            refresh.grid(row=2, column=0, columnspan=2, padx=8, pady=2, sticky="ew")
            create.grid(row=3, column=0, columnspan=2, padx=8, pady=2, sticky="ew")
            edit.grid(row=4, column=0, columnspan=2, padx=8, pady=2, sticky="ew")
            delete.grid(row=5, column=0, columnspan=2, padx=8, pady=2, sticky="ew")
            apply.grid(row=6, column=0, columnspan=2, padx=8, pady=(2, 8), sticky="ew")
        else:
            refresh.grid(row=2, column=0, padx=(8, 4), pady=2, sticky="ew")
            create.grid(row=2, column=1, padx=(4, 8), pady=2, sticky="ew")
            edit.grid(row=3, column=0, padx=(8, 4), pady=2, sticky="ew")
            delete.grid(row=3, column=1, padx=(4, 8), pady=2, sticky="ew")
            apply.grid(row=4, column=0, columnspan=2, padx=8, pady=(2, 8), sticky="ew")
        frm.grid_columnconfigure(0, weight=1)
        frm.grid_columnconfigure(1, weight=1)
        self.yaml_file_combos.append(file_combo)
        self.refresh_manifest_files()
    def add_list_ui(self, list_cmd, kind):
        self.last_kind = kind.lower()
        frm = ctk.CTkFrame(self.actions)
        frm.pack(pady=8, fill="x", anchor="w", padx=5)
        list_button = ctk.CTkButton(frm, text=f"List {kind}s", command=lambda: self.fetch_items(list_cmd))
        wide_button = ctk.CTkButton(frm, text="List Wide View", command=lambda: self.fetch_items(f"{list_cmd} -o wide"))
        self.item_combo = ctk.CTkComboBox(frm, values=["(fetch first)"], width=250)
        describe_button = ctk.CTkButton(frm, text="Describe Selected", command=lambda: self.kubectl_action("describe"))
        delete_button = ctk.CTkButton(frm, text="Delete", fg_color="red", hover_color="darkred", command=lambda: self.kubectl_action("delete"))
        log_button = ctk.CTkButton(frm, text="View Logs", command=lambda: self.kubectl_action("logs")) if kind == "Pod" else None
        if self.compact_layout:
            list_button.grid(row=0, column=0, columnspan=2, padx=8, pady=(6, 2), sticky="ew")
            wide_button.grid(row=1, column=0, columnspan=2, padx=8, pady=2, sticky="ew")
            self.item_combo.grid(row=2, column=0, columnspan=2, padx=8, pady=2, sticky="ew")
            describe_button.grid(row=3, column=0, columnspan=2, padx=8, pady=2, sticky="ew")
            delete_button.grid(row=4, column=0, columnspan=2, padx=8, pady=(2, 6), sticky="ew")
            if log_button:
                log_button.grid(row=5, column=0, columnspan=2, padx=8, pady=(2, 8), sticky="ew")
        else:
            list_button.grid(row=0, column=0, padx=(8, 4), pady=(6, 2), sticky="ew")
            wide_button.grid(row=0, column=1, padx=(4, 8), pady=(6, 2), sticky="ew")
            self.item_combo.grid(row=1, column=0, columnspan=2, padx=8, pady=2, sticky="ew")
            describe_button.grid(row=2, column=0, padx=(8, 4), pady=(2, 8), sticky="ew")
            delete_button.grid(row=2, column=1, padx=(4, 8), pady=(2, 8), sticky="ew")
            if log_button:
                log_button.grid(row=3, column=0, columnspan=2, padx=8, pady=(0, 8), sticky="ew")
        frm.grid_columnconfigure(0, weight=1)
        frm.grid_columnconfigure(1, weight=1)
        # number selection
        num_frm = ctk.CTkFrame(self.actions, fg_color="transparent")
        num_frm.pack(pady=4, fill="x", anchor="w", padx=5)
        ctk.CTkLabel(num_frm, text="Pick #:").pack(side="left", padx=5)
        self.num_entry = ctk.CTkEntry(num_frm, width=60, placeholder_text="2")
        self.num_entry.pack(side="left", padx=5)
        ctk.CTkButton(num_frm, text="Select", command=self.select_by_number).pack(side="left", padx=5)
    def fetch_items(self, cmd):
        def on_done(output):
            lines = output.strip().split('\n')
            if len(lines) <= 1:
                self.item_combo.configure(values=["(no items)"])
                self.item_combo.set("(no items)")
                self.last_items = []
                return
            header = lines[0].split()
            has_ns = "NAMESPACE" in header
            items = []
            self.last_items = []
            for idx, line in enumerate(lines[1:], start=1):
                parts = line.split()
                if not parts:
                    continue
                if has_ns:
                    ns, name = parts[0], parts[1]
                    display = f"{idx}) {ns}/{name}"
                    self.last_items.append((ns, name))
                else:
                    name = parts[0]
                    display = f"{idx}) {name}"
                    self.last_items.append(("", name))
                items.append(display)
            self.item_combo.configure(values=items)
            if items:
                self.item_combo.set(items[0])
        self.run_cmd(cmd, on_done)
    def add_yaml_editor_launcher(self):
        frm = ctk.CTkFrame(self.actions, fg_color="transparent")
        frm.pack(pady=8, fill="x", anchor="w", padx=5)
        ctk.CTkButton(frm, text="Create YAML File", command=self.open_yaml_editor).pack(side="left", padx=5)
        ctk.CTkLabel(frm, text="Files save to the Working Directory.").pack(side="left", padx=8)

    def add_manifest_browser(self):
        """Show YAML manifests found in the current working directory."""
        frm = ctk.CTkFrame(self.actions)
        frm.pack(pady=8, fill="x", anchor="w", padx=5)
        ctk.CTkLabel(frm, text="YAML files in Working Directory:").grid(row=0, column=0, padx=8, pady=(6, 2), sticky="w")
        self.manifest_combo = ctk.CTkComboBox(frm, values=["(loading files...)"], width=340)
        self.manifest_combo.grid(row=1, column=0, padx=8, pady=2, sticky="ew")
        ctk.CTkButton(frm, text="Refresh YAML Files", command=self.refresh_manifest_files).grid(row=2, column=0, padx=8, pady=2, sticky="ew")
        ctk.CTkButton(frm, text="Open Selected in Editor", command=self.open_selected_manifest).grid(row=3, column=0, padx=8, pady=2, sticky="ew")
        ctk.CTkButton(frm, text="Apply Selected YAML", command=self.apply_selected_manifest).grid(row=4, column=0, padx=8, pady=(2, 8), sticky="ew")
        frm.grid_columnconfigure(0, weight=1)
        self.yaml_file_combos.append(self.manifest_combo)
        self.refresh_manifest_files()

    def get_working_directory(self):
        """Return the normalized working directory, or None when it is invalid."""
        directory = os.path.abspath(os.path.expanduser(self.work_dir_entry.get().strip()))
        if not os.path.isdir(directory):
            self.terminal.append_output(f"\nError: Working Directory does not exist: {directory}\n", tag="error")
            return None
        return directory

    def refresh_manifest_files(self):
        if not self.yaml_file_combos:
            return
        directory = self.get_working_directory()
        if not directory:
            for combo in self.yaml_file_combos:
                combo.configure(values=["(invalid working directory)"])
                combo.set("(invalid working directory)")
            return
        try:
            files = sorted(
                entry.name for entry in os.scandir(directory)
                if entry.is_file() and entry.name.lower().endswith((".yaml", ".yml"))
            )
        except OSError as e:
            self.terminal.append_output(f"\nError reading YAML files: {e}\n", tag="error")
            files = []
        values = files or ["(no YAML files found)"]
        for combo in self.yaml_file_combos:
            current = combo.get()
            combo.configure(values=values)
            combo.set(current if current in files else values[0])

    def selected_manifest_path(self):
        return self.yaml_path_from_combo(self.manifest_combo)

    def yaml_path_from_combo(self, combo):
        if not combo:
            return None
        filename = combo.get()
        if not filename or filename.startswith("("):
            self.terminal.append_output("\nChoose a YAML file first.\n", tag="warning")
            return None
        directory = self.get_working_directory()
        if not directory:
            return None
        return os.path.join(directory, filename)

    def open_selected_manifest(self):
        path = self.selected_manifest_path()
        if path:
            self.open_yaml_editor(path)

    def apply_selected_manifest(self):
        path = self.selected_manifest_path()
        if path:
            self.run_cmd(f'kubectl apply -f "{path}"')

    def apply_yaml_from_combo(self, combo):
        path = self.yaml_path_from_combo(combo)
        if path:
            self.run_cmd(f'kubectl apply -f "{path}"')

    def edit_yaml_from_combo(self, combo):
        path = self.yaml_path_from_combo(combo)
        if path:
            self.open_yaml_editor(path)

    def delete_yaml_from_combo(self, combo):
        path = self.yaml_path_from_combo(combo)
        if not path:
            return
        filename = os.path.basename(path)
        if not messagebox.askyesno("Delete YAML file", f"Permanently delete {filename} from the Working Directory?"):
            return
        try:
            os.remove(path)
            self.terminal.append_output(f"\nDeleted YAML file: {path}\n", tag="info")
            self.refresh_manifest_files()
        except OSError as e:
            self.terminal.append_output(f"\nError deleting YAML file: {e}\n", tag="error")

    def open_yaml_editor(self, file_path=None):
        """Open a YAML editor that creates files in the selected working directory."""
        editor = ctk.CTkToplevel(self)
        editor.title("DocKube YAML Editor")
        editor.geometry("900x680")
        editor.grid_rowconfigure(1, weight=1)
        editor.grid_columnconfigure(0, weight=1)
        templates = {
            "Deployment": """apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  labels:
    app: my-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: my-container
        image: nginx:latest
        ports:
        - containerPort: 80
""",
            "Service": """apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 80
  type: ClusterIP
""",
            "ConfigMap": """apiVersion: v1
kind: ConfigMap
metadata:
  name: my-config
data:
  APP_ENV: development
""",
            "Blank": "",
        }
        top = ctk.CTkFrame(editor, fg_color="transparent")
        top.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
        ctk.CTkLabel(top, text="Starter:").pack(side="left", padx=(0, 5))
        template_menu = ctk.CTkComboBox(top, values=list(templates), width=180)
        template_menu.set("Deployment")
        template_menu.pack(side="left", padx=(0, 16))
        txt = tk.Text(editor, wrap="none", font=ctk.CTkFont(family="Consolas", size=12), bg="#1e1e1e", fg="#d4d4d4", insertbackground="#d4d4d4", relief="flat")
        txt.insert("1.0", templates["Deployment"])
        txt.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        def use_template(choice):
            txt.delete("1.0", "end")
            txt.insert("1.0", templates[choice])
        template_menu.configure(command=use_template)
        frm = ctk.CTkFrame(editor)
        frm.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        ctk.CTkLabel(frm, text="Filename:").pack(side="left", padx=5)
        fname_entry = ctk.CTkEntry(frm, placeholder_text="my-manifest.yaml", width=300)
        fname_entry.pack(side="left", padx=5)
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as manifest_file:
                    content = manifest_file.read()
                txt.delete("1.0", "end")
                txt.insert("1.0", content)
                fname_entry.insert(0, os.path.basename(file_path))
                editor.title(f"DocKube YAML Editor — {os.path.basename(file_path)}")
            except OSError as e:
                self.terminal.append_output(f"\nError opening YAML file: {e}\n", tag="error")
                editor.destroy()
                return
        def save_file():
            name = fname_entry.get().strip()
            if not name:
                self.terminal.append_output("\nError: Filename cannot be empty.\n", tag="error")
                return
            if os.path.basename(name) != name or not name.lower().endswith((".yaml", ".yml")):
                self.terminal.append_output("\nError: Use a filename ending in .yaml or .yml; it will be saved in the Working Directory.\n", tag="error")
                return
            directory = self.get_working_directory()
            if not directory:
                return
            full_path = os.path.join(directory, name)
            try:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(txt.get("1.0", "end-1c"))
                self.terminal.append_output(f"\nSaved YAML to {full_path}\n", tag="info")
                self.refresh_manifest_files()
                editor.destroy()
            except Exception as e:
                self.terminal.append_output(f"\nError saving file: {e}\n", tag="error")
        ctk.CTkButton(frm, text="Save", command=save_file).pack(side="left", padx=5)
        ctk.CTkButton(frm, text="Close", command=editor.destroy).pack(side="right", padx=5)

    def select_by_number(self):
        try:
            n = int(self.num_entry.get())
            if 1 <= n <= len(self.last_items):
                self.item_combo.set(self.item_combo.cget("values")[n-1])
        except Exception:
            pass
    def kubectl_action(self, act):
        sel = self.item_combo.get()
        if not sel or sel.startswith("("):
            return
        # sel looks like "1) ns/name" or "1) name"
        parts = sel.split(') ',1)
        if len(parts)!=2:
            return
        identifier = parts[1]
        if '/' in identifier:
            ns, name = identifier.split('/',1)
            ns_opt = f"-n {ns} "
        else:
            name = identifier
            ns_opt = ""
        kind = self.last_kind
        if act == "describe":
            cmd = f"kubectl describe {kind} {name} {ns_opt}".strip()
        elif act == "logs":
            cmd = f"kubectl logs {name} {ns_opt}".strip()
        elif act == "delete":
            cmd = f"kubectl delete {kind} {name} {ns_opt}".strip()
        else:
            cmd = ""
        if cmd:
            self.run_cmd(cmd)

if __name__ == "__main__":
    app = App()
    app.mainloop()
