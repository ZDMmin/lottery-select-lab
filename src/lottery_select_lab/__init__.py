"""Lottery-Select-Lab / SSQ-Number-Engine / Number-Picking-Lab.

中文：双色球红球选号引擎的研究工作台——把「权重累加 → 位次挖掘 → 多窗口共识投票」
这套思路做成可复现、可回测、可对比的实验框架。

Quick start / 快速开始::

    from lottery_select_lab import BacktestConfig, make_synthetic_draws, run

    draws = make_synthetic_draws(300, seed=42)
    result = run("ensemble", draws, BacktestConfig(top_k=6))
    print(result.average_hits, result.baseline_hits)

一句话提醒：彩票开奖是独立随机事件，本项目的研究价值在**方法学与工程实践**，
而不是「预测中奖」。README 里有完整的基线对照与结论说明。
"""

from __future__ import annotations

__version__ = "0.1.0"

from .backtest import (
    STRATEGIES,
    RankFactorTracker,
    run,
    run_ensemble_backtest,
    run_horizon_topk_backtest,
    run_rank_factor_backtest,
    run_topk_backtest,
)
from .data import load_draws, make_synthetic_draws, parse_line, save_draws, split_train_test
from .metrics import (
    average_hit_rate,
    average_hits,
    baseline_hits,
    format_report,
    hit_count,
    hit_distribution,
    lift_vs_baseline,
    round_variance,
    summarize,
    z_score,
)
from .models import (
    RED_POOL_SIZE,
    REDS_PER_DRAW,
    BacktestConfig,
    BacktestResult,
    Draw,
    RoundResult,
)
from .ranking import (
    consensus_order,
    numbers_at_ranks,
    rank_order,
    ranks_of,
    select_top_k,
    vote,
)
from .weights import (
    decayed_scores,
    draw_weight_vector,
    horizon_scores,
    normalize,
    weight_matrix,
    window_scores,
)

__all__ = [
    "__version__",
    # models
    "Draw",
    "BacktestConfig",
    "BacktestResult",
    "RoundResult",
    "RED_POOL_SIZE",
    "REDS_PER_DRAW",
    # data
    "load_draws",
    "make_synthetic_draws",
    "parse_line",
    "save_draws",
    "split_train_test",
    # weights
    "draw_weight_vector",
    "weight_matrix",
    "window_scores",
    "horizon_scores",
    "decayed_scores",
    "normalize",
    # ranking
    "rank_order",
    "select_top_k",
    "numbers_at_ranks",
    "ranks_of",
    "consensus_order",
    "vote",
    # metrics
    "hit_count",
    "hit_distribution",
    "average_hits",
    "average_hit_rate",
    "baseline_hits",
    "lift_vs_baseline",
    "z_score",
    "round_variance",
    "summarize",
    "format_report",
    # backtest
    "run",
    "STRATEGIES",
    "RankFactorTracker",
    "run_topk_backtest",
    "run_rank_factor_backtest",
    "run_ensemble_backtest",
    "run_horizon_topk_backtest",
]
