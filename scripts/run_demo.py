#!/usr/bin/env python3
"""One-command demo runner. / 一键跑完全部示例并生成展示素材。

中文：CI 与首次 clone 之后都用它验证「仓库能不能跑通」。
产物落在 ``examples/output/``，README 里引用的图就是这里生成的。

Usage::

    python scripts/run_demo.py            # 全部示例
    python scripts/run_demo.py 01 03      # 只跑指定编号
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = sorted((ROOT / "examples").glob("[0-9][0-9]_*.py"))


def main(argv: list[str]) -> int:
    wanted = set(argv)
    targets = [p for p in EXAMPLES if not wanted or p.name[:2] in wanted]
    if not targets:
        print(f"[error] no example matched {sorted(wanted)}")
        return 1

    env = {"PYTHONPATH": str(ROOT / "src")}
    import os

    merged = os.environ.copy()
    merged.update(env)

    failures = 0
    for script in targets:
        started = time.perf_counter()
        result = subprocess.run(
            [sys.executable, str(script)], cwd=ROOT, env=merged, capture_output=True, text=True
        )
        elapsed = time.perf_counter() - started
        status = "ok" if result.returncode == 0 else "FAILED"
        print(f"[{status}] {script.name} ({elapsed:.1f}s)")
        if result.returncode != 0:
            failures += 1
            print(result.stdout[-2000:])
            print(result.stderr[-2000:])
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
