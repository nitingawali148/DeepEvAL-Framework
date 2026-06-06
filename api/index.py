import os
import sys
from pathlib import Path

print("[vercel] api/index.py starting", flush=True)

os.chdir("/tmp")
print(f"[vercel] cwd changed to /tmp", flush=True)

ROOT = Path(__file__).resolve().parent.parent / "03_deepeval_framework"
print(f"[vercel] ROOT = {ROOT}", flush=True)
print(f"[vercel] ROOT exists = {ROOT.exists()}", flush=True)
print(f"[vercel] ROOT contents = {list(ROOT.iterdir()) if ROOT.exists() else 'MISSING'}", flush=True)

sys.path.insert(0, str(ROOT))
print(f"[vercel] sys.path[0] = {sys.path[0]}", flush=True)

try:
    print("[vercel] importing dashboard.app ...", flush=True)
    from dashboard.app import app
    print("[vercel] import OK", flush=True)
except Exception as e:
    print(f"[vercel] IMPORT ERROR: {e}", flush=True)
    raise
