import sys
import traceback
from pathlib import Path

CHATBOT = Path(__file__).resolve().parent.parent / "01_chatbot" / "backend"
sys.path.insert(0, str(CHATBOT))

try:
    from app import app
except Exception:
    from fastapi import FastAPI
    from fastapi.responses import PlainTextResponse

    _err = traceback.format_exc()
    app = FastAPI()

    @app.get("/{path:path}")
    def show_error(path: str = ""):
        return PlainTextResponse(_err, status_code=500)
