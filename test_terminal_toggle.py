"""Verify the in-app terminal behaviour toggle.

run_cmd now takes open_external=None, meaning "follow the saved preference".
The toggle must flip the saved value and actually control whether a visible
cmd.exe window is launched.
"""

import importlib.util
import os
import subprocess
import sys
import tempfile
import time
import traceback

spec = importlib.util.spec_from_file_location("app", "app.py")
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except Exception:
    traceback.print_exc()
    sys.exit(1)

# Keep the test off the real user profile.
temp_profile = tempfile.mkdtemp(prefix="dockeybe_prefs_")
os.environ["APPDATA"] = temp_profile

app = mod.App()
app.withdraw()

failures = []
launched = []
app.run_in_external_terminal = lambda cmd: launched.append(cmd)

print("prefs file:", app._prefs_path())
print("default preference:", app.open_terminal_on_run)
if app.open_terminal_on_run is not True:
    failures.append(f"expected the default to be True, got {app.open_terminal_on_run}")

# The switch must reflect the loaded preference.
if not app.terminal_toggle.get():
    failures.append("switch does not show the enabled default")

# --- toggle off -> no external terminal -------------------------------
app.terminal_toggle.deselect()
app._toggle_terminal_pref()
launched.clear()
app.run_cmd("echo one")
if launched:
    failures.append(f"terminal opened while switched off: {launched}")
print("after switching off, launched:", launched)

if app._load_pref("open_terminal_on_run", None) is not False:
    failures.append("preference was not persisted as False")

# --- toggle on -> external terminal ----------------------------------
app.terminal_toggle.select()
app._toggle_terminal_pref()
launched.clear()
app.run_cmd("echo two")
if launched != ["echo two"]:
    failures.append(f"expected a terminal for 'echo two', got {launched}")
print("after switching on, launched:", launched)

if app._load_pref("open_terminal_on_run", None) is not True:
    failures.append("preference was not persisted as True")

# --- an explicit argument must still override the toggle -------------
launched.clear()
app.run_cmd("echo three", open_external=False)
if launched:
    failures.append(f"open_external=False was ignored: {launched}")

launched.clear()
app.run_cmd("echo four", open_external=True)
if launched != ["echo four"]:
    failures.append(f"open_external=True was ignored: {launched}")
print("explicit overrides honoured: True/False")

# --- the real launcher must use cmd.exe /k so output stays visible ---
app.run_in_external_terminal = mod.App.run_in_external_terminal.__get__(app)
directory = tempfile.mkdtemp(prefix="dockeybe_cwd_")
app.work_dir_entry.delete(0, "end")
app.work_dir_entry.insert(0, directory)

real = []
original_popen = subprocess.Popen
subprocess.Popen = lambda args, **kwargs: real.append((args, kwargs))
try:
    app.run_in_external_terminal("echo visible")
finally:
    subprocess.Popen = original_popen

print("real launcher call:", real)
if not real:
    failures.append("run_in_external_terminal spawned nothing")
else:
    args, kwargs = real[0]
    if args[0].lower().endswith("cmd.exe") and args[1].lower() != "/k":
        failures.append(f"expected cmd.exe /k so output stays visible, got {args}")
    if "cwd" not in kwargs:
        failures.append("launcher did not pass a cwd")

# run_cmd also starts a worker thread that reads the command output and posts
# it back with after(). Those threads touch Tk, so the main loop has to keep
# running until they are done; otherwise they complain once the widgets are
# destroyed.
def settle(seconds=1.5):
    deadline = time.time() + seconds
    while time.time() < deadline:
        app.update()
        time.sleep(0.02)


settle()
app.destroy()

if failures:
    print(f"\n{len(failures)} TERMINAL TOGGLE FAILURES:")
    for failure in failures:
        print("   ", failure)
    sys.exit(1)
print("\nTERMINAL TOGGLE TEST PASSED")
