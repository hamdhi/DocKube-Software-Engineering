"""Regression test: sidebar navigation must match the visible chapter.

The bug this guards against subtracted the current scroll offset before
computing the document fraction, which is only correct when jumping from the
very top. Out-of-order clicks made the sidebar highlight one chapter while the
content pane showed another.
"""
import importlib.util
import sys
import traceback

spec = importlib.util.spec_from_file_location("app", "app.py")
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

names = [title for title, _body in window.chapters]
marks = dict(window._section_marks)
canvas = window.outer._parent_canvas
canvas.update_idletasks()

# CustomTkinter widgets all report the class name "Frame"; the real type is in
# the widget name such as "!ctkscrollbar". Find the sidebar TOC scrollbar that
# way. It sits next to the TOC canvas inside the sidebar's inner frame.
def find_scrollbars(widget, found=None):
    found = [] if found is None else found
    for child in widget.winfo_children():
        if child.winfo_name() == "!ctkscrollbar":
            found.append(child)
        find_scrollbars(child, found)
    return found


scrollbars = find_scrollbars(window)
print(f"chapters: {len(names)}")
print(f"sidebar width: {window.grid_bbox(0, 1)[2]} px")
print(f"scrollbars: {[b.winfo_name() + ' in ' + b.master.winfo_name() for b in scrollbars]}")

# The TOC scrollbar is the one that is NOT the content pane's scrollbar.
toc_bars = [b for b in scrollbars if b.master is not window.outer]
window.update_idletasks()
if toc_bars:
    bar = toc_bars[0]
    print(f"TOC scrollbar height: {bar.winfo_height()} px")
    assert bar.winfo_height() > 0, "TOC scrollbar has zero height, so it is invisible"
else:
    print("TOC scrollbar: NOT FOUND")
    raise AssertionError("sidebar TOC scrollbar is missing")

count = len(names)

# Visit chapters in a deliberately scrambled order, twice, so that any
# dependence on the previous scroll position would show up.
order = [3, 8, 1, count - 1, 5, 0, 7, 2]
failures = []

for pass_number in (1, 2):
    for target in order:
        window.show_chapter(target)
        window.update_idletasks()
        total = float(canvas.cget("scrollregion").split()[3])
        top = canvas.yview()[0] * total
        expected = marks[target].winfo_y()
        # Which chapter banner is actually closest to the top of the viewport?
        visible = min(marks.items(), key=lambda kv: abs(kv[1].winfo_y() - top))[0]
        ok = visible == target
        if not ok:
            failures.append((pass_number, target, visible, top, expected))
        print(f"  pass{pass_number} clicked={target:2d} {names[target][:28]:28s} "
              f"visible={visible:2d} top={top:8.0f} expected={expected:8.0f} "
              f"{'OK' if ok else 'MISMATCH'}")

# A chapter near the end must scroll to the very bottom, not short of it.
window.show_chapter(count - 1)
window.update_idletasks()
last = marks[count - 1].winfo_y()
total = float(canvas.cget("scrollregion").split()[3])
print(f"\nlast chapter y={last:.0f} of {total:.0f}")
if last > total:
    failures.append(("end", count - 1, -1, 0, 0))

app.close_learning_centre()
app.destroy()

if failures:
    print(f"\n{len(failures)} NAVIGATION FAILURES:")
    for failure in failures:
        print("   ", failure)
    sys.exit(1)
print("\nNAVIGATION REGRESSION TEST PASSED")