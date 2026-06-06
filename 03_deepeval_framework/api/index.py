import sys
from pathlib import Path

# Add 03_deepeval_framework/ to path so llm_providers/, targets/, datasets/ are importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dashboard.app import app  # noqa: E402 — must come after sys.path fix
