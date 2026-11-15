"""Chart rendering for back-tests. / 回测图表渲染。

中文：把所有「看结果」的需求收在这里。手稿里只有 ``test_1.py`` 画了一张散点图，
而且坐标轴标题是 ``X-axis / Y-axis``；这里统一成可直接放进 README 的四类图：

* 位次命中频次图（``test_1`` 的可读版）
* 命中分布对比图（实测 vs 随机基线）
* 滚动命中曲线（看策略是否稳定，而不是只看平均数）
* 策略横向对比图（一图看完所有实验）
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Sequence, Union

import matplotlib

matplotlib.use("Agg")  # 无显示环境下也能出图 / headless-safe backend

import matplotlib.pyplot as plt
import numpy as np

from .models import BacktestResult

# 中文字体缺失时自动回退，避免出现「方块字」/ graceful fallback when CJK font is absent.
plt.rcParams["font.sans-serif"] = [
    "Noto Sans CJK SC",
    "WenQuanYi Zen Hei",
    "Microsoft YaHei",
    "SimHei",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False

PALETTE = {
    "primary": "#2B6CB0",
    "accent": "#DD6B20",
    "baseline": "#718096",
    "grid": "#E2E8F0",
}


def _save(fig: plt.Figure, path: Union[str, Path], dpi: int = 160) -> Path:
    """Save and close. / 保存并关闭画布。"""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def plot_rank_hit_counts(
    counts: np.ndarray,
    path: Union[str, Path],
    title: str = "Which rank positions get hit?",
    subtitle: str = "位次命中频次",
) -> Path:
    """Bar+scatter of hit frequency per rank position. / 每个位次的命中频次。

    这正是 ``test_1.py`` 想表达但没标清的东西：横轴 = 推荐位次（第 0 位到第 32 位），
    纵轴 = 该位次上的号码被开出的次数。
    """
    counts = np.asarray(counts, dtype=float)
    fig, ax = plt.subplots(figsize=(10, 4.2))
    positions = np.arange(len(counts))
    ax.bar(positions, counts, color=PALETTE["primary"], alpha=0.75, label="频次 / count")
    ax.plot(positions, counts, color=PALETTE["accent"], marker="*", ms=7, lw=1.0, label="趋势 / trend")

    mean = counts.mean()
    ax.axhline(mean, color=PALETTE["baseline"], ls="--", lw=1.2, label=f"均值 / mean = {mean:.1f}")
    for idx in np.argsort(-counts)[:6]:
        ax.annotate(
            f"{idx}",
            (idx, counts[idx]),
            textcoords="offset points",
            xytext=(0, 4),
            ha="center",
            fontsize=8,
            color=PALETTE["accent"],
        )

    ax.set_xlabel("推荐位次 rank position（0 = 得分最高）")
    ax.set_ylabel("命中次数 hits")
    ax.set_title(f"{title}\n{subtitle}", fontsize=12, loc="left")
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    ax.grid(axis="y", color=PALETTE["grid"], lw=0.8)
    ax.set_axisbelow(True)
    return _save(fig, path)


def plot_hit_distribution(
    result: BacktestResult,
    path: Union[str, Path],
    title: str = "Hit distribution vs random baseline",
) -> Path:
    """Observed hit-count distribution with the analytic baseline overlaid. / 命中分布对比随机基线。

    基线用二项分布近似：每期抽 6 个，命中数量 ~ Hypergeometric(33, 6, k)，
    这里画期望频次，读者一眼就能看出策略是否真的越过了「运气」。
    """
    from scipy.stats import hypergeom

    dist = result.distribution
    keys = sorted(dist)
    observed = np.array([dist[k] for k in keys], dtype=float)
    total = observed.sum()

    # 超几何分布：总体 33、命中球 6、抽取 top_k 个 / hypergeometric expectation.
    hyp = hypergeom(M=33, n=6, N=result.config.top_k)
    expected = np.array([hyp.pmf(k) for k in keys]) * total

    fig, ax = plt.subplots(figsize=(9, 4.2))
    width = 0.38
    x = np.arange(len(keys))
    ax.bar(x - width / 2, observed, width, color=PALETTE["primary"], label="实测 observed")
    ax.bar(x + width / 2, expected, width, color=PALETTE["baseline"], alpha=0.55, label="随机基线 baseline")

    ax.set_xticks(x)
    ax.set_xticklabels([str(k) for k in keys])
    ax.set_xlabel("单期命中数 hits per round")
    ax.set_ylabel("期数 issues")
    ax.set_title(f"{title}  |  avg={result.average_hits:.2f} vs baseline={result.baseline_hits:.2f}",
                 fontsize=11, loc="left")
    ax.legend(frameon=False, fontsize=9)
    ax.grid(axis="y", color=PALETTE["grid"], lw=0.8)
    ax.set_axisbelow(True)
    return _save(fig, path)


def plot_rolling_hits(
    results: Dict[str, BacktestResult],
    path: Union[str, Path],
    window: int = 20,
    title: str = "Rolling hit rate — is the edge stable?",
) -> Path:
    """Rolling mean of hits per round for one or more strategies. / 滚动命中均值曲线。

    只看平均值很容易被少数几轮「爆表」带偏，滚动曲线才是判断策略是否稳定的正确视角。
    """
    fig, ax = plt.subplots(figsize=(10, 4.4))
    colors = [PALETTE["primary"], PALETTE["accent"], "#2F855A", "#805AD5"]
    for i, (label, result) in enumerate(results.items()):
        hits = np.array([r.hits for r in result.rounds], dtype=float)
        if hits.size < 2:
            continue
        kernel = np.ones(min(window, hits.size)) / min(window, hits.size)
        smooth = np.convolve(hits, kernel, mode="valid")
        ax.plot(np.arange(len(smooth)), smooth, lw=1.8, label=label, color=colors[i % len(colors)])

    ax.axhline(
        next(iter(results.values())).baseline_hits,
        color=PALETTE["baseline"],
        ls="--",
        lw=1.2,
        label="随机基线 baseline",
    )
    ax.set_xlabel(f"回测轮次 round（滑动窗口 {window}）")
    ax.set_ylabel("滑动平均命中数 rolling avg hits")
    ax.set_title(title, fontsize=12, loc="left")
    ax.legend(
        fontsize=9,
        loc="upper left",
        frameon=True,
        facecolor="white",
        framealpha=0.92,
        edgecolor=PALETTE["grid"],
    )
    ax.grid(color=PALETTE["grid"], lw=0.8)
    ax.set_axisbelow(True)
    return _save(fig, path)


def plot_strategy_comparison(
    labels: Sequence[str],
    averages: Sequence[float],
    baseline: float,
    path: Union[str, Path],
    title: str = "Strategy comparison",
) -> Path:
    """Horizontal bars of average hits, with the baseline as a vertical rule. / 策略横向对比。

    README 首图就用这张——一眼能看出「哪个思路真的有用」。
    """
    fig, ax = plt.subplots(figsize=(9, 0.72 * len(labels) + 1.6))
    y = np.arange(len(labels))
    colors = [PALETTE["primary"] if v >= baseline else PALETTE["baseline"] for v in averages]
    bars = ax.barh(y, averages, color=colors, alpha=0.85, height=0.42,
                   edgecolor="white", linewidth=0.6)
    ax.axvline(baseline, color=PALETTE["accent"], ls="--", lw=1.4)

    # 右侧留出 15% 余量，避免数值标签压到基线虚线上 / head-room for the value labels.
    upper = max(max(averages), baseline) * 1.18
    ax.set_xlim(0, upper)
    for bar, value in zip(bars, averages):
        ax.text(
            value + upper * 0.015,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.2f}",
            va="center",
            fontsize=9,
            color="#1A202C",
        )
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_ylim(len(labels) - 0.4, -0.95)
    ax.text(
        baseline,
        -0.62,
        f"随机基线 baseline = {baseline:.2f}",
        ha="center",
        va="center",
        fontsize=9,
        color=PALETTE["accent"],
    )
    ax.set_xlabel("平均命中数 avg hits per round")
    ax.set_title(title, fontsize=12, loc="left")
    ax.grid(axis="x", color=PALETTE["grid"], lw=0.8)
    ax.set_axisbelow(True)
    return _save(fig, path)


def plot_score_landscape(
    scores: np.ndarray,
    picked: Sequence[int],
    path: Union[str, Path],
    title: str = "Score landscape of one issue",
    subtitle: str = "",
) -> Path:
    """One issue's 33 scores with the selected numbers highlighted. / 单期得分地形图。

    对读者最友好的一张图：33 个号码的得分柱状图，被选中的号码高亮，
    读者能立刻理解「这套引擎到底在给每个号码打什么分」。
    """
    scores = np.asarray(scores, dtype=float)
    picked = set(int(p) for p in picked)
    fig, ax = plt.subplots(figsize=(11, 4.2))
    x = np.arange(1, len(scores) + 1)
    colors = [PALETTE["accent"] if n in picked else PALETTE["primary"] for n in x]
    ax.bar(x, scores, color=colors, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels([str(n) for n in x], fontsize=8)
    ax.set_xlabel("红球号码 red ball (1-33)")
    ax.set_ylabel("综合得分 aggregated score")
    ax.set_title(f"{title}\n{subtitle}" if subtitle else title, fontsize=11, loc="left")
    ax.grid(axis="y", color=PALETTE["grid"], lw=0.8)
    ax.set_axisbelow(True)
    return _save(fig, path)
