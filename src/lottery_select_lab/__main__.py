"""``python -m lottery_select_lab`` entry point. / 模块直接运行入口。"""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
