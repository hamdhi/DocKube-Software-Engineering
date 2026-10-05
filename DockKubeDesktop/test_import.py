import importlib.util, traceback
spec = importlib.util.spec_from_file_location('app', r'c:/Users/32813 MHM Hamdhi/Desktop/DocKube/app.py')
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
    print('module loaded OK')
except Exception:
    traceback.print_exc()
