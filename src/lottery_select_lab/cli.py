"""Command line interface. / 命令行入口。

中文：三条命令覆盖日常使用：

    python -m lottery_select_lab generate-data --n 200 --out data/sample/ssq_sample.csv
    python -m lottery_select_lab backtest --data data/sample/ssq_sample.csv --strategy ensemble
    python -m lottery_select_lab compare --data data/sample/ssq_sample.csv --charts

设计原则：CLI 只做「读参数 → 调库 → 落盘」，不含任何算法逻辑，
这样同一套能力既能在 Notebook 里被 import，也能在终端里被脚本调用。
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from .backtest import STRATEGIES, run
from .data import load_draws, make_synthetic_draws, save_draws
from .metrics import format_report, summarize
from .models import BacktestConfig, BacktestResult
from .report import export_distribution_csv, export_json, export_rounds_csv, write_summary_table
from .viz import plot_hit_distribution, plot_rank_hit_counts, plot_rolling_hits


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--hit", type=float, default=2.0, help="命中权重 / weight of a drawn number")
    parser.add_argument("--diffusive", type=float, default=1.0, help="邻居扩散权重 / neighbour weight")
    parser.add_argument("--top-k", type=int, default=6, help="每轮选几个号 / numbers picked per round")
    parser.add_argument("--lookback", type=int, default=19, help="回看期数 / look-back window")
    parser.add_argument(
        "--mode",
        choices=["expanding", "full"],
        default="expanding",
        help="因子挖掘口径 / expanding = leakage-free (default)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lottery_select_lab",
        description="Lottery-Select-Lab / SSQ-Number-Engine / Number-Picking-Lab",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate-data", help="生成可复现的样本数据 / create reproducible sample data")
    gen.add_argument("--n", type=int, default=200, help="期数 / number of issues")
    gen.add_argument("--seed", type=int, default=42, help="随机种子 / random seed")
    gen.add_argument("--out", default="data/sample/ssq_sample.csv", help="输出路径 / output path")

    bt = sub.add_parser("backtest", help="运行单个策略 / run one strategy")
    bt.add_argument("--data", required=True, help="数据文件 / data file (csv or txt)")
    bt.add_argument("--strategy", choices=sorted(STRATEGIES), default="ensemble")
    bt.add_argument("--out", default="outputs/backtest", help="输出目录 / output directory")
    bt.add_argument("--charts", action="store_true", help="同时生成图表 / also render charts")
    _add_common(bt)

    cmp_ = sub.add_parser("compare", help="横向对比全部策略 / compare all strategies")
    cmp_.add_argument("--data", required=True)
    cmp_.add_argument("--out", default="outputs/compare")
    cmp_.add_argument("--charts", action="store_true")
    _add_common(cmp_)

    return parser


def _config(args: argparse.Namespace) -> BacktestConfig:
    cfg = BacktestConfig(
        hit=args.hit,
        diffusive=args.diffusive,
        top_k=args.top_k,
        lookback=args.lookback,
        mode=args.mode,
    )
    cfg.validate()
    return cfg


def _dump(name: str, result: BacktestResult, out_dir: Path) -> None:
    """Write CSV + JSON artifacts for one run. / 落盘一次运行的全部产物。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    export_rounds_csv(result, out_dir / f"{name}_rounds.csv")
    export_distribution_csv(result, out_dir / f"{name}_distribution.csv")
    export_json(result, out_dir / f"{name}_summary.json")


def _charts(name: str, result: BacktestResult, out_dir: Path) -> None:
    """Render the standard chart set. / 生成标准图集。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    plot_hit_distribution(result, out_dir / f"{name}_hit_distribution.png")
    counts = (result.rank_factors or {}).get("counts") or {}
    for horizon, values in counts.items():
        plot_rank_hit_counts(
            np.asarray(values, dtype=float),
            out_dir / f"{name}_rank_counts_l{horizon}.png",
            subtitle=f"回看期数 lookback = {horizon}",
        )
        break


def cmd_generate_data(args: argparse.Namespace) -> int:
    draws = make_synthetic_draws(args.n, seed=args.seed)
    path = save_draws(draws, args.out)
    print(f"[ok] wrote {len(draws)} synthetic issues -> {path}")
    return 0


def cmd_backtest(args: argparse.Namespace) -> int:
    draws = load_draws(args.data)
    cfg = _config(args)
    result = run(args.strategy, draws, cfg)
    out_dir = Path(args.out)
    _dump(args.strategy, result, out_dir)
    print(format_report([summarize([r.hits for r in result.rounds], cfg.top_k)], [args.strategy]))
    if args.charts:
        _charts(args.strategy, result, out_dir)
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    draws = load_draws(args.data)
    cfg = _config(args)
    out_dir = Path(args.out)
    results = {}
    rows = []
    labels = []
    for name in ("topk", "rank", "horizon-topk", "ensemble"):
        result = run(name, draws, cfg)
        results[name] = result
        labels.append(name)
        rows.append(summarize([r.hits for r in result.rounds], cfg.top_k))
        _dump(name, result, out_dir)

    print(format_report(rows, labels))
    write_summary_table(rows, labels, out_dir / "summary.md")
    if args.charts:
        for name, result in results.items():
            _charts(name, result, out_dir)
        plot_rolling_hits(results, out_dir / "rolling_hits.png")
    print(f"[ok] artifacts -> {out_dir}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {
        "generate-data": cmd_generate_data,
        "backtest": cmd_backtest,
        "compare": cmd_compare,
    }
    return handlers[args.command](args)
