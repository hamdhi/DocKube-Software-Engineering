"""Verify starter files are written correctly and docs render as expected."""
import importlib.util
import os
import sys
import tempfile
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

import devops_tools
import templates_content as templates

app = mod.App()
app.withdraw()
app.run_cmd = lambda cmd, callback=None, open_external=True: None
app.run_in_external_terminal = lambda cmd: None

workdir = tempfile.mkdtemp(prefix="dockeybe_")
app.work_dir_entry.delete(0, "end")
app.work_dir_entry.insert(0, workdir)

failures = []

# 1. Every manifest template must be written and be valid YAML.
try:
    import yaml
except ImportError:
    yaml = None

for label, (relative, content) in templates.MANIFEST_TEMPLATES.items():
    ok = devops_tools.write_template(app, relative, content)
    path = os.path.join(workdir, relative)
    exists = os.path.isfile(path)
    print(f"  manifest {label:9s} {relative:14s} written={ok and exists}")
    if not (ok and exists):
        failures.append(f"{label} not written")
        continue
    if yaml:
        docs = [d for d in yaml.safe_load_all(open(path, encoding="utf-8")) if d]
        kinds = [d.get("kind") for d in docs]
        print(f"      kinds: {kinds}")
        if "StatefulSet" not in kinds:
            failures.append(f"{label} has no StatefulSet")

# 2. Auxiliary templates, including the nested workflow path.
for label, (relative, content) in templates.AUX_TEMPLATES.items():
    ok = devops_tools.write_template(app, relative, content)
    path = os.path.join(workdir, relative)
    print(f"  aux      {label:26s} {relative:32s} written={ok and os.path.isfile(path)}")
    if not (ok and os.path.isfile(path)):
        failures.append(f"{label} not written")

# 3. The nested .github/workflows path must actually exist on disk.
workflow_path = os.path.join(workdir, ".github", "workflows", "ci-cd.yml")
print("\n  nested workflow exists:", os.path.isfile(workflow_path))
if not os.path.isfile(workflow_path):
    failures.append("nested workflow path missing")

# 4. Argument templating must refuse empty input.
print("\n  resolve_command no-arg ->", repr(devops_tools.resolve_command("git status", "")))
print("  resolve_command with   ->", repr(devops_tools.resolve_command("git log -p {arg}", "file.py")))
print("  resolve_command empty  ->", repr(devops_tools.resolve_command("git log -p {arg}", "  ")))
if devops_tools.resolve_command("git log -p {arg}", "  ") is not None:
    failures.append("empty argument should be rejected")

# 5. Documentation highlighting: indented commands must be tagged as commands.
app.select_category("Terraform")
doc = app.doc_text.get("1.0", "end")
command_lines = [l.strip() for l in doc.splitlines()
                 if l.strip().startswith(("terraform", "git", "gh ", "kubectl"))]
print(f"\n  Terraform doc shows {len(command_lines)} command lines, e.g. {command_lines[:3]}")
if len(command_lines) < 15:
    failures.append("documentation commands did not render")

app.destroy()
print("\nworkdir used:", workdir)

if failures:
    print("\nFAILURES:")
    for failure in failures:
        print("  -", failure)
    sys.exit(1)
print("\nTEMPLATE + DOCS TEST PASSED")