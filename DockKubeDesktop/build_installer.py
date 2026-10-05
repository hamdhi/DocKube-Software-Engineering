"""Build dist\\DocKubeSetup.exe, the installer people actually get.

Usage:
    python build_installer.py            build the app, then the installer
    python build_installer.py --no-app   use the app build already in dist

Why an installer rather than a single .exe:

A onefile build unpacks several hundred DLLs into %TEMP% on every launch, and
antivirus software quarantines them mid-unpack, which produced "Failed to load
Python DLL" on launch. A folder bundle avoids that but means handing someone a
folder. This splits the difference: the bundle stays a folder at runtime, and
the installer is the single file you share. It installs everything, creates a
desktop and Start menu shortcut, and registers a proper uninstaller.

The install directory is under LOCALAPPDATA rather than Program Files, because
Program Files cannot be written without elevation and the in-app Update button
replaces its own files.

Requires Inno Setup 6 (https://jrsoftware.org/isdl.php). If it is not
installed, this script says so instead of failing with a missing compiler.
"""

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(ROOT, "installer.iss")
BUNDLE = os.path.join(ROOT, "dist", "DocKube")
SETUP = os.path.join(ROOT, "dist", "DocKubeSetup.exe")

# ISCC is not on PATH after a normal install, so the usual locations are tried.
CANDIDATES = [
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"),
]


def find_compiler():
    for candidate in CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
    return None


def current_version():
    """Read APP_VERSION out of app_update.py so it cannot drift.

    The installer, the updater and the publish workflow all quote the same
    number, and the test suite asserts the first two agree.
    """
    source = open(os.path.join(ROOT, "app_update.py"), encoding="utf-8").read()
    match = re.search(r'^APP_VERSION = "(.*)"', source, re.MULTILINE)
    return match.group(1) if match else None


def sync_version(version):
    """Write the version into installer.iss before compiling."""
    text = open(SCRIPT, encoding="utf-8").read()
    updated = re.sub(r'#define AppVersion ".*"', f'#define AppVersion "{version}"', text)
    if updated != text:
        with open(SCRIPT, "w", encoding="utf-8") as handle:
            handle.write(updated)


def main():
    version = current_version()
    if not version:
        print("Could not read APP_VERSION from app_update.py")
        return 1

    compiler = find_compiler()
    if not compiler:
        print("Inno Setup 6 was not found.\n\n"
              "Install it from https://jrsoftware.org/isdl.php and run this again.")
        return 1

    if "--no-app" not in sys.argv:
        print("Building the application bundle first...\n")
        result = subprocess.run([sys.executable, os.path.join(ROOT, "build_exe.py")],
                                cwd=ROOT)
        if result.returncode != 0 or not os.path.isdir(BUNDLE):
            print("\nBUILD FAILED: the application bundle is missing")
            return 1

    sync_version(version)
    print(f"Compiling the installer with {compiler}")
    result = subprocess.run([compiler, SCRIPT], cwd=ROOT)
    if result.returncode != 0:
        print("\nBUILD FAILED: the installer did not compile")
        return result.returncode

    if not os.path.isfile(SETUP):
        print("\nBUILD FAILED: dist\\DocKubeSetup.exe was not produced")
        return 1

    size_mb = os.path.getsize(SETUP) / (1024 * 1024)
    print(f"\nBUILD OK: {SETUP}  ({size_mb:.1f} MB)")
    print(f"DocKube {version}. Double-click it to install.")
    print("It installs to %LOCALAPPDATA%\\Programs\\DocKube and creates a")
    print("desktop shortcut. No administrator rights are needed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())