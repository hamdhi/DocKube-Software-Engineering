"""Validate every new learning chapter added for the 1.3.0 release."""
import learning

MODULES = [
    "testing", "deployment", "auth", "python_adv", "python_internals",
    "fastapi", "email", "crypto", "net_advanced", "ccna", "packettracer",
    "windows_admin", "linux_admin", "kernel", "diagnostics", "ml",
    "ai_models", "ai_engineering", "platform", "docker",
]

total = tables = 0
failures = []
for offset, name in enumerate(MODULES, start=24):
    try:
        module = __import__("learning_content_" + name)
        blocks = learning.parse_content(module.CHAPTER)
        tables_here = sum(1 for b in blocks if b.kind == "table")
        pipes = [b.text[:40] for b in blocks
                 if b.kind == "p" and b.text.startswith("|")]
        total += len(blocks)
        tables += tables_here
        flag = " RAW-PIPES!" if pipes else ""
        print(f"{offset:2d} {name:20s} {len(blocks):4d} blocks "
              f"{tables_here:2d} tables {len(module.CHAPTER):6d} chars{flag}")
        if pipes:
            failures.append((name, pipes[:2]))
        if not blocks or len(module.CHAPTER) < 3000:
            failures.append((name, "too small"))
    except Exception as exc:
        failures.append((name, repr(exc)))
        print(f"{offset:2d} {name:20s} FAILED {exc!r}")

print(f"\nTOTAL {total} blocks, {tables} tables across {len(MODULES)} chapters")
if failures:
    print("FAILURES:")
    for item in failures:
        print("   ", item)
    raise SystemExit(1)
print("ALL NEW CHAPTERS PARSE CLEANLY")
