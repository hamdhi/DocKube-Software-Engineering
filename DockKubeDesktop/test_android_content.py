"""Check the JSON that will ship inside the APK.

The phone app reads android_content.json and nothing else, so if that file is
malformed or empty the app would launch to a blank screen with no clue why.
This validates the exact file that is packaged, not a copy of it.

Usage:
    python test_android_content.py
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, "android_content.json")
# The Android project is a sibling of this folder, not a child, so this has to
# step up one level. It pointed here before, which made the check below always
# report the packaged copy missing.
SHIPPED = os.path.join(HERE, os.pardir, "DocKubeAndroid", "app", "src", "main",
                       "assets", "android_content.json")

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


with open(CONTENT, encoding="utf-8") as handle:
    data = json.load(handle)

categories = data["categories"]
commands = data["commands"]
chapters = data["chapters"]

print(f"categories: {len(categories)}")
print(f"chapters  : {len(chapters)}")

# The desktop app's own sidebar plus the Learning Guides section. Both must
# agree: the JSON is supposed to be exactly what the desktop app would draw.
# Parse the hardcoded self.categories list out of app.py without importing Tk.
import re as _re
_app_src = open(os.path.join(HERE, "app.py"), encoding="utf-8").read()
_m = _re.search(r"self\.categories\s*=\s*\[(.*?)\]", _app_src, _re.DOTALL)
if _m:
    _app_cats = _re.findall(r'"([^"]+)"', _m.group(1))
    check(list(categories) == _app_cats,
          f"JSON categories drifted from app.py: json={list(categories)} app={_app_cats}")
else:
    check(False, "could not find self.categories in app.py")

# --- structure -------------------------------------------------------------
# A category is either a command panel (groups/flat commands) or the Learning
# Guides section, whose entries are {label, html} documentation pages.
def _is_guide_entry(item):
    return isinstance(item, dict) and "label" in item and "html" in item

def _is_command_entry(item):
    return isinstance(item, dict) and "label" in item and "command" in item
# The intro chapter plus one per entry in learning_index.CHAPTERS.
import learning_index as _li
_expected_chapters = 1 + len(_li.CHAPTERS)
check(len(chapters) == _expected_chapters,
      f"expected {_expected_chapters} chapters (intro + {len(_li.CHAPTERS)}), got {len(chapters)}")

for name in categories:
    check(name in commands, f"category {name!r} has no commands entry")

total = 0
empty = []
for name in categories:
    entry = commands[name]
    # The Learning Guides section is documentation, not shell commands:
    # validate its guide entries instead of command entries.
    if entry.get("learning"):
        guides = entry.get("commands", [])
        for item in guides:
            check(_is_guide_entry(item), f"{name}: malformed guide {item}")
        print(f"guides    : {len(guides)} in {name}")
        continue
    count = len(entry.get("commands", []))
    for group in entry.get("groups", []):
        check("title" in group, f"{name}: a group is missing its title")
        for item in group.get("items", []):
            check("label" in item and "command" in item,
                  f"{name}: malformed item {item}")
        count += len(group.get("items", []))
    for item in entry.get("commands", []):
        check("label" in item and "command" in item,
              f"{name}: malformed command {item}")
    total += count
    if count == 0:
        empty.append(name)

print(f"commands  : {total}")
print(f"categories with no commands: {empty}")
check(total > 300, f"expected 300+ commands, got {total}")

# Two categories are deliberately empty on the phone: "Custom" is a free-text
# box on the desktop and "Networking Masterclass" is only a launcher.
check(set(empty) <= {"Custom", "Networking Masterclass"},
      f"unexpected empty categories: {empty}")

# --- command text ----------------------------------------------------------
bad = []
for name in categories:
    entry = commands[name]
    # Guide entries are documentation pages, not shell commands: skip them
    # here; their shape is already checked above.
    if entry.get("learning"):
        continue
    items = list(entry.get("commands", []))
    for group in entry.get("groups", []):
        items.extend(group.get("items", []))
    for item in items:
        command = item.get("command", "")
        if not command.strip():
            bad.append(f"{name}: {item.get('label')} has an empty command")
        elif "\n" in command:
            bad.append(f"{name}: {item.get('label')} spans multiple lines")
print(f"malformed commands: {len(bad)}")
for entry in bad[:5]:
    print("   ", entry)
check(not bad, f"{len(bad)} malformed commands")

# --- learning content ------------------------------------------------------
for chapter in chapters:
    html = chapter.get("html", "")
    check(bool(html.strip()), f"chapter {chapter.get('title')!r} is empty")
    check("<h" in html, f"chapter {chapter.get('title')!r} has no heading")

html_bytes = sum(len(c["html"]) for c in chapters)
print(f"chapter html total: {html_bytes / 1024:.0f} KB")
check(html_bytes > 100_000, f"learning content looks too small: {html_bytes} bytes")

# Unbalanced tags would leave the WebView showing raw markup.
unbalanced = []
for chapter in chapters:
    opens = len(re.findall(r"<table\b", chapter["html"]))
    closes = len(re.findall(r"</table>", chapter["html"]))
    if opens != closes:
        unbalanced.append(chapter["title"])
check(not unbalanced, f"unbalanced <table> in: {unbalanced}")

# --- the packaged copy must match -----------------------------------------
check(os.path.exists(SHIPPED), f"packaged asset missing: {SHIPPED}")
if os.path.exists(SHIPPED):
    with open(SHIPPED, "rb") as handle:
        packaged = handle.read()
    with open(CONTENT, "rb") as handle:
        source = handle.read()
    check(packaged == source,
          "the packaged asset is stale; re-run export_android_content.py "
          "and copy it into the Android assets folder")
    print(f"packaged asset matches source: {packaged == source} "
          f"({len(packaged) / 1024:.0f} KB)")

if failures:
    print(f"\n{len(failures)} CONTENT FAILURES:")
    for failure in failures:
        print("   ", failure)
    sys.exit(1)
print("\nANDROID CONTENT OK: the packaged library is complete and valid")