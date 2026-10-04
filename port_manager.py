"""Local TCP/UDP port table with process lookup and a guarded kill action.

The parsing functions are deliberately pure so they can be unit tested
without a GUI: ``parse_netstat`` turns ``netstat -ano`` output into records
and ``parse_tasklist`` maps PIDs onto process names.

Verified against real Windows output:

* TCP rows carry a state column, so they split into 5 fields::

      TCP    0.0.0.0:135            0.0.0.0:0              LISTENING       1756

* UDP rows have no state column, so they split into 4 fields::

      UDP    0.0.0.0:53             *:*                                    3676

* IPv6 addresses appear bracketed, so the port is taken after the last colon::

      TCP    [::]:135               [::]:0                 LISTENING       1756
"""

import csv
import io
import queue
import subprocess
import threading
import tkinter as tk
from tkinter import TclError, messagebox, ttk

import customtkinter as ctk

# PIDs owned by the kernel. They can never be terminated by taskkill.
PROTECTED_PIDS = {0, 4}

# Processes whose termination would destabilise Windows itself.
PROTECTED_PROCESSES = {
    "system", "system idle process", "registry", "memory compression",
    "secure system", "csrss", "wininit", "services", "lsass", "svchost",
    "winlogon", "smss", "dwm", "explorer", "audiodg", "fontdrvhost",
    "spoolsv", "wudfhost", "runtime broker", "sihost", "ctfmon",
    "conhost.exe", "msmpeng.exe", "mssecsvc.exe",
}

# Columns shown in the table, in order, as (heading, width, anchor).
COLUMNS = (
    ("PID", 60, "e"),
    ("Process", 170, "w"),
    ("Proto", 60, "center"),
    ("Local Address", 150, "w"),
    ("Local Port", 75, "e"),
    ("Remote Address", 150, "w"),
    ("Remote Port", 75, "e"),
    ("State", 100, "w"),
)


def _split_endpoint(endpoint):
    """Split ``0.0.0.0:135`` or ``[::]:135`` into (address, port)."""
    endpoint = endpoint.strip()
    if ":" not in endpoint:
        return endpoint, ""
    address, _, port = endpoint.rpartition(":")
    return address.strip("[]"), port.strip()


def parse_netstat(text):
    """Return a list of port records parsed from ``netstat -ano`` output.

    Each record is a dict with proto, local_address, local_port,
    remote_address, remote_port, state and pid keys. Unparseable lines
    (headers, blanks) are skipped.
    """
    records = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line or not line.startswith(("TCP", "UDP")):
            continue
        parts = line.split()
        proto = parts[0].upper()
        if proto == "TCP" and len(parts) >= 5:
            local, remote, state, pid = parts[1], parts[2], parts[3], parts[4]
        elif proto == "UDP" and len(parts) >= 4:
            local, remote, state, pid = parts[1], parts[2], "", parts[3]
        else:
            continue
        if not pid.isdigit():
            continue
        local_address, local_port = _split_endpoint(local)
        remote_address, remote_port = _split_endpoint(remote)
        records.append({
            "proto": proto,
            "local_address": local_address,
            "local_port": local_port,
            "remote_address": remote_address,
            "remote_port": remote_port,
            "state": state,
            "pid": int(pid),
        })
    return records


def parse_tasklist(text):
    """Map PID to process name using ``tasklist /FO CSV /NH`` output."""
    names = {}
    for row in csv.reader(io.StringIO(text or "")):
        # "node.exe","1234","Console","1","12,345 K"
        if len(row) < 2 or not row[1].strip().isdigit():
            continue
        image = row[0].strip().strip('"')
        if image:
            names.setdefault(int(row[1].strip()), image)
    return names


def record_matches(record, protocol="All", query=""):
    """Filter helper used by the protocol selector and the search box."""
    if protocol and protocol != "All" and record["proto"] != protocol:
        return False
    query = (query or "").strip().lower()
    if not query:
        return True
    haystack = " ".join((
        record["proto"], record["local_address"], record["local_port"],
        record["remote_address"], record["remote_port"], record["state"],
    )).lower()
    return query in haystack


def is_protected(pid, process_name):
    """True when the process must not be killed from the UI."""
    if pid in PROTECTED_PIDS:
        return True
    if not process_name:
        return False
    name = process_name.strip().lower()
    name = name[:-4] if name.endswith(".exe") else name
    return name in PROTECTED_PROCESSES
def format_summary(records):
    """One-line status such as ``1420 connections, 38 listening``."""
    listening = sum(1 for r in records if r["state"].upper() == "LISTENING")
    return f"{len(records)} connections, {listening} listening"


def filter_summary(records, total):
    """Status text describing how many rows survived the current filter."""
    if len(records) == total:
        return f"{total} rows"
    return f"{len(records)} of {total} rows"
class PortManagerFrame(ctk.CTkFrame):
    """Live table of local ports with filtering, sorting and a kill button."""

    def __init__(self, master, terminal, app=None):
        super().__init__(master, fg_color="transparent")
        self.terminal = terminal
        self.app = app
        self.records = []
        self.pid_names = {}
        self.sort_column = "#1"
        self.sort_reverse = False
        self._auto_job = None
        self._drain_job = None
        self._poll_job = None
        self._loading = False
        self._last_protocol = "All"
        self._last_query = ""
        self._queue = queue.Queue()
        self._build()
        self.after(150, self.refresh)

    # -- layout -----------------------------------------------------------
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=(4, 0))
        toolbar.grid_columnconfigure(3, weight=1)

        self.refresh_btn = ctk.CTkButton(toolbar, text="Refresh", width=100, command=self.refresh)
        self.refresh_btn.grid(row=0, column=0, padx=(0, 6), pady=4)

        self.kill_btn = ctk.CTkButton(
            toolbar, text="Kill Port", width=110, command=self.kill_selected,
            fg_color="#b3261e", hover_color="#8f1d17")
        self.kill_btn.grid(row=0, column=1, padx=6, pady=4)

        self.proto_combo = ctk.CTkComboBox(
            toolbar, values=["All", "TCP", "UDP"], width=90,
            command=lambda _=None: self.apply_filter())
        self.proto_combo.set("All")
        self.proto_combo.grid(row=0, column=2, padx=6, pady=4)
        # The combo's command fires on user clicks only; CustomTkinter 6.x
        # exposes no textvariable to trace, so poll the value instead.
        self.proto_combo.configure(command=lambda value: self.apply_filter())
        self._poll_job = self.after(250, self._poll_filters)

        self.search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(
            toolbar, textvariable=self.search_var,
            placeholder_text="filter port, address, state or PID", width=280)
        self.search_entry.grid(row=0, column=3, padx=6, pady=4, sticky="ew")
        self.search_var.trace_add("write", lambda *_: self.apply_filter())

        self.auto_var = tk.BooleanVar(value=False)
        self.auto_check = ctk.CTkCheckBox(
            toolbar, text="Auto (5s)", variable=self.auto_var, command=self.toggle_auto)
        self.auto_check.grid(row=0, column=4, padx=6, pady=4)

        table_wrap = ctk.CTkFrame(self)
        table_wrap.grid(row=1, column=0, sticky="nsew", padx=5, pady=(4, 0))
        table_wrap.grid_columnconfigure(0, weight=1)

        headings = [c[0] for c in COLUMNS]
        self.ports_tree = ttk.Treeview(
            table_wrap, columns=headings, show="headings", height=12,
            style="DocKube.Treeview", selectmode="browse")
        for heading, _, anchor in COLUMNS:
            self.ports_tree.heading(heading, text=heading,
                                    command=lambda h=heading: self.sort_by(h))
            self.ports_tree.column(heading, width=dict((c[0], c[1]) for c in COLUMNS)[heading],
                                   anchor=anchor, stretch=False)
        self.ports_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ctk.CTkScrollbar(table_wrap, command=self.ports_tree.yview, width=14)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.ports_tree.configure(yscrollcommand=scrollbar.set)
        self.ports_tree.bind("<Double-1>", self._show_row_detail)
        self.ports_tree.tag_configure("odd", background="#252526")
        self.ports_tree.tag_configure("listening", foreground="#7ee787")

        self.status_label = ctk.CTkLabel(self, text="Loading ports...", anchor="w")
        self.status_label.grid(row=2, column=0, sticky="ew", padx=10, pady=(2, 6))

        ctk.CTkLabel(
            self,
            text="Select a row then press Kill Port. PID 0/4 and Windows "
                 "services are protected and cannot be terminated.",
            anchor="w", wraplength=620, text_color=("gray40", "gray60")
        ).grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 6))

    def _poll_filters(self):
        """Re-apply the filter when the combo or search box changed."""
        self._poll_job = None
        try:
            protocol = self.proto_combo.get()
            query = self.search_var.get()
        except (RuntimeError, TclError):
            return  # window is going away
        if protocol != self._last_protocol or query != self._last_query:
            self._last_protocol = protocol
            self._last_query = query
            self.apply_filter()
        self._poll_job = self.after(250, self._poll_filters)

    # -- thread dispatch --------------------------------------------------

    # -- thread dispatch --------------------------------------------------
    def _drain(self):
        """Deliver worker results on the Tk thread (scheduled from here)."""
        self._drain_job = None
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "refresh":
                    self._populate(*payload)
                elif kind == "kill":
                    self._taskkill_done(*payload)
        except queue.Empty:
            pass
        except (RuntimeError, TclError):
            return  # window is going away
        if self._pending():
            self._drain_job = self.after(60, self._drain)

    def _pending(self):
        return self._loading or not self._queue.empty()

    def _submit(self, kind, payload):
        """Hand a worker result to the main thread.

        Only the queue is touched here; the drain loop is started on the Tk
        thread by ``refresh``/``_run_taskkill`` so Tk is never called from a
        worker.
        """
        self._queue.put((kind, payload))

    def _ensure_drain(self):
        """Start the drain loop; must be called on the Tk thread."""
        if self._drain_job is None:
            self._drain_job = self.after(60, self._drain)

    # -- data -------------------------------------------------------------
    def refresh(self):
        """Re-read netstat and tasklist in the background, then repopulate."""
        self._loading = True
        self.refresh_btn.configure(state="disabled", text="Loading...")
        self.terminal.append_output("> refreshing local port table...\n")
        self._ensure_drain()

        def task():
            try:
                net = subprocess.run(["netstat", "-ano"], capture_output=True,
                                     text=True, errors="replace", timeout=25)
                tl = subprocess.run(["tasklist", "/FO", "CSV", "/NH"],
                                    capture_output=True, text=True, errors="replace", timeout=25)
                records = parse_netstat(net.stdout)
                names = parse_tasklist(tl.stdout)
            except Exception as exc:  # surface failures instead of hanging the UI
                self._submit("refresh", (None, None, str(exc)))
                return
            self._submit("refresh", (records, names, None))

        threading.Thread(target=task, daemon=True).start()

    def _populate(self, records, names, error=None):
        self._loading = False
        self.refresh_btn.configure(state="normal", text="Refresh")
        if error:
            self.status_label.configure(text="Could not read the port table")
            self.terminal.append_output(f"\nError reading ports: {error}\n", tag="error")
            return
        self.records = records
        self.pid_names = names
        self.apply_filter()
        self.terminal.append_output(format_summary(records) + "\n", tag="info")

    def apply_filter(self):
        protocol = self.proto_combo.get() if self.proto_combo else "All"
        query = self.search_var.get() if self.search_var else ""
        self._last_protocol, self._last_query = protocol, query
        rows = [r for r in self.records if record_matches(r, protocol, query)]
        self._fill_tree(rows)
        if not rows:
            self.status_label.configure(
                text=f"No matching ports ({format_summary(self.records) or 'table empty'})")
        else:
            self.status_label.configure(text=filter_summary(rows, len(self.records)))

    def _fill_tree(self, rows):
        tree = self.ports_tree
        tree.delete(*tree.get_children())
        for index, record in enumerate(rows):
            name = self.pid_names.get(record["pid"], "(unknown)")
            tags = ("odd",) if index % 2 else ()
            if record["state"].upper() == "LISTENING":
                tags = tags + ("listening",)
            tree.insert("", "end", values=(
                record["pid"], name, record["proto"],
                record["local_address"], record["local_port"],
                record["remote_address"], record["remote_port"],
                record["state"] or "-",
            ), tags=tags)

    def sort_by(self, heading):
        order = [c[0] for c in COLUMNS]
        column = order.index(heading) if heading in order else 0
        self.sort_reverse = not self.sort_reverse if self.sort_column == heading else False
        self.sort_column = heading
        keys = ("pid", None, "proto", "local_address", "local_port",
                "remote_address", "remote_port", "state")
        sort_key = keys[column]
        if sort_key is None:  # the Process column sorts by resolved name
            self.records.sort(key=lambda r: self.pid_names.get(r["pid"], "").lower(),
                              reverse=self.sort_reverse)
        elif sort_key in ("local_port", "remote_port"):
            self.records.sort(key=lambda r: int(r[sort_key] or 0), reverse=self.sort_reverse)
        else:
            self.records.sort(key=lambda r: str(r[sort_key]).lower(), reverse=self.sort_reverse)
        self.apply_filter()

    # -- actions ----------------------------------------------------------
    def selected_record(self):
        selection = self.ports_tree.selection()
        if not selection:
            messagebox.showwarning("Port Manager", "Select a port row first.")
            self.terminal.append_output("\nSelect a port row first.\n", tag="warning")
            return None
        values = self.ports_tree.item(selection[0], "values")
        return {
            "pid": int(values[0]),
            "process": values[1],
            "proto": values[2],
            "local_address": values[3],
            "local_port": values[4],
            "remote_address": values[5],
            "remote_port": values[6],
            "state": values[7],
        }

    def kill_selected(self):
        """Confirm then terminate the process owning the selected port."""
        record = self.selected_record()
        if not record:
            return
        pid = record["pid"]
        name = record["process"]
        if is_protected(pid, name):
            messagebox.showerror(
                "Port Manager - blocked",
                f"{name} (PID {pid}) is a protected Windows process and "
                "cannot be terminated from here.\n\n"
                "Stopping it could make Windows unstable.")
            self.terminal.append_output(
                f"\nBlocked: {name} (PID {pid}) is protected.\n", tag="warning")
            return
        if not messagebox.askyesno(
            "Kill process",
            f"Terminate this process?\n\n"
            f"Process: {name}\n"
            f"PID: {pid}\n"
            f"Port: {record['local_port']} ({record['proto']})\n"
            f"State: {record['state'] or '-'}\n\n"
            "Unsaved work in that application will be lost.",
            icon="warning", default="no"):
            return
        self._run_taskkill(pid, name)

    def _run_taskkill(self, pid, name):
        self.terminal.clear()
        self.terminal.append_output(f"> taskkill /PID {pid} /F /T\n")
        self._ensure_drain()

        def task():
            try:
                proc = subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"],
                                      capture_output=True, text=True, errors="replace", timeout=20)
                output = (proc.stdout or "") + (proc.stderr or "")
            except Exception as exc:
                self._submit("kill", (pid, name, str(exc), False))
                return
            self._submit("kill", (pid, name, output.strip(), proc.returncode == 0))

        threading.Thread(target=task, daemon=True).start()

    def _taskkill_done(self, pid, name, output, success):
        for line in (output or "").splitlines():
            self.terminal.append_output(line + "\n", tag="info" if success else "error")
        if success:
            self.terminal.append_output(f"\nKilled {name} (PID {pid}).\n", tag="info")
        else:
            self.terminal.append_output(
                f"\nCould not kill {name} (PID {pid}). "
                "Administrator rights are usually required.\n", tag="error")
        self.refresh()

    def _show_row_detail(self, _event=None):
        record = self.selected_record()
        if not record:
            return
        messagebox.showinfo(
            "Port detail",
            f"Process:  {record['process']}\n"
            f"PID:      {record['pid']}\n"
            f"Protocol: {record['proto']}\n\n"
            f"Local:    {record['local_address']}:{record['local_port']}\n"
            f"Remote:   {record['remote_address']}:{record['remote_port']}\n"
            f"State:    {record['state'] or '-'}")

    def toggle_auto(self):
        if self.auto_var.get():
            self._schedule_auto()
        elif self._auto_job:
            self.after_cancel(self._auto_job)
            self._auto_job = None

    def _schedule_auto(self):
        if self._auto_job:
            self.after_cancel(self._auto_job)
        self._auto_job = self.after(5000, self._auto_tick)

    def _auto_tick(self):
        self._auto_job = None
        if self.auto_var.get():
            self.refresh()

    def destroy(self):
        """Cancel the pending timers before the frame goes away."""
        for attribute in ("_auto_job", "_drain_job", "_poll_job"):
            job = getattr(self, attribute, None)
            if job:
                try:
                    self.after_cancel(job)
                except (RuntimeError, TclError):
                    pass
                setattr(self, attribute, None)
        super().destroy()
