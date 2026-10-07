"""Check GitHub workflow runs and release state for the mobile build."""
import json
import sys
import urllib.request

REPO = "hamdhi/DocKube-Software-Engineering"
HEADERS = {"User-Agent": "DocKube"}


def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "runs"
    if which == "runs":
        data = get(f"https://api.github.com/repos/{REPO}/actions/runs?per_page=8")
        for r in data["workflow_runs"]:
            print(
                f"{r['id']} | {r['name']:<38} | {r['status']:<10} | "
                f"{str(r.get('conclusion')):<10} | {r['created_at']}"
            )
    elif which == "android-release":
        data = get(f"https://api.github.com/repos/{REPO}/releases/tags/android-latest")
        print(f"tag: {data['tag_name']}")
        print(f"name: {data['name']}")
        print(f"body: {data['body']!r}")
        print(f"id: {data['id']}")
        for a in data["assets"]:
            digest = a.get("digest", "") or ""
            print(f"  asset: {a['name']} size={a['size']} id={a['id']} digest={digest}")
    elif which == "desktop-release":
        data = get(f"https://api.github.com/repos/{REPO}/releases/tags/desktop-latest")
        print(f"tag: {data['tag_name']}")
        print(f"name: {data['name']}")
        print(f"body: {data['body']!r}")
        for a in data["assets"]:
            digest = a.get("digest", "") or ""
            print(f"  asset: {a['name']} size={a['size']} digest={digest}")
    else:
        print(f"unknown mode: {which}")
        sys.exit(1)


if __name__ == "__main__":
    main()
