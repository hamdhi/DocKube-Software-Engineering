"""Build dist\\DocKube.exe with PyInstaller.

Usage:
    python build_exe.py            build a fresh executable
    python build_exe.py --clean    remove build artefacts first

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
        "--onefile",
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

    built = os.path.join(ROOT, "dist", f"{NAME}.exe")
    if not os.path.isfile(built):
        print("\nBUILD FAILED: dist\\DocKube.exe was not produced")
        return 1

    size_mb = os.path.getsize(built) / (1024 * 1024)
    print(f"\nBUILD OK: {built}  ({size_mb:.1f} MB)")
    print(f"Double-click DocKube.bat, or run dist\\{NAME}.exe directly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())