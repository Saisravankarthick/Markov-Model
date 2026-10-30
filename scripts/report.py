"""Build report/REPORT.md (table + embedded charts) from report/stats.json.

    python scripts/report.py report/stats.json report/REPORT.md

GitHub renders the Markdown, tables and the relative PNG links directly, so the
page can be read in the repo with no download. Standard library only.
"""

from __future__ import annotations

import datetime as dt
import json
import sys


def pct(x, digits=1):
    return "–" if x is None else f"{x * 100:.{digits}f}%"


def num(x):
    return "–" if x is None else f"{x:.2f}"


def build(stats: dict) -> str:
    p = stats["params"]
    rows = stats["tickers"]
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out = [
        "# Markov regime report",
        "",
        f"Updated {now} · {p['years']} years of daily data · {p['window']}-day window · "
        f"±{p['threshold'] * 100:g}% threshold",
        "",
        "Each day is labelled **Bull**, **Bear** or **Sideways** from the trailing return. "
        "*Long-run mix* is the share of time the model expects in each regime. "
        "*Stays* is the chance a regime continues the next day. *Strategy* goes long in "
        "Bull-leaning states and short in Bear-leaning ones, re-fitted every day with no "
        "lookahead; *B&H* is simply holding the asset over the same days. "
        "Backtests are historical, not forward-looking, and exclude trading costs.",
        "",
        "![Long-run regime mix](charts/_comparison_long_run_mix.png)",
        "",
        "## Table",
        "",
        "| Ticker | Now | Bear | Sideways | Bull | Bear stays | Bull stays | Sharpe: strategy | Sharpe: B&H | Max DD: strategy | Max DD: B&H | Data from |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        out.append(
            f"| [{r['ticker']}](#{r['ticker'].lower().replace('^', '')}) | {r['current']} | "
            f"{pct(r['bear'])} | {pct(r['side'])} | {pct(r['bull'])} | "
            f"{pct(r['bear_stay'])} | {pct(r['bull_stay'])} | "
            f"{num(r['sharpe'])} | {num(r['bh_sharpe'])} | "
            f"{pct(r['maxdd'], 0)} | {pct(r['bh_maxdd'], 0)} | {r['start']} |"
        )
    if stats["failed"]:
        out += ["", "Could not be fetched: " + ", ".join(stats["failed"])]
    out += ["", "## Charts", ""]
    for r in rows:
        t = r["ticker"]
        safe = "".join(c if c.isalnum() or c in "_.-" else "_" for c in t)
        out += [f"### {t}", "", f"![{t}](charts/{safe}.png)", ""]
    return "\n".join(out)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: report.py STATS_JSON OUT_MD", file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8") as f:
        stats = json.load(f)
    with open(argv[2], "w", encoding="utf-8") as f:
        f.write(build(stats))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
