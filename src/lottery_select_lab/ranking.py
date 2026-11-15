"""Ranking, selection and voting rules.

中文：本模块把「33 维得分」翻译成「号码顺序 / 推荐集合 / 共识票数排名」。
手稿里 :func:`guess` / :func:`map_w` / :func:`map_s` 三个函数其实是同一件事的三种切片方式，
区别只在「取前 p 位」还是「取指定置信位次」，所以这里合并为一套 API。
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np

from .models import RED_POOL_SIZE


def rank_order(scores: np.ndarray) -> np.ndarray:
    """Rank numbers 1..33 by descending score, ties broken by the smaller number.

    / 将 1-33 按得分降序排列；同分时号码小的在前。

    与手稿的关键差异：**不修改入参**。手稿的 ``guess`` 会把入参数组里的元素改成 ``-1``，
    一旦调用方复用同一个数组就会得到全错的次序——这类「隐式副作用」是重构时最该清掉的东西。
    """
    scores = np.asarray(scores, dtype=float)
    if scores.shape != (RED_POOL_SIZE,):
        raise ValueError(f"expect {RED_POOL_SIZE} scores, got shape {scores.shape}")
    numbers = np.arange(1, RED_POOL_SIZE + 1)
    # lexsort: 主键是「负得分」（升序 => 得分降序），次键是号码升序。
    order = np.lexsort((numbers, -scores))
    return numbers[order]


def select_top_k(scores: np.ndarray, k: int) -> tuple[int, ...]:
    """Top-``k`` numbers, returned in ascending order. / 取前 ``k`` 名，按号码升序返回。

    手稿的「猜测集合」是按推荐顺序排列的，但作为一注号码它天然无序；
    统一升序输出便于与开奖号码逐位比较，也便于写进日志。
    """
    if not 1 <= k <= RED_POOL_SIZE:
        raise ValueError(f"k must be in 1..{RED_POOL_SIZE}, got {k}")
    return tuple(sorted(int(n) for n in rank_order(scores)[:k]))


def numbers_at_ranks(scores: np.ndarray, ranks: Sequence[int]) -> tuple[int, ...]:
    """Pick numbers sitting at specific rank positions (0-based). / 按指定位次取号。

    这是手稿 ``map_s(weight, subscript)`` 的语义：不取「前 k 名」，
    而是取「作者认为历史上最靠谱的那 6 个位次」。``ranks`` 用 0 起下标。
    """
    order = rank_order(scores)
    picked = []
    for rank in ranks:
        if not 0 <= int(rank) < RED_POOL_SIZE:
            raise ValueError(f"rank {rank} out of 0..{RED_POOL_SIZE - 1}")
        picked.append(int(order[int(rank)]))
    return tuple(sorted(picked))


def ranks_of(scores: np.ndarray, numbers: Iterable[int]) -> tuple[int, ...]:
    """Inverse lookup: which rank position does each number occupy? / 反查：这些号码各在第几位。

    手稿 ``acc_t`` / ``verify`` 统计的就是这个位次集合，然后再看哪些位次最常命中。
    返回 0 起的位次，升序。
    """
    order = rank_order(scores)
    position = {int(number): idx for idx, number in enumerate(order)}
    ranks = []
    for number in numbers:
        if int(number) not in position:
            raise ValueError(f"number {number} not in 1..{RED_POOL_SIZE}")
        ranks.append(position[int(number)])
    return tuple(sorted(ranks))


def consensus_order(votes: dict[int, int] | np.ndarray) -> np.ndarray:
    """Rank numbers by accumulated votes, ties broken by the smaller number.

    / 按累计票数排名，同票时号码小的在前。

    手稿 ``main`` 里那段「反复找最大值再置 -1」的双层循环就是这件事，
    但它在全零票时会返回号码 1 并污染结果（见 ``maxi`` 初值），这里用确定性排序替代。
    """
    if isinstance(votes, dict):
        counts = np.zeros(RED_POOL_SIZE, dtype=float)
        for number, count in votes.items():
            counts[int(number) - 1] += float(count)
    else:
        counts = np.asarray(votes, dtype=float)
        if counts.shape != (RED_POOL_SIZE,):
            raise ValueError(f"expect {RED_POOL_SIZE} vote counts, got {counts.shape}")
    numbers = np.arange(1, RED_POOL_SIZE + 1)
    return numbers[np.lexsort((numbers, -counts))]


def vote(score_rows: np.ndarray, top_k: int) -> np.ndarray:
    """Accumulate votes from several score vectors into one count vector. / 多路打分投票汇总。

    每一行代表一个「选号专家」（例如一个不同长度的回看窗口）的一票，
    汇总后的票数分布就是共识排序的依据。
    """
    scores = np.atleast_2d(np.asarray(score_rows, dtype=float))
    if scores.shape[1] != RED_POOL_SIZE:
        raise ValueError(f"expect {RED_POOL_SIZE} columns, got {scores.shape}")
    counts = np.zeros(RED_POOL_SIZE, dtype=float)
    for row in scores:
        for number in select_top_k(row, top_k):
            counts[number - 1] += 1.0
    return counts
