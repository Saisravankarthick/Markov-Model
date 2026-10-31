"""Compare hand-recorded closing prices with Yahoo's, then compute 20-day regimes.

Readings within ±TOL of Yahoo's unadjusted close are accepted and used as-is
(the reader's own numbers). Larger differences are flagged and Yahoo's price is
used instead. Each day's 20-day return and regime is then computed from that
series, alongside the model's own view (dividend-adjusted closes).

    uv run python scripts/vxus_check.py --ticker VXUS --readings data/vxus_readings_oct2026.csv --out report/VXUS_CHECK.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from markov_hedge_fund_method.regime import STATES, build_transition_matrix, label_regimes  # noqa: E402

TOL = 0.10
WINDOW, THRESHOLD = 20, 0.02


def regime(r: float) -> str:
    if r is None or np.isnan(r):
        return "–"
    return "Bull" if r > THRESHOLD else "Bear" if r < -THRESHOLD else "Sideways"


def build(ticker: str, readings: pd.Series, raw: pd.Series, adj: pd.Series, divs: pd.Series) -> tuple[str, dict]:
    raw, adj = raw.dropna(), adj.dropna()
    # 1. compare readings with Yahoo
    rows, used = [], raw.copy()
    for d, mine in readings.items():
        y = raw.get(d, np.nan)
        if np.isnan(y):
            status, val = "no Yahoo price — yours used", mine
        elif abs(mine - y) <= TOL + 1e-9:
            status, val = "match (±0.10) — yours used", mine
        else:
            status, val = "**differs — Yahoo's used**", y
        rows.append((d, mine, y, mine - y if not np.isnan(y) else np.nan, status))
        used.loc[d] = val
    used = used.sort_index()

    # 2. 20-day return and regime for each reading date
    cal = used.index
    reg_rows = []
    for d in readings.index:
        i = cal.get_loc(d)
        if i < WINDOW:
            reg_rows.append((d, np.nan, None, np.nan, np.nan, "–", "–"))
            continue
        base_d = cal[i - WINDOW]
        r_mine = used.iloc[i] / used.iloc[i - WINDOW] - 1
        r_model = adj.get(d, np.nan) / adj.get(base_d, np.nan) - 1 if d in adj.index and base_d in adj.index else np.nan
        reg_rows.append((d, used.iloc[i - WINDOW], base_d, used.iloc[i], r_mine, regime(r_mine), r_model))

    # 3. long-run table (10y, adjusted, as the model does) and tomorrow's odds
    labels = label_regimes(adj, window=WINDOW, threshold=THRESHOLD)
    P = build_transition_matrix(labels)
    last_d, last_reg = readings.index[-1], reg_rows[-1][5]
    row = P[STATES.index(last_reg)] if last_reg in STATES else None

    # 4. peak over two years
    two = raw[raw.index >= raw.index[-1] - pd.DateOffset(years=2)]
    peak_d, peak = two.idxmax(), two.max()
    dd_from_peak = readings.iloc[-1] / peak - 1

    recent_divs = divs[(divs > 0) & (divs.index >= cal[max(0, cal.get_loc(readings.index[0]) - WINDOW)])]

    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    n_match = sum(1 for r in rows if r[4].startswith("match"))
    n_diff = sum(1 for r in rows if "differs" in r[4])
    out = [f"# {ticker}: your readings vs Yahoo, and the 20-day regime", "",
           f"Updated {now} · tolerance ±{TOL:.2f} · window {WINDOW} trading days · threshold ±{THRESHOLD * 100:g}%", "",
           f"**{n_match} of {len(rows)}** readings match Yahoo's close within ±{TOL:.2f} (your numbers are used); "
           f"**{n_diff}** differ by more and use Yahoo's price.", "",
           "## 1. Price check", "",
           "| Date | Your reading | Yahoo close | Difference | Result |", "|---|---|---|---|---|"]
    for d, mine, y, diff, status in rows:
        out.append(f"| {d.date()} | {mine:.2f} | {'–' if np.isnan(y) else f'{y:.2f}'} | {'–' if np.isnan(diff) else f'{diff:+.2f}'} | {status} |")
    out += ["", "## 2. 20-day return and regime, day by day", "",
            "Return = price that day ÷ price 20 trading days earlier − 1, using your readings (and Yahoo's unadjusted September closes for the start of the window). "
            "*Model view* uses dividend-adjusted prices, which is what the regime model itself uses.", "",
            "| Date | Price 20 days earlier (date) | Price | 20-day return | Regime | Model view |", "|---|---|---|---|---|---|"]
    for d, base_p, base_d, p, r, reg, r_model in reg_rows:
        if base_d is None:
            out.append(f"| {d.date()} | – | – | – | – | – |")
            continue
        model = f"{r_model * 100:+.2f}% ({regime(r_model)})" if not np.isnan(r_model) else "–"
        flag = "" if regime(r_model) == reg or np.isnan(r_model) else " ⚠"
        out.append(f"| {d.date()} | {base_p:.2f} ({base_d.date()}) | {p:.2f} | **{r * 100:+.2f}%** | **{reg}** | {model}{flag} |")
    out += ["", "## 3. What the model says for the next day", ""]
    if row is not None:
        sig = row[2] - row[0]
        pos = "long (+1)" if sig > 0 else "short (−1)" if sig < 0 else "flat (0)"
        out += [f"On {last_d.date()} the regime is **{last_reg}**. Using {ticker}'s own transition table (about 10 years, adjusted prices), the next day's odds are:", "",
                "| Bear | Sideways | Bull | Signal = P(Bull) − P(Bear) | Position |", "|---|---|---|---|---|",
                f"| {row[0] * 100:.1f}% | {row[1] * 100:.1f}% | {row[2] * 100:.1f}% | {sig * 100:+.1f}% | {pos} |", ""]
    out += ["## 4. Peak and dividends", "",
            f"Highest close in the last two years: **{peak:.2f}** on {peak_d.date()} (your note: about 89.00). "
            f"Your last reading ({readings.iloc[-1]:.2f}) is **{dd_from_peak * 100:.1f}%** below that peak.", ""]
    if len(recent_divs):
        out.append("Dividends paid inside these 20-day windows (they lower the unadjusted price on the ex-date, so the unadjusted return can look slightly worse than the model's adjusted one): "
                   + ", ".join(f"{d.date()} ${v:.4f}" for d, v in recent_divs.items()) + ".")
    else:
        out.append("No dividends were paid inside these 20-day windows, so your readings and the adjusted prices tell the same story.")
    out += ["", "_Backtests and regimes are historical, not forward-looking._", ""]
    stats = {"match": n_match, "differ": n_diff, "last_regime": last_reg, "peak": float(peak), "peak_date": str(peak_d.date())}
    return "\n".join(out), stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", default="VXUS")
    ap.add_argument("--readings", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import yfinance as yf

    r = pd.read_csv(a.readings, parse_dates=["date"]).set_index("date")["close"].sort_index()
    end = (r.index[-1] + pd.Timedelta(days=3)).strftime("%Y-%m-%d")
    start = (r.index[-1] - pd.DateOffset(years=10)).strftime("%Y-%m-%d")
    h = yf.Ticker(a.ticker).history(start=start, end=end, auto_adjust=False, actions=True)
    if h.empty:
        print("no data from Yahoo", file=sys.stderr)
        return 1
    h.index = pd.DatetimeIndex(h.index).tz_localize(None).normalize()
    md, stats = build(a.ticker, r, h["Close"], h["Adj Close"], h.get("Dividends", pd.Series(dtype=float)))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(md)
    print("vxus check ok:", stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
