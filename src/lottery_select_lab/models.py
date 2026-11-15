"""Shared data models for the selection engine.

中文：本模块定义整个选号引擎共享的数据结构（一次开奖、一次回测轮次、回测配置与汇总结果）。
为什么单独抽出来：原始手稿里这些信息散落在裸 list 与字符串拼接中，
抽成 dataclass 之后，日志输出、图表绘制、结果导出都能共用同一份结构。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Red-ball pool size for the double-color-ball game. / 双色球红球号池大小（1-33）。
RED_POOL_SIZE: int = 33
# Number of red balls drawn per issue. / 每期开出的红球个数。
REDS_PER_DRAW: int = 6


@dataclass(frozen=True)
class Draw:
    """A single lottery issue. / 单期开奖记录。

    Attributes:
        issue: 期号 / issue number, e.g. ``"2024001"``.
        date: 开奖日期，可留空 / draw date, may be empty.
        reds: 升序排列的 6 个红球 / six red balls in ascending order.
        blue: 蓝球号码，缺失时为 ``None`` / blue ball, ``None`` when absent.
    """

    issue: str
    reds: Tuple[int, ...]
    date: str = ""
    blue: Optional[int] = None

    def __post_init__(self) -> None:
        if len(self.reds) != REDS_PER_DRAW:
            raise ValueError(f"expect {REDS_PER_DRAW} reds, got {len(self.reds)}: {self.reds}")
        if any(not 1 <= n <= RED_POOL_SIZE for n in self.reds):
            raise ValueError(f"red ball out of range 1-{RED_POOL_SIZE}: {self.reds}")
        if len(set(self.reds)) != REDS_PER_DRAW:
            raise ValueError(f"duplicated red ball: {self.reds}")

    def to_row(self) -> Tuple[str, str, str, str]:
        """Flatten to a CSV-ready row. / 转成可直接写 CSV 的一行。"""
        return (
            self.issue,
            self.date,
            " ".join(str(n) for n in self.reds),
            "" if self.blue is None else str(self.blue),
        )


@dataclass(frozen=True)
class BacktestConfig:
    """Knobs of one back-test run. / 一次回测的全部参数。

    原始手稿里的 ``h`` / ``d`` / ``p`` / ``l`` 在这里有了名字：
    ``hit`` / ``diffusive`` / ``top_k`` / ``lookback``。
    """

    hit: float = 2.0
    """命中权重 / weight added to the drawn number itself."""
    diffusive: float = 1.0
    """扩散权重 / weight leaking to the two neighbouring numbers."""
    top_k: int = 6
    """每轮选出的号码个数 / how many numbers to pick each round."""
    lookback: int = 19
    """回看窗口长度（期）/ number of past issues summed into the score."""
    horizons: Tuple[int, ...] = tuple(range(1, 20))
    """多周期投票所用的窗口长度集合 / lookbacks used by the ensemble vote."""
    mode: str = "expanding"
    """因子挖掘模式：``expanding``（无前视）或 ``full``（复刻手稿的全样本口径）。"""

    def validate(self) -> None:
        if self.top_k < 1 or self.top_k > RED_POOL_SIZE:
            raise ValueError(f"top_k must be in 1..{RED_POOL_SIZE}, got {self.top_k}")
        if self.lookback < 1:
            raise ValueError(f"lookback must be >= 1, got {self.lookback}")
        if not self.horizons:
            raise ValueError("horizons must not be empty")
        if self.mode not in {"expanding", "full"}:
            raise ValueError(f"unknown mode: {self.mode!r}")


@dataclass
class RoundResult:
    """Outcome of a single back-test round. / 单轮回测结果。

    ``ranks`` 记录命中号码在推荐序列中的位次（0 起），
    这正是原始手稿 ``acc_t`` 函数在统计的东西。
    """

    index: int
    target_issue: str
    predicted: Tuple[int, ...]
    actual: Tuple[int, ...]
    hits: int
    ranks: Tuple[int, ...] = ()
    votes: Dict[int, int] = field(default_factory=dict)

    @property
    def hit_rate(self) -> float:
        """命中占比（命中数 / 开出个数） / share of drawn numbers that were picked."""
        return self.hits / REDS_PER_DRAW


@dataclass
class BacktestResult:
    """Aggregated output of a back-test. / 回测汇总结果。"""

    config: BacktestConfig
    rounds: List[RoundResult]
    distribution: Dict[int, int]
    average_hits: float
    baseline_hits: float
    rank_factors: Optional[Dict[str, object]] = None

    @property
    def n_rounds(self) -> int:
        return len(self.rounds)

    def to_dict(self) -> Dict[str, object]:
        """Plain-dict view for JSON export. / 供 JSON 导出的扁平字典。"""
        return {
            "config": {
                "hit": self.config.hit,
                "diffusive": self.config.diffusive,
                "top_k": self.config.top_k,
                "lookback": self.config.lookback,
                "mode": self.config.mode,
            },
            "n_rounds": self.n_rounds,
            "average_hits": self.average_hits,
            "baseline_hits": self.baseline_hits,
            "distribution": self.distribution,
            "rank_factors": self.rank_factors,
            "rounds": [
                {
                    "index": r.index,
                    "target_issue": r.target_issue,
                    "predicted": list(r.predicted),
                    "actual": list(r.actual),
                    "hits": r.hits,
                    "ranks": list(r.ranks),
                }
                for r in self.rounds
            ],
        }
