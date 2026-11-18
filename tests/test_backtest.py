"""Tests for back-tests, metrics and recommendations. / 回测、指标与推荐测试。

中文：这一层不做「命中率是否够高」的判断（那是业务结论），
只验证三件工程事实：

1. 回测轮次数、分布计数守恒；
2. 增量统计与全量重算结果一致（重构的核心优化不能改变结果）；
3. 前视口径（``full``）在合成数据上必须**优于**无前视口径——否则说明我们的
   泄漏检测逻辑本身失效了。
"""

from __future__ import annotations

import numpy as np
import pytest

from lottery_select_lab import BacktestConfig, make_synthetic_draws
from lottery_select_lab.backtest import (
    RankFactorTracker,
    run,
    run_ensemble_backtest,
    run_horizon_topk_backtest,
    run_rank_factor_backtest,
    run_topk_backtest,
)
from lottery_select_lab.metrics import (
    baseline_hits,
    hit_count,
    hit_distribution,
    round_variance,
    summarize,
    z_score,
)
from lottery_select_lab.predict import predict_next
from lottery_select_lab.ranking import ranks_of
from lottery_select_lab.weights import weight_matrix, window_scores


@pytest.fixture(scope="module")
def draws():
    return make_synthetic_draws(120, seed=21)


def test_baseline_is_analytic() -> None:
    np.testing.assert_allclose(baseline_hits(6), 6 * 6 / 33)


def test_hit_count_and_distribution() -> None:
    assert hit_count([1, 2, 3, 4, 5, 6], [3, 4, 9, 10, 11, 12]) == 2
    table = hit_distribution([0, 1, 1, 2, 6])
    assert table[1] == 2 and table[6] == 1
    assert sum(table.values()) == 5


def test_summarize_consistency() -> None:
    row = summarize([1, 2, 3], top_k=6)
    assert row["rounds"] == 3
    np.testing.assert_allclose(row["average_hits"], 2.0)
    np.testing.assert_allclose(row["average_hit_rate"], 2.0 / 6)
    np.testing.assert_allclose(row["lift"], 2.0 / baseline_hits(6))


def test_round_variance_matches_hypergeometric() -> None:
    """单轮方差 == 超几何分布方差。 / analytic variance of Hypergeometric(33, 6, k)."""
    expected = 6 * (6 / 33) * (1 - 6 / 33) * (33 - 6) / (33 - 1)
    np.testing.assert_allclose(round_variance(6), expected)


def test_z_score_is_zero_at_baseline_and_scales_with_n() -> None:
    base = baseline_hits(6)
    np.testing.assert_allclose(z_score(base, 264), 0.0, atol=1e-12)
    # 同样的偏差，样本翻四倍，z 翻两倍 / same gap, 4x rounds -> 2x z.
    np.testing.assert_allclose(z_score(base + 0.05, 4 * 264) / z_score(base + 0.05, 264), 2.0)


def test_z_score_flags_noise_on_real_scale() -> None:
    """真实样本上最优策略的 z 必须落在噪声区间。 / the real-data lift must read as noise."""
    row = summarize([1, 1, 2, 1, 1, 1, 0, 1] * 33, top_k=6)
    assert abs(row["z_score"]) < 2


def test_strategy_round_counts(draws) -> None:
    cfg = BacktestConfig(top_k=6, lookback=19, horizons=tuple(range(1, 8)))
    expected_rounds = len(draws) - max(cfg.lookback, max(cfg.horizons))
    for runner in (run_topk_backtest, run_rank_factor_backtest, run_horizon_topk_backtest):
        result = runner(draws, cfg)
        assert result.n_rounds == expected_rounds
        assert sum(result.distribution.values()) == expected_rounds


def test_incremental_tracker_matches_batch(draws) -> None:
    """增量统计 == 一次性全量统计。 / incremental counting must equal a from-scratch pass."""
    cfg = BacktestConfig(top_k=6, horizons=(3, 7))
    matrix = weight_matrix(draws, cfg.hit, cfg.diffusive)
    tracker = RankFactorTracker(matrix=matrix, draws=draws, horizons=(3, 7), mode="expanding")
    target = 60
    tracker.update_to(target)

    for horizon in (3, 7):
        batch = np.zeros(33)
        for t in range(horizon, target):
            for rank in ranks_of(window_scores(matrix, t, horizon), draws[t].reds):
                batch[rank] += 1.0
        np.testing.assert_allclose(tracker.counts[horizon], batch)


def test_tracker_cold_start_is_deterministic() -> None:
    matrix = np.zeros((5, 33))
    tracker = RankFactorTracker(matrix=matrix, draws=make_synthetic_draws(5), horizons=(4,))
    assert tracker.rank_factors(4, 6) == (0, 1, 2, 3, 4, 5)


def test_full_mode_is_not_weaker_than_expanding(draws) -> None:
    """前视口径只能虚高，不可能变差。 / leakage can only inflate, never deflate."""
    cfg_kwargs = dict(top_k=6, lookback=19, horizons=tuple(range(1, 8)))
    honest = run_ensemble_backtest(draws, BacktestConfig(**cfg_kwargs, mode="expanding"))
    leaky = run_ensemble_backtest(draws, BacktestConfig(**cfg_kwargs, mode="full"))
    assert leaky.average_hits >= honest.average_hits


def test_run_dispatch_and_unknown_strategy(draws) -> None:
    cfg = BacktestConfig(top_k=6, lookback=19, horizons=(1, 2, 3))
    assert run("topk", draws, cfg).n_rounds > 0
    with pytest.raises(ValueError):
        run("magic", draws, cfg)


def test_config_validation() -> None:
    with pytest.raises(ValueError):
        BacktestConfig(top_k=0).validate()
    with pytest.raises(ValueError):
        BacktestConfig(lookback=0).validate()
    with pytest.raises(ValueError):
        BacktestConfig(mode="future").validate()


def test_predict_next_shape(draws) -> None:
    cfg = BacktestConfig(top_k=6, lookback=19, horizons=tuple(range(1, 8)))
    prediction = predict_next(draws, cfg)
    assert len(prediction.numbers) == 6
    assert len(set(prediction.numbers)) == 6
    assert prediction.numbers == tuple(sorted(prediction.numbers))
    assert all(1 <= n <= 33 for n in prediction.numbers)
    assert prediction.votes  # 每期至少有一个号码被投到票


def test_predict_next_needs_history() -> None:
    with pytest.raises(ValueError):
        predict_next(make_synthetic_draws(3), BacktestConfig(horizons=(1, 2, 5)))
