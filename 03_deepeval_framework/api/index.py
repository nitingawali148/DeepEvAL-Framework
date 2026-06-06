import os
import sys
from pathlib import Path

os.chdir("/tmp")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dashboard.app import app  # noqa: E402
