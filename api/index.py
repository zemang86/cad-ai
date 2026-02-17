"""Vercel serverless entrypoint."""

import os
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root / "src"))
os.environ.setdefault("ACAD_CMD_KNOWLEDGE_DIR", str(_root / "knowledge"))
os.environ.setdefault("ACAD_CMD_STANDARDS_DIR", str(_root / "standards"))

from autocad_batch_commander.web.api import app  # noqa: E402, F401
