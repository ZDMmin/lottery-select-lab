"""Weight vectors: the scoring primitive of the whole engine.

中文：本模块是整套引擎的评分底座。一期开奖会被投影成一个长度 33 的权重向量：
被开出的号码拿到 ``hit``，其左右邻居各拿到 ``diffusive``；回测时把过去 ``lookback`` 期的
权重向量累加，就得到当期 33 个号码的得分。

手稿对照：
    ``create_33``       -> :func:`zeros33`
    ``merge_33``        -> 向量直接相加（numpy 广播，不再逐元素循环）
    内联的权重累加代码   -> :func:`draw_weight_vector`
    固定 ``range(l)`` 窗口 -> :func:`window_scores`
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np

from .models import RED_POOL_SIZE, Draw


def zeros33(n: int = RED_POOL_SIZE) -> np.ndarray:
    """Zero-filled score vector. / 长度为 33 的全零权重向量（对应手稿 ``create_33``）。"""
    return np.zeros(n, dtype=float)


def draw_weight_vector(
    reds: Sequence[int],
    hit: float = 2.0,
    diffusive: float = 1.0,
    n: int = RED_POOL_SIZE,
) -> np.ndarray:
    """Project one draw onto the 33-dim weight space. / 把一期开奖投影到 33 维权重空间。

    规则（与手稿完全一致 / identical to the handwritten script）:
        * 号码 ``j`` 本身 → 下标 ``j-1`` 加 ``hit``
        * 右邻 ``j+1``  → 下标 ``j``   加 ``diffusive``
        * 左邻 ``j-1``  → 下标 ``j-2`` 加 ``diffusive``
        * ``j == 1`` 没有左邻，``j == 33`` 没有右邻（不做环形回绕）

    为什么要「相邻扩散」：手稿作者的假设是开奖号码之间存在邻域惯性，
    命中本身给出强信号，邻居给出弱信号。这个假设是否成立，由回测来检验。
    """
    weights = zeros33(n)
    for number in reds:
        if not 1 <= number <= n:
            raise ValueError(f"red ball {number} out of 1..{n}")
        weights[number - 1] += hit
        if number == 1:
            weights[number] += diffusive
        elif number == n:
            weights[number - 2] += diffusive
        else:
            weights[number] += diffusive
            weights[number - 2] += diffusive
    return weights


def weight_matrix(
    draws: Iterable[Draw],
    hit: float = 2.0,
    diffusive: float = 1.0,
    n: int = RED_POOL_SIZE,
) -> np.ndarray:
    """Stack per-draw weight vectors into a ``(n_draws, 33)`` matrix. / 堆叠成矩阵，供向量化滑窗。"""
    rows = [draw_weight_vector(d.reds, hit=hit, diffusive=diffusive, n=n) for d in draws]
    if not rows:
        raise ValueError("no draws supplied")
    return np.vstack(rows)


def window_scores(matrix: np.ndarray, target_index: int, lookback: int) -> np.ndarray:
    """Sum the ``lookback`` issues that precede ``target_index``. / 累加目标期之前的 ``lookback`` 期。

    严格只使用 ``target_index`` 之前的数据，因此该函数本身不会产生前视偏差；
    手稿里用零填充去凑不足窗口的期次，这里改为显式报错，避免静默失真。
    """
    if lookback < 1:
        raise ValueError(f"lookback must be >= 1, got {lookback}")
    if target_index < lookback:
        raise ValueError(
            f"target_index={target_index} has fewer than lookback={lookback} issues before it"
        )
    return matrix[target_index - lookback : target_index].sum(axis=0)


def horizon_scores(matrix: np.ndarray, target_index: int, horizons: Sequence[int]) -> np.ndarray:
    """Multi-horizon stack: one score vector per lookback length. / 多周期得分矩阵。

    对应手稿 ``test_5`` 里对 ``l = 1..19`` 分别建窗、各投一票的做法。
    Returns:
        shape ``(len(horizons), 33)``，行顺序与 ``horizons`` 一致。
    """
    rows = [window_scores(matrix, target_index, h) for h in horizons]
    return np.vstack(rows)


def decayed_scores(
    matrix: np.ndarray,
    target_index: int,
    lookback: int,
    half_life: float | None = None,
) -> np.ndarray:
    """Optional recency weighting: recent issues count more. / 可选的时间衰减加权。

    手稿是等权累加。这里额外提供半衰期版本作为对照实验：
    ``half_life=None`` 时等价于等权，便于在同一套回测框架里做 A/B。

    Args:
        half_life: 半衰期（单位：期）。越小的期数权重衰减越快。
    """
    if lookback < 1:
        raise ValueError(f"lookback must be >= 1, got {lookback}")
    if target_index < lookback:
        raise ValueError(f"target_index={target_index} shorter than lookback={lookback}")
    block = matrix[target_index - lookback : target_index]
    if half_life is None:
        return block.sum(axis=0)
    if half_life <= 0:
        raise ValueError(f"half_life must be positive, got {half_life}")
    # 距离目标期越近，权重越高 / closer issues weigh more.
    ages = np.arange(lookback, 0, -1, dtype=float)
    weights = 0.5 ** (ages / float(half_life))
    return weights @ block


def normalize(scores: np.ndarray) -> np.ndarray:
    """Scale scores into ``[0, 1]`` for cross-parameter comparison. / 归一化，便于跨参数比较与绘图。"""
    if scores.size == 0:
        return scores
    low, high = float(scores.min()), float(scores.max())
    if high - low == 0:
        return np.zeros_like(scores)
    return (scores - low) / (high - low)
