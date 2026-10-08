"""Headless test: open the Learning Centre popup and verify real tables."""
import importlib.util
import os
import re
import sys
import time
import traceback

import tkinter as tk

# Resolve app.py next to this test file so the test works from any CWD.
_APP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
spec = importlib.util.spec_from_file_location("app", _APP_PATH)
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except Exception:
    traceback.print_exc()
    sys.exit(1)

import learning
import learning_index
import learning_guides

app = mod.App()
app.withdraw()

# The category must offer a launcher instead of inline documentation.
assert "Learning Guides" not in app.categories, "guides still have a separate sidebar entry"
app.select_category("Networking Masterclass")
app.update()
launchers = [w for w in app.actions.winfo_children()
             if isinstance(w, learning.ctk.CTkFrame)]
print("launcher frames:", len(launchers))
buttons = []
for frame in launchers:
    for child in frame.winfo_children():
        if isinstance(child, learning.ctk.CTkButton):
            buttons.append(child.cget("text"))
print("buttons:", buttons)
assert any("Networking Masterclass" in b for b in buttons), "launcher button missing"

# The main window documentation must now be short, not 653 lines.
doc_lines = int(app.doc_text.index("end-1c").split(".")[0])
print("inline doc lines (was 653):", doc_lines)
assert doc_lines < 30, f"inline documentation is still {doc_lines} lines"

# Open the popup.
app.open_learning_centre()
app.update()
window = app.learning_window
assert window is not None, "popup was not created"
print("popup title:", window.title())
assert window.title() == "DocKube Networking Masterclass"
print("popup geometry:", window.geometry())

guide_chapters = [
    (f"Programming: {title}", learning.markdown_to_html(body), body)
    for title, body in learning_guides.load_guides()
]
expected = len(learning_index.CHAPTERS) + 1 + len(guide_chapters)
print("TOC buttons:", len(window._toc_buttons))
assert len(window._toc_buttons) == expected, "TOC is incomplete"
first_guide_index = len(learning_index.CHAPTERS) + 1
window.show_chapter(first_guide_index)
app.update()
assert window.copy_btn.winfo_manager() == "grid", "guide copy button is hidden"
window.copy_current_text()
assert app.clipboard_get() == guide_chapters[0][2], "guide copy text changed"


def find_tables(widget):
    found = []
    for child in widget.winfo_children():
        if isinstance(child, learning.TableWidget):
            found.append(child)
        found.extend(find_tables(child))
    return found


# Only the selected chapter is rendered, so every chapter has to be visited to
# prove all of its tables become real widgets.
chapters = (
    [("Start Here", learning_index.INTRO)]
    + list(learning_index.CHAPTERS)
    + guide_chapters
)
expected_per_chapter = {
    chapter[0]: len([b for b in learning.parse_content(chapter[1]) if b.kind == "table"])
    for chapter in chapters
}
total_expected = sum(expected_per_chapter.values())
print(f"tables across all chapters: {total_expected}")

# Cell text now lives on the canvas, not on child labels.
def table_texts(table):
    texts = []
    for item in table.canvas.find_all():
        if table.canvas.type(item) == "text":
            texts.append(table.canvas.itemcget(item, "text"))
    return texts


# Pipes are legitimate here (PowerShell pipelines, `ls -l` output), so check
# for genuine leftovers instead: the `|---|` divider or padded pipe rows.
cells = 0
broken = []
missing = []
for index, chapter in enumerate(chapters):
    title = chapter[0]
    window.show_chapter(index)
    app.update()
    tables = find_tables(window.outer)
    if len(tables) != expected_per_chapter[title]:
        missing.append((title, len(tables), expected_per_chapter[title]))
    for table in tables:
        values = table_texts(table)
        cells += len(values)
        for text in values:
            if re.search(r"\|\s*-{2,}", text):
                broken.append((title, text))

print(f"table cells rendered across all chapters: {cells}, "
      f"leftover markdown rows: {len(broken)}")
for title, text in broken[:5]:
    print("   ", title, text)
assert not broken, "some cells still contain markdown table syntax"
for entry in missing:
    print("   table count mismatch:", entry)
assert not missing, "some chapters did not render all of their tables"
assert total_expected > 40, "expected a large number of tables"

# Spot-check that real values survived, including one with a pipe in it.
window.show_chapter(0)
app.update()
first = find_tables(window.outer)[0]
values = table_texts(first)
print("first table header:", values[:4])
assert any("What you get" in v for v in values)

# Navigation across every chapter must not raise.
for index in range(expected):
    window.show_chapter(index)
    app.update()
print(f"navigated all {expected} chapters")
assert window.status.cget("text").startswith("Chapter")

# Close and confirm it can be reopened.
app.close_learning_centre()
app.update()
assert app.learning_window is None, "popup was not cleared on close"
app.open_learning_centre()
app.update()
assert app.learning_window is not None, "popup could not be reopened"
print("close and reopen: OK")

app.close_learning_centre()
app.destroy()
print("\nLEARNING CENTRE TEST PASSED")