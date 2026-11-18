"""Demo 04 — recommendation for the next issue, with full transparency.

中文：给下一期推荐 6 个号码，并把「票数 / 得分 / 各窗口专家的意见」全部摊开。
这正是手稿 ``start_prediction()`` 想做的事。

Run / 运行::

    PYTHONPATH=src python examples/04_predict_next.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from demo_data import load_demo_draws

from lottery_select_lab import BacktestConfig
from lottery_select_lab.predict import predict_next
from lottery_select_lab.viz import plot_score_landscape

OUT = Path(__file__).parent / "output"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    draws = load_demo_draws()
    cfg = BacktestConfig(hit=2.0, diffusive=1.0, top_k=6, lookback=19, mode="expanding")

    prediction = predict_next(draws, cfg)
    print(prediction.explain())

    print("\n各窗口专家意见 / per-horizon experts:")
    for horizon, picked in prediction.experts.items():
        print(f"  lookback={horizon:>2}  ->  {' '.join(f'{n:02d}' for n in picked)}")

    payload = {
        "numbers": list(prediction.numbers),
        "votes": prediction.votes,
        "scores": {str(k): round(v, 4) for k, v in prediction.scores.items()},
        "experts": {str(k): list(v) for k, v in prediction.experts.items()},
        "history_size": prediction.history_size,
        "warnings": prediction.warnings,
        "disclaimer": "This is a combination generator, not a prediction of a random event.",
    }
    (OUT / "04_recommendation.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    scores = np.array([prediction.scores[n] for n in range(1, 34)])
    path = plot_score_landscape(
        scores,
        prediction.numbers,
        OUT / "04_score_landscape.png",
        title="One issue's score landscape (highlighted = selected)",
        subtitle=f"多窗口共识 · 历史 {prediction.history_size} 期",
    )
    print(f"\n[ok] artifacts -> {OUT / '04_recommendation.json'}, {path}")


if __name__ == "__main__":
    main()
