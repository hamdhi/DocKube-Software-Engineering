# DocKube Test Suite

Regression and smoke tests that verify the desktop app and mobile app stay
perfectly synchronized.

## Run the tests

```bash
# Smoke + regression tests (structure, counts, versions, workflow, updater)
python tests/test_sync_smoke.py

# Deep content diff (byte-level comparison of every command and guide)
python tests/test_deep_sync.py
```

Both scripts exit with code `0` when everything passes and `1` when any check
fails, so they can be wired into CI.

## What is checked

**test_sync_smoke.py (37 checks)**
- JSON parses for both apps
- Top-level keys present (app, categories, commands, docs)
- Category and command-section sets match
- Per-section command counts match
- Database groups (including MySQL/PostgreSQL/MongoDB SQL command groups)
- Learning Guides present in both apps with HTML content
- Desktop `APP_VERSION` matches mobile `versionName`
- GitHub workflow publishes `DocKubeSetup.exe` before `dockeybe.zip`
- Updater prefers the installer exe and runs it with `/VERYSILENT`

**test_deep_sync.py**
- Byte-level comparison of every (group, label, command) tuple
- Byte-level comparison of every learning guide title and HTML body
- Byte-level comparison of doc descriptions

## Sync rule

Both apps read from the same content:

- Desktop: `DockKubeDesktop/android_content.json`
- Mobile: `DocKubeAndroid/app/src/main/assets/android_content.json`

If you change one, run these tests. If they fail, copy the change to the other
file (or regenerate both) before pushing.
