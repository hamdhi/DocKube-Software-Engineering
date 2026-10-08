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
import shutil
import subprocess
import sys
import tempfile

import app_update

HERE = os.path.dirname(os.path.abspath(__file__))
# The onedir bundle, used both as the thing an update mirrors over an
# installation and as the thing the packaging checks look for.
BUNDLE = os.path.join(HERE, "dist", "DocKube")

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
check(app_update.select_asset(assets)["name"] == "DocKube.exe",
      "DocKube.exe must win over the other executables")
check(app_update.select_asset([{"name": "other.exe"}])["name"] == "other.exe",
      "an unlisted executable should still be usable")
check(app_update.select_asset([{"name": "readme.md"}]) is None,
      "picked an artifact out of a release with none")
check(app_update.select_asset([]) is None, "an empty asset list should give None")
check(app_update.select_asset(None) is None, "a missing asset list should give None")

# A folder build publishes a zip, and that zip is the only artifact that can
# update a folder install, so it has to win over any loose .exe.
print("\nasset selection: the bundle zip wins")
mixed = [{"name": "dockube.exe", "size": 1}, {"name": "dockube.zip", "size": 30}]
check(app_update.select_asset(mixed)["name"] == "dockube.zip",
      "the bundle zip must be preferred over a loose exe")
check(app_update.ReleaseInfo(payload(assets=[
    {"name": "dockube.zip", "size": 30, "digest": "sha256:" + "c" * 64,
     "browser_download_url": "u"}])).is_bundle,
    "a .zip asset must be marked as a bundle")
check(not app_update.ReleaseInfo(payload()).is_bundle,
      "an .exe asset must not be marked as a bundle")

# ------------------------------------------------------------------ assess
print("\nupdate decision")
stamped = app_update.ReleaseInfo(payload(body="DocKube-Desktop v2.0.0 (build 9)"))
state, message = app_update.assess(stamped, "1.1.0")
check(state == "update", f"2.0.0 should be newer than 1.1.0 ({state})")
state, message = app_update.assess(stamped, "2.0.0")
check(state == "current", f"2.0.0 against 2.0.0 should be current ({state})")
state, message = app_update.assess(stamped, "9.9.9")
check(state == "current", f"1.1.0 against 9.9.9 should be current ({state})")

# The UI blocks the download on exactly "current", so a build that is already
# installed must never come back as "update".
same, _ = app_update.assess(stamped, "2.0.0")
check(same != "update", "the installed version must never be offered as an update")

# An unstamped release is the real case in the wild right now.
unstamped = app_update.ReleaseInfo(payload())
check(unstamped.version is None, "the live release should have no parseable version")
state, message = app_update.assess(unstamped, "1.1.0", known_digest="b" * 64)
check(state == "update", "a changed digest with no version should report an update")
state, message = app_update.assess(unstamped, "1.1.0", known_digest=unstamped.sha256)
check(state == "current", "an unchanged digest must report current, blocking the download")
state, message = app_update.assess(unstamped, "1.1.0")
check(state == "unknown", "with nothing to compare the state must be unknown")
check(state != "current", "an undecidable check must not claim to be up to date")
check(state != "update", "an undecidable check must not invent an update")
check("cannot tell" in message, f"an undecidable check should say so ({message})")

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

# A real folder swap, using the real generated script, proves the mirror works
# and that stale libraries are removed. Running the script rather than just
# inspecting it is the only way to catch a broken batch file.
old_install = tempfile.mkdtemp(prefix="dockeybe_old_")
os.makedirs(os.path.join(old_install, "_internal"), exist_ok=True)
open(os.path.join(old_install, "DocKube.exe"), "w").write("OLD-EXE")
open(os.path.join(old_install, "_internal", "old.dll"), "w").write("OLD")

staged_build = tempfile.mkdtemp(prefix="dockeybe_new_")
os.makedirs(os.path.join(staged_build, "_internal"), exist_ok=True)
open(os.path.join(staged_build, "DocKube.exe"), "w").write("NEW-EXE")
open(os.path.join(staged_build, "_internal", "new.dll"), "w").write("NEW")

batch = app_update._installer_script(
    staged_build, old_install, os.path.join(old_install, "upd.log"), True)
# The relaunch is stubbed out so the test does not start a second copy of the
# app. Everything else, including the robocopy mirror, runs for real.
batch = batch.replace('start "" "%LAUNCH%"', "rem launch stubbed")
script_path = os.path.join(tmp, "swap_test.bat")
with open(script_path, "w", encoding="utf-8", newline="") as handle:
    handle.write(batch)
result = subprocess.run(["cmd", "/c", script_path], capture_output=True,
                        text=True, timeout=180)
check(result.returncode == 0,
      f"the folder swap script failed: {result.stderr[:200]}")
check(open(os.path.join(old_install, "DocKube.exe")).read() == "NEW-EXE",
      "the exe was not replaced")
check(os.path.isfile(os.path.join(old_install, "_internal", "new.dll")),
      "the new libraries were not installed")
check(not os.path.exists(os.path.join(old_install, "_internal", "old.dll")),
      "the mirror left a stale library behind")
print("folder swap: exe replaced, new libraries in, stale ones removed")

shutil.rmtree(old_install, ignore_errors=True)
shutil.rmtree(staged_build, ignore_errors=True)

# --------------------------------------- updating the real install folder
# The promise is "update by clicking the button", which means swapping a
# staged bundle over %LOCALAPPDATA%\Programs\DocKube while it is installed.
# This runs that swap against a real folder-shaped stand-in, using the real
# generated batch file, because that is the only way to know the mirror
# actually replaces an installed application.
installed = tempfile.mkdtemp(prefix="dockeybe_installed_")
os.makedirs(os.path.join(installed, "_internal"), exist_ok=True)
open(os.path.join(installed, "DocKube.exe"), "w").write("OLD-EXE")
open(os.path.join(installed, "_internal", "OLDSTALE.dll"), "w").write("stale")

staged_update = tempfile.mkdtemp(prefix="dockeybe_staged_")
shutil.copytree(BUNDLE, os.path.join(staged_update, "DocKube"))
swap_batch = app_update._installer_script(
    os.path.join(staged_update, "DocKube"), installed,
    os.path.join(installed, "upd.log"), True)
swap_batch = swap_batch.replace('start "" "%LAUNCH%"', "rem launch stubbed")
swap_script = os.path.join(tmp, "installed_swap.bat")
with open(swap_script, "w", encoding="utf-8", newline="") as handle:
    handle.write(swap_batch)
swapped = subprocess.run(["cmd", "/c", swap_script], capture_output=True,
                         text=True, timeout=300)
check(swapped.returncode == 0,
      f"the install swap failed: {swapped.stderr[:200]}")
check(os.path.isfile(os.path.join(installed, "_internal", "python314.dll")),
      "the interpreter was not installed by the update")
check(not os.path.exists(os.path.join(installed, "_internal", "OLDSTALE.dll")),
      "the update left a stale library in the installed application")
print("installed folder updated: interpreter in place, stale files cleared")

shutil.rmtree(installed, ignore_errors=True)
shutil.rmtree(staged_update, ignore_errors=True)

# -------------------------------------------------------- installer script
print("\ninstaller script")
check(app_update.current_exe_path() is None,
      "running from source, so there should be no executable to replace")
check(app_update.install_folder() is None,
      "running from source, so there should be no install folder to replace")

single = app_update._installer_script(r"C:\tmp\new.exe", r"C:\app\DocKube.exe", r"C:\app\log.txt")
check("@echo off" in single, "the installer script is not a batch file")
check(r'"STAGED=C:\tmp\new.exe"' in single, "the staged path is missing")
check(r'"TARGET=C:\app\DocKube.exe"' in single, "the target path is missing")
check("copy /Y" in single, "the single-file script never copies anything")
check("start" in single, "the script does not restart the app")
check("for /L" in single, "the script does not retry the locked copy")
check('set "PYINSTALLER_RESET_ENVIRONMENT=1"' in single,
      "the restarted app does not get a fresh PyInstaller runtime")

# The folder build has a thousand libraries beside the exe, so replacing one
# file would leave the old ones behind. The bundle path must mirror the folder.
bundle = app_update._installer_script(r"C:\tmp\staged", r"C:\app\DocKube", r"C:\app\log.txt", True)
check("robocopy" in bundle, "the bundle script does not mirror the folder")
check("/MIR" in bundle, "the bundle script must mirror, so stale files are removed")
check("copy /Y" not in bundle, "the bundle script must not copy a single file")
check(r'"TARGET=C:\app\DocKube"' in bundle, "the target folder is missing")
check('set "PYINSTALLER_RESET_ENVIRONMENT=1"' in bundle,
      "the restarted bundle does not get a fresh PyInstaller runtime")

# ------------------------------------------- the two update-blocking regressions
# 1. Success must not fall through into :failed. The :swapped block used to end
#    at the relaunch with no goto, so execution walked straight into :failed
#    and wrote "could not replace the running app" even when it had.
for name, script in (("single", single), ("bundle", bundle)):
    lines = [l for l in script.splitlines() if l.strip()]
    start = next(i for i, l in enumerate(lines) if l.startswith("start "))
    check(lines[start - 1] == 'set "PYINSTALLER_RESET_ENVIRONMENT=1"',
          f"{name}: the PyInstaller runtime reset is not set before restart")
    check(lines[start + 1] == "goto :cleanup",
          f"{name}: the success path falls through past 'start' "
          f"(next line is {lines[start + 1]!r}, want 'goto :cleanup')")
    failed = lines.index(":failed")
    check(start < failed, f"{name}: ':failed' appears before the success path")

# 2. A missing staged path must fail fast. Handing the script something that
#    is not there (historically: the zip instead of the extracted folder) used
#    to burn sixty retries - two minutes of a console window on screen - before
#    giving up. The timeout below is the assertion: without the pre-check this
#    script runs for ~120 seconds and the test dies on the timeout.
missing = app_update._installer_script(
    r"C:\tmp\really_not_here", r"C:\app\DocKube",
    os.path.join(tmp, "missing.log"), True)
check('if exist "%SOURCE%' in missing,
      "the script does not pre-check the staged path before retrying")
missing = missing.replace('start "" "%LAUNCH%"', "rem launch stubbed")
fast_path = os.path.join(tmp, "missing_staged.bat")
with open(fast_path, "w", encoding="utf-8", newline="") as handle:
    handle.write(missing)
fast = subprocess.run(["cmd", "/c", fast_path], capture_output=True,
                      text=True, timeout=60)
check(os.path.isfile(os.path.join(tmp, "missing.log")),
      "the fast-fail path did not write its log")
check("staged update is missing" in open(os.path.join(tmp, "missing.log"),
                                         encoding="utf-8", errors="replace").read(),
      "the fast-fail log does not say what was missing")
print("installer script: success path cleans up, missing staged fails fast")

# ------------------------------------- app.py must pass the unpacked folder
# unpack_bundle RETURNS the extracted folder; app.py once threw that away and
# handed the installer the zip path itself, so robocopy retried against a file
# and the update silently never applied. The contract lives in source, because
# exercising it end to end would need a frozen executable.
app_src = open(os.path.join(HERE, "app.py"), encoding="utf-8").read()
check("staged = app_update.unpack_bundle(staged)" in app_src,
      "app.py discards unpack_bundle's return value, so the installer would be "
      "handed the zip instead of the extracted folder and never update")
print("app.py: unpack_bundle return value is handed to the installer")

# -------------------------------------------------------------- unpack
print("\nbundle unpack")
check(hasattr(app_update, "unpack_bundle"), "unpack_bundle is missing")
import zipfile

zdir = tempfile.mkdtemp(prefix="dockeybe_zip_")
flat = os.path.join(zdir, "flat.zip")
with zipfile.ZipFile(flat, "w") as z:
    z.writestr("DocKube.exe", "binary")
    z.writestr("_internal/python314.dll", "lib")
out = app_update.unpack_bundle(flat)
check(os.path.isfile(os.path.join(out, "DocKube.exe")), "flat zip: exe missing")
check(os.path.isdir(os.path.join(out, "_internal")), "flat zip: _internal missing")

# Zipping a folder by path wraps everything in one folder, which must be
# stripped or the mirror would nest the application inside itself.
wrapped = os.path.join(zdir, "wrapped.zip")
with zipfile.ZipFile(wrapped, "w") as z:
    z.writestr("DocKube/DocKube.exe", "binary")
    z.writestr("DocKube/_internal/python314.dll", "lib")
out = app_update.unpack_bundle(wrapped)
check(os.path.isfile(os.path.join(out, "DocKube.exe")),
      f"wrapped zip was not unwrapped, got {sorted(os.listdir(out))}")
check(os.path.isdir(os.path.join(out, "_internal")),
      "wrapped zip: _internal missing after unwrapping")

# A path that escapes the target directory must be refused outright.
evil = os.path.join(zdir, "evil.zip")
with zipfile.ZipFile(evil, "w") as z:
    z.writestr("../../escaped.txt", "bad")
try:
    app_update.unpack_bundle(evil)
    failures.append("a zip-slip archive was extracted instead of refused")
except app_update.UpdateError:
    check(True, "")

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
        # The exact body build-mobile.yml publishes.
        stamped = f"DocKube-Android v{name.group(1)} (versionCode {code.group(1)})"
        check(app_update.parse_version(stamped) is not None,
              f"the app cannot read a version back out of {stamped!r}")
        # Android refuses to install an APK whose versionCode is not higher than
        # the installed one. If this ever stops rising, the in-app update
        # downloads an APK the installer then rejects.
        check(int(code.group(1)) > 2,
              f"versionCode is {code.group(1)}; it must keep rising or the "
              "package installer will reject the update")
        print("release body:", stamped)
else:
    print("build.gradle.kts not found next to the desktop app; skipped")

# The desktop installer tracks the desktop updater version, independently of
# the Android app's versionName.
iss = os.path.join(HERE, "installer.iss")
if os.path.isfile(iss):
    text = open(iss, encoding="utf-8").read()
    declared = re.search(r'#define AppVersion "(.*)"', text)
    check(declared is not None, "installer.iss has no AppVersion")
    if declared:
        check(declared.group(1) == app_update.APP_VERSION,
              f"the installer says {declared.group(1)} but the desktop app "
              f"reports {app_update.APP_VERSION}")
        print("desktop installer version:", declared.group(1))

# ------------------------------------------------ the frozen build has it
# PyInstaller bundles only what --hidden-import names, so a module that
# imports cleanly from source can still be missing from the bundle. The only
# way to know is to look at the archive the build actually produced.
toc = os.path.join(HERE, "build", "DocKube", "PYZ-00.toc")
exe = os.path.join(BUNDLE, "DocKube.exe")
internal = os.path.join(BUNDLE, "_internal")
if os.path.isfile(toc) and os.path.isfile(exe):
    contents = open(toc, encoding="utf-8", errors="replace").read()
    check("'app_update'" in contents,
          "app_update is not in the frozen build; the Update button would "
          "raise ImportError in the exe")
    # The onedir bundle is only complete with its library folder. Missing it is
    # exactly what produces "Failed to load Python DLL" on another machine.
    check(os.path.isdir(internal),
          "the build has no _internal folder, so the bundle cannot run")
    check(os.path.getsize(exe) > 0, "the built exe is empty")
    total = sum(os.path.getsize(os.path.join(base, name))
                for base, _, names in os.walk(bundle) for name in names)
    print(f"frozen bundle: {total / (1024 * 1024):.1f} MB in dist\\DocKube, "
          "app_update bundled")
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
