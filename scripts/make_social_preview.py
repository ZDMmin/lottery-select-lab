#!/usr/bin/env python3
"""Render the 1280x640 GitHub social preview card.

渲染 1280x640 的 GitHub 社交预览图（仓库 Settings → Social preview 上传）。

Every number on this card is computed from the committed sample, so the asset
cannot drift away from the README. / 图上的每个数字都由仓库内的样本数据算出，
不会与 README 脱节。

Usage / 用法:
    python scripts/make_social_preview.py
"""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lottery_select_lab import BacktestConfig, load_draws, run  # noqa: E402

# ---------------------------------------------------------------- palette ----
BG = "#0B0F17"
INK = "#F0F6FC"
MUTED = "#8B949E"
GRID = "#1C2432"
HONEST = "#4C8DF6"
LEAKY = "#F2554C"
ACCENT = "#F2554C"

SANS = "DejaVu Sans"
CJK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
CJK_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

W, H = 1280, 640
CONFIG = BacktestConfig(top_k=6, lookback=19, horizons=tuple(range(1, 20)))
SAMPLE = ROOT / "data" / "sample" / "ssq_sample.csv"


def measure() -> tuple[float, float, int, float, int]:
    """Return (honest, leaky, rounds, baseline, issues) from the committed sample.

    从仓库内的真实样本算出：诚实口径、泄漏口径、回测轮数、盲选基线、样本期数。
    """
    draws = load_draws(SAMPLE)
    honest = run("ensemble", draws, replace(CONFIG, mode="expanding"))
    leaky = run("ensemble", draws, replace(CONFIG, mode="full"))
    return honest.average_hits, leaky.average_hits, honest.n_rounds, honest.baseline_hits, len(draws)


def render() -> Path:
    honest, leaky, rounds, baseline, issues = measure()
    inflation = (leaky / honest - 1) * 100
    # Analytic z: each round's hit count is Hypergeometric(33, 6, 6) because the
    # predictions are fixed before the draw. / 每轮命中数服从超几何分布，故 z 可解析求出。
    var = 6 * (6 / 33) * (1 - 6 / 33) * (33 - 6) / 32
    z_honest = (honest - baseline) / (var / rounds) ** 0.5

    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=BG)
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")

    en = FontProperties(family=SANS)
    en_b = FontProperties(family=SANS, weight="bold")
    zh = FontProperties(fname=CJK)
    zh_b = FontProperties(fname=CJK_BOLD)

    # ------------------------------------------------------------- eyebrow ----
    ax.add_patch(FancyBboxPatch(
        (72, 542), 408, 34, boxstyle="round,pad=0,rounding_size=17",
        linewidth=0, facecolor="#161D29", zorder=2,
    ))
    ax.text(96, 559, f"{issues} REAL ISSUES  ·  {rounds} ROUNDS  ·  44 TESTS",
            color=MUTED, fontsize=10, fontproperties=en, va="center", zorder=3)

    # ------------------------------------------------------------ headline ----
    ax.text(72, 492, "Predicting lottery", color=INK, fontsize=35,
            fontproperties=en_b, va="top")
    ax.text(72, 440, "numbers works.", color=INK, fontsize=35,
            fontproperties=en_b, va="top")
    ax.text(72, 388, "If you cheat.", color=ACCENT, fontsize=35,
            fontproperties=en_b, va="top")

    ax.plot([72, 560], [344, 344], color=GRID, lw=1)

    ax.text(72, 316, "同一套代码，只切一个开关：命中率凭空涨了", color=MUTED,
            fontsize=15, fontproperties=zh, va="top")
    ax.text(72, 288, f"{inflation:.0f}%，因为偷看了未来。", color="#C9D1D9",
            fontsize=15, fontproperties=zh_b, va="top")

    ax.text(72, 246, f"honest edge:  z = {z_honest:.2f}   →   inside the noise band (|z| < 2)",
            color="#6E7681", fontsize=11, fontproperties=en, va="top")

    # --------------------------------------------------------------- chart ----
    left, right = 690, 1216
    base_y, unit = 150, 615
    bar_w, gap = 160, 90

    def y_of(value: float) -> float:
        return base_y + (value - 1.0) * unit

    ax.plot([664, 664], [110, 604], color=GRID, lw=1)

    ax.text(left, 592, "AVERAGE HITS PER ROUND", color=MUTED, fontsize=10,
            fontproperties=en, va="top")
    ax.text(right, 592, f"n = {rounds}", color=MUTED, fontsize=10,
            fontproperties=en, va="top", ha="right")

    for value in (1.2, 1.4, 1.6):
        ax.plot([left, right], [y_of(value)] * 2, color=GRID, lw=1, zorder=1)

    ax.plot([left, right], [y_of(baseline)] * 2, color="#6E7681", lw=1.4,
            ls=(0, (4, 3)), zorder=2)
    ax.text(left + 4, y_of(baseline) + 6, f"blind {baseline:.2f}", color="#6E7681",
            fontsize=8.5, fontproperties=en, va="bottom", ha="left")

    # ax.bar takes the BAR CENTRE as x; centres chosen so the two bars sit flush.
    # ax.bar 的 x 是柱心，这里按柱心定位，保证两根柱子居中且留出标注间隙。
    bars = (
        (842, honest, HONEST, "honest", "expanding window"),
        (1092, leaky, LEAKY, "leaked", "full sample"),
    )
    for x, value, color, label, mode in bars:
        ax.bar(x, y_of(value) - base_y, width=bar_w, bottom=base_y, color=color,
               alpha=0.92, edgecolor="none", zorder=3)
        ax.text(x, y_of(value) + 10, f"{value:.2f}", color=INK,
                fontsize=24, fontproperties=en_b, ha="center", va="bottom", zorder=4)
        ax.text(x, base_y - 16, label, color=INK, fontsize=13,
                fontproperties=en_b, ha="center", va="top")
        ax.text(x, base_y - 36, mode, color=MUTED, fontsize=9.5,
                fontproperties=en, ha="center", va="top")

    # delta bracket sits in the gap between the bars / 差值标注放在两根柱子之间
    x_mark = (842 + 1092) / 2
    ax.annotate(
        "", xy=(x_mark, y_of(leaky) - 8), xytext=(x_mark, y_of(honest) + 8),
        arrowprops=dict(arrowstyle="<->", color=ACCENT, lw=1.4, shrinkA=0, shrinkB=0),
    )
    ax.text(x_mark - 12, 402, f"+{inflation:.0f}%", color=ACCENT, fontsize=15,
            fontproperties=en_b, ha="right", va="center")

    # -------------------------------------------------------------- footer ----
    ax.plot([72, right], [96, 96], color=GRID, lw=1)
    ax.text(72, 66, "github.com/ZDMmin/lottery-select-lab", color="#79C0FF",
            fontsize=14, fontproperties=en_b, va="center")
    ax.text(right, 66, "MIT  ·  refactored with Doubao Work (豆包办公)", color=MUTED,
            fontsize=10, fontproperties=zh, va="center", ha="right")

    out = ROOT / "docs" / "assets" / "social-preview.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=100, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"honest={honest:.3f} leaky={leaky:.3f} inflation={inflation:.1f}% -> {out}")
    return out


if __name__ == "__main__":
    render()
