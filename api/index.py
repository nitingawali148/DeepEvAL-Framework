import os
import sys
from pathlib import Path

# Vercel filesystem is read-only; deepeval writes .deepeval/ on import
os.chdir("/tmp")

# Add 03_deepeval_framework/ to sys.path
ROOT = Path(__file__).resolve().parent.parent / "03_deepeval_framework"
sys.path.insert(0, str(ROOT))

from dashboard.app import app  # noqa: E402
