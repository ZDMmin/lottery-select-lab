# Contributing

Thanks for looking. This is a small research codebase; the bar for a PR is **"can a stranger
verify it?"**.

## Before you open a PR

```bash
pip install -r requirements.txt
python -m pytest -q          # 41 tests, ~3 s
python scripts/run_demo.py   # 4 demos, ~6 s
ruff check src tests
```

All three must pass. If you changed algorithm semantics, add or update a test that pins the new
behaviour — numbers in `docs/ALGORITHM.md` and the README tables must stay reproducible from
`python scripts/run_demo.py`.

## What is welcome

- **Bugs**, especially anything that reintroduces look-ahead bias.
- **New factors** (value-ranges, odd/even, co-occurrence graph features) as long as they enter
  through `ranking` / `weights` and are back-tested with `mode="expanding"`.
- **Docs**: clearer explanations of the math, translations, chart readability.
- **Performance**: faster window sums or vectorised trackers, with a test proving identical output.

## What is not

- Anything that claims to predict lottery outcomes or improves the odds of a ticket.
- Marketing-style language in docs or charts.
- Silent changes to the scoring rules (`hit` / `diffusive` placement, tie-breaking, edge handling)
  without a test that documents the change.

## Style

- Python 3.9+ syntax, type hints on public functions.
- Bilingual docstrings: English first, Chinese second (`中文：...`), so both audiences can read it.
- Keep modules single-purpose; if a file grows past ~400 lines, propose a split.

## Reporting results

If you add an experiment, include the exact command and seed so the number can be reproduced.
A result without a reproduction command is treated as a rumour.
