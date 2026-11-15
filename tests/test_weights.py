"""Tests for the weight-vector primitive. / 权重向量底座测试。

中文：这一层是整套引擎的地基。手稿里那三个 ``if`` 分支（1 号、33 号、中间号码）
最容易在重构时写错，所以直接用「手工推演的期望值」把它们钉死。
"""

from __future__ import annotations

import numpy as np
import pytest

from lottery_select_lab import make_synthetic_draws
from lottery_select_lab.weights import (
    decayed_scores,
    draw_weight_vector,
    horizon_scores,
    normalize,
    weight_matrix,
    window_scores,
)


def test_boundary_numbers_1_and_33_do_not_wrap() -> None:
    """1 号没有左邻，33 号没有右邻。 / no wrap-around at the pool edges."""
    w = draw_weight_vector([1, 33], hit=2.0, diffusive=1.0)
    # 1 号：本体 + 右邻
    assert w[0] == 2.0
    assert w[1] == 1.0
    # 33 号：本体 + 左邻
    assert w[32] == 2.0
    assert w[31] == 1.0
    # 绝不能有环形回绕：第 33 个不该扩散到 1 号，1 号也不该扩散到 33 号
    assert w[0] == 2.0 and w[32] == 2.0


def test_middle_number_gets_two_neighbours() -> None:
    """中间号码左右各拿一份扩散权重。 / interior numbers receive both neighbours."""
    w = draw_weight_vector([10], hit=3.0, diffusive=0.5)
    assert w[9] == 3.0          # 本体 / itself
    assert w[8] == 0.5          # 左邻 9 / left neighbour
    assert w[10] == 0.5         # 右邻 11 / right neighbour


def test_reference_implementation_matches() -> None:
    """与手稿逐字节同构的朴素实现对比。 / compare against the naive handwritten version."""
    reds = [3, 7, 12, 20, 25, 31]

    def naive(hit: float, diffusive: float) -> np.ndarray:
        table = [0.0] * 33
        for j in reds:
            if j == 1:
                table[j - 1] += hit
                table[j] += diffusive
            elif j == 33:
                table[j - 1] += hit
                table[j - 2] += diffusive
            else:
                table[j] += diffusive
                table[j - 1] += hit
                table[j - 2] += diffusive
        return np.array(table)

    np.testing.assert_allclose(draw_weight_vector(reds, 2.0, 0.5), naive(2.0, 0.5))


def test_weight_matrix_shape_and_symmetry() -> None:
    draws = make_synthetic_draws(20, seed=1)
    matrix = weight_matrix(draws, hit=2.0, diffusive=1.0)
    assert matrix.shape == (20, 33)
    # 每期总权重 = 6*hit + 每个号码的邻居槽位；1 号与 33 号只有一个邻居，
    # 因此边界号码会少贡献一份 diffusive。/ edge numbers contribute one neighbour only.
    expected = np.array(
        [6 * 2.0 + (12 - sum(n in (1, 33) for n in d.reds)) * 1.0 for d in draws]
    )
    np.testing.assert_allclose(matrix.sum(axis=1), expected)


def test_window_scores_is_sum_of_history_only() -> None:
    draws = make_synthetic_draws(30, seed=2)
    matrix = weight_matrix(draws)
    got = window_scores(matrix, target_index=10, lookback=5)
    np.testing.assert_allclose(got, matrix[5:10].sum(axis=0))


def test_window_scores_rejects_short_history() -> None:
    matrix = np.zeros((5, 33))
    with pytest.raises(ValueError):
        window_scores(matrix, target_index=2, lookback=5)


def test_horizon_scores_row_order() -> None:
    matrix = np.ones((30, 33))
    row = horizon_scores(matrix, target_index=20, horizons=(1, 3, 5))
    assert row.shape == (3, 33)
    np.testing.assert_allclose(row[:, 0], [1.0, 3.0, 5.0])


def test_half_life_none_equals_plain_sum() -> None:
    matrix = np.ones((20, 33))
    np.testing.assert_allclose(
        decayed_scores(matrix, target_index=10, lookback=4),
        window_scores(matrix, target_index=10, lookback=4),
    )


def test_decayed_scores_weights_recent_issues_more() -> None:
    matrix = np.zeros((10, 33))
    matrix[8, 0] = 1.0   # 距今 1 期 / one issue ago
    matrix[0, 1] = 1.0   # 距今 9 期 / nine issues ago
    scores = decayed_scores(matrix, target_index=9, lookback=9, half_life=2.0)
    assert scores[0] > scores[1]


def test_normalize_bounds() -> None:
    out = normalize(np.array([1.0, 5.0, 3.0]))
    np.testing.assert_allclose(out, [0.0, 1.0, 0.5])
