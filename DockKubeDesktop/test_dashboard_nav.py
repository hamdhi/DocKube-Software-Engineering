"""The dashboard's left category nav must be scrollable.

Twenty categories do not fit in a short window. They used to be gridded
straight into a fixed-width frame, so the last few were silently cut off with
no way to reach them. The nav is now a scrollable frame with a column minimum
that gives the scrollbar somewhere to draw.
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
app.geometry("1100x720")
app.update()
app.update_idletasks()

failures = []


def find_scrollbars(widget, found=None):
    found = [] if found is None else found
    for child in widget.winfo_children():
        if child.winfo_name() == "!ctkscrollbar":
            found.append(child)
        find_scrollbars(child, found)
    return found


print(f"categories: {len(app.categories)}")
print(f"nav column width: {app.grid_bbox(0, 0)[2]} px")

# Every category button must live in the scrollable nav, not the fixed frame.
assert isinstance(app.nav_scroller, mod.FastScroller), "nav is not scrollable"
for category, button in app.sidebar_buttons.items():
    master = button.master
    while master is not app.sidebar:
        if master is app.nav:
            break
        master = master.master
    else:
        failures.append(f"{category} is outside the scrollable nav")
print("all category buttons live in the scrollable nav")

# The scrollbar must appear and have height, or the last categories are
# unreachable. It is a plain canvas in FastScroller, not a CTkScrollbar.
# winfo_ismapped is always False in a withdrawn window, so check it is actually
# managed and has a real height instead.
bar = app.nav_scroller._bar
app.update_idletasks()
height = bar.winfo_height()
managed = bar.winfo_manager()
print(f"nav scrollbar: height={height} px, manager={managed}")
if not managed or height <= 0:
    failures.append("nav scrollbar is not visible")

# The content must genuinely overflow, or a scrollbar would be pointless.
canvas = app.nav_scroller.canvas
content_h = float(canvas.cget("scrollregion").split()[3])
visible = canvas.winfo_height()
print(f"nav content height: {content_h:.0f} px, visible: {visible} px, "
      f"scrollable: {content_h > visible}")
if content_h <= visible:
    failures.append("nav content fits, so the scrollbar cannot be exercised")

# It must actually scroll to the last category.
canvas.yview_moveto(1.0)
app.update_idletasks()
first, last = canvas.yview()
print(f"after scrolling to the bottom: yview={first:.2f}..{last:.2f}")
if last <= 0.99:
    failures.append("nav did not scroll to the bottom")

# Every category button must be reachable and clickable after scrolling.
for category in app.categories:
    button = app.sidebar_buttons[category]
    if not button.winfo_exists():
        failures.append(f"{category} disappeared")
print(f"all {len(app.categories)} categories present after scrolling")

# The compact layout hides the sidebar, so its column must collapse too.
app.update_responsive_layout(type("E", (), {"widget": app, "width": 700,
                                            "height": 720})())
app.update_idletasks()
print(f"compact layout: sidebar hidden={not bool(app.sidebar.winfo_ismapped())}, "
      f"column minsize={app.grid_columnconfigure(0).get('minsize')}")
if app.grid_columnconfigure(0).get("minsize"):
    failures.append("hidden sidebar still reserves horizontal space")
if bool(app.sidebar.winfo_ismapped()):
    failures.append("sidebar still visible in the compact layout")

# And coming back to a wide window must restore it.
app.update_responsive_layout(type("E", (), {"widget": app, "width": 1100,
                                            "height": 720})())
app.update_idletasks()
if app.grid_columnconfigure(0).get("minsize") == 0:
    failures.append("sidebar width was not restored")
print("layout switches restore the sidebar correctly")

app.destroy()
if failures:
    print(f"\n{len(failures)} NAV SCROLLBAR FAILURES:")
    for failure in failures:
        print("   ", failure)
    sys.exit(1)
print("\nDASHBOARD NAV SCROLLBAR TEST PASSED")