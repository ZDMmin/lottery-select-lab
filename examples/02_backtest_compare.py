"""Demo 02 — head-to-head back-test of all strategies.

中文：一次跑完四种策略并给出对比图。这是「别人 clone 下来第一件事」应该看到的 demo：
一条命令，全部产物落到 ``examples/output/``。

Run / 运行::

    PYTHONPATH=src python examples/02_backtest_compare.py
"""

from __future__ import annotations

from pathlib import Path

from demo_data import load_demo_draws

from lottery_select_lab import BacktestConfig, run, summarize
from lottery_select_lab.metrics import format_report, lift_vs_baseline
from lottery_select_lab.report import export_rounds_csv, write_summary_table
from lottery_select_lab.viz import plot_hit_distribution, plot_rolling_hits, plot_strategy_comparison

OUT = Path(__file__).parent / "output"
OUT.mkdir(parents=True, exist_ok=True)

STRATEGY_LABELS = {
    "topk": "A. top-k（直接取前 6）",
    "rank": "B. rank-factor（位次挖掘）",
    "horizon-topk": "C. horizon-top-k（多窗取前 6）",
    "ensemble": "D. ensemble（多窗位次投票）",
}


def main() -> None:
    draws = load_demo_draws()
    cfg = BacktestConfig(hit=2.0, diffusive=1.0, top_k=6, lookback=19, mode="expanding")

    results = {}
    labels = []
    rows = []
    rounds = 0
    for key, label in STRATEGY_LABELS.items():
        result = run(key, draws, cfg)
        results[label] = result
        labels.append(label)
        rows.append(summarize([r.hits for r in result.rounds], cfg.top_k))
        rounds = result.n_rounds
        export_rounds_csv(result, OUT / f"02_{key}_rounds.csv")

    print(format_report(rows, labels, title=f"strategy comparison ({len(draws)} issues, {rounds} rounds)"))
    print(f"\nbaseline (blind pick) = {rows[0]['baseline_hits']:.3f} hits/round")
    for label, row in zip(labels, rows):
        print(f"  {label:<32} lift = {lift_vs_baseline(row['average_hits'], cfg.top_k):.2f}x")

    plot_strategy_comparison(
        labels,
        [r["average_hits"] for r in rows],
        rows[0]["baseline_hits"],
        OUT / "02_strategy_comparison.png",
        title=f"Strategy comparison — average hits per round ({rounds} rounds)",
    )
    plot_rolling_hits(results, OUT / "02_rolling_hits.png")
    plot_hit_distribution(results[labels[1]], OUT / "02_rank_hit_distribution.png")
    write_summary_table(rows, labels, OUT / "02_summary.md", title="Demo 02 — strategy comparison")
    print(f"\n[ok] artifacts -> {OUT}")


if __name__ == "__main__":
    main()
