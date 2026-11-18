"""Demo 03 — the look-ahead bias experiment (why ``test_3.py`` over-reported).

中文：手稿 test_3 / test_4 / test_5 在挖掘「优秀位次」时用了全样本，
也就是让模型看到了它将要预测的那几期。本 demo 把同一套代码跑两遍，
只切换一个开关，量化「作弊」能虚增多少命中率。

这个实验的价值：它是整个仓库方法学的门面——任何人在自己的回测里都可能犯同样的错。

Run / 运行::

    PYTHONPATH=src python examples/03_leakage_demo.py
"""

from __future__ import annotations

from pathlib import Path

from demo_data import load_demo_draws

from lottery_select_lab import BacktestConfig, run, summarize
from lottery_select_lab.viz import plot_strategy_comparison

OUT = Path(__file__).parent / "output"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    draws = load_demo_draws()
    base = dict(hit=2.0, diffusive=1.0, top_k=6, lookback=19)

    honest = run("ensemble", draws, BacktestConfig(**base, mode="expanding"))
    leaky = run("ensemble", draws, BacktestConfig(**base, mode="full"))

    honest_row = summarize([r.hits for r in honest.rounds], 6)
    leaky_row = summarize([r.hits for r in leaky.rounds], 6)

    print(f"expanding (leakage-free) : avg={honest_row['average_hits']:.3f}  lift={honest_row['lift']:.2f}x")
    print(f"full sample (leaky)      : avg={leaky_row['average_hits']:.3f}  lift={leaky_row['lift']:.2f}x")
    print(f"inflation                : {leaky_row['average_hits'] / honest_row['average_hits']:.2f}x "
          "of the honest result")

    # 同一批数据上，池子若真是随机的，任何策略都不该显著超过基线；
    # 一旦「变强」，先怀疑口径而不是庆祝。/ a sudden edge is a bug until proven otherwise.
    plot_strategy_comparison(
        ["expanding（无前视）", "full sample（前视，手稿口径）"],
        [honest_row["average_hits"], leaky_row["average_hits"]],
        honest_row["baseline_hits"],
        OUT / "03_leakage_bias.png",
        title="Look-ahead bias: same code, one switch, two very different stories",
    )
    print(f"[ok] chart -> {OUT / '03_leakage_bias.png'}")


if __name__ == "__main__":
    main()
