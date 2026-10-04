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
import json

import devops_tools
import learning_index
from docs_content import COMMAND_PREFIXES, EXTRA_DOCS
from learning import LearningWindow, SIDEBAR_WIDTH

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
        # Give the nav column a real minimum width; without it the scrollable
        # frame has zero width to draw its scrollbar in.
        self.grid_columnconfigure(0, minsize=SIDEBAR_WIDTH)
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(1, weight=1)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.categories = [
            "Dashboard", "Docker", "Minikube/Kind", "Pods", "Deployments",
            "Services", "ReplicaSets", "StatefulSets", "Volumes & PVC",
            "MySQL", "Postgres", "MongoDB", "CI/CD & GitHub Actions",
            "GitHub", "Jenkins", "Terraform", "Ansible", "Port Manager",
            "Custom", "Networking Masterclass"
        ]
        ctk.CTkLabel(self.sidebar, text="DocKube",
                     font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        # The category list is taller than a short window, so it must scroll
        # rather than silently hiding the last few buttons.
        self.nav = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent",
            scrollbar_button_color="#30363d",
            scrollbar_button_hover_color="#484f58")
        self.nav.grid(row=1, column=0, sticky="nsew", padx=(4, 2), pady=(0, 8))
        self.sidebar_buttons = {}
        for i, cat in enumerate(self.categories):
            btn = ctk.CTkButton(self.nav, text=cat, fg_color="transparent",
                                text_color=("gray10","gray90"), hover_color=("gray70","gray30"),
                                anchor="w", command=lambda c=cat: self.select_category(c))
            btn.grid(row=i, column=0, padx=16, pady=5, sticky="ew")
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
        # Toggle controlling whether every run also pops open a cmd.exe window.
        self.open_terminal_on_run = self._load_pref("open_terminal_on_run", True)
        self.terminal_toggle = ctk.CTkSwitch(
            self.main, text="Open a terminal for each command",
            command=self._toggle_terminal_pref)
        if self.open_terminal_on_run:
            self.terminal_toggle.select()
        # Row 8 is below the actions (4 or 6) and terminal (5 or 7) frames used
        # by both layouts, so the toggle never collides with either.
        self.terminal_toggle.grid(row=8, column=0, columnspan=2, padx=20,
                                  pady=(0, 6), sticky="w")
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
        self.learning_window = None
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
            "Networking Masterclass": (
                "Open the Learning Centre for the full study guide.\n\n"
                f"{len(learning_index.CHAPTERS)} chapters covering networking "
                "fundamentals, IP addresses, subnetting, ports, TCP vs UDP, "
                "protocols, network devices, the Linux command line and "
                "permissions, software engineering, Linux and Windows "
                "sysadmin, and DevOps.\n\n"
                "Every chapter explains the theory in plain English, shows "
                "the real commands, gives memory tricks, includes a "
                "Learning vs Production comparison, and ends with an "
                "exercise you can run on this machine.\n\n"
                "Press the button below to open it in its own window."
            ),
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
        elif cat == "Networking Masterclass":
            self.add_learning_launcher()
        else:
            self.add_yaml_apply()
    # ------------------------------------------------------------------
    def add_learning_launcher(self):
        """Opening the guide in a popup keeps the main window uncluttered."""
        frm = ctk.CTkFrame(self.actions)
        frm.pack(pady=10, fill="x", anchor="w", padx=5)
        ctk.CTkLabel(
            frm, text="The full study guide opens in its own window.",
            text_color=("gray40", "gray60"), anchor="w"
        ).pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkButton(
            frm, text="Open Learning Centre", height=40,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.open_learning_centre
        ).pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(
            frm,
            text=f"{len(learning_index.CHAPTERS)} chapters, fully explained, with\n"
                 "real commands, memory tricks, Learning vs Production\n"
                 "tables and hands-on exercises you can run here.",
            text_color=("gray40", "gray60"), anchor="w", justify="left"
        ).pack(fill="x", padx=10, pady=(0, 10))
    # ------------------------------------------------------------------
    def open_learning_centre(self):
        """Open (or focus) the Learning Centre popup window."""
        if self.learning_window is not None and self.learning_window.winfo_exists():
            self.learning_window.lift()
            self.learning_window.focus_force()
            return
        chapters = [("Start Here", learning_index.INTRO)] + learning_index.CHAPTERS
        self.learning_window = LearningWindow(self, chapters)
        self.learning_window.protocol("WM_DELETE_WINDOW", self.close_learning_centre)
    # ------------------------------------------------------------------
    def close_learning_centre(self):
        """Destroy the popup and forget it so it can be reopened cleanly."""
        if self.learning_window is not None:
            self.learning_window.destroy()
        self.learning_window = None
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
            # The column must collapse too, otherwise a hidden sidebar leaves
            # a 200px gap down the left of a narrow window.
            self.grid_columnconfigure(0, minsize=0)
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
            self.grid_columnconfigure(0, minsize=SIDEBAR_WIDTH)
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

    # ------------------------------------------------------------------
    # Small persisted preferences, stored next to the user's app data so
    # they survive a rebuild of the executable.
    # ------------------------------------------------------------------
    PREF_FILE_NAME = "dockeybe_prefs.json"

    @classmethod
    def _prefs_path(cls):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        folder = os.path.join(base, "DocKube")
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, cls.PREF_FILE_NAME)

    def _load_pref(self, key, default):
        try:
            with open(self._prefs_path(), "r", encoding="utf-8") as handle:
                return json.load(handle).get(key, default)
        except Exception:
            return default

    def _save_pref(self, key, value):
        path = self._prefs_path()
        prefs = {}
        try:
            with open(path, "r", encoding="utf-8") as handle:
                prefs = json.load(handle)
        except Exception:
            pass
        prefs[key] = value
        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(prefs, handle, indent=2)
        except Exception:
            pass

    def _toggle_terminal_pref(self):
        self.open_terminal_on_run = bool(self.terminal_toggle.get())
        self._save_pref("open_terminal_on_run", self.open_terminal_on_run)

    def run_cmd(self, cmd, callback=None, open_external=None):
        self.terminal.clear()
        print(f"> {cmd}")
        self.terminal.append_output(f"> {cmd}\n")
        self.cmd_preview.delete(0, ctk.END)
        self.cmd_preview.insert(0, cmd)
        # None means "follow the user's in-app toggle"; True or False overrides it.
        if open_external is None:
            open_external = self.open_terminal_on_run
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
