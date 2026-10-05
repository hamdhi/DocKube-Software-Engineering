"""One long-lived command prompt shared by the whole app.

Opening a ``cmd.exe`` per command buried the user in windows: a dozen buttons
left a dozen windows behind. This keeps exactly one ``cmd.exe /k`` alive for the
lifetime of the app and feeds every command into it.

Why pipes and not a visible console window
------------------------------------------
It is tempting to spawn a real window and type into it, but that combination
does not work for DocKube. The packaged ``DocKube.exe`` is a GUI-subsystem
binary with no console of its own. A ``cmd.exe`` given redirected stdin while
the parent has no console exits immediately with code 1 - verified against
pythonw.exe, which shares that subsystem. You can have a visible window *or*
drive the prompt programmatically, not both.

So the single prompt runs headless with its stdin and stdout piped to the app,
and the reader thread below pushes that output into the app's own terminal
widget. The user still watches every command run, in one consistent place, and
the prompt keeps its state (current directory, environment, ``doskey`` history)
between commands.

How commands are serialised
---------------------------
cmd.exe reads its input as a plain stream with no reply channel, so there is no
way to ask when a command finished. After each command the session writes an
``echo`` of a unique token; the reader thread sees that token come back and
knows the command is done. Only then is the next queued command written, which
keeps the output of two commands from mixing together.
"""

import os
import queue
import subprocess
import threading

# CREATE_NO_WINDOW: cmd.exe must not flash a console window behind the app.
_CREATE_NO_WINDOW = 0x08000000

_TOKEN_PREFIX = "__dockeybe_done_"


class SharedTerminal:
    """A single ``cmd.exe`` that runs every command the app sends."""

    def __init__(self, on_output=None):
        """``on_output(text)`` is called for every line the prompt produces.

        It is invoked from the reader thread, so a GUI caller must marshal it
        onto its own thread, for example with Tk's ``after``.
        """
        self.on_output = on_output
        self._process = None
        self._reader = None
        self._lock = threading.Lock()
        self._pending = queue.Queue()
        self._in_flight = None
        self._marker = None
        self._counter = 0

    # ------------------------------------------------------------------
    # Lifetime
    # ------------------------------------------------------------------
    def is_running(self):
        return (self._process is not None
                and self._process.poll() is None)

    def ensure_open(self, cwd=None):
        """Start the shared prompt if it is not already running."""
        with self._lock:
            return self._ensure_open_locked(cwd)

    def _ensure_open_locked(self, cwd=None):
        if self.is_running():
            return True
        if os.name != "nt":
            # No cmd.exe here; the caller falls back to running in-process.
            return False

        try:
            self._process = subprocess.Popen(
                ["cmd.exe", "/k"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="mbcs",
                errors="replace",
                bufsize=1,
                cwd=cwd or os.getcwd(),
                creationflags=_CREATE_NO_WINDOW)
        except Exception:
            self._process = None
            return False

        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        return True

    def close(self):
        """Shut the shared prompt down and drop anything still queued."""
        with self._lock:
            process = self._process
            self._process = None
        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except Exception:
                pass
            try:
                process.wait(timeout=3)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
        while not self._pending.empty():
            try:
                self._pending.get_nowait()
            except queue.Empty:
                break

    # ------------------------------------------------------------------
    # Running commands
    # ------------------------------------------------------------------
    def run(self, command, cwd=None, callback=None):
        """Queue ``command`` to run in the shared prompt.

        ``callback(output)`` runs on the reader thread once that specific
        command has finished. Returns False only when the prompt cannot be
        started at all, which lets the caller fall back to running the command
        in-process instead of silently doing nothing.
        """
        if not command or not command.strip():
            return False
        if not self.ensure_open(cwd):
            return False
        self._pending.put((command, cwd, callback))
        self._pump()
        return True

    def _pump(self):
        """Write the next queued command, if nothing is already running."""
        with self._lock:
            if self._in_flight is not None or not self.is_running():
                return
            try:
                command, cwd, callback = self._pending.get_nowait()
            except queue.Empty:
                return

            self._counter += 1
            self._marker = f"{_TOKEN_PREFIX}{self._counter}_{os.getpid()}_"
            self._in_flight = (command, callback)
            lines = []
            if cwd:
                lines.append(f'cd /d "{os.path.abspath(cwd)}"')
            lines.append(command)
            lines.append(f"echo {self._marker}")
            payload = "\r\n".join(lines) + "\r\n"

        try:
            self._process.stdin.write(payload)
            self._process.stdin.flush()
        except Exception:
            # The prompt died between the check and the write. Drop the
            # command so the caller is not left waiting forever.
            with self._lock:
                failed = self._in_flight
                self._in_flight = None
            if failed and failed[1]:
                try:
                    failed[1]("")
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Reader thread
    # ------------------------------------------------------------------
    def _read_loop(self):
        process = self._process
        if process is None or process.stdout is None:
            return
        collected = []
        try:
            for line in process.stdout:
                marker = self._marker
                if marker and marker in line:
                    if line.strip() == marker:
                        # The marker itself: the command has finished.
                        self._finish(collected)
                        collected = []
                    # Either the marker or the prompt echoing "echo <marker>"
                    # is bookkeeping, so neither is shown to the user.
                    continue
                collected.append(line)
                if self.on_output:
                    try:
                        self.on_output(line)
                    except Exception:
                        # A broken listener must not kill the reader thread.
                        pass
        except Exception:
            pass
        finally:
            # The prompt exited on its own. Clear the state so the next command
            # starts a fresh one, then keep the queue moving.
            with self._lock:
                if self._process is process:
                    self._process = None
                self._in_flight = None
            self._pump()

    def _finish(self, collected):
        with self._lock:
            finished = self._in_flight
            self._in_flight = None
        if finished and finished[1]:
            try:
                finished[1]("".join(collected))
            except Exception:
                pass
        self._pump()
