#!/usr/bin/env python3
"""Fetch / normalize historical draw data. / 下载并把原始数据规范化为统一 CSV。

中文：仓库里只放小样本（``data/sample/ssq_sample.csv``），真实历史数据靠这个脚本取回本地。
它做两件事：

1. ``--url``：下载任意纯文本/CSV 数据源，按本项目的解析规则清洗；
2. ``--from-file``：把你手上的原始导出（txt / csv）转成统一格式。

统一格式（4 列，加载器会自动识别）::

    issue,date,reds,blue
    2024001,2024-01-02,3 8 12 19 25 31,7

用法 / Usage::

    python scripts/download_data.py --url https://example.com/ssq.txt --out data/ssq_history.csv
    python scripts/download_data.py --from-file ~/Desktop/彩票研究/data_3.txt --out data/ssq_history.csv
"""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from pathlib import Path

# 让脚本无需安装即可运行 / allow running straight from a clone.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lottery_select_lab.data import load_draws, save_draws  # noqa: E402


def _download(url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "lottery-select-lab/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="fetch or normalize historical draw data")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="远程数据源 / remote text or csv url")
    source.add_argument("--from-file", help="本地原始文件 / local raw export")
    parser.add_argument("--out", default="data/ssq_history.csv", help="输出路径 / output csv path")
    parser.add_argument("--min-issues", type=int, default=100, help="最少期数告警线 / minimum issues")
    args = parser.parse_args(argv)

    if args.url:
        try:
            body = _download(args.url)
        except urllib.error.URLError as exc:
            print(f"[error] download failed: {exc}")
            return 1
        scratch = Path(args.out).with_suffix(".raw.txt")
        scratch.parent.mkdir(parents=True, exist_ok=True)
        scratch.write_text(body, encoding="utf-8")
        print(f"[info] raw payload cached -> {scratch}")
        raw_path = scratch
    else:
        raw_path = Path(args.from_file).expanduser()
        if not raw_path.is_file():
            print(f"[error] file not found: {raw_path}")
            return 1

    draws = load_draws(raw_path)
    out = save_draws(draws, args.out)
    print(f"[ok] parsed {len(draws)} issues -> {out}")
    print(f"     first={draws[0].issue} last={draws[-1].issue}")
    if len(draws) < args.min_issues:
        print(
            f"[warn] only {len(draws)} issues available (< {args.min_issues}); "
            "factor discovery will be unstable",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
