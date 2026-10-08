"""Drive the real App and prove every command shares one prompt.

This exists because of a bug that unit tests missed. The prompt's reader
thread used to call Tk's after() to push output into the terminal widget.
Tkinter serialises calls from other threads behind a lock that the main thread
holds while inside update(), so the reader blocked, the completion marker was
never seen, and the queue stalled after the third command. The commands still
ran, which is exactly what made it look healthy.

So this test asserts the whole path: several commands, one cmd.exe, output
arriving in the real widget, and nothing left running afterwards.
"""

import importlib.util
import os
import subprocess
import sys
import tempfile
import time

# Resolve app.py next to this test file so the test works from any CWD.
_APP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
spec = importlib.util.spec_from_file_location("app", _APP_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

WORDS = ["alpha", "bravo", "charlie", "delta"]


def cmd_process_count():
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-Process cmd -ErrorAction SilentlyContinue).Count"],
        capture_output=True, text=True)
    try:
        return int(out.stdout.strip() or 0)
    except ValueError:
        return 0


def main():
    work = tempfile.mkdtemp(prefix="dockeybe_shared_")
    marker = os.path.join(work, "log.txt")

    app = mod.App()
    app.geometry("1200x760+40+40")
    app.withdraw()
    entry = app.work_dir_entry
    entry.delete(0, "end")
    entry.insert(0, work)
    app.update()

    def pump(seconds):
        deadline = time.time() + seconds
        while time.time() < deadline:
            app.update()
            time.sleep(0.02)

    before = cmd_process_count()
    print("cmd processes before:", before)

    failures = []
    pids = set()
    # Click faster than a command completes, which is what exposed the stall.
    for word in WORDS:
        app.run_in_external_terminal(f'echo {word} >> "{marker}"')
        for _ in range(60):
            if app.console._process is not None:
                break
            pump(0.1)
        if app.console._process is not None:
            pids.add(app.console._process.pid)
        pump(0.4)

    deadline = time.time() + 30
    executed = []
    while time.time() < deadline:
        if os.path.exists(marker):
            with open(marker, encoding="utf-8", errors="replace") as handle:
                executed = [line.strip() for line in handle if line.strip()]
            if len(executed) == len(WORDS):
                break
        pump(0.2)

    after = cmd_process_count()
    print("cmd processes after :", after, f"(added {after - before})")
    print("shared prompt pids  :", pids)
    print("commands that ran   :", executed)

    pump(1.0)
    text = app.terminal.textbox.get("1.0", "end")
    missing = [word for word in WORDS if word not in text]
    print("all output reached the terminal widget:", not missing)

    if len(pids) != 1:
        failures.append(f"expected one shared prompt, saw {pids}")
    if after - before > 1:
        failures.append(f"{after - before} cmd windows opened for "
                        f"{len(WORDS)} commands")
    if executed != WORDS:
        failures.append(f"commands did not all run in order: {executed}")
    if missing:
        failures.append(f"output never reached the widget: {missing}")

    app._shutdown()
    time.sleep(0.5)
    if app.console.is_running():
        failures.append("the shared prompt outlived the app")
    print("prompt closed with the app:", not app.console.is_running())

    if failures:
        print("\nFAILURES:")
        for failure in failures:
            print("   ", failure)
        return 1
    print(f"\nSHARED TERMINAL APP OK: {len(WORDS)} commands, 1 prompt, "
          f"output streamed, clean shutdown")
    return 0


if __name__ == "__main__":
    sys.exit(main())