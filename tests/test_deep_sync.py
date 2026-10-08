import json
import os
import sys

base = r"C:\Users\32813 MHM Hamdhi\Desktop\DocKube"
desktop = json.load(open(os.path.join(base, "DockKubeDesktop", "android_content.json"), encoding="utf-8"))
mobile = json.load(open(os.path.join(base, "DocKubeAndroid", "app", "src", "main", "assets", "android_content.json"), encoding="utf-8"))

def extract_commands(section):
    """Extract all (label, command) pairs from a command section."""
    pairs = []
    for g in section.get("groups", []):
        for item in g.get("items", []):
            pairs.append((g.get("title", ""), item.get("label", ""), item.get("command", "")))
    for item in section.get("commands", []):
        pairs.append(("", item.get("label", ""), item.get("command", item.get("html", ""))[:80]))
    return pairs

diffs = 0
for section in sorted(set(desktop["commands"].keys()) | set(mobile["commands"].keys())):
    d_sec = desktop["commands"].get(section, {})
    m_sec = mobile["commands"].get(section, {})
    d_pairs = extract_commands(d_sec)
    m_pairs = extract_commands(m_sec)

    if d_pairs != m_pairs:
        diffs += 1
        print(f"DIFF in '{section}': desktop={len(d_pairs)} vs mobile={len(m_pairs)}")
        d_set = set(d_pairs)
        m_set = set(m_pairs)
        only_d = d_set - m_set
        only_m = m_set - d_set
        for p in list(only_d)[:3]:
            print(f"  only-desktop: {p}")
        for p in list(only_m)[:3]:
            print(f"  only-mobile: {p}")

# Deep compare learning guides content
d_lg = desktop["commands"].get("Learning Guides", {}).get("commands", [])
m_lg = mobile["commands"].get("Learning Guides", {}).get("commands", [])
lg_diffs = 0
for i, (d, m) in enumerate(zip(d_lg, m_lg)):
    if d.get("label") != m.get("label") or d.get("html") != m.get("html"):
        lg_diffs += 1
        print(f"Learning guide {i} differs: '{d.get('label')}' vs '{m.get('label')}'")

# Compare docs descriptions
d_docs = desktop.get("docs", {})
m_docs = mobile.get("docs", {})
docs_diffs = 0
for key in set(d_docs.keys()) | set(m_docs.keys()):
    if d_docs.get(key) != m_docs.get(key):
        docs_diffs += 1
        print(f"Doc description differs: '{key}'")

print(f"\nCommand section diffs: {diffs}")
print(f"Learning guide diffs: {lg_diffs}")
print(f"Doc description diffs: {docs_diffs}")

if diffs == 0 and lg_diffs == 0 and docs_diffs == 0:
    print("\nDEEP SYNC VERIFIED - Content is byte-identical between apps")
    sys.exit(0)
else:
    print("\nSYNC GAPS FOUND")
    sys.exit(1)
