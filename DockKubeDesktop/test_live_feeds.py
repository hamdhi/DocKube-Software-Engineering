"""Validate the live GitHub release feeds both apps' update checks read.

The update flows are only as good as the data GitHub serves, and both apps
read the same two pinned tags: ``desktop-latest`` (app_update.py) and
``android-latest`` (UpdateRepository.kt). These checks hit the real API and
assert exactly what the apps will see:

* the desktop body carries a parseable version and the asset is the zip
  bundle the installer can actually apply, with a sha256 digest;
* the android body is stamped the way build-mobile.yml stamps it and the APK
  is the single release asset, not a stale debug build;
* the published android version matches what is in build.gradle.kts, so a
  freshly cloned repo and the published release can never disagree;
* both download URLs answer.

A network failure SKIPs the whole run so this stays usable offline; data
that comes back wrong from GitHub fails hard.

Usage:
    python test_live_feeds.py
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def get(url):
    request = urllib.request.Request(
        url, headers={"User-Agent": "DocKube-Test",
                      "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def probe(url):
    """Confirm a download URL answers, reading one byte only."""
    request = urllib.request.Request(
        url, headers={"User-Agent": "DocKube-Test"})
    with urllib.request.urlopen(request, timeout=30) as response:
        response.read(1)
        return response.status


try:
    desktop = get("https://api.github.com/repos/hamdhi/DocKube-Software-Engineering"
                  "/releases/tags/desktop-latest")
    android = get("https://api.github.com/repos/hamdhi/DocKube-Software-Engineering"
                  "/releases/tags/android-latest")
except (urllib.error.URLError, OSError) as exc:
    print(f"SKIPPED: cannot reach GitHub ({exc})")
    sys.exit(0)

import app_update  # noqa: E402  (after the skip check, so offline runs never import-fail)

# ---------------------------------------------------------------- desktop ---
print("desktop-latest")
release = app_update.ReleaseInfo(desktop)
check(release.version is not None,
      f"the desktop body carries no version: {desktop.get('body')!r}")
check(release.version == app_update.parse_version(app_update.APP_VERSION),
      f"published {release.version_label()} but the repo says "
      f"{app_update.APP_VERSION} - push the version bump or republish")
check(release.is_bundle,
      f"the desktop asset is {release.asset_name!r}, not the zip bundle; "
      "the in-app installer cannot apply a bare exe over a folder install")
check(bool(release.sha256), "the desktop asset has no sha256 digest")
check(bool(release.download_url), "the desktop asset has no download URL")
status, _ = app_update.assess(release, app_update.APP_VERSION, None)
check(status in ("update", "current", "unknown"),
      f"assess() returned an unknown status: {status!r}")
print(f"  {release.version_label()} asset={release.asset_name} "
      f"sha256={release.sha256[:12]}... status={status}")

# ----------------------------------------------------------------- android ---
print("android-latest")
body = android.get("body") or ""
version = re.search(r"v(\d+\.\d+\.\d+)", body)
code = re.search(r"versionCode (\d+)", body)
check(version is not None,
      f"the android body is not stamped by build-mobile.yml: {body!r}")
check(code is not None,
      f"the android body carries no versionCode: {body!r}")

apks = [a for a in android.get("assets", [])
        if str(a.get("name", "")).lower().endswith(".apk")]
check(len(apks) == 1,
      f"expected exactly one APK asset, got {[a['name'] for a in apks]}")
if apks:
    apk = apks[0]
    check(apk["name"] == "app-release.apk",
          f"the release serves {apk['name']!r}, not the release build")
    digest = str(apk.get("digest") or "")
    check(bool(re.match(r"^sha256:[0-9a-f]{64}$", digest)),
          f"the APK asset has no usable sha256 digest: {digest!r}")
    check(bool(apk.get("browser_download_url")),
          "the APK asset has no download URL")

# The repo and the release must agree, or the in-app update offers a build
# that does not match what a fresh clone produces.
gradle = os.path.join(HERE, os.pardir, "DocKubeAndroid", "app",
                      "build.gradle.kts")
if os.path.isfile(gradle):
    text = open(gradle, encoding="utf-8").read()
    local_name = re.search(r'^ *versionName = "(.*)"', text, re.MULTILINE)
    local_code = re.search(r'^ *versionCode = ([0-9]+)', text, re.MULTILINE)
    if version and local_name:
        check(version.group(1) == local_name.group(1),
              f"published android {version.group(1)} but build.gradle.kts says "
              f"{local_name.group(1)} - the workflow has not republished yet, "
              "or the version bump did not reach both places")
    if code and local_code:
        check(code.group(1) == local_code.group(1),
              f"published versionCode {code.group(1)} but build.gradle.kts says "
              f"{local_code.group(1)}")

if version and code:
    print(f"  DocKube-Android v{version.group(1)} (versionCode {code.group(1)})")
if apks:
    print(f"  asset={apks[0]['name']} size={apks[0]['size']}")

# ------------------------------------------------------- download endpoints ---
print("download endpoints")
try:
    if release.download_url:
        probe(release.download_url)
        print(f"  {release.asset_name}: answers")
    if apks:
        probe(apks[0]["browser_download_url"])
        print(f"  {apks[0]['name']}: answers")
except (urllib.error.URLError, OSError) as exc:
    check(False, f"a published download URL does not answer: {exc}")

if failures:
    print(f"\n{len(failures)} LIVE FEED FAILURES:")
    for failure in failures:
        print("   ", failure)
    sys.exit(1)
print("\nLIVE FEEDS OK: both release feeds are what the apps expect")