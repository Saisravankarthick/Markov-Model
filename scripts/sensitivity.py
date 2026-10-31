"""Window / threshold sensitivity test for the Markov regime model.

For each ticker, re-runs the skill's regime model over a grid of rolling windows
and thresholds and reports the long-run regime mix, the walk-forward strategy's
Sharpe (before and after trading costs), max drawdown and turnover, against
buy-and-hold. It then picks the best setting on the first half of the period
and checks it on the second half (out-of-sample).

    uv run python scripts/sensitivity.py --tickers "SPY, TLT" --out report/SENSITIVITY.md

The walk-forward loop is the incremental form of
markov_hedge_fund_method.regime.walk_forward_backtest (same labels, matrices and
signal); main() checks it against the package's Sharpe at the default setting.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from markov_hedge_fund_method.regime import (  # noqa: E402
    build_transition_matrix,
    label_regimes,
    stationary_distribution,
    walk_forward_backtest,
)

WINDOWS = (10, 20, 60)
THRESHOLDS = (0.01, 0.02, 0.05)
DEFAULT = (20, 0.02)
COST = 0.0005  # 5 basis points per unit of position change
MIN_TRAIN = 252


def walk_forward(close: pd.Series, labels: pd.Series, min_train: int = MIN_TRAIN):
    """Daily strategy returns, positions and buy-and-hold returns (no lookahead)."""
    rets = close.pct_change().dropna()
    idx = labels.index.intersection(rets.index)
    lab = labels.loc[idx].to_numpy(dtype=int)
    r = rets.loc[idx].to_numpy(dtype=float)
    if len(lab) < min_train + 30:
        return None
    counts = np.zeros((3, 3))
    for i in range(min_train - 1):
        counts[lab[i], lab[i + 1]] += 1
    out, pos = [], []
    for t in range(min_train, len(lab) - 1):
        rs = counts.sum(axis=1, keepdims=True)
        P = counts / np.where(rs == 0, 1.0, rs)
        p = float(np.sign(P[lab[t], 2] - P[lab[t], 0]))
        out.append(p * r[t + 1])
        pos.append(p)
        counts[lab[t - 1], lab[t]] += 1
    dates = idx[min_train + 1:len(lab)]
    df = pd.DataFrame({"ret": out, "pos": pos, "bh": r[min_train + 1:len(lab)]}, index=dates)
    df["net"] = df["ret"] - COST * df["pos"].diff().abs().fillna(df["pos"].abs())
    return df


def sharpe(x) -> float:
    x = np.asarray(x, dtype=float)
    sd = x.std(ddof=1) if len(x) > 1 else 0.0
    return float(x.mean() / sd * np.sqrt(252)) if sd > 0 else float("nan")


def max_dd(x) -> float:
    eq = np.cumprod(1 + np.asarray(x, dtype=float))
    peak = np.maximum.accumulate(eq)
    return float(((eq - peak) / peak).min()) if len(eq) else float("nan")


def analyse(close: pd.Series) -> dict:
    rows, series = [], {}
    for w in WINDOWS:
        for th in THRESHOLDS:
            labels = label_regimes(close, window=w, threshold=th)
            pi = stationary_distribution(build_transition_matrix(labels))
            df = walk_forward(close, labels)
            if df is None:
                continue
            series[(w, th)] = df
            years = len(df) / 252
            rows.append({"window": w, "threshold": th, "bear": pi[0], "side": pi[1], "bull": pi[2],
                         "sharpe": sharpe(df["ret"]), "sharpe_net": sharpe(df["net"]),
                         "maxdd": max_dd(df["ret"]), "changes": df["pos"].diff().abs().gt(0).sum() / years})
    if not series:
        return {"rows": [], "oos": None, "bh": None}
    any_df = series[next(iter(series))]
    bh = {"sharpe": sharpe(any_df["bh"]), "maxdd": max_dd(any_df["bh"])}

    # out-of-sample: choose on first half, test on second half
    common = sorted(set.intersection(*[set(d.index) for d in series.values()]))
    mid = common[len(common) // 2]
    first = {k: sharpe(d.loc[d.index < mid, "ret"]) for k, d in series.items()}
    best = max(first, key=lambda k: -np.inf if np.isnan(first[k]) else first[k])
    second = lambda k: sharpe(series[k].loc[series[k].index >= mid, "ret"])  # noqa: E731
    second_net = lambda k: sharpe(series[k].loc[series[k].index >= mid, "net"])  # noqa: E731
    oos = {"split": str(pd.Timestamp(mid).date()), "best": best, "best_first": first[best],
           "best_second": second(best), "best_second_net": second_net(best),
           "default_second": second(DEFAULT) if DEFAULT in series else float("nan"),
           "bh_second": sharpe(any_df.loc[any_df.index >= mid, "bh"])}
    return {"rows": rows, "oos": oos, "bh": bh}


def fmt(x, pct=False, d=2):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "–"
    return f"{x * 100:.0f}%" if pct else f"{x:.{d}f}"


def render(results: dict, years: int) -> str:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out = ["# Window and threshold sensitivity test", "",
           f"Updated {now} · {years} years of daily data · walk-forward (no lookahead) · costs: {COST * 1e4:.0f} basis points per unit of position change",
           "",
           "Each row re-runs the regime model with a different rolling window and threshold. "
           "**Sharpe (net)** subtracts trading costs. **Changes/yr** is how often the position flips. "
           "The **out-of-sample** line picks the best setting on the first half of the period and then shows how that same setting did on the second half.",
           ""]
    for t, res in results.items():
        out += [f"## {t}", ""]
        if not res["rows"]:
            out += ["Not enough data.", ""]
            continue
        out += ["| Window | Threshold | Bear | Sideways | Bull | Sharpe | Sharpe (net) | Max DD | Changes/yr |",
                "|---|---|---|---|---|---|---|---|---|"]
        for r in res["rows"]:
            mark = " **(default)**" if (r["window"], r["threshold"]) == DEFAULT else ""
            out.append(f"| {r['window']}d{mark} | ±{r['threshold'] * 100:g}% | {fmt(r['bear'], 1)} | {fmt(r['side'], 1)} | {fmt(r['bull'], 1)} | "
                       f"{fmt(r['sharpe'])} | {fmt(r['sharpe_net'])} | {fmt(r['maxdd'], 1)} | {r['changes']:.0f} |")
        out.append(f"| **Buy & hold** | | | | | **{fmt(res['bh']['sharpe'])}** | | **{fmt(res['bh']['maxdd'], 1)}** | 0 |")
        o = res["oos"]
        w, th = o["best"]
        out += ["", f"**Out-of-sample** (split {o['split']}): best on the first half was {w}d / ±{th * 100:g}% (Sharpe {fmt(o['best_first'])}). "
                    f"On the second half it scored **{fmt(o['best_second'])}** ({fmt(o['best_second_net'])} after costs), "
                    f"vs {fmt(o['default_second'])} for the 20d / ±2% default and **{fmt(o['bh_second'])}** for buy & hold.", ""]
    out += ["_Backtests are historical, not forward-looking._", ""]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", required=True)
    ap.add_argument("--years", type=int, default=10)
    ap.add_argument("--out", default="report/SENSITIVITY.md")
    a = ap.parse_args()
    from markov_hedge_fund_method.run import _fetch_with_retry

    results = {}
    for t in [x for x in re.split(r"[,\s]+", a.tickers) if x]:
        try:
            df = _fetch_with_retry(t, a.years)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            close = df["Close"].dropna()
            res = analyse(close)
            ref = walk_forward_backtest(close, label_regimes(close, *DEFAULT))["sharpe"]
            mine = next((r["sharpe"] for r in res["rows"] if (r["window"], r["threshold"]) == DEFAULT), float("nan"))
            if np.isfinite(ref) and abs(ref - mine) > 1e-9:
                print(f"  ! {t}: sensitivity Sharpe {mine} != package {ref}", file=sys.stderr)
            results[t] = res
            print(f"sensitivity ok: {t}")
        except Exception as exc:  # noqa: BLE001
            print(f"sensitivity FAILED: {t}: {exc}", file=sys.stderr)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(render(results, a.years))
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
