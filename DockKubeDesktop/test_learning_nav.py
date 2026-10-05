"""Regression test: the sidebar must select the chapter that is actually shown.

An earlier version scrolled one long document and compared pixel offsets, so a
click could highlight one chapter while the pane showed another. The pane now
swaps to a single chapter at a time, so the assertion is that the rendered
banner, the highlighted entry and the internal state all agree with the click.
The order is deliberately scrambled and repeated, to catch any dependence on
the previously selected chapter.
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

app = mod.App()
app.withdraw()
app.open_learning_centre()
app.update()
window = app.learning_window
window.update_idletasks()

names = [title for title, _body in window.chapters]

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


def banner_text():
    """The 'n. Title' banner shown at the top of the rendered chapter."""
    _index, frame = window._section_marks[0]
    for child in frame.winfo_children():
        return str(child.cget("text"))
    return ""


count = len(names)
order = [3, 8, 1, count - 1, 5, 0, 7, 2]
failures = []

for pass_number in (1, 2):
    for target in order:
        window.show_chapter(target)
        window.update_idletasks()

        shown = banner_text()
        want = f"{target + 1}. {names[target]}"
        ok = shown == want
        if not ok:
            failures.append((pass_number, target, shown, want))

        highlighted = [n for n, b in window._toc_buttons.items()
                       if str(b.cget("fg_color")) == "#1f6feb"]
        if highlighted != [target]:
            failures.append((pass_number, target, "highlight", highlighted))

        if window._current != target:
            failures.append((pass_number, target, "current", window._current))

        print(f"  pass{pass_number} clicked={target:2d} {names[target][:26]:26s} "
              f"shown='{shown}' {'OK' if ok else 'MISMATCH'}")

# Out-of-range clicks must be ignored rather than crashing or blanking the pane.
window.show_chapter(3)
window.update_idletasks()
before = window._current
for bad in (-1, count, 999):
    window.show_chapter(bad)
    window.update_idletasks()
    if window._current != before:
        failures.append(("out-of-range", bad, window._current, before))
print(f"out-of-range clicks ignored (still showing {before})")

# Previous/Next must step exactly one chapter and disable at the ends.
window.show_chapter(0)
window.update_idletasks()
assert str(window.prev_btn.cget("state")) == "disabled", "Previous enabled at chapter 0"
window.step_chapter(1)
window.update_idletasks()
if window._current != 1:
    failures.append(("next", 1, window._current))
window.step_chapter(-1)
window.update_idletasks()
if window._current != 0:
    failures.append(("prev", 0, window._current))
window.show_chapter(count - 1)
window.update_idletasks()
assert str(window.next_btn.cget("state")) == "disabled", "Next enabled on last chapter"
print("Previous/Next stepping: OK")

app.close_learning_centre()
app.destroy()

if failures:
    print(f"\n{len(failures)} NAVIGATION FAILURES:")
    for failure in failures:
        print("   ", failure)
    sys.exit(1)
print("\nNAVIGATION REGRESSION TEST PASSED")