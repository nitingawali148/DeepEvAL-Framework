import sys
from pathlib import Path

CHATBOT = Path(__file__).resolve().parent.parent / "01_chatbot" / "backend"
sys.path.insert(0, str(CHATBOT))

from app import app  # noqa: E402
