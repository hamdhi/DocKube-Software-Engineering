"""Headless test: open the Learning Centre popup and verify real tables."""
import importlib.util
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

# Count real table widgets rendered inside the popup.
def find_tables(widget):
    found = []
    for child in widget.winfo_children():
        if isinstance(child, learning.TableWidget):
            found.append(child)
        found.extend(find_tables(child))
    return found

tables = find_tables(window.outer)
expected_tables = sum(
    len([b for b in learning.parse_content(body) if b.kind == "table"])
    for _title, body in [("Start Here", learning_index.INTRO)] + learning_index.CHAPTERS
)
print(f"table widgets rendered: {len(tables)} (expected {expected_tables})")
assert len(tables) == expected_tables, "some tables did not become widgets"
assert len(tables) > 40, "expected a large number of tables"

# Every table must have real labels, not raw pipe text.
cells = 0
piped = 0
for table in tables:
    for child in table.winfo_children():
        cells += 1
        text = child.cget("text") if child.winfo_class() == "Label" else ""
        if "|" in str(text) or "---" in str(text):
            piped += 1
print(f"table cells: {cells}, still showing pipes: {piped}")
assert piped == 0, "some cells still contain pipe characters"

# Check one table's actual values survived correctly.
first = tables[0]
values = [c.cget("text") for c in first.winfo_children()]
print("first table header:", values[:4])
assert all("|" not in v and "---" not in v for v in values)

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