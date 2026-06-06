import os
import sys
import traceback
from pathlib import Path

os.chdir("/tmp")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from dashboard.app import app
except Exception as e:
    # Show exact error in browser for debugging
    from fastapi import FastAPI
    from fastapi.responses import PlainTextResponse
    app = FastAPI()

    _error = traceback.format_exc()

    @app.get("/{path:path}")
    def error_page(path: str = ""):
        return PlainTextResponse(f"IMPORT ERROR:\n\n{_error}", status_code=500)
