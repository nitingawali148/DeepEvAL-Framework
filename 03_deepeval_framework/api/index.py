import os
import sys
import traceback
from pathlib import Path

os.environ["HOME"] = "/tmp"
os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "YES"
os.chdir("/tmp")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from dashboard.app import app
except Exception:
    from fastapi import FastAPI
    from fastapi.responses import PlainTextResponse
    _err = traceback.format_exc()
    app = FastAPI()

    @app.get("/{path:path}")
    def show_error(path: str = ""):
        return PlainTextResponse(_err, status_code=500)
