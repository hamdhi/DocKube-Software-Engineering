"""Action-panel builders for the DocKube categories.

Each function takes the running ``App`` instance as its first argument and
pops controls into ``app.actions``. They deliberately avoid importing
``app`` so that the modules stay independent of the UI entry point.

Shared helpers here cover the patterns the original ``app.py`` established:
buttons run through ``app.run_cmd``, templates are written into the selected
working directory, and long-running probes run in a background thread.
"""

import os
import subprocess
import threading

import customtkinter as ctk

import command_specs as specs
import templates_content as templates
from port_manager import PortManagerFrame


def capture_cmd(app, command, callback=None):
    """Run ``command`` in the background and hand the output to ``callback``.

    Unlike ``app.run_cmd`` this does not clear the terminal and does not open
    an extra console window, so it suits silent probes such as netstat.
    """
    def task():
        try:
            directory = os.path.abspath(os.path.expanduser(
                app.work_dir_entry.get().strip() or os.getcwd()))
            proc = subprocess.run(command, shell=True, capture_output=True, text=True,
                                  errors="replace", cwd=directory, timeout=60)
            output = (proc.stdout or "") + (proc.stderr or "")
        except Exception as exc:
            output = f"Error: {exc}"
        if callback:
            app.after(0, callback, output)
    threading.Thread(target=task, daemon=True).start()


def resolve_command(template, argument):
    """Substitute ``{arg}``; returns None when the argument is required."""
    if "{arg}" not in template:
        return template
    argument = (argument or "").strip()
    if not argument:
        return None
    return template.replace("{arg}", argument)


def add_arg_group(app, title, items, placeholder="argument..."):
    """Render one labelled group of command buttons with a shared arg entry."""
    frame = ctk.CTkFrame(app.actions)
    frame.pack(pady=6, fill="x", anchor="w", padx=5)
    frame.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(weight="bold")).grid(
        row=0, column=0, columnspan=2, padx=8, pady=(6, 2), sticky="w")

    entry = ctk.CTkEntry(frame, placeholder_text=placeholder)
    entry.grid(row=1, column=0, columnspan=2, padx=8, pady=(0, 4), sticky="ew")

    columns = 1 if app.compact_layout else 2
    for index, (label, template) in enumerate(items):
        row = 2 + index // columns
        column = index % columns

        def make(template=template):
            def run():
                resolved = resolve_command(template, entry.get())
                if resolved is None:
                    message = f"This command needs a value for '{label}'.\n\nEnter it in the box above."
                    app.terminal.append_output(f"\nMissing argument for: {template}\n", tag="warning")
                    from tkinter import messagebox
                    messagebox.showwarning("Argument required", message)
                    return
                app.run_cmd(resolved)
            return run

        ctk.CTkButton(frame, text=label, command=make()).grid(
            row=row, column=column, padx=(8, 4) if column == 0 else (4, 8),
            pady=2, sticky="ew")
        frame.grid_columnconfigure(column, weight=1)
    return frame


def add_command_groups(app, groups, placeholder="argument..."):
    """Render every ``(title, items)`` group from a spec collection."""
    for title, items in groups:
        add_arg_group(app, title, items, placeholder)


def write_template(app, relative_path, content):
    """Write a starter file into the working directory; returns True on success."""
    directory = app.get_working_directory()
    if not directory:
        return False
    target = os.path.join(directory, relative_path)
    try:
        parent = os.path.dirname(target)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(content)
    except OSError as exc:
        app.terminal.append_output(f"\nError writing {relative_path}: {exc}\n", tag="error")
        return False
    app.terminal.append_output(f"\nWrote {target}\n", tag="info")
    app.refresh_manifest_files()
    return True


def add_template_saver(app, label, relative_path, content):
    """Add a single button that writes a starter file on click."""
    button = ctk.CTkButton(
        app.actions, text=label,
        command=lambda: write_template(app, relative_path, content))
    button.pack(pady=4, anchor="w", padx=5)
    return button


def add_template_row(app, entries):
    """One frame holding a button per starter file."""
    frame = ctk.CTkFrame(app.actions)
    frame.pack(pady=6, fill="x", anchor="w", padx=5)
    frame.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(frame, text="Write starter file:", font=ctk.CTkFont(weight="bold")).grid(
        row=0, column=0, columnspan=2, padx=8, pady=(6, 2), sticky="w")
    for index, (label, relative_path, content) in enumerate(entries):
        ctk.CTkButton(
            frame, text=label,
            command=lambda p=relative_path, c=content: write_template(app, p, c)
        ).grid(row=1 + index, column=0, padx=8, pady=2, sticky="ew")
    return frame
def add_database_tools(app, category):
    """Database panel: starter manifest, kubectl operations, pod list."""
    relative_path, content = templates.MANIFEST_TEMPLATES[category]
    add_template_saver(app, f"Write {category} Manifest ({relative_path})", relative_path, content)
    app.add_yaml_apply()
    app.add_list_ui(f"kubectl get pods -l app={category.lower()}", "Pod")
    add_command_groups(app, specs.DATABASE_COMMANDS[category], "pod name, namespace...")
    app.add_custom_input()


def add_github_tools(app):
    """Git plus GitHub CLI panels."""
    workflow_path, workflow = templates.AUX_TEMPLATES["GitHub Actions Workflow"]
    add_template_saver(app, "Write GitHub Actions Workflow", workflow_path, workflow)
    add_template_saver(app, "Write Jenkinsfile", *templates.AUX_TEMPLATES["Jenkinsfile"])
    add_command_groups(app, specs.GIT_GROUPS, specs.ARG_PLACEHOLDERS["git"])
    add_command_groups(app, specs.GITHUB_CLI_GROUPS, specs.ARG_PLACEHOLDERS["gh"])
    app.add_custom_input()


def add_cicd_tools(app):
    """Pipeline panel: Actions, local runner, image build and deployment."""
    workflow_path, workflow = templates.AUX_TEMPLATES["GitHub Actions Workflow"]
    add_template_saver(app, "Write GitHub Actions Workflow", workflow_path, workflow)
    add_command_groups(app, specs.CICD_GROUPS, specs.ARG_PLACEHOLDERS["cicd"])
    app.add_custom_input()


def add_jenkins_tools(app):
    """Jenkins panel driven by Docker."""
    add_template_saver(app, "Write Jenkinsfile", *templates.AUX_TEMPLATES["Jenkinsfile"])
    app.add_cmd_button("Open Jenkins UI", "start http://localhost:8080")
    add_command_groups(app, specs.JENKINS_GROUPS, "container name, url...")
    app.add_custom_input()


def add_terraform_tools(app):
    """Terraform panel plus a starter configuration file."""
    add_template_saver(app, "Write main.tf", *templates.AUX_TEMPLATES["Terraform main.tf"])
    add_command_groups(app, specs.TERRAFORM_GROUPS, specs.ARG_PLACEHOLDERS["terraform"])
    app.add_custom_input()


def add_ansible_tools(app):
    """Ansible panel plus starter playbook and inventory files."""
    add_template_saver(app, "Write playbook.yml", *templates.AUX_TEMPLATES["Ansible Playbook"])
    add_template_saver(app, "Write inventory.ini", *templates.AUX_TEMPLATES["Ansible Inventory"])
    add_command_groups(app, specs.ANSIBLE_GROUPS, specs.ARG_PLACEHOLDERS["ansible"])
    app.add_custom_input()

def add_security_testing_tools(app):
    """Security testing panel: recon, scanning, and the checks that gate a build."""
    add_command_groups(app, specs.SECURITY_GROUPS, specs.ARG_PLACEHOLDERS["security"])
    app.add_cmd_button("Explain OWASP Top 10", "echo Start with the OWASP Top 10, then read the Security Testing chapter")
    app.add_custom_input()


def add_firewall_tools(app):
    """Firewall panel across ufw, firewalld, nftables and Windows Firewall."""
    add_command_groups(app, specs.FIREWALL_GROUPS, specs.ARG_PLACEHOLDERS["firewall"])
    app.add_custom_input()


def add_diagram_tools(app):
    """Diagram tooling panel: PlantUML, Graphviz, Mermaid and schema export."""
    add_command_groups(app, specs.DIAGRAM_GROUPS, specs.ARG_PLACEHOLDERS["diagram"])
    app.add_custom_input()


def add_database_admin_tools(app):
    """Database admin panel for Postgres, MySQL and Mongo, plus schema design."""
    add_command_groups(app, specs.DATABASE_ADMIN_GROUPS, specs.ARG_PLACEHOLDERS["database"])
    app.add_custom_input()


def add_port_manager(app):
    """Mount the live port table with its kill button."""
    app.ports_frame = PortManagerFrame(app.actions, app.terminal, app)
    app.ports_frame.pack(fill="both", expand=True, padx=2, pady=4)
    app.ports_tree = app.ports_frame.ports_tree
    app.add_cmd_button("Show netstat -ano", "netstat -ano")
    app.add_cmd_button("Show Listening Ports", "netstat -ano | findstr LISTENING")
    app.add_cmd_button("Task Manager", "tasklist")