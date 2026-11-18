"""Demo 01 — rank-position hit analysis (the readable version of ``test_1.py``).

中文：这个 demo 回答一个最基础的问题——「把 33 个号码按得分排序后，排在第几位的号码最容易真的开出来？」
手稿 test_1 用一张没有标注的散点图表达这件事；这里给出完整统计 + 可出版级的图。

Run / 运行::

    PYTHONPATH=src python examples/01_rank_hit_analysis.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from demo_data import load_demo_draws

from lottery_select_lab import BacktestConfig
from lottery_select_lab.ranking import ranks_of
from lottery_select_lab.viz import plot_rank_hit_counts
from lottery_select_lab.weights import weight_matrix, window_scores

OUT = Path(__file__).parent / "output"
OUT.mkdir(parents=True, exist_ok=True)


def rank_hit_counts(draws, hit: float, diffusive: float, lookback: int) -> np.ndarray:
    """Count how often each rank position contains a drawn number.

    / 统计每个位次上「确实开出号码」的次数。
    注意这里刻意使用 expanding 口径：第 t 期只用第 t 期之前的信息排序。
    """
    matrix = weight_matrix(draws, hit=hit, diffusive=diffusive)
    counts = np.zeros(33, dtype=float)
    for target in range(lookback, len(draws)):
        scores = window_scores(matrix, target, lookback)
        for rank in ranks_of(scores, draws[target].reds):
            counts[rank] += 1.0
    return counts


def main() -> None:
    draws = load_demo_draws()
    cfg = BacktestConfig(hit=2.0, diffusive=1.0, lookback=19)

    counts = rank_hit_counts(draws, cfg.hit, cfg.diffusive, cfg.lookback)
    rounds = len(draws) - cfg.lookback
    print(f"rounds={rounds}")
    print("top-6 rank positions:", np.argsort(-counts)[:6].tolist())
    print("hit frequency per rank (first 12):", counts[:12].astype(int).tolist())

    # 如果没有信号，每个位次的期望命中次数 = rounds * 6 / 33
    expected = rounds * 6 / 33
    print(f"expected per rank if no signal = {expected:.2f}")

    path = plot_rank_hit_counts(
        counts,
        OUT / "01_rank_hit_counts.png",
        title="Which rank positions actually get hit?",
        subtitle=f"口径 expanding · 回看 {cfg.lookback} 期 · {rounds} 轮 · 真实样本",
    )
    print(f"[ok] chart -> {path}")

    np.savetxt(OUT / "01_rank_hit_counts.csv", counts.astype(int), fmt="%d", delimiter=",")


if __name__ == "__main__":
    main()
