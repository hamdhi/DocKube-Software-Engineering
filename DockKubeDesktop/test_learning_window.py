"""Headless test: open the Learning Centre popup and verify real tables."""
import importlib.util
import re
import sys
import time
import traceback

import tkinter as tk

spec = importlib.util.spec_from_file_location("app", "app.py")
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except Exception:
    traceback.print_exc()
    sys.exit(1)

import learning
import learning_index

app = mod.App()
app.withdraw()

# The category must offer a launcher instead of inline documentation.
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
assert any("Learning" in b for b in buttons), "launcher button missing"

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
print("popup geometry:", window.geometry())

expected = len(learning_index.CHAPTERS) + 1
print("TOC buttons:", len(window._toc_buttons))
assert len(window._toc_buttons) == expected, "TOC is incomplete"


def find_tables(widget):
    found = []
    for child in widget.winfo_children():
        if isinstance(child, learning.TableWidget):
            found.append(child)
        found.extend(find_tables(child))
    return found


# Only the selected chapter is rendered, so every chapter has to be visited to
# prove all of its tables become real widgets.
chapters = [("Start Here", learning_index.INTRO)] + list(learning_index.CHAPTERS)
expected_per_chapter = {
    title: len([b for b in learning.parse_content(body) if b.kind == "table"])
    for title, body in chapters
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
for index, (title, _body) in enumerate(chapters):
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