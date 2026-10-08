"""Regression test: the Learning window must scroll with the wheel, with a
precision touchpad's small deltas, and after other scrollers have come and
gone.

Two bugs are covered:

1. FastScroller used to bind <MouseWheel> on <Enter> and call unbind_all()
   on <Leave>, which removed every application-wide wheel handler -- the
   Learning Centre's included. Once the pointer had passed over the sidebar
   or the actions pane, two-finger trackpad scrolling in the Learning window
   did nothing at all.
2. CustomTkinter converts the wheel with -int(delta / 6) units, so the tiny
   deltas (1..5) a Windows precision touchpad emits moved nothing even when
   the handler survived. The Learning window now owns its own dispatcher.

The test drives the real app: it opens the Learning window, generates real
<MouseWheel> events over a content child, and asserts the pane actually
moves. It then churns a FastScroller through the Enter/Leave cycle that used
to wipe the bindings, reopens the Learning window (the second open used to
append handlers behind dead ones) and scrolls again.

Usage:
    python test_learning_scroll.py
"""
import importlib.util
import os
import tkinter as tk

# Resolve app.py next to this test file so the test works from any CWD.
_APP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
spec = importlib.util.spec_from_file_location("app", _APP_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

failures = []

app = mod.App()
app.withdraw()
app.open_learning_centre()
app.update()
window = app.learning_window
window.deiconify()
window.lift()
window.update()


def open_pane():
    """Show the largest chapter so the pane definitely overflows."""
    names = [title for title, _body in window.chapters]
    window.show_chapter(names.index("Linux Command Line"))
    window.update_idletasks()


def wheel(widget, delta):
    widget.event_generate("<MouseWheel>", delta=delta)
    window.update_idletasks()
    return canvas.yview()


def binding_script():
    return str(window.tk.call("bind", "all", "<MouseWheel>")).strip()


# --- 1. the application-wide binding must exist -----------------------------
if not binding_script():
    failures.append("no application-wide <MouseWheel> handler is registered")

open_pane()
canvas = window.outer._parent_canvas
children = [c for c in window.outer.winfo_children()]
if len(children) < 2:
    failures.append("chapter rendered no content children to aim at")
child = children[min(1, len(children) - 1)]

# --- 2. a real wheel notch scrolls down -------------------------------------
canvas.yview_moveto(0.0)
window.update_idletasks()
before = canvas.yview()
after = wheel(child, -120)
print(f"wheel -120: {before} -> {after}")
if not after[0] > before[0]:
    failures.append(f"wheel delta=-120 did not scroll down: {before} -> {after}")

# --- 3. touchpad micro-deltas scroll too ------------------------------------
# int(-3 / 6) is 0, so CustomTkinter's own maths would move nothing here.
before = after
after = wheel(child, -3)
print(f"micro -3:   {before} -> {after}")
if not after[0] > before[0]:
    failures.append(f"micro delta=-3 did not scroll down: {before} -> {after}")

before = after
after = wheel(child, 3)
print(f"micro +3:   {before} -> {after}")
if not after[0] < before[0]:
    failures.append(f"micro delta=+3 did not scroll up: {before} -> {after}")

# --- 4. a FastScroller Enter/Leave cycle must not wipe the bindings ---------
import fast_scroller  # noqa: E402  (after app import, like the app does)

holder = tk.Toplevel(window)
holder.geometry("220x260")
scroller = fast_scroller.FastScroller(holder, bg="#161b22")
scroller.pack(fill="both", expand=True)
tk.Frame(scroller.body, height=2000, width=180).pack()
holder.update()

scroller.canvas.event_generate("<Enter>")
scroller.canvas.event_generate("<Leave>")
holder.update()
if not binding_script():
    failures.append("a FastScroller Enter/Leave cycle wiped the wheel binding")

# The scroller itself must still scroll: wheel over a child of its body.
label = tk.Label(scroller.body, text="wheel target")
label.pack()
holder.update()
scroller.canvas.yview_moveto(0.0)
holder.update()
fs_before = scroller.canvas.yview()
label.event_generate("<MouseWheel>", delta=-120)
holder.update()
fs_after = scroller.canvas.yview()
print(f"FastScroller -120: {fs_before} -> {fs_after}")
if fs_after[0] == fs_before[0]:
    failures.append(f"FastScroller did not scroll: {fs_before} -> {fs_after}")

# A wheel event aimed at the Learning window must NOT move this scroller.
held = scroller.canvas.yview()
child.event_generate("<MouseWheel>", delta=-120)
window.update_idletasks()
holder.update()
if scroller.canvas.yview() != held:
    failures.append("a Learning-window wheel event moved a foreign scroller")

# --- 5. closing and reopening the Learning window keeps scrolling -----------
app.close_learning_centre()
app.update()
app.open_learning_centre()
app.update()
window = app.learning_window
window.deiconify()
window.lift()
window.update()
open_pane()
canvas = window.outer._parent_canvas
children = [c for c in window.outer.winfo_children()]
child = children[min(1, len(children) - 1)]
canvas.yview_moveto(0.0)
window.update_idletasks()
before = canvas.yview()
after = wheel(child, -120)
print(f"reopened wheel -120: {before} -> {after}")
if not after[0] > before[0]:
    failures.append(f"reopened Learning window did not scroll: {before} -> {after}")

holder.destroy()
app.close_learning_centre()
app.destroy()

if failures:
    print(f"\n{len(failures)} SCROLL FAILURES:")
    for failure in failures:
        print("   ", failure)
    raise SystemExit(1)
print("\nLEARNING SCROLL REGRESSION TEST PASSED")
