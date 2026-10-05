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

# Single source of truth for the desktop version. The publish workflow greps
# this line out of the file to stamp the release body, so keep the format.
APP_VERSION = "1.2.0"

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
# time, so the download name is a preference rather than a formality.
_PREFERRED_ASSETS = ("dockeybe.exe", "dockube.exe")

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
        asset = select_exe_asset(data.get("assets")) or {}
        self.asset_name = asset.get("name", "")
        self.asset_size = asset.get("size", 0) or 0
        self.download_url = asset.get("browser_download_url", "")
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

    Two signals, because the feed is a pinned tag with no version in it:

    * A parsed version, compared numerically. Exact when the workflow has
      stamped one.
    * The asset sha256 against the digest recorded by the last check. This
      covers releases published before stamping began. On a first run there
      is nothing to compare, so it reports "up to date" rather than claiming
      an update it cannot substantiate.
    """
    remote = release.version
    local = parse_version(current_version)

    if remote is not None and local is not None:
        if compare_versions(remote, local) > 0:
            return True, f"Version {current_version} is installed; {release.version_label()} is published."
        return False, f"DocKube {release.version_label()} is already installed."

    if known_digest and release.sha256 and release.sha256 != known_digest:
        return True, "A newer build has been published since the last check."

    if known_digest and release.sha256:
        return False, "The published build matches the last one checked."

    # No version on the release and no previous check to compare against, so
    # there is genuinely nothing to go on. Say that rather than implying the
    # app is current, which we cannot actually claim.
    return False, ("This release carries no version number and there is no "
                   "earlier check to compare it against, so DocKube cannot "
                   f"tell whether {current_version} is the newest build.")


def select_exe_asset(assets):
    """Return the application .exe from a release's asset list, or None."""
    executables = [asset for asset in (assets or [])
                   if str(asset.get("name", "")).lower().endswith(".exe")]
    if not executables:
        return None
    for preferred in _PREFERRED_ASSETS:
        for asset in executables:
            if str(asset.get("name", "")).lower() == preferred:
                return asset
    return executables[0]


def current_exe_path():
    """The .exe to replace, or None when running from source.

    Frozen, that is the running executable itself. From source there is no
    single install target, so the caller is told so rather than being handed
    a path it cannot write to.
    """
    if getattr(sys, "frozen", False):
        return sys.executable
    return None


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


# The helper must outlive the app it is updating, so it is fully detached
# rather than a child process that dies with its parent's console.
_DETACHED = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(
    subprocess, "CREATE_NEW_PROCESS_GROUP", 0)


def _installer_script(staged, target, log_path):
    """The batch file that does the swap once the app has exited.

    Windows will not let the running exe be overwritten, so the copy is
    retried for a minute rather than attempted once and silently abandoned.
    """
    return "\r\n".join([
        "@echo off",
        "rem Written by DocKube: waits for the running app to exit, replaces",
        "rem it with the newly downloaded build, then starts the new version.",
        "setlocal",
        f'set "STAGED={staged}"',
        f'set "TARGET={target}"',
        f'set "LOG={log_path}"',
        "",
        "rem Wait for the old process to release its lock on the target.",
        "for /L %%i in (1,1,60) do (",
        "    copy /Y \"%STAGED%\" \"%TARGET%\" >NUL 2>&1 && goto :swapped",
        "    ping -n 2 127.0.0.1 >NUL",
        ")",
        "",
        "rem Still locked after a minute. Keep the download so it is not lost.",
        "echo DocKube could not replace the running app. > \"%LOG%\"",
        "goto :cleanup",
        "",
        ":swapped",
        "del \"%STAGED%\" >NUL 2>&1",
        "del \"%LOG%\" >NUL 2>&1",
        "start \"\" \"%TARGET%\"",
        "",
        ":cleanup",
        "endlocal",
        "",
    ])


def install_downloaded(staged, target, log_path=None):
    """Launch a detached helper that swaps `staged` into `target` and restarts.

    Returns the script path. The caller must close the app afterwards: the
    helper waits for the old process to exit before it can copy anything.
    """
    staged = os.path.abspath(staged)
    target = os.path.abspath(target)
    if log_path is None:
        log_path = os.path.join(os.path.dirname(target), "DocKube-update.log")
    script_dir = tempfile.mkdtemp(prefix="dockeybe_install_")
    script_path = os.path.join(script_dir, "apply_update.bat")
    with open(script_path, "w", encoding="utf-8") as handle:
        handle.write(_installer_script(staged, target, log_path))
    subprocess.Popen(
        ["cmd", "/c", script_path],
        creationflags=_DETACHED,
        close_fds=True,
    )
    return script_path