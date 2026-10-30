# Markov Regime Model

Markov regime detection for any asset. For a price series it:

- Labels every day Bull / Bear / Sideways via a rolling-return rule (default 20-day, ±5%)
- Builds a 3×3 transition matrix from the asset's history (maximum-likelihood)
- Forecasts n steps ahead by raising the matrix to powers (Chapman-Kolmogorov)
- Computes the long-run stationary distribution (baseline regime mix)
- Emits a signed signal: `bull_prob − bear_prob` → direction + conviction
- Runs a walk-forward backtest (no lookahead) → reports Sharpe + max drawdown
- Optionally fits a Hidden Markov Model via `hmmlearn`

Input is either a ticker (`--ticker BTC-USD`, fetched via `yfinance`) or your
own CSV (`--csv my_prices.csv`, a date column + a close column).

Backtests are historical, not forward-looking, and exclude trading costs.

---

## Run it on GitHub (no install)

1. Open the repo's **Actions** tab.
2. Pick **Markov regime** in the left sidebar → **Run workflow**.
3. Enter a ticker (e.g. `SPY`, `AAPL`, `BTC-USD`, `^NSEI`) or leave it blank
   and give the path of a CSV committed to the repo. Adjust window, threshold,
   years and HMM if you want → **Run workflow**.
4. Open the finished run. The results (current regime, signal, transition
   matrix, long-run mix, backtest, HMM) are on the run's **Summary** page, and
   the raw JSON is attached under **Artifacts** as `regime-result`.

The workflow is [`.github/workflows/regime.yml`](./.github/workflows/regime.yml).
Yahoo Finance occasionally rate-limits GitHub's runners; if a ticker run fails
with "empty data", re-run it a few minutes later.

## Run it locally

Requires [`uv`](https://docs.astral.sh/uv/getting-started/installation/);
dependencies install automatically on first run.

```bash
uv run scripts/markov_regime.py --ticker SPY            # pretty terminal output
uv run scripts/markov_regime.py --ticker SPY --json     # machine-readable
uv run scripts/markov_regime.py --csv my_prices.csv     # your own data
```

Options: `--window 20`, `--threshold 0.05`, `--years 10`, `--min-train 252`,
`--no-hmm`.

## Use it as a Claude Code plugin

On your own machine, in Claude Code:

```
/plugin marketplace add Saisravankarthick/Markov-Model
/plugin install markov-hedge-fund-method@markov-hedge-fund-method
```

Then invoke `/markov-hedge-fund-method:regime`, or ask in plain English
(*"detect the regime on BTC-USD"*). See
[`skills/regime/SKILL.md`](./skills/regime/SKILL.md) for the JSON contract and
composition patterns.

## TradingView indicator

[`pine-script/markov-hedge-fund-method.pine`](./pine-script/markov-hedge-fund-method.pine)
is a Pine Script v5 indicator: regime ribbon, live 3×3 transition matrix,
stationary-distribution table and current-regime banner.
TradingView → Pine Editor → paste → Save → Add to Chart.

It labels with log returns, while the Python script uses simple returns, so
labels near the threshold can differ slightly between the two.

## Other files

- [`markov-hedge-fund-method.md`](./markov-hedge-fund-method.md) — the
  original one-shot onboarding prompt that builds an earlier version of the
  skill into `~/.claude/skills/` (defaults to a ±2% threshold).
- [`scripts/summarize.py`](./scripts/summarize.py) — renders the `--json`
  output as Markdown (used by the workflow).

## Credit and license

- Framework: Roan ([@RohOnChain](https://x.com/RohOnChain)).
- Plugin, installer and Pine Script: Lewis Jackson —
  [jackson-video-resources/markov-hedge-fund-method](https://github.com/jackson-video-resources/markov-hedge-fund-method).

Upstream is MIT-licensed; see the upstream repository for the license text.
