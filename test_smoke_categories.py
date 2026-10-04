"""Headless smoke test: build every category panel without running commands."""
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

# Never shell out or spawn terminals during the smoke test.
executed = []
app.run_cmd = lambda cmd, callback=None, open_external=True: executed.append(cmd)
app.run_in_external_terminal = lambda cmd: executed.append(cmd)

failures = []
for category in app.categories:
    try:
        app.select_category(category)
        app.update_idletasks()
        widgets = len(app.actions.winfo_children())
        doc_lines = int(app.doc_text.index("end-1c").split(".")[0])
        print(f"  {category:28s} widgets={widgets:3d} doc_lines={doc_lines:4d}")
        if widgets == 0:
            failures.append(f"{category}: no widgets built")
        if doc_lines < 3:
            failures.append(f"{category}: documentation missing")
    except Exception as exc:
        failures.append(f"{category}: {exc!r}")
        traceback.print_exc()

print(f"\nCategories: {len(app.categories)}  commands captured: {len(executed)}")
app.destroy()

if failures:
    print("\nFAILURES:")
    for failure in failures:
        print("  -", failure)
    sys.exit(1)
print("\nAll category panels built successfully.")