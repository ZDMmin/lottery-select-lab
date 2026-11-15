"""Rolling back-tests — the experiments behind ``test.py`` … ``test_5.py``.

中文：本模块把 6 份手稿里重复的「Windows 路径 + 全局变量 + 就地打印」骨架，
重写为三种可对比的回测策略：

==============  =====================================================  ==================
策略            逻辑                                                    手稿对应
==============  =====================================================  ==================
``top-k``       累加过去 ``lookback`` 期得分，直接取前 k 名              ``test.py`` / ``test_2.py``
``rank-factor`` 先统计「哪些位次最容易命中」，再按位次取号              ``test_1.py`` / ``test_3.py``
``ensemble``    多个回看窗口各投一票，按共识票数取号                    ``test_4.py`` / ``test_5.py``
==============  =====================================================  ==================

**最重要的方法学修正**：手稿的因子挖掘用到了全样本（包括被预测期之后的数据），
这属于前视偏差（look-ahead bias）。本模块默认 ``mode="expanding"``，只用目标期之前的历史；
``mode="full"`` 仅用于复刻手稿口径并展示「偏差究竟能虚增多少命中率」。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np

from . import metrics
from .models import RED_POOL_SIZE, BacktestConfig, BacktestResult, Draw, RoundResult
from .ranking import consensus_order, numbers_at_ranks, ranks_of, select_top_k
from .weights import horizon_scores, weight_matrix, window_scores


@dataclass
class RankFactorTracker:
    """Incremental frequency counter over rank positions. / 位次命中频次的增量统计器。

    为什么是增量的：每轮都从头统计是 O(N²)，把「新加入的一期」一次性累加进去就是 O(N)，
    300 期、19 个窗口下从 ~85 万次排序降到 ~6 千次，回测从分钟级降到秒级。
    """

    matrix: np.ndarray
    draws: Sequence[Draw]
    horizons: Sequence[int]
    mode: str = "expanding"

    def __post_init__(self) -> None:
        self.counts = {int(h): np.zeros(RED_POOL_SIZE, dtype=float) for h in self.horizons}
        self._cursor = 0
        if self.mode == "full":
            # 全样本口径：把整段历史一次性看完（含未来数据，故意保留以复刻手稿）。
            self._accumulate_until(len(self.draws))

    def _accumulate_until(self, stop: int) -> None:
        for target in range(self._cursor, stop):
            for h, bucket in self.counts.items():
                if target < h:
                    continue
                scores = window_scores(self.matrix, target, h)
                for rank in ranks_of(scores, self.draws[target].reds):
                    bucket[rank] += 1.0
        self._cursor = max(self._cursor, stop)

    def update_to(self, target_index: int) -> None:
        """Absorb every issue strictly before ``target_index``. / 吸收目标期之前的全部历史。"""
        if self.mode == "full":
            return
        if target_index > self._cursor:
            self._accumulate_until(target_index)

    def rank_factors(self, horizon: int, top_k: int) -> tuple[int, ...]:
        """The ``top_k`` most frequently hit rank positions for this horizon. / 该窗口下最常命中的位次。"""
        counts = self.counts[int(horizon)]
        if counts.sum() == 0:
            # 冷启动：没有任何样本时退化为「取前 top_k 位」，并保持确定性。
            return tuple(range(top_k))
        positions = np.arange(RED_POOL_SIZE)
        return tuple(int(p) for p in positions[np.lexsort((positions, -counts))][:top_k])

    def snapshot(self) -> dict[str, object]:
        """Serializable view of the counter state. / 统计状态的序列化视图。"""
        return {
            "mode": self.mode,
            "horizons": [int(h) for h in self.horizons],
            "accumulated_until": int(self._cursor),
            "counts": {str(h): [float(v) for v in c] for h, c in self.counts.items()},
        }


def _warmup(cfg: BacktestConfig) -> int:
    """First predictable issue index under the current config. / 首个可预测期的下标。"""
    return max(cfg.lookback, max(cfg.horizons))


def _finalize(
    cfg: BacktestConfig,
    rounds: List[RoundResult],
    rank_factors: Optional[dict[str, object]] = None,
) -> BacktestResult:
    hits = [r.hits for r in rounds]
    return BacktestResult(
        config=cfg,
        rounds=rounds,
        distribution=metrics.hit_distribution(hits),
        average_hits=metrics.average_hits(hits),
        baseline_hits=metrics.baseline_hits(cfg.top_k),
        rank_factors=rank_factors,
    )


def run_topk_backtest(draws: Sequence[Draw], cfg: BacktestConfig) -> BacktestResult:
    """Strategy A: sum the window, take the top ``k``. / 策略 A：窗口累加后直接取前 k 名。

    这是最朴素的口径，也是所有花哨策略必须打败的对手。
    """
    cfg.validate()
    matrix = weight_matrix(draws, cfg.hit, cfg.diffusive)
    rounds: List[RoundResult] = []
    for target in range(_warmup(cfg), len(draws)):
        scores = window_scores(matrix, target, cfg.lookback)
        predicted = select_top_k(scores, cfg.top_k)
        actual = draws[target].reds
        rounds.append(
            RoundResult(
                index=target,
                target_issue=draws[target].issue,
                predicted=predicted,
                actual=actual,
                hits=metrics.hit_count(predicted, actual),
            )
        )
    return _finalize(cfg, rounds, {"strategy": "top-k", "horizon": cfg.lookback})


def run_rank_factor_backtest(draws: Sequence[Draw], cfg: BacktestConfig) -> BacktestResult:
    """Strategy B: learn the best rank positions, then pick by position.

    / 策略 B：先学「哪些位次靠谱」，再按位次取号（对应 ``test_3.py`` 的思路，但去掉前视）。
    """
    cfg.validate()
    matrix = weight_matrix(draws, cfg.hit, cfg.diffusive)
    tracker = RankFactorTracker(
        matrix=matrix,
        draws=draws,
        horizons=(cfg.lookback,),
        mode=cfg.mode,
    )
    rounds: List[RoundResult] = []
    for target in range(_warmup(cfg), len(draws)):
        tracker.update_to(target)
        factors = tracker.rank_factors(cfg.lookback, cfg.top_k)
        scores = window_scores(matrix, target, cfg.lookback)
        predicted = numbers_at_ranks(scores, factors)
        actual = draws[target].reds
        rounds.append(
            RoundResult(
                index=target,
                target_issue=draws[target].issue,
                predicted=predicted,
                actual=actual,
                hits=metrics.hit_count(predicted, actual),
                ranks=ranks_of(scores, actual),
            )
        )
    info = {"strategy": "rank-factor", **tracker.snapshot()}
    info["final_factors"] = list(tracker.rank_factors(cfg.lookback, cfg.top_k))
    return _finalize(cfg, rounds, info)


def run_ensemble_backtest(draws: Sequence[Draw], cfg: BacktestConfig) -> BacktestResult:
    """Strategy C: multi-horizon voting (the ``test_5`` idea, made leakage-free).

    / 策略 C：多周期投票。每个回看长度算一个「专家」，各自按自己学到的位次推荐号码，
    再把 19 张票加总，取票数最高的 k 个号。
    """
    cfg.validate()
    matrix = weight_matrix(draws, cfg.hit, cfg.diffusive)
    horizons = tuple(int(h) for h in cfg.horizons)
    tracker = RankFactorTracker(matrix=matrix, draws=draws, horizons=horizons, mode=cfg.mode)

    rounds: List[RoundResult] = []
    for target in range(_warmup(cfg), len(draws)):
        tracker.update_to(target)
        votes = np.zeros(RED_POOL_SIZE, dtype=float)
        experts = {}
        for h in horizons:
            factors = tracker.rank_factors(h, cfg.top_k)
            scores = window_scores(matrix, target, h)
            picked = numbers_at_ranks(scores, factors)
            experts[h] = picked
            for number in picked:
                votes[number - 1] += 1.0
        consensus = consensus_order(votes)
        predicted = tuple(sorted(int(n) for n in consensus[: cfg.top_k]))
        actual = draws[target].reds
        rounds.append(
            RoundResult(
                index=target,
                target_issue=draws[target].issue,
                predicted=predicted,
                actual=actual,
                hits=metrics.hit_count(predicted, actual),
                votes={int(n): int(votes[n - 1]) for n in range(1, RED_POOL_SIZE + 1) if votes[n - 1]},
            )
        )
    info = {"strategy": "ensemble", **tracker.snapshot()}
    info["experts_last_round"] = {
        str(h): list(v) for h, v in (experts if rounds else {}).items()
    }
    return _finalize(cfg, rounds, info)


def run_horizon_topk_backtest(draws: Sequence[Draw], cfg: BacktestConfig) -> BacktestResult:
    """Ablation: vote over top-k experts instead of learned rank factors.

    / 消融实验：多周期投票，但每个专家直接取自己的前 k 名（不做位次学习）。
    用来回答一个很实际的问题——收益到底来自「多窗口投票」，还是来自「位次挖掘」？
    """
    cfg.validate()
    matrix = weight_matrix(draws, cfg.hit, cfg.diffusive)
    horizons = tuple(int(h) for h in cfg.horizons)
    rounds: List[RoundResult] = []
    for target in range(_warmup(cfg), len(draws)):
        rows = horizon_scores(matrix, target, horizons)
        votes = np.zeros(RED_POOL_SIZE, dtype=float)
        for row in rows:
            for number in select_top_k(row, cfg.top_k):
                votes[number - 1] += 1.0
        consensus = consensus_order(votes)
        predicted = tuple(sorted(int(n) for n in consensus[: cfg.top_k]))
        actual = draws[target].reds
        rounds.append(
            RoundResult(
                index=target,
                target_issue=draws[target].issue,
                predicted=predicted,
                actual=actual,
                hits=metrics.hit_count(predicted, actual),
            )
        )
    return _finalize(cfg, rounds, {"strategy": "horizon-top-k", "horizons": list(horizons)})


STRATEGIES = {
    "topk": run_topk_backtest,
    "rank": run_rank_factor_backtest,
    "ensemble": run_ensemble_backtest,
    "horizon-topk": run_horizon_topk_backtest,
}


def run(strategy: str, draws: Sequence[Draw], cfg: BacktestConfig) -> BacktestResult:
    """Dispatch by name. / 按名称分发。"""
    try:
        runner = STRATEGIES[strategy]
    except KeyError:
        raise ValueError(f"unknown strategy {strategy!r}; choose from {sorted(STRATEGIES)}") from None
    return runner(draws, cfg)
