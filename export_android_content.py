"""Export DocKube's commands and Learning Centre to JSON for the Android app.

The desktop app builds its action panels imperatively: every button is a call to
add_cmd_button() or add_command_groups() from inside select_category(). Reading
those calls by hand would be slow and would drift the moment one command changes,
so this drives the real app instead.

It constructs the real App, swaps the panel builders for recorders, then selects
every category. Whatever the desktop app would have drawn as a button comes out
here as JSON, so the two apps cannot silently disagree.

Usage:
    python export_android_content.py
"""

import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load_app_module():
    spec = importlib.util.spec_from_file_location("app", os.path.join(HERE, "app.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    mod = load_app_module()
    import devops_tools as dt

    app = mod.App()
    app.withdraw()

    categories = list(app.categories)

    # Record what each category would have drawn, instead of drawing it.
    captured = {}

    def record(category):
        captured[category] = {"groups": [], "commands": []}

    def fake_add_cmd_button(label, cmd):
        current["commands"].append({"label": label, "command": cmd})

    def fake_add_command_groups(_app, groups, placeholder="argument..."):
        for entry in groups:
            title, items = entry[0], entry[1]
            bucket = []
            for item in items:
                bucket.append({"label": item[0], "command": item[1]})
            current["groups"].append({"title": title, "items": bucket})

    def fake_add_arg_group(_app, title, items, placeholder="argument..."):
        bucket = []
        for item in items:
            bucket.append({"label": item[0], "command": item[1],
                           "arg": True, "placeholder": placeholder})
        current["groups"].append({"title": title, "items": bucket})

    def fake_add_list_ui(list_cmd, kind):
        # add_list_ui derives four buttons from one command; recreate them here
        # so the reference commands survive into the mobile app.
        plural = kind if kind.endswith("s") else f"{kind}s"
        bucket = [
            {"label": f"List {plural}", "command": list_cmd},
            {"label": "List Wide View", "command": f"{list_cmd} -o wide"},
            {"label": "Describe Selected", "command": f"kubectl describe {kind.lower()} <name> -n <namespace>"},
            {"label": "Delete", "command": f"kubectl delete {kind.lower()} <name> -n <namespace>"},
        ]
        if kind == "Pod":
            bucket.append({"label": "View Logs", "command": f"kubectl logs <name> -n <namespace>"})
        current["groups"].append({"title": f"{kind} Explorer", "items": bucket})

    current = {}
    app.add_cmd_button = fake_add_cmd_button
    app.add_list_ui = fake_add_list_ui
    dt.add_command_groups = fake_add_command_groups
    dt.add_arg_group = fake_add_arg_group

    # The per-tool helpers all funnel through those two functions, so swapping
    # them is enough to capture GitHub, CI/CD, Jenkins, Terraform, Ansible and
    # the database panels without touching each one.
    for category in categories:
        current = {"groups": [], "commands": []}
        captured[category] = current
        try:
            app.select_category(category)
        except Exception as exc:
            print(f"  ! {category}: {type(exc).__name__}: {exc}")

    # Documentation blurbs the desktop app shows above the commands.
    docs = {}
    for category in categories:
        text = getattr(app, "docs", {}).get(category, "")
        docs[category] = text

    app._shutdown()

    # Learning Centre: the intro plus all fourteen chapters.
    import learning_index

    chapters = [{"title": "Start Here", "html": learning_index.INTRO}]
    for title, html in learning_index.CHAPTERS:
        chapters.append({"title": title, "html": html})

    payload = {
        "app": "DocKube",
        "version": 1,
        "categories": categories,
        "commands": captured,
        "docs": docs,
        "chapters": chapters,
    }

    out_path = os.path.join(HERE, "android_content.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=1)

    total_cmds = 0
    for category in categories:
        entry = captured[category]
        count = len(entry["commands"]) + sum(len(g["items"]) for g in entry["groups"])
        total_cmds += count
        print(f"  {category:32s} {count:3d} commands")
    print(f"\nchapters: {len(chapters)}")
    print(f"total commands: {total_cmds}")
    print(f"wrote {out_path} "
          f"({os.path.getsize(out_path) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()