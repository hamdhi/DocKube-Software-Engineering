r"""The self-updater must never act on a build it cannot identify.

DocKube updates itself from a pinned GitHub tag that carries no version
number, so the parsing that decides "is there something newer" is the part
most likely to go quietly wrong. A mistake here either hides a real update
or offers one that does not exist.

It also pins the APP_VERSION line format, because build-desktop.yml lifts the
version straight out of this module to stamp the release body:

    sed -n 's/^APP_VERSION = "\(.*\)"/\1/p' app_update.py

Offline: every case below is built from a synthetic payload, so this runs
anywhere without touching the network.

Usage:
    python test_app_update.py
"""
import hashlib
import os
import re
import sys
import tempfile

import app_update

HERE = os.path.dirname(os.path.abspath(__file__))

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def payload(**overrides):
    """A minimal but realistic GitHub release payload."""
    data = {
        "tag_name": "desktop-latest",
        "name": "Latest Desktop Build",
        "body": "",
        "published_at": "2026-10-05T04:16:41Z",
        "html_url": app_update.RELEASES_PAGE,
        "assets": [{
            "name": "dockube.exe",
            "size": 14669779,
            "digest": "sha256:" + "a" * 64,
            "browser_download_url": "https://example.invalid/dockube.exe",
        }],
    }
    data.update(overrides)
    return data


print("APP_VERSION:", app_update.APP_VERSION)
check(bool(app_update.APP_VERSION), "APP_VERSION is empty")
check("releases/tags/desktop-latest" in app_update.RELEASE_URL,
      "RELEASE_URL does not point at the desktop-latest tag")

# The workflow lifts the version out of this file, so the line it greps for
# has to exist verbatim. Asserted here because reformatting it would only
# show up later as an update check that never sees a version.
source = open(os.path.join(HERE, "app_update.py"), encoding="utf-8").read()
stamp = re.search(r'^APP_VERSION = "(.*)"', source, re.MULTILINE)
check(stamp is not None,
      "no 'APP_VERSION = \"x.y.z\"' line for the workflow's sed to read")
if stamp:
    check(stamp.group(1) == app_update.APP_VERSION,
          "the workflow would stamp a different version than the app reports")

# ---------------------------------------------------------------- versions
print("\nversion parsing")
check(app_update.parse_version("DocKube-Desktop v1.2.0 (build 42)") == (1, 2, 0),
      "did not parse a stamped body")
check(app_update.parse_version("DocKube v2.0.1") == (2, 0, 1),
      "did not parse a version without a build stamp")
check(app_update.parse_version("Latest Desktop Build") is None,
      "invented a version out of a plain release name")
check(app_update.parse_version("") is None, "parsed a version out of an empty body")
check(app_update.parse_version(None) is None, "did not handle a missing body")

print("version comparison")
check(app_update.compare_versions((1, 2, 0), (1, 2, 0)) == 0, "equal versions compared unequal")
check(app_update.compare_versions((1, 2, 3), (1, 2, 0)) == 1, "1.2.3 should beat 1.2.0")
check(app_update.compare_versions((1, 10, 0), (1, 9, 0)) == 1, "10 must beat 9, not compare as 1 > 9")
check(app_update.compare_versions((2, 0, 0), (1, 99, 99)) == 1, "major bump lost to minor padding")
check(app_update.compare_versions((1, 2), (1, 2, 0)) == 0, "1.2 and 1.2.0 should be the same build")
check(app_update.compare_versions(None, (1, 0, 0)) == 0, "an unknown version must not claim to be newer")

# ------------------------------------------------------------------ assets
print("\nasset selection")
assets = [{"name": "notes.txt"}, {"name": "setup.exe.blockmap"},
          {"name": "Other.exe"}, {"name": "DocKube.exe"}, {"name": "dockube.exe"}]
check(app_update.select_exe_asset(assets)["name"] == "DocKube.exe",
      "DocKube.exe must win over the other executables")
check(app_update.select_exe_asset([{"name": "other.exe"}])["name"] == "other.exe",
      "an unlisted executable should still be usable")
check(app_update.select_exe_asset([{"name": "readme.md"}]) is None,
      "picked an executable out of a release with none")
check(app_update.select_exe_asset([]) is None, "an empty asset list should give None")
check(app_update.select_exe_asset(None) is None, "a missing asset list should give None")

# ------------------------------------------------------------------ assess
print("\nupdate decision")
stamped = app_update.ReleaseInfo(payload(body="DocKube-Desktop v2.0.0 (build 9)"))
newer, message = app_update.assess(stamped, "1.1.0")
check(newer, f"2.0.0 should be newer than 1.1.0 ({message})")
newer, message = app_update.assess(stamped, "2.0.0")
check(not newer, f"2.0.0 should not beat 2.0.0 ({message})")
newer, message = app_update.assess(stamped, "9.9.9")
check(not newer, f"1.1.0 should not beat 9.9.9 ({message})")

# An unstamped release is the real case in the wild right now.
unstamped = app_update.ReleaseInfo(payload())
check(unstamped.version is None, "the live release should have no parseable version")
newer, message = app_update.assess(unstamped, "1.1.0", known_digest="b" * 64)
check(newer, "a changed digest with no version should still report an update")
newer, message = app_update.assess(unstamped, "1.1.0", known_digest=unstamped.sha256)
check(not newer, "an unchanged digest must not report an update")
newer, message = app_update.assess(unstamped, "1.1.0")
check(not newer, "with nothing to compare, an update must not be invented")
# ---------------------------------------------------------------- download
print("\ndownload verification")
tmp = tempfile.mkdtemp(prefix="dockeybe_test_")


class _FakeResponse:
    """Just enough of a urlopen result for the download loop."""

    headers = {}

    def __init__(self, body):
        self._body = body

    def read(self, size=-1):
        chunk, self._body = self._body, b""
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def with_body(body):
    """Serve `body` for the next urlopen call, then restore the real one."""
    real = app_update.urllib.request.urlopen
    app_update.urllib.request.urlopen = lambda *a, **k: _FakeResponse(body)
    return real


# A body that does not match the published digest must be rejected, and must
# leave nothing behind that a later step could mistake for a good download.
corrupt = app_update.ReleaseInfo(payload())
real = with_body(b"not the right bytes")
target = os.path.join(tmp, "DocKube.exe")
try:
    try:
        app_update.download(corrupt, target)
        failures.append("a corrupt download was accepted")
    except app_update.UpdateError:
        check(not os.path.exists(target), "the corrupt file was left on disk")
        check(not os.path.exists(target + ".part"), "the .part file was left on disk")
finally:
    app_update.urllib.request.urlopen = real

# A matching digest is written through to the final name.
good_bytes = b"correct bytes"
good_digest = "sha256:" + hashlib.sha256(good_bytes).hexdigest()
good = app_update.ReleaseInfo(payload(assets=[{
    "name": "dockube.exe",
    "size": len(good_bytes),
    "digest": good_digest,
    "browser_download_url": "https://example.invalid/dockube.exe",
}]))
real = with_body(good_bytes)
target = os.path.join(tmp, "DocKube.exe")
try:
    written, _total = app_update.download(good, target)
    check(written == len(good_bytes), f"wrote {written} bytes, expected {len(good_bytes)}")
    with open(target, "rb") as handle:
        check(handle.read() == good_bytes, "the downloaded bytes are wrong")
    check(not os.path.exists(target + ".part"), "the .part file survived a good download")
finally:
    app_update.urllib.request.urlopen = real

# A release with no digest must still download, since there is nothing to
# verify against and refusing would break every pre-digest release.
undigested = app_update.ReleaseInfo(payload(assets=[{"name": "dockube.exe",
                                                     "browser_download_url": "https://example.invalid/x.exe"}]))
real = with_body(b"anything at all")
nodigest_target = os.path.join(tmp, "nodigest.exe")
try:
    app_update.download(undigested, nodigest_target)
    check(os.path.exists(nodigest_target), "a release with no digest refused to download")
finally:
    app_update.urllib.request.urlopen = real

# -------------------------------------------------------- installer script
print("\ninstaller script")
check(app_update.current_exe_path() is None,
      "running from source, so there should be no executable to replace")

script = app_update._installer_script(r"C:\tmp\new.exe", r"C:\app\DocKube.exe", r"C:\app\log.txt")
check("@echo off" in script, "the installer script is not a batch file")
check(r'"STAGED=C:\tmp\new.exe"' in script, "the staged path is missing")
check(r'"TARGET=C:\app\DocKube.exe"' in script, "the target path is missing")
check("copy /Y" in script, "the script never copies anything")
check("start" in script, "the script does not restart the app")
check("for /L" in script, "the script does not retry the locked copy")

# --------------------------------------------------- the workflow's stamp
# build-mobile.yml lifts versionName and versionCode out of this file to stamp
# the release body, and the app parses that line back out. Asserting the
# extraction here means a reformatting cannot quietly stop the update check.
gradle = os.path.join(HERE, "..", "DocKubeAndroid", "app", "build.gradle.kts")
if os.path.isfile(gradle):
    text = open(gradle, encoding="utf-8").read()
    name = re.search(r'^ *versionName = "(.*)"', text, re.MULTILINE)
    code = re.search(r'^ *versionCode = ([0-9]+)', text, re.MULTILINE)
    check(name is not None, "no versionName line for the workflow to read")
    check(code is not None, "no versionCode line for the workflow to read")
    if name and code:
        # This is the exact body build-mobile.yml publishes.
        stamped = f"DocKube-Android v{name.group(1)} (versionCode {code.group(1)})"
        check(app_update.parse_version(stamped) is not None,
              f"the app cannot read a version back out of {stamped!r}")
        print("release body:", stamped)
else:
    print("build.gradle.kts not found next to the desktop app; skipped")

# ------------------------------------------------ the frozen build has it
# PyInstaller bundles only what --hidden-import names, so a module that
# imports cleanly from source can still be missing from the .exe. The only
# way to know is to look at the archive the build actually produced.
toc = os.path.join(HERE, "build", "DocKube", "PYZ-00.toc")
exe = os.path.join(HERE, "dist", "DocKube.exe")
if os.path.isfile(toc) and os.path.isfile(exe):
    contents = open(toc, encoding="utf-8", errors="replace").read()
    check("'app_update'" in contents,
          "app_update is not in the frozen build; the Update button would "
          "raise ImportError in the .exe")
    check(os.path.getsize(exe) > 0, "the built exe is empty")
    print(f"frozen exe: {os.path.getsize(exe) / (1024 * 1024):.1f} MB, app_update bundled")
else:
    print("no frozen build present; skipped the packaging check")

if failures:
    print(f"\n{len(failures)} UPDATE FAILURES:")
    for failure in failures:
        print("   ", failure)
    sys.exit(1)
print("\nAPP UPDATE TEST PASSED")
check("cannot tell" in message,
      f"an undecidable check should say so, not claim to be up to date ({message})")

# -------------------------------------------------------- release metadata
print("\nrelease metadata")
info = app_update.ReleaseInfo(payload())
check(info.tag == "desktop-latest", "tag_name not read")
check(info.asset_name == "dockube.exe", "asset name not read")
check(abs(info.size_mb - 14.0) < 0.1, f"size_mb looks wrong: {info.size_mb}")
check(len(info.sha256) == 64, "sha256 digest not extracted")
check(info.download_url.endswith("dockube.exe"), "download url not read")

# A release with no digest is legal; it must not invent one.
nodigest = app_update.ReleaseInfo(payload(assets=[{"name": "dockube.exe", "size": 10}]))
check(nodigest.sha256 == "", "invented a digest for a release that has none")
check(nodigest.size_mb == 0.0, "invented a size for a release that has none")