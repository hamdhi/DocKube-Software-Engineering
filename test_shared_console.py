"""Prove the shared terminal works from a windowed (GUI-subsystem) process.

pythonw.exe shares its subsystem with the packaged --windowed DocKube.exe, so
this reproduces the packaged app's constraint: no console to inherit. Results go
to a file because pythonw has nowhere to print.

Run it the same way twice:

    python  test_shared_console.py
    pythonw test_shared_console.py <report-file>
"""

import os
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared_console import SharedTerminal


def main():
    work = tempfile.mkdtemp(prefix="dockeybe_win_")
    marker = os.path.join(work, "marker.txt")
    seen = []
    fired = []

    session = SharedTerminal(on_output=seen.append)
    print("running before use:", session.is_running())
    if session.is_running():
        print("FAIL: reported running before anything was sent")
        return 1

    def wait_for(event, seconds=20):
        deadline = time.time() + seconds
        while time.time() < deadline and not event.is_set():
            time.sleep(0.05)
        return event.is_set()

    # First command, capturing its own output through the callback.
    first_done = threading.Event()
    captured = {}

    def on_first(output):
        captured["first"] = output
        first_done.set()

    if not session.run(f'echo first >> "{marker}"', cwd=work,
                       callback=on_first):
        print("FAIL: could not start the shared prompt")
        return 1
    print("shared prompt started, running the first command")

    if not wait_for(first_done):
        print("FAIL: the completion marker never came back")
        session.close()
        return 1
    print("first callback fired, output:", repr(captured["first"]))

    pid = session._process.pid

    # Three more commands, all through the same process.
    for index in range(3):
        event = threading.Event()

        def make(idx=index, ev=event):
            def handler(_output):
                fired.append(idx)
                ev.set()
            return handler

        session.run(f'echo idx{index} >> "{marker}"', cwd=work,
                    callback=make())
        if not wait_for(event):
            print(f"FAIL: command {index} never completed")
            session.close()
            return 1

    still = session._process.pid if session._process else None
    print("commands completed in order:", fired)
    print("same cmd.exe pid for all four:", pid, "->", still, pid == still)
    print("output lines streamed to the listener:", len(seen))

    session.close()
    time.sleep(0.5)
    print("running after close:", session.is_running())

    executed = []
    if os.path.exists(marker):
        with open(marker, encoding="utf-8", errors="replace") as handle:
            executed = [line.strip() for line in handle if line.strip()]
    print("commands that actually ran:", executed)

    problems = []
    if fired != [0, 1, 2]:
        problems.append(f"commands did not run in order: {fired}")
    if pid != still:
        problems.append("a new cmd.exe was started per command")
    if executed != ["first", "idx0", "idx1", "idx2"]:
        problems.append(f"unexpected commands ran: {executed}")
    if session.is_running():
        problems.append("the process survived close()")
    if not seen:
        problems.append("no output was streamed to the listener")

    if problems:
        print("\nFAILURES:")
        for problem in problems:
            print("   ", problem)
        return 1
    print("\nSHARED TERMINAL OK: one cmd.exe, 4 serialised commands, "
          "clean close")
    return 0


if __name__ == "__main__":
    # pythonw has no stdout, so mirror everything into a report file.
    if sys.stdout is None or not hasattr(sys.stdout, "write"):
        lines = []
        original = print

        def record(*args, **kwargs):
            line = " ".join(str(a) for a in args)
            lines.append(line)
            original(*args, **kwargs)

        import builtins
        builtins.print = record
        try:
            code = main()
        except Exception:
            import traceback
            lines.append(traceback.format_exc())
            code = 1
        finally:
            builtins.print = original
        if len(sys.argv) > 1:
            with open(sys.argv[1], "w", encoding="utf-8") as handle:
                handle.write("\n".join(lines) + f"\nEXIT={code}\n")
        os._exit(code)

    sys.exit(main())