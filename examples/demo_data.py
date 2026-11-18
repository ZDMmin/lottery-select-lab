"""Shared demo data loader. / demo 共用的数据加载器。

中文：默认读仓库里那份真实开奖样本（283 期，2025-01-02 ~ 2026-11-17）。
如果文件被清理掉了，自动回退到固定种子的合成数据，保证 demo 永远能跑。
"""

from __future__ import annotations

from pathlib import Path

from lottery_select_lab import Draw, load_draws, make_synthetic_draws

SAMPLE_PATH = Path(__file__).resolve().parents[1] / "data" / "sample" / "ssq_sample.csv"


def load_demo_draws(fallback_n: int = 300, seed: int = 7) -> list[Draw]:
    """Real sample when available, synthetic otherwise. / 优先真实样本，缺失时用合成数据。"""
    if SAMPLE_PATH.is_file():
        return load_draws(SAMPLE_PATH)
    return make_synthetic_draws(fallback_n, seed=seed)
