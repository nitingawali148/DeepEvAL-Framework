import sys
from pathlib import Path

# Make the project root importable (app.py, rag/, etc.)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402 — must come after sys.path fix
