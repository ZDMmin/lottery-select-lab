"""Result export: CSV / JSON / plain-text summaries. / 结果导出。

中文：手稿的产出只有一个 ``LOG_*.txt``。对外开源后，别人更希望拿到能直接喂给 Excel、
Notebook 或看板的文件，所以这里统一提供三种格式，并且**列名固定**，便于二次分析。
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, Sequence, Union

from .models import BacktestResult


def export_rounds_csv(result: BacktestResult, path: Union[str, Path]) -> Path:
    """Per-round detail as CSV. / 逐轮明细 CSV。

    列：轮次、期号、预测集合、实际开奖、命中数、命中位次。
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["round", "issue", "predicted", "actual", "hits", "ranks"])
        for row in result.rounds:
            writer.writerow(
                [
                    row.index,
                    row.target_issue,
                    " ".join(f"{n:02d}" for n in row.predicted),
                    " ".join(f"{n:02d}" for n in row.actual),
                    row.hits,
                    " ".join(str(r) for r in row.ranks),
                ]
            )
    return out


def export_distribution_csv(result: BacktestResult, path: Union[str, Path]) -> Path:
    """Hit-count distribution table. / 命中分布表。"""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["hits", "issues", "share"])
        total = result.n_rounds or 1
        for hits in sorted(result.distribution):
            count = result.distribution[hits]
            writer.writerow([hits, count, f"{count / total:.4f}"])
    return out


def export_json(result: BacktestResult, path: Union[str, Path]) -> Path:
    """Full result payload, safe for dashboards. / 完整结果，供看板或后续分析使用。"""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out


def write_summary_table(
    rows: Sequence[Dict[str, float]],
    labels: Sequence[str],
    path: Union[str, Path],
    title: str = "Back-test summary",
) -> Path:
    """Markdown table — drop it straight into a README. / 直接可粘进 README 的 Markdown 表格。"""
    from .metrics import format_report

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"## {title}", ""]
    lines.append("| strategy | rounds | avg hits | hit rate | baseline | lift |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for label, row in zip(labels, rows):
        lines.append(
            f"| {label} | {int(row['rounds'])} | {row['average_hits']:.3f} | "
            f"{row['average_hit_rate']:.3f} | {row['baseline_hits']:.3f} | {row['lift']:.2f}x |"
        )
    lines += ["", "```text", format_report(rows, labels, title=title), "```", ""]
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
