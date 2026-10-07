"""Check GitHub for a newer DocKube.exe and put it in place.

The desktop app is a PyInstaller one-file executable, and two consequences
shape this module. A running .exe is locked by Windows, so the process doing
the updating can never overwrite itself; the swap has to happen from outside
after the app closes. And ``sys.executable`` only points at the real
application when frozen, so every path here is derived rather than assumed.

The feed is a pinned tag (``desktop-latest``) rather than a version, so the
newest build is identified two ways: a version line written into the release
body by the publish workflow, and the asset's sha256 as a fallback for
releases published before that line existed.

Blocking throughout. ``app.py`` calls these from a worker thread and comes
back to the Tk thread with ``after()``.
"""

import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile

# Single source of truth for the desktop version. The publish workflow greps
# this line out of the file to stamp the release body, so keep the format.
APP_VERSION = "1.4.2"

RELEASE_URL = ("https://api.github.com/repos/hamdhi/DocKube-Software-Engineering"
               "/releases/tags/desktop-latest")
RELEASES_PAGE = ("https://github.com/hamdhi/DocKube-Software-Engineering"
                 "/releases/tag/desktop-latest")

USER_AGENT = "DocKube-Desktop"
API_ACCEPT = "application/vnd.github+json"

# GitHub reports asset digests as "sha256:<64 hex chars>".
_DIGEST_RE = re.compile(r"^sha256:([0-9a-f]{64})$", re.IGNORECASE)
# Matches the version in a body such as "DocKube-Desktop v1.2.0 (build 42)".
_VERSION_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")

# The published asset has been called both dockube.exe and DocKube.exe over
# time, and the application is now a folder rather than a single file, so the
# download name is a preference rather than a formality. Current builds publish
# DocKubeSetup.exe (the installer) and dockeybe.zip (the folder the in-app
# updater swaps in), so those come first.
_PREFERRED_ASSETS = ("dockeybe.zip", "dockube.zip",
                     "DocKubeSetup.exe", "dockeybe.exe",
                     "dockube.exe", "DocKube.exe")

_CHUNK = 64 * 1024


class UpdateError(Exception):
    """The update check failed, e.g. no network or a 404 from GitHub."""


def parse_version(text):
    """Pull a (major, minor, patch) tuple out of a release body or name.

    Returns None when there is no version to be found, which is what the
    releases published before the workflow started stamping one look like.
    """
    if not text:
        return None
    match = _VERSION_RE.search(str(text))
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def compare_versions(remote, local):
    """Compare two parsed versions. Returns 1, 0 or -1 for newer, same, older.

    Missing components count as zero, so 1.2 and 1.2.0 are the same build.
    A version that could not be parsed compares equal, which makes the caller
    fall back to its other signal rather than guessing in either direction.
    """
    if remote is None or local is None:
        return 0
    width = max(len(remote), len(local))
    padded_remote = tuple(list(remote) + [0] * (width - len(remote)))
    padded_local = tuple(list(local) + [0] * (width - len(local)))
    if padded_remote > padded_local:
        return 1
    if padded_remote < padded_local:
        return -1
    return 0


class ReleaseInfo:
    """The parts of a GitHub release that the update flow actually uses."""

    def __init__(self, payload):
        data = payload or {}
        self.tag = data.get("tag_name", "")
        self.name = data.get("name", "")
        self.body = data.get("body", "") or ""
        self.published_at = data.get("published_at", "")
        self.html_url = data.get("html_url") or RELEASES_PAGE
        asset = select_asset(data.get("assets")) or {}
        self.asset_name = asset.get("name", "")
        self.asset_size = asset.get("size", 0) or 0
        self.download_url = asset.get("browser_download_url", "")
        # True when the asset is a zip of the whole folder, which is what the
        # current build publishes and the only thing that can update it.
        self.is_bundle = self.asset_name.lower().endswith(".zip")
        # GitHub added digests in 2025; an older release simply has none.
        digest = asset.get("digest", "") or ""
        match = _DIGEST_RE.match(str(digest))
        self.sha256 = match.group(1).lower() if match else ""
        # The body is stamped by the workflow, the name is the older fallback.
        self.version = parse_version(self.body) or parse_version(self.name)

    @property
    def size_mb(self):
        return round(self.asset_size / (1024 * 1024), 1) if self.asset_size else 0

    def version_label(self, fallback="unknown"):
        """A dotted version for display, or `fallback` when unparseable."""
        return ".".join(str(part) for part in self.version) if self.version else fallback


def fetch_latest(timeout=15):
    """GET the pinned release and return it as a ReleaseInfo.

    Raises UpdateError with something readable, because the message ends up in
    a dialog box rather than a traceback.
    """
    request = urllib.request.Request(
        RELEASE_URL,
        headers={"Accept": API_ACCEPT, "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise UpdateError(f"GitHub returned HTTP {exc.code} for {RELEASE_URL}") from exc
    except urllib.error.URLError as exc:
        raise UpdateError(f"Could not reach GitHub: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise UpdateError("GitHub sent a reply that was not valid JSON") from exc

    release = ReleaseInfo(payload)
    if not release.download_url:
        raise UpdateError(
            f"The {release.tag} release has no .exe attached to it yet.")
    return release


def assess(release, current_version=APP_VERSION, known_digest=None):
    """Decide whether `release` is newer than what is running.

    Returns ``(status, message)`` where status is one of:

    * ``"update"``  - a genuinely newer build; the download may be offered.
    * ``"current"`` - proven to be the newest build; the download must be
      blocked, because downloading it would change nothing.
    * ``"unknown"`` - the feed carries no version and there is no earlier
      check to compare against. The download stays available, since the user
      may legitimately want the newest build regardless.

    Two signals are used, because the feed is a pinned tag with no version:

    * A parsed version, compared numerically. Exact when the workflow has
      stamped one.
    * The asset sha256 against the digest recorded by the last check, which
      covers releases published before stamping began.
    """
    remote = release.version
    local = parse_version(current_version)

    if remote is not None and local is not None:
        if compare_versions(remote, local) > 0:
            return "update", (f"Version {current_version} is installed; "
                              f"{release.version_label()} is published.")
        return "current", f"DocKube {release.version_label()} is already installed."

    if known_digest and release.sha256 and release.sha256 != known_digest:
        return "update", "A newer build has been published since the last check."

    if known_digest and release.sha256:
        return "current", "The published build matches the last one checked."

    # No version on the release and no previous check to compare against, so
    # there is genuinely nothing to go on. Say that rather than claiming the
    # app is current, which we cannot actually claim.
    return "unknown", ("This release carries no version number and there is no "
                       "earlier check to compare it against, so DocKube cannot "
                       f"tell whether {current_version} is the newest build.")


def select_asset(assets):
    """Return the asset that carries the application, or None.

    The application ships as a folder now, so the publish workflow uploads a
    zip of the whole bundle. A bare .exe is still accepted, because that is
    what older releases contain and what the update path has to keep working.
    A bare .exe cannot update a folder build safely, and install_update says so
    rather than corrupting the installation.
    """
    items = list(assets or [])
    if not items:
        return None

    def named(candidate):
        return next((a for a in items
                     if str(a.get("name", "")).lower() == candidate), None)

    # A zip of the folder is the correct artifact and always wins.
    for archive in ("dockeybe.zip", "dockube.zip"):
        found = named(archive)
        if found:
            return found
    for archive in items:
        if str(archive.get("name", "")).lower().endswith(".zip"):
            return archive

    executables = [a for a in items
                   if str(a.get("name", "")).lower().endswith(".exe")]
    for preferred in ("dockeybe.exe", "dockube.exe"):
        found = named(preferred)
        if found:
            return found
    return executables[0] if executables else None


def current_exe_path():
    """The installed .exe, or None when running from source.

    Frozen, that is the running executable itself. From source there is no
    install target, so the caller is told so rather than being handed a path it
    cannot write to.
    """
    if getattr(sys, "frozen", False):
        return sys.executable
    return None


def install_folder():
    """The folder to replace, which is the whole application.

    A bundle install cannot be updated by replacing one file, because the
    interpreter and every library live in _internal beside the executable.
    This returns that folder, or None when running from source.
    """
    exe = current_exe_path()
    return os.path.dirname(os.path.abspath(exe)) if exe else None


def download(release, dest_path, on_progress=None, chunk=_CHUNK):
    """Stream the release asset to `dest_path` and verify its digest.

    Writes to a .part file and renames only after the bytes are verified, so a
    half-finished download can never be mistaken for a complete one. Returns
    (bytes_written, expected_bytes); either may be 0 when the server does not
    send a length.
    """
    staging = f"{dest_path}.part"
    request = urllib.request.Request(
        release.download_url,
        headers={"Accept": "application/octet-stream", "User-Agent": USER_AGENT},
    )
    digest = hashlib.sha256()
    written = 0
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            total = int(response.headers.get("Content-Length") or 0)
            with open(staging, "wb") as handle:
                while True:
                    block = response.read(chunk)
                    if not block:
                        break
                    handle.write(block)
                    digest.update(block)
                    written += len(block)
                    if on_progress:
                        on_progress(written, total)
        if release.sha256 and digest.hexdigest() != release.sha256:
            raise UpdateError(
                "The download did not match the checksum GitHub published, "
                "so it was discarded.")
        os.replace(staging, dest_path)
        return written, total
    except Exception:
        # Never leave a truncated file that a later step might pick up.
        if os.path.exists(staging):
            os.remove(staging)
        raise


def unpack_bundle(archive_path):
    """Unpack a zip of the application folder and return the folder path.

    The archive is read first and unpacked into a sibling directory, because
    the archive itself lives at `archive_path` and must survive until it has
    been read.

    Zipping a folder usually leaves one wrapping folder inside the archive, so a
    lone directory at the root is stripped to reveal the real contents. The
    result is the folder that gets mirrored over the installation.
    """
    target = archive_path.rstrip("\\/") + "_unpacked"
    if os.path.isdir(target):
        shutil.rmtree(target, ignore_errors=True)
    os.makedirs(target, exist_ok=True)

    with zipfile.ZipFile(archive_path) as archive:
        # Refuse any member that would be written outside the target directory.
        for member in archive.namelist():
            resolved = os.path.abspath(os.path.join(target, member))
            if resolved != os.path.abspath(target) and not resolved.startswith(
                    os.path.abspath(target) + os.sep):
                raise UpdateError(f"the archive contains an unsafe path: {member}")
        archive.extractall(target)

    entries = os.listdir(target)
    # One entry and it is a folder means the zip wrapped everything; step in.
    if len(entries) == 1:
        only = os.path.join(target, entries[0])
        if os.path.isdir(only):
            inner = target + "_inner"
            os.rename(only, inner)
            shutil.rmtree(target, ignore_errors=True)
            os.rename(inner, target)

    # Zipping a folder by path can leave the archive inside the tree.
    for base, _, names in os.walk(target):
        for name in names:
            if name.lower().endswith(".zip"):
                os.remove(os.path.join(base, name))
    return target


# The helper must outlive the app it is updating, so it is fully detached
# rather than a child process that dies with its parent's console.
# CREATE_NO_WINDOW is essential: without it the helper opens a visible
# console that sits on screen running the ping delay while it retries the
# swap, which is the "terminal that says ping and updates nothing" the user
# sees. Detached + new group + no window = invisible background swap.
_DETACHED = (getattr(subprocess, "DETACHED_PROCESS", 0)
             | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
             | getattr(subprocess, "CREATE_NO_WINDOW", 0)
             | 0x08000000)


def _installer_script(staged, target, log_path, is_bundle=False):
    """The batch file that does the swap once the app has exited.

    Windows will not let the running exe be overwritten, so the copy is
    retried for a minute rather than attempted once and silently abandoned.

    For a bundle the whole folder is mirrored instead of a single file being
    copied, because a bundle build keeps roughly a thousand library files
    beside the exe and replacing only the exe would leave the old ones behind.
    robocopy /MIR also removes files the previous version had and this one does
    not, which is what stops stale DLLs accumulating over many updates.

    robocopy's exit code is a bitmask, not pass/fail: 0-7 means the mirror
    worked (1 = files copied, which is the normal success), 8+ means real
    failure. The loop below therefore treats <8 as success and retries
    otherwise. A bare ``if errorlevel 8`` only catches >= 8, and with no goto
    on success the old script fell through the loop into ``:failed`` every
    time: the files were actually replaced but the log claimed failure and
    the app was never restarted. That is why updates "downloaded but did
    nothing".

    Two more traps are defused here:
    * The staged path is verified BEFORE the retry loop. Handing the script
      a zip instead of the extracted folder used to make robocopy fail the
      same way sixty times over two minutes with a console window sitting
      on screen the whole time.
    * The success path ends with ``goto :cleanup``. Without it, execution
      fell straight out of ``:swapped`` into ``:failed`` and wrote the
      failure log even though the update had worked.
    """
    if is_bundle:
        launch = os.path.join(target, "DocKube.exe")
        swap = [
            'robocopy "%SOURCE%" "%TARGET%" /MIR /NFL /NDL /NJH /NJS /NP >NUL 2>&1',
            "if not errorlevel 8 goto :swapped",
        ]
    else:
        launch = target
        swap = [
            'copy /Y "%STAGED%" "%TARGET%" >NUL 2>&1',
            'if not errorlevel 1 goto :swapped',
        ]
    cleanup = ('rmdir /S /Q "%STAGED%" >NUL 2>&1' if is_bundle
               else 'del /F /Q "%STAGED%" >NUL 2>&1')
    retry_block = [
        "rem The staged update must exist before the retries start, otherwise",
        "rem a bad hand-off burns two minutes failing the same way sixty times.",
        'if exist "%SOURCE%\\." goto :staged_ok',
        'if exist "%SOURCE%" goto :staged_ok',
        'echo The staged update is missing: %SOURCE% > "%LOG%"',
        "goto :cleanup",
        "",
        ":staged_ok",
        "rem Wait for the old process to release its lock on the target.",
        "rem timeout (not ping) so no stray terminal output ever appears.",
        "for /L %%i in (1,1,60) do (",
    ] + [f"    {line}" for line in swap] + [
        "    timeout /t 1 /nobreak >NUL",
        ")",
        "goto :failed",
        "",
        ":swapped",
        cleanup,
        'del "%LOG%" >NUL 2>&1',
        'start "" "%LAUNCH%"',
        "goto :cleanup",
        "",
        ":failed",
        "rem The old files are still intact, so the app was not damaged.",
        'echo DocKube could not replace the running app. > "%LOG%"',
        "",
        ":cleanup",
        "endlocal",
        "",
    ]
    return "\r\n".join([
        "@echo off",
        "rem Written by DocKube: waits for the running app to exit, replaces",
        "rem it with the newly downloaded build, then starts the new version.",
        "setlocal",
        f'set "STAGED={staged}"',
        f'set "TARGET={target}"',
        f'set "LAUNCH={launch}"',
        f'set "SOURCE={staged}"',
        f'set "LOG={log_path}"',
        "",
    ] + retry_block)


def install_downloaded(staged, target, log_path=None, is_bundle=False):
    """Launch a detached helper that swaps `staged` into `target` and restarts.

    With `is_bundle`, `staged` is an extracted folder and `target` is the
    installation folder that gets mirrored over; otherwise `staged` is a single
    executable and `target` is the file to overwrite.

    Returns the script path. The caller must close the app afterwards: the
    helper waits for the old process to exit before it can replace anything.
    """
    staged = os.path.abspath(staged)
    target = os.path.abspath(target)
    if log_path is None:
        log_path = os.path.join(os.path.dirname(target), "DocKube-update.log")
    script_dir = tempfile.mkdtemp(prefix="dockeybe_install_")
    script_path = os.path.join(script_dir, "apply_update.bat")
    with open(script_path, "w", encoding="utf-8") as handle:
        handle.write(_installer_script(staged, target, log_path, is_bundle))
    # close_fds must stay False on Windows: True forces the child onto the
    # parent's console (or a new visible one), which overrides CREATE_NO_WINDOW
    # and is exactly the "terminal that says ping" from the screenshot.
    subprocess.Popen(
        ["cmd", "/c", script_path],
        creationflags=_DETACHED,
        close_fds=False,
    )
    return script_path