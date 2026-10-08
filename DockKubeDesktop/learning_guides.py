"""Load the production-programming learning guides shipped as markdown.

The guides live as plain ``.md`` files in ``docs/learning`` at the repository
root.  They are read at runtime rather than pasted into Python so a single
edit to a markdown file updates both the desktop app and (via the exported
JSON) the phone app.

Three locations are probed, in order:

1. Next to this module (the repository layout: ``DockKubeDesktop/../docs``)
   - this is what a development checkout uses.
2. Under ``sys._MEIPASS`` (the PyInstaller bundle) - the build adds
   ``docs/learning`` as data, so a frozen ``DocKube.exe`` finds them there.
3. A ``docs/learning`` folder beside the executable, for completeness.

If nothing is found the module degrades to an empty list; the panel then
tells the user the guides are unavailable instead of crashing the app.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

_CANDIDATE_DIRS = [
    os.path.join(os.path.dirname(_HERE), "docs", "learning"),
    os.path.join(getattr(sys, "_MEIPASS", _HERE), "docs", "learning"),
    os.path.join(os.path.dirname(sys.executable), "docs", "learning"),
]


def _guide_dir():
    for candidate in _CANDIDATE_DIRS:
        if os.path.isdir(candidate):
            return candidate
    return None


def _title_for(filename):
    """Turn ``01_pydantic_v2.md`` into ``pydantic v2``."""
    stem = os.path.splitext(filename)[0]
    # Strip the two-digit ordering prefix and any remaining digits, then
    # make the first letter lowercase so buttons read like topic names.
    parts = stem.split("_", 1)
    name = parts[1] if len(parts) > 1 else parts[0]
    while name[:1].isdigit():
        name = name[1:].lstrip("0123456789_")
    if name[:1].isdigit():
        name = name.lstrip("0123456789_")
    return name.replace("_", " ")


def load_guides():
    """Return ``[(title, markdown), ...]`` ordered by the file name."""
    folder = _guide_dir()
    if folder is None:
        return []
    guides = []
    for filename in sorted(os.listdir(folder)):
        if not filename.endswith(".md") or filename.startswith("_"):
            continue
        try:
            with open(os.path.join(folder, filename), encoding="utf-8") as handle:
                body = handle.read()
        except OSError:
            continue
        if body.strip():
            guides.append((_title_for(filename), body))
    return guides


def guide_titles():
    return [title for title, _ in load_guides()]


if __name__ == "__main__":
    found = load_guides()
    print(f"{len(found)} guides in {_guide_dir()}")
    for title, body in found:
        print(f"  {title:32s} {len(body):6d} bytes")
