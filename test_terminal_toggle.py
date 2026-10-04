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

# --- one shared prompt for every command, never a window per command ------
# The session is stubbed so the test never starts a real cmd.exe, and the real
# run_in_external_terminal is restored so it is the code under test.
app.run_in_external_terminal = mod.App.run_in_external_terminal.__get__(app)
sent = []
app.console.run = lambda cmd, cwd=None, callback=None: sent.append(cmd) or True

sent.clear()
app.run_in_external_terminal("echo one")
app.run_in_external_terminal("echo two")
app.run_in_external_terminal("echo three")
print("commands sent to the shared prompt:", sent)
if sent != ["echo one", "echo two", "echo three"]:
    failures.append(f"shared prompt did not receive every command: {sent}")

# A single SharedTerminal instance must serve the whole app.
from shared_console import SharedTerminal

if not isinstance(app.console, SharedTerminal):
    failures.append("app is not using a SharedTerminal")

# --- commands that parse their own output must not run twice -------------
# fetch_items / fetch_service_options pass a callback and rely on the captured
# output, so they must run in-process and never reach the shared prompt.
captured = []
original_capture = app._capture_output
app._capture_output = lambda cmd, callback: captured.append((cmd, callback))


def on_done(output):
    pass


sent.clear()
captured.clear()
app.run_cmd("kubectl get pods -A", on_done)
if sent:
    failures.append(f"a callback command also went to the prompt: {sent}")
if len(captured) != 1 or captured[0][1] is not on_done:
    failures.append(f"callback command was not captured in-process: {captured}")
print("callback command captured in-process, not sent to the prompt")

# Without a callback it goes to the shared prompt and is not run locally.
sent.clear()
captured.clear()
app.run_cmd("kubectl delete pod x", open_external=True)
if sent != ["kubectl delete pod x"]:
    failures.append(f"plain command did not reach the prompt: {sent}")
if captured:
    failures.append(f"plain command also ran locally: {captured}")
print("plain command sent to the shared prompt only")

# Closing the app must shut the prompt down.
closed = []
app.console.close = lambda: closed.append(True)
app._shutdown()
if not closed:
    failures.append("closing the app did not stop the shared prompt")
print("shared prompt closed on shutdown:", bool(closed))

app._capture_output = original_capture

if failures:
    print(f"\n{len(failures)} TERMINAL TOGGLE FAILURES:")
    for failure in failures:
        print("   ", failure)
    sys.exit(1)
print("\nTERMINAL TOGGLE TEST PASSED")
