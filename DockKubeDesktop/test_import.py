import importlib.util, traceback
import os
# Resolve app.py next to this test file so the test works from any CWD.
_APP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
spec = importlib.util.spec_from_file_location('app', _APP_PATH)
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
    print('module loaded OK')
except Exception:
    traceback.print_exc()
