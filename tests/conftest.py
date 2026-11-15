"""Shared fixtures. / 测试公共夹具。"""

from __future__ import annotations

import sys
from pathlib import Path

# 让测试无需安装包就能跑 / run tests straight from src without installation.
SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
