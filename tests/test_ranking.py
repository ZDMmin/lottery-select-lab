"""Tests for ranking / selection / voting rules. / 排序、取号与投票规则测试。

中文：重点验证两件事——
1. **无副作用**：排序函数不能像手稿那样把入参数组改成 ``-1``；
2. **确定性**：同分时的口径固定为「号码小者优先」，否则回测不可复现。
"""

from __future__ import annotations

import numpy as np
import pytest

from lottery_select_lab.ranking import (
    consensus_order,
    numbers_at_ranks,
    rank_order,
    ranks_of,
    select_top_k,
    vote,
)


def test_rank_order_does_not_mutate_input() -> None:
    """手稿 ``guess`` 的最大隐患：改掉了调用方的数组。 / guards against in-place mutation."""
    scores = np.array([5.0, 9.0, 1.0] + [0.0] * 30)
    before = scores.copy()
    order = rank_order(scores)
    np.testing.assert_array_equal(scores, before)
    assert order[0] == 2


def test_rank_order_ties_break_by_smaller_number() -> None:
    scores = np.zeros(33)
    order = rank_order(scores)
    np.testing.assert_array_equal(order, np.arange(1, 34))


def test_rank_order_is_a_permutation() -> None:
    rng = np.random.default_rng(0)
    order = rank_order(rng.normal(size=33))
    assert sorted(order.tolist()) == list(range(1, 34))


def test_select_top_k_is_ascending_and_correct() -> None:
    scores = np.zeros(33)
    scores[[4, 9, 15, 22, 28, 30]] = 3.0     # 5/10/16/23/29/31
    picked = select_top_k(scores, 6)
    assert picked == (5, 10, 16, 23, 29, 31)


def test_select_top_k_rejects_bad_k() -> None:
    with pytest.raises(ValueError):
        select_top_k(np.zeros(33), 0)
    with pytest.raises(ValueError):
        select_top_k(np.zeros(33), 34)


def test_numbers_at_ranks_and_ranks_of_are_inverse() -> None:
    rng = np.random.default_rng(3)
    scores = rng.normal(size=33)
    ranks = (0, 3, 7, 12, 20, 31)
    numbers = numbers_at_ranks(scores, ranks)
    assert ranks_of(scores, numbers) == tuple(sorted(ranks))


def test_numbers_at_ranks_rejects_out_of_range() -> None:
    with pytest.raises(ValueError):
        numbers_at_ranks(np.zeros(33), [33])


def test_consensus_order_prefers_more_votes() -> None:
    votes = np.zeros(33)
    votes[6] = 5.0    # number 7
    votes[2] = 5.0    # number 3  <- tie, smaller number first
    votes[30] = 9.0   # number 31
    order = consensus_order(votes)
    assert order[:3].tolist() == [31, 3, 7]


def test_consensus_order_accepts_dict() -> None:
    order = consensus_order({5: 2, 7: 3})
    assert order[0] == 7 and order[1] == 5


def test_vote_accumulates_every_row() -> None:
    rows = np.zeros((2, 33))
    rows[0, [0, 1, 2, 3, 4, 5]] = 1.0
    rows[1, [0, 1, 2, 3, 4, 5]] = 1.0
    counts = vote(rows, top_k=6)
    np.testing.assert_allclose(counts[:6], np.full(6, 2.0))
    assert counts.sum() == 12.0
