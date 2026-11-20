# v0.1.0 — Honest Baseline / 诚实基线

**A lottery selection engine that measures itself, finds nothing, and says so out loud.**
**一个会给自己做体检的选号引擎——结论是什么都没找到，并且如实写出来。**

---

## Highlights / 本次发布包含

**English**

- Six handwritten scripts (`test.py` … `test_5.py`) rebuilt as one typed package
  `lottery_select_lab` (10 modules: `models`, `data`, `weights`, `ranking`, `metrics`,
  `backtest`, `predict`, `viz`, `report`, `cli`).
- **Look-ahead bias is a first-class config flag** (`mode="expanding"` vs `mode="full"`),
  not a comment in the source. The same code path produces 1.12 vs 1.58 average hits per
  round — a **+41%** inflation that looks exactly like a working strategy.
- **Analytic significance test.** Because the predicted set is fixed before the draw, each
  round's hit count is `Hypergeometric(33, 6, 6)`, so `Var = k·p·(1−p)·(33−k)/32` and
  `z = (mean − baseline) / sqrt(Var/n)` need no bootstrap. Every strategy lands inside
  `|z| < 2`; the honest edge is noise.
- 283 real SSQ issues (2025-01-02 → 2026-11-17) ship as `data/sample/ssq_sample.csv`,
  plus `scripts/download_data.py` to refresh or extend it.
- 4 runnable demos, 44 pytest cases, GitHub Actions CI on Python 3.9 & 3.12, CLI with
  `generate-data` / `backtest` / `compare`, CSV/JSON/Markdown export, bilingual docstrings.

**中文**

- 6 份手写脚本（`test.py` … `test_5.py`）重构为一个带类型标注的包 `lottery_select_lab`
  （10 个模块：`models`、`data`、`weights`、`ranking`、`metrics`、`backtest`、`predict`、
  `viz`、`report`、`cli`）。
- **前视偏差是一个一等配置项**（`mode="expanding"` 与 `mode="full"`），而不是源码里的一句注释。
  同一段代码路径跑出 1.12 与 1.58 的每期平均命中数——虚增 **41%**，看起来和"有效策略"一模一样。
- **解析式显著性检验**：预测集合在开奖前固定，每轮命中数服从 `Hypergeometric(33, 6, 6)`，
  因此 `Var = k·p·(1−p)·(33−k)/32`、`z = (均值 − 基线) / sqrt(Var/n)`，无需 bootstrap。
  四个策略全部落在 `|z| < 2` 内：诚实口径下的那点"优势"就是噪声。
- 283 期真实开奖数据随仓库提供（`data/sample/ssq_sample.csv`，2025-01-02 ~ 2026-11-17），
  另附 `scripts/download_data.py` 用于更新或扩充样本。
- 4 个可直接运行的 demo、44 个 pytest 用例、Python 3.9 与 3.12 双版本 CI、
  `generate-data` / `backtest` / `compare` 三条 CLI 命令、CSV/JSON/Markdown 导出、中英双语 docstring。

## Results on the bundled sample / 内置样本上的结果

264 rounds, `top_k=6`, `lookback=19`, horizons 1..19. Baseline (blind pick) = 1.091.

| Strategy | Avg hits | vs baseline | z |
| --- | --- | --- | --- |
| `topk` | 1.133 | 1.04× | 0.78 |
| `rank-factor` | 1.042 | 0.95× | −0.92 |
| `horizon-topk` | 1.152 | 1.06× | 1.13 |
| `ensemble` | 1.125 | 1.03× | 0.64 |
| `ensemble`, `mode="full"` (leaked) | 1.583 | 1.45× | — |

## Install / 安装

```bash
pip install -e .
python scripts/run_demo.py                 # all four demos, < 6 s
python -m lottery_select_lab compare --data data/sample/ssq_sample.csv --charts
```

## Assets / 附件

- `lottery-select-lab.zip` — source archive, no git history / 纯源码包
- `lottery-select-lab-with-git.zip` — full repository including commit history / 含提交历史的完整仓库

## Known limits / 已知限制

The sample covers 283 issues, so the confidence band is wide: a real effect smaller than
about ±0.11 hits/round would be indistinguishable from noise here. This is a statistics and
software-engineering exercise — it does not predict lottery results and must not be used as
gambling advice.

样本只有 283 期，置信区间较宽：小于约 ±0.11 命中/期 的真实效应在本样本中无法与噪声区分。
本项目是统计与工程实践，不预测开奖结果，也不能作为购彩建议。

---

**Full detail:** [README.md](README.md) · [README_ZH.md](README_ZH.md) · [docs/ALGORITHM.md](ALGORITHM.md) · [docs/REFACTOR_NOTES.md](REFACTOR_NOTES.md) · [CONTRIBUTING.md](../CONTRIBUTING.md)
