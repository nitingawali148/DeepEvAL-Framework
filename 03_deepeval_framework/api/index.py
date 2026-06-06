import os
import sys
from pathlib import Path

# deepeval writes ~/.deepeval at import time; set HOME to /tmp (only writable dir on Vercel)
os.environ["HOME"] = "/tmp"
os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "YES"
os.chdir("/tmp")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dashboard.app import app  # noqa: E402
