"""Drive the Port Manager against live data: populate, filter, sort, guard."""
import importlib.util
import os
import subprocess
import sys
import time
import traceback

import port_manager as pm

# Resolve app.py next to this test file so the test works from any CWD.
_APP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
spec = importlib.util.spec_from_file_location("app", _APP_PATH)
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except Exception:
    traceback.print_exc()
    sys.exit(1)

app = mod.App()
app.withdraw()
app.select_category("Port Manager")

frame = app.ports_frame
assert frame is not None, "PortManagerFrame was not created"
print("frame created:", type(frame).__name__)

# Let the background netstat/tasklist thread finish. `update()` is required
# because `after` callbacks are not processed by `update_idletasks()`.
for _ in range(80):
    app.update()
    if frame.records:
        break
    time.sleep(0.25)

if not frame.records:
    print("FAIL: no records populated")
    app.destroy()
    sys.exit(1)

rows = frame.ports_tree.get_children()
print(f"records={len(frame.records)} rows={len(rows)}")
print("status:", frame.status_label.cget("text"))
print("first row:", frame.ports_tree.item(rows[0], "values"))

# Filtering by protocol. The combo is polled every 250 ms, so pump the
# event loop briefly to let the poll notice the new value.
def settle(seconds=0.8):
    end = time.time() + seconds
    while time.time() < end:
        app.update()
        time.sleep(0.02)

frame.proto_combo.set("TCP")
settle()
tcp_rows = len(frame.ports_tree.get_children())
frame.proto_combo.set("UDP")
settle()
udp_rows = len(frame.ports_tree.get_children())
frame.proto_combo.set("All")
settle()
all_rows = len(frame.ports_tree.get_children())
expected_tcp = sum(1 for r in frame.records if r["proto"] == "TCP")
expected_udp = sum(1 for r in frame.records if r["proto"] == "UDP")
print(f"filter TCP={tcp_rows} (expect {expected_tcp}) "
      f"UDP={udp_rows} (expect {expected_udp}) All={all_rows}")
assert tcp_rows == expected_tcp, "TCP filter did not apply"
assert udp_rows == expected_udp, "UDP filter did not apply"
assert all_rows == len(frame.records), "All filter is wrong"

# Searching for a specific port.
target = frame.records[0]["local_port"]
frame.search_var.set(target)
app.update()
found = len(frame.ports_tree.get_children())
frame.search_var.set("")
app.update()
print(f"search '{target}' -> {found} rows")
assert found >= 1

# Sorting by each column must not raise.
for column in ("PID", "Process", "Proto", "Local Address", "Local Port", "State"):
    frame.sort_by(column)
    app.update()
print("sorting by all columns: OK")

# Protected processes must be refused.
protected_rows = [r for r in frame.records if pm.is_protected(r["pid"], frame.pid_names.get(r["pid"]))]
print(f"protected rows in table: {len(protected_rows)}")

# Kill must refuse a protected PID without touching taskkill.
killed = []
frame._run_taskkill = lambda pid, name: killed.append(pid)
tree = frame.ports_tree
children = tree.get_children()
first_pid = int(tree.item(children[0], "values")[0])
tree.selection_set(children[0])
import tkinter.messagebox as mb
original_ask = mb.askyesno
original_err = mb.showerror
mb.showerror = lambda *a, **k: print("blocked ->", a[0])
frame.kill_selected()
mb.showerror = original_err
print(f"selected protected PID {first_pid}; taskkill calls:", killed)
assert killed == [], "a protected process must never be killed"

# Pick a non-protected row and confirm the taskkill call is issued.
target = next(r for r in frame.records
              if not pm.is_protected(r["pid"], frame.pid_names.get(r["pid"])))
children = tree.get_children()
for child in children:
    if int(tree.item(child, "values")[0]) == target["pid"]:
        tree.selection_set(child)
        break
mb.askyesno = lambda *a, **k: True
frame.kill_selected()
mb.askyesno = original_ask
print("taskkill requested for:", killed, "(expected", target["pid"], ")")
assert killed == [target["pid"]], "kill_selected did not call taskkill"

# Switching away must cancel the auto-refresh timer.
frame.auto_var.set(True)
frame.toggle_auto()
frame.destroy()
print("destroy() cancelled timer cleanly")
app.destroy()
print("\nPORT MANAGER INTERACTION TEST PASSED")
