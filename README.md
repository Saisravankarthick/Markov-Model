# Markov regime model

**[→ Open the latest report](report/REPORT.md)** (table and charts for every ticker)

## Update the report

1. Go to the **Actions** tab → **Run Markov skill** → **Run workflow**.
2. Enter tickers, comma separated (e.g. `SPY, AAPL, BTC-USD`) and click **Run workflow**.
3. In about a minute per ticker, the run commits a fresh `report/` folder to this repo.
   Open [`report/REPORT.md`](report/REPORT.md) to see the table and charts.

## What's here

| Path | What it is |
|---|---|
| `markov_hedge_fund_method/` | The model: regime labels, transition matrix, stationary mix, walk-forward backtest, optional HMM |
| `scripts/charts.py`, `scripts/report.py` | Draw the charts and build the report page |
| `.github/workflows/run.yml` | The workflow behind **Run workflow** |
| `pine-script/markov-hedge-fund-method.pine` | Optional TradingView indicator (paste into Pine Editor) |

Framework: Roan ([@RohOnChain](https://x.com/RohOnChain)). Skill: Lewis Jackson.
Backtests are historical, not forward-looking, and exclude trading costs.
