import os
import sys
from pathlib import Path

# Vercel root filesystem is read-only; deepeval writes .deepeval/ on import
os.chdir("/tmp")

# Add 03_deepeval_framework/ to path so llm_providers/, targets/, datasets/ are importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dashboard.app import app  # noqa: E402
