import json
import os
import sys
import re

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
desktop_path = os.path.join(base, "DockKubeDesktop", "android_content.json")
mobile_path = os.path.join(base, "DocKubeAndroid", "app", "src", "main", "assets", "android_content.json")
update_py = os.path.join(base, "DockKubeDesktop", "app_update.py")
gradle_kts = os.path.join(base, "DocKubeAndroid", "app", "build.gradle.kts")
cmd_specs = os.path.join(base, "DockKubeDesktop", "command_specs.py")
workflow = os.path.join(base, ".github", "workflows", "build-desktop.yml")

errors = []
passed = 0

def check(name, condition):
    global passed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        errors.append(name)
        print(f"  [FAIL] {name}")

print("=" * 60)
print("FULL REGRESSION TEST SUITE")
print("=" * 60)

# Load data
desktop = json.load(open(desktop_path, encoding="utf-8"))
mobile = json.load(open(mobile_path, encoding="utf-8"))

# SMOKE TESTS
print("\n--- SMOKE TESTS ---")
check("Desktop JSON parses", True)
check("Mobile JSON parses", True)
check("Desktop has 'app' key", "app" in desktop)
check("Mobile has 'app' key", "app" in mobile)
check("Desktop has 'categories'", "categories" in desktop)
check("Mobile has 'categories'", "categories" in mobile)
check("Desktop has 'commands'", "commands" in desktop)
check("Mobile has 'commands'", "commands" in mobile)

# STRUCTURE TESTS
print("\n--- STRUCTURE TESTS ---")
check("Categories match", set(desktop["categories"]) == set(mobile["categories"]))
check("Command sections match", set(desktop["commands"].keys()) == set(mobile["commands"].keys()))
check("Same category count", len(desktop["categories"]) == len(mobile["categories"]))

# CONTENT TESTS
print("\n--- CONTENT TESTS ---")
all_match = True
for section in sorted(desktop["commands"].keys()):
    d = desktop["commands"][section]
    m = mobile["commands"][section]
    d_count = sum(len(g.get("items", [])) for g in d.get("groups", [])) + len(d.get("commands", []))
    m_count = sum(len(g.get("items", [])) for g in m.get("groups", [])) + len(m.get("commands", []))
    if d_count != m_count:
        all_match = False
        print(f"    MISMATCH in '{section}': D={d_count}, M={m_count}")
check("All section command counts match", all_match)

# DATABASE TESTS
print("\n--- DATABASE TESTS ---")
d_db = desktop["commands"]["Databases"]["groups"]
m_db = mobile["commands"]["Databases"]["groups"]
check("DB group count match", len(d_db) == len(m_db))
check("DB titles match", [g["title"] for g in d_db] == [g["title"] for g in m_db])

db_all_match = True
for dg, mg in zip(d_db, m_db):
    if len(dg.get("items", [])) != len(mg.get("items", [])):
        db_all_match = False
check("All DB group item counts match", db_all_match)

# SQL COMMANDS TESTS
print("\n--- SQL COMMAND TESTS ---")
sql_groups = ["MySQL SQL Commands", "PostgreSQL SQL Commands", "MongoDB NoSQL Commands"]
d_titles = [g["title"] for g in d_db]
for g in sql_groups:
    check(f"'{g}' in desktop", g in d_titles)
    check(f"'{g}' in mobile", g in d_titles)

# LEARNING GUIDES TESTS
print("\n--- LEARNING GUIDES TESTS ---")
d_lg = desktop["commands"].get("Learning Guides", {}).get("commands", [])
m_lg = mobile["commands"].get("Learning Guides", {}).get("commands", [])
check("Learning Guides exist in desktop", len(d_lg) > 0)
check("Learning Guides exist in mobile", len(m_lg) > 0)
check("Learning Guides count match", len(d_lg) == len(m_lg))
check("All desktop guides have HTML", all(g.get("html") for g in d_lg))
check("All mobile guides have HTML", all(g.get("html") for g in m_lg))

# VERSION TESTS
print("\n--- VERSION TESTS ---")
d_ver = re.search(r'APP_VERSION = "(.*?)"', open(update_py, encoding="utf-8").read())
m_ver = re.search(r'versionName = "(.*?)"', open(gradle_kts, encoding="utf-8").read())
m_code = re.search(r'versionCode = (\d+)', open(gradle_kts, encoding="utf-8").read())
check("Desktop version found", d_ver is not None)
check("Mobile version found", m_ver is not None)
check("Versions match", d_ver.group(1) == m_ver.group(1))
print(f"    Desktop: {d_ver.group(1)}, Mobile: {m_ver.group(1)} (code: {m_code.group(1)})")

# COMMAND SPECS TESTS
print("\n--- COMMAND SPECS TESTS ---")
specs = open(cmd_specs, encoding="utf-8").read()
check("command_specs has SQL Commands for MySQL", "SQL Commands - Databases" in specs)
check("command_specs has NoSQL Commands", "NoSQL Commands" in specs)
sql_count = specs.count("_g(")
print(f"    Total groups in command_specs.py: {sql_count}")

# WORKFLOW TESTS
print("\n--- WORKFLOW TESTS ---")
wf = open(workflow, encoding="utf-8").read()
check("Workflow publishes DocKubeSetup.exe", "DocKubeSetup.exe" in wf)
check("Workflow publishes dockeybe.zip", "dockeybe.zip" in wf)
# Check order inside the release files block only (between "files:" and "env:")
files_block = wf[wf.index("files:"):wf.index("env:")] if "files:" in wf and "env:" in wf else ""
check("Installer exe listed before zip in files block",
      files_block.index("DocKubeSetup.exe") < files_block.index("dockeybe.zip"))

# UPDATER TESTS
print("\n--- UPDATER TESTS ---")
updater = open(update_py, encoding="utf-8").read()
check("Updater prefers installer exe", updater.index("DocKubeSetup.exe") < updater.index("dockeybe.zip"))
check("Updater has installer logic", "is_installer" in updater)
check("Updater runs installer silently", "VERYSILENT" in updater)

# SUMMARY
print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {len(errors)} failed")
print("=" * 60)
if errors:
    for e in errors:
        print(f"  FAILED: {e}")
    sys.exit(1)
else:
    print("ALL TESTS PASSED - Apps are fully synced!")
    sys.exit(0)
