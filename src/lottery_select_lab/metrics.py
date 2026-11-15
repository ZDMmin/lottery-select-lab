"""Hit accounting and back-test reporting.

中文：本模块负责「算命中」和「讲清楚命中」——命中数、命中分布、平均命中率、
以及与随机基线相比的增益。手稿把这些逻辑写在 ``main`` 的尾部（``add`` / ``hitnum`` / ``hitp``），
每份脚本复制一遍；这里抽成纯函数，并补上原始手稿缺失的**基线对照**。
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence

from .models import RED_POOL_SIZE, REDS_PER_DRAW


def hit_count(predicted: Iterable[int], actual: Iterable[int]) -> int:
    """How many predicted numbers were actually drawn. / 命中个数。

    注意：手稿这里用「推荐位次是否命中」统计（``acc_t``），另一处用「号码是否命中」（``acc``），
    两者统计口径不同，容易混淆；本模块只保留号码口径，位次口径交给 :func:`ranking.ranks_of`。
    """
    return len(set(predicted) & set(actual))


def hit_distribution(hits: Sequence[int], max_hits: int = REDS_PER_DRAW) -> Dict[int, int]:
    """Frequency table of hit counts ``0..max_hits``. / 命中数频次表。"""
    table = {i: 0 for i in range(max_hits + 1)}
    for value in hits:
        table[int(value)] = table.get(int(value), 0) + 1
    return table


def average_hits(hits: Sequence[int]) -> float:
    """Mean hits per round. / 每轮平均命中数。"""
    return sum(hits) / len(hits) if hits else 0.0


def average_hit_rate(hits: Sequence[int]) -> float:
    """Mean share of drawn balls that were picked (handwritten metric). / 平均命中率（手稿口径）。"""
    return sum(hits) / (REDS_PER_DRAW * len(hits)) if hits else 0.0


def baseline_hits(top_k: int = REDS_PER_DRAW, pool: int = RED_POOL_SIZE) -> float:
    """Expected hits of a blind pick. / 盲选的期望命中数。

    抽 6 个自 33 个号码的池子，任选 k 个：``E = k * 6 / 33``。
    这个数字是整套实验的「及格线」——任何排序策略如果长期贴着它就等于没有信息量。
    """
    return top_k * REDS_PER_DRAW / pool


def lift_vs_baseline(observed: float, top_k: int = REDS_PER_DRAW) -> float:
    """Relative improvement over blind picking. / 相对盲选的提升倍数。"""
    base = baseline_hits(top_k)
    return observed / base if base else 0.0


def summarize(hits: Sequence[int], top_k: int = REDS_PER_DRAW) -> Dict[str, float]:
    """One-stop summary dict used by CLI and README tables. / 汇总字典，供 CLI 与 README 表格使用。"""
    base = baseline_hits(top_k)
    observed = average_hits(hits)
    return {
        "rounds": float(len(hits)),
        "average_hits": observed,
        "average_hit_rate": average_hit_rate(hits),
        "baseline_hits": base,
        "lift": observed / base if base else 0.0,
        "max_hits": float(max(hits)) if hits else 0.0,
    }


def format_report(
    summaries: Sequence[Dict[str, float]],
    labels: Sequence[str],
    title: str = "Back-test report",
) -> str:
    """Render summary rows as a plain-text table (the handwritten ``LOG_*.txt`` successor).

    / 把汇总行渲染成纯文本表格，替代手稿里那套 ``LOG_*.txt`` 拼接。
    """
    header = f"{'run':<28}{'rounds':>8}{'avg_hits':>10}{'hit_rate':>10}{'baseline':>10}{'lift':>8}"
    lines: List[str] = [title, "=" * len(header), header, "-" * len(header)]
    for label, row in zip(labels, summaries):
        lines.append(
            f"{label:<28}{int(row['rounds']):>8}{row['average_hits']:>10.3f}"
            f"{row['average_hit_rate']:>10.3f}{row['baseline_hits']:>10.3f}{row['lift']:>8.2f}x"
        )
    lines.append("-" * len(header))
    return "\n".join(lines)
