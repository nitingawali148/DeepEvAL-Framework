import sys
from pathlib import Path

# Make the backend root importable (app.py, etc.)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402 — must come after sys.path fix
