"""Build dist\\DocKube\\ with PyInstaller.

Usage:
    python build_exe.py            build a fresh application
    python build_exe.py --clean    remove build artefacts first

This builds a **onedir** bundle, not a single .exe. That is deliberate.

A onefile build unpacks roughly 250 DLLs into %TEMP%\\_MEIxxxxxx on every
launch and deletes them afterwards. Antivirus software watches that folder,
and on a machine with ESET installed it quarantines DLLs *during* the unpack.
The app then dies on startup with "Failed to load Python DLL", which looks
like a broken build but is actually antivirus interfering with the temp
extraction.

A ononedir bundle keeps the interpreter and every library in one ordinary
folder next to the app, so there is no unpack step for antivirus to attack
and the folder can be moved or copied anywhere.

The bundled modules are listed explicitly because they are imported by name
rather than discovered, so PyInstaller's static analysis cannot see them.
"""

import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(ROOT, "app.py")
NAME = "DocKube"

# Imported by name, so they must be handed to PyInstaller explicitly.
HIDDEN_IMPORTS = [
    "customtkinter",
    "app_update",
    "fast_scroller",
    "shared_console",
    "learning",
    "learning_index",
    "port_manager",
    "devops_tools",
    "command_specs",
    "docs_content",
    "templates_content",
] + [f"learning_content_{name}" for name in (
    "net1", "net2", "net3", "net4", "net5", "net6", "net7",
    "linux", "se", "sysadmin", "agile", "aws", "delivery", "devops",
    "security", "firewall", "diagrams", "database",
    "observability", "sre", "cloud", "fintech", "business",
)]

# tkinter can drag large unrelated packages into the bundle when they happen to
# be installed. DocKube does no image or array work, so keep them out; this is
# the difference between a 14 MB and a 31 MB executable.
EXCLUDES = [
    "PIL", "Pillow", "numpy", "pandas", "matplotlib", "scipy",
    "PyQt5", "PyQt6", "PySide2", "PySide6", "pytest", "setuptools",
    "pip", "unittest", "pydoc", "doctest", "lib2to3", "distutils",
]

# tkinter data files that the frozen build needs on disk.
DATAS = []
if hasattr(sys, "frozen"):
    DATAS = []
else:
    import customtkinter

    package_root = os.path.dirname(customtkinter.__file__)
    DATAS.append((os.path.join(package_root, "assets"),
                  os.path.join("customtkinter", "assets")))


def clean():
    """Remove build and dist folders so the build starts from scratch."""
    for folder in ("build", "dist"):
        target = os.path.join(ROOT, folder)
        if os.path.isdir(target):
            print(f"removing {folder}/")
            shutil.rmtree(target, ignore_errors=True)


def main():
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller is not installed.")
        print("Run:  python -m pip install pyinstaller")
        return 1

    if "--clean" in sys.argv:
        clean()

    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        # A folder, not a single file. See the module docstring for why.
        "--onedir",
        "--windowed",
        "--name", NAME,
        "--hidden-import", "customtkinter",
    ]
    for module in HIDDEN_IMPORTS:
        command += ["--hidden-import", module]
    for module in EXCLUDES:
        command += ["--exclude-module", module]
    for source, destination in DATAS:
        command += ["--add-data", f"{source}{os.pathsep}{destination}"]
    command.append(APP)

    print("\n".join(command))
    print("\nBuilding, this takes a minute or two...\n")
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        print("\nBUILD FAILED")
        return result.returncode

    bundle = os.path.join(ROOT, "dist", NAME)
    built = os.path.join(bundle, f"{NAME}.exe")
    if not os.path.isfile(built):
        print(f"\nBUILD FAILED: {built} was not produced")
        return 1
    # A onedir bundle is incomplete without the library folder next to the exe,
    # and that is the failure the user actually sees at runtime.
    internal = os.path.join(bundle, "_internal")
    if not os.path.isdir(internal):
        print(f"\nBUILD FAILED: {internal} is missing, the bundle cannot run")
        return 1

    def folder_size(path):
        return sum(os.path.getsize(os.path.join(base, name))
                   for base, _, names in os.walk(path) for name in names)

    size_mb = folder_size(bundle) / (1024 * 1024)
    libraries = sum(len(names) for _, _, names in os.walk(internal))
    print(f"\nBUILD OK: {bundle}  ({size_mb:.1f} MB, {libraries} bundled libraries)")
    print("The whole folder must be kept together: it is the application.")
    print(f"Run it with: {built}")
    return 0


if __name__ == "__main__":
    sys.exit(main())