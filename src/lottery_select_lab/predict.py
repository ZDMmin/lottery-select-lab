"""Next-issue recommendation — the ``start_prediction`` stub, finally implemented.

中文：``test_5.py`` 末尾留了一个空的 ``start_prediction()``，说明作者当时已经想到
「把回测结论用在下一期」这一步。本模块把它补完：

1. 用历史学到的位次因子 → 多窗口推荐 → 票数共识；
2. 输出 6 个号码，并附带每个号码的票数与得分，**不输出任何「中奖概率」**；
3. 明确打印冷启动与数据不足的告警，避免给出「看起来很确定」的空结果。

⚠️ 责任边界：这只是一种组合生成器，不改变开奖的随机性。
中文说明见 README「免责声明」一节。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

import numpy as np

from .backtest import RankFactorTracker
from .models import RED_POOL_SIZE, BacktestConfig, Draw
from .ranking import consensus_order, numbers_at_ranks
from .weights import weight_matrix, window_scores


@dataclass
class Prediction:
    """A single next-issue recommendation. / 单期推荐结果。"""

    numbers: Tuple[int, ...]
    votes: Dict[int, int]
    scores: Dict[int, float]
    experts: Dict[int, Tuple[int, ...]] = field(default_factory=dict)
    history_size: int = 0
    warnings: List[str] = field(default_factory=list)

    def explain(self) -> str:
        """Human-readable report. / 可读报告。"""
        lines = [f"推荐号码 / recommendation: {' '.join(f'{n:02d}' for n in self.numbers)}"]
        lines.append(f"历史期数 / history: {self.history_size}")
        for number in self.numbers:
            lines.append(
                f"  #{number:02d}  票数 votes = {self.votes.get(number, 0):>2}  "
                f"得分 score = {self.scores.get(number, 0.0):.2f}"
            )
        if self.warnings:
            lines.append("警告 / warnings:")
            lines.extend(f"  - {w}" for w in self.warnings)
        return "\n".join(lines)


def predict_next(draws: Sequence[Draw], cfg: BacktestConfig) -> Prediction:
    """Generate a recommendation for the issue *after* the last draw. / 为最后一期之后的下一期选号。

    Args:
        draws: 历史开奖记录（按期号升序）/ draws in ascending issue order.
        cfg: 参数；``mode`` 建议保持 ``expanding``（生产中永远不该看未来）。

    Returns:
        :class:`Prediction`，含号码、票数、得分与告警。
    """
    cfg.validate()
    if len(draws) < max(cfg.horizons) + 1:
        raise ValueError(
            f"need at least {max(cfg.horizons) + 1} issues, got {len(draws)}"
        )

    matrix = weight_matrix(draws, cfg.hit, cfg.diffusive)
    horizons = tuple(int(h) for h in cfg.horizons)
    tracker = RankFactorTracker(matrix=matrix, draws=draws, horizons=horizons, mode=cfg.mode)
    tracker.update_to(len(draws))  # 吸收全部已知历史 / absorb the whole known history

    votes = np.zeros(RED_POOL_SIZE, dtype=float)
    experts: Dict[int, Tuple[int, ...]] = {}
    for h in horizons:
        factors = tracker.rank_factors(h, cfg.top_k)
        picked = numbers_at_ranks(window_scores(matrix, len(draws), h), factors)
        experts[h] = picked
        for number in picked:
            votes[number - 1] += 1.0

    order = consensus_order(votes)
    numbers = tuple(sorted(int(n) for n in order[: cfg.top_k]))

    # 综合得分：把各窗口的得分归一化后平均，仅用于解释强弱，不参与选号。
    score_rows = [window_scores(matrix, len(draws), h) for h in horizons]
    combined = np.mean([row / row.max() if row.max() else row for row in score_rows], axis=0)

    warnings: List[str] = []
    if cfg.mode == "full":
        warnings.append("mode=full 使用了全样本（含未来）口径，仅用于对照实验，勿用于实际选号")
    if votes.max() < len(horizons) // 2:
        warnings.append("票数分散：各窗口分歧较大，本期共识不强")
    if len(draws) < 200:
        warnings.append(f"历史样本偏少（{len(draws)} 期），因子统计不稳定")

    return Prediction(
        numbers=numbers,
        votes={int(n): int(votes[n - 1]) for n in range(1, RED_POOL_SIZE + 1) if votes[n - 1]},
        scores={int(n): float(combined[n - 1]) for n in range(1, RED_POOL_SIZE + 1)},
        experts=experts,
        history_size=len(draws),
        warnings=warnings,
    )
