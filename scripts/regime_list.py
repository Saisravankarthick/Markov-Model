"""Day-by-day regime list (Bull / Bear / Sideways) for one ticker and date range.

Uses Yahoo Finance closes. The main column uses Yahoo's ordinary (unadjusted)
close, as shown on the Yahoo website; the model column uses dividend-adjusted
closes, which is what the regime model itself uses. Also counts the
day-to-day switches inside the range and turns them into a transition table.

    uv run python scripts/regime_list.py --ticker VXUS --start 2026-09-01 --end 2026-10-31 --out report/VXUS_REGIMES.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys

import numpy as np
import pandas as pd

WINDOW, THRESHOLD = 20, 0.02
CODE = {"Bull": "B", "Bear": "E", "Sideways": "S"}
ORDER = ["Bear", "Sideways", "Bull"]


def regime(r: float) -> str:
    return "Bull" if r > THRESHOLD else "Bear" if r < -THRESHOLD else "Sideways"


def build(ticker: str, raw: pd.Series, adj: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> str:
    raw, adj = raw.dropna(), adj.dropna()
    r_raw = raw / raw.shift(WINDOW) - 1
    r_adj = adj / adj.shift(WINDOW) - 1
    days = raw.index[(raw.index >= start) & (raw.index <= end)]
    rows, labels = [], []
    for d in days:
        i = raw.index.get_loc(d)
        if i < WINDOW:
            continue
        reg, reg_m = regime(r_raw.loc[d]), regime(r_adj.loc[d])
        labels.append(reg)
        rows.append((d, raw.index[i - WINDOW], raw.iloc[i - WINDOW], raw.loc[d], r_raw.loc[d], reg, r_adj.loc[d], reg_m))

    counts = pd.DataFrame(0, index=ORDER, columns=ORDER)
    for a, b in zip(labels[:-1], labels[1:]):
        counts.loc[a, b] += 1
    tally = pd.Series(labels).value_counts()

    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out = [f"# {ticker}: daily regime, {days[0].date()} to {days[-1].date()}", "",
           f"Updated {now} · Yahoo Finance closes · 20-day return = close ÷ close 20 trading days earlier − 1 · "
           f"**B** = Bull (&gt; +2%), **S** = Sideways (−2% to +2%), **E** = Bear (&lt; −2%)", "",
           "**Summary:** " + ",  ".join(f"{CODE[k]} {k}: {int(tally.get(k, 0))} days" for k in ["Bull", "Sideways", "Bear"])
           + f"  (total {len(labels)} trading days)", "",
           "**Sequence:** `" + " ".join(CODE[x] for x in labels) + "`", "",
           "## Day by day", "",
           "| Date | Day | Close 20 trading days earlier | Close | 20-day return | State | Model view (dividend-adjusted) |",
           "|---|---|---|---|---|---|---|"]
    for d, bd, bp, p, r, reg, rm, regm in rows:
        flag = "" if regm == reg else " ⚠ differs"
        out.append(f"| {d.date()} | {d.strftime('%a')} | {bp:.2f} ({bd.date()}) | {p:.2f} | {r * 100:+.2f}% | **{CODE[reg]}** ({reg}) | "
                   f"{rm * 100:+.2f}% {CODE[regm]}{flag} |")
    out += ["", "## Transitions inside this period", "",
            f"Each pair of neighbouring days is one transition ({len(labels) - 1} pairs). Rows = today, columns = tomorrow.", "",
            "| Today \\ Tomorrow | E Bear | S Sideways | B Bull | Row total |", "|---|---|---|---|---|"]
    for a in ORDER:
        tot = int(counts.loc[a].sum())
        cells = []
        for b in ORDER:
            n = int(counts.loc[a, b])
            cells.append(f"{n} ({n / tot * 100:.0f}%)" if tot else "0 (–)")
        out.append(f"| **{CODE[a]} {a}** | " + " | ".join(cells) + f" | {tot} |")
    out += ["", "Two months is only about 40 pairs, so these percentages are rough. The long-run table in the main report uses about 10 years.", "",
            "_Historical, not forward-looking._", ""]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", default="VXUS")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import yfinance as yf

    start, end = pd.Timestamp(a.start), pd.Timestamp(a.end)
    h = yf.Ticker(a.ticker).history(start=(start - pd.Timedelta(days=60)).strftime("%Y-%m-%d"),
                                    end=(end + pd.Timedelta(days=1)).strftime("%Y-%m-%d"), auto_adjust=False)
    if h.empty:
        print("no data from Yahoo", file=sys.stderr)
        return 1
    h.index = pd.DatetimeIndex(h.index).tz_localize(None).normalize()
    md = build(a.ticker, h["Close"], h["Adj Close"], start, end)
    open(a.out, "w").write(md)
    print("regime list ok:", a.ticker, a.start, a.end)
    return 0


if __name__ == "__main__":
    sys.exit(main())
