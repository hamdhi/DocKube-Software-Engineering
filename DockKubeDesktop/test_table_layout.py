"""Tables must not overlap: each cell's text has to stay inside its column.

The original bug set wraplength=0 on every cell label, so when the pane was
narrower than the sum of the column minimums the columns were squeezed while
the text still rendered at full natural width, so neighbouring cells drew over
each other. Canvas text is constrained by the column width, and this test
asserts that directly.
"""
import importlib.util
import os
import sys
import traceback

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

app = mod.App()
app.withdraw()
app.open_learning_centre()
app.update()
window = app.learning_window
window.update_idletasks()

NARROW = 520   # tight enough to force the squeeze that caused the overlap
WIDE = 1150


def find_tables(widget):
    found = []
    for child in widget.winfo_children():
        if isinstance(child, learning.TableWidget):
            found.append(child)
        found.extend(find_tables(child))
    return found


def column_edges(table):
    """Column x boundaries, recovered from the header rectangles/lines."""
    canvas = table.canvas
    edges = set()
    for item in canvas.find_all():
        kind = canvas.type(item)
        if kind == "rectangle":
            x0, _, x1, _ = (float(v) for v in canvas.coords(item))
            edges.add(round(x0))
            edges.add(round(x1))
        elif kind == "line":
            x0, y0, x1, _ = (float(v) for v in canvas.coords(item))
            if y0 != 0 or True:
                edges.add(round(x0))
    return sorted(edges)


def check(width, chapter_index):
    window.geometry(f"{width + 320}x820+40+40")
    window.update()
    window.show_chapter(chapter_index)
    window.update_idletasks()

    tables = find_tables(window.outer)
    problems = []
    for table in tables:
        canvas = table.canvas
        texts = [i for i in canvas.find_all() if canvas.type(i) == "text"]
        if not texts:
            continue

        # Use the widths the table actually laid out with, not a guess.
        columns = table._column_widths(max(table._last_width,
                                           table._columns * table.MIN_COLUMN + 2))
        offsets = []
        x = 1
        for column_width in columns:
            offsets.append(x)
            x += column_width

        # Group text by y so one table row is checked at a time.
        rows = {}
        for item in texts:
            tx, ty = canvas.coords(item)[:2]
            rows.setdefault(round(ty), []).append((tx, item))

        for y, row in rows.items():
            row.sort()
            for column, (tx, item) in enumerate(row):
                if column >= len(offsets):
                    continue
                left = offsets[column]
                right = left + columns[column]
                box = canvas.bbox(item)
                if not box:
                    continue
                # Cell text must stay inside its own column.
                if box[0] < left - 1 or box[2] > right + 1:
                    problems.append(("horizontal", chapter_index, width, y,
                                     column, round(box[0]), round(box[2]),
                                     left, right))
                # ...and inside the table vertically, so no line is clipped.
                if box[3] > table._last_height + 1:
                    problems.append(("vertical", chapter_index, width, y,
                                     column, round(box[3]), table._last_height))

        drawn_bottom = max(
            (canvas.bbox(i)[3] for i in texts if canvas.bbox(i)), default=0)
        if drawn_bottom > table._last_height + 1:
            problems.append(("canvas", chapter_index, width,
                             round(drawn_bottom), table._last_height))
    return len(tables), problems


total_problems = []
for width in (NARROW, WIDE):
    for chapter in (12, 11, 13, 3):  # AWS, Agile, Delivery, Subnetting
        count, problems = check(width, chapter)
        print(f"width={width:5d} chapter={chapter:2d} tables={count:3d} "
              f"overflows={len(problems)}")
        total_problems.extend(problems)

window.geometry("1250x820")
app.destroy()

if total_problems:
    print(f"\n{len(total_problems)} OVERLAPPING CELLS:")
    for entry in total_problems[:10]:
        print("   ", entry)
    sys.exit(1)
print("\nNO OVERLAPPING TABLE CELLS AT ANY TESTED WIDTH")