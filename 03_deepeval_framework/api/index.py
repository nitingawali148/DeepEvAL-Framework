import os
import sys
from pathlib import Path

print("[vercel] START api/index.py", flush=True)
print(f"[vercel] __file__ = {__file__}", flush=True)

os.chdir("/tmp")
print("[vercel] chdir /tmp OK", flush=True)

ROOT = Path(__file__).resolve().parent.parent
print(f"[vercel] ROOT = {ROOT}", flush=True)
print(f"[vercel] ROOT exists = {ROOT.exists()}", flush=True)

if ROOT.exists():
    print(f"[vercel] ROOT contents = {[x.name for x in ROOT.iterdir()]}", flush=True)

sys.path.insert(0, str(ROOT))

try:
    print("[vercel] importing dashboard.app ...", flush=True)
    from dashboard.app import app
    print("[vercel] import SUCCESS", flush=True)
except Exception as e:
    import traceback
    print(f"[vercel] IMPORT FAILED: {e}", flush=True)
    traceback.print_exc()
    raise
