"""Draw charts for the Markov regime model, using the skill's own functions.

For every ticker it saves one PNG with three panels:
  1. price, shaded by regime (green = Bull, rose = Bear, grey = Sideways)
  2. walk-forward strategy equity curve vs buy-and-hold
  3. the 3x3 transition-matrix heatmap
and, across all tickers, one stacked bar chart of the long-run regime mix.

    uv run --with matplotlib python scripts/charts.py \
        --tickers "SPY, AAPL" --years 10 --window 20 --threshold 0.02 --out charts

The walk-forward loop below repeats the one in
markov_hedge_fund_method.regime.walk_forward_backtest (same labels, same
matrices, same signal) but keeps the daily returns so they can be plotted. It
checks its Sharpe against the package's own number.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from markov_hedge_fund_method.regime import (  # noqa: E402
    STATES,
    build_transition_matrix,
    label_regimes,
    signal_from_matrix,
    stationary_distribution,
    walk_forward_backtest,
)

COLORS = {0: "#C57F86", 1: "#A4ABB7", 2: "#84BBA1"}  # Bear, Sideways, Bull
MIN_TRAIN = 252


def strategy_series(close: pd.Series, labels: pd.Series, min_train: int = MIN_TRAIN):
    """Daily strategy and buy-and-hold returns, aligned on the same dates."""
    rets = close.pct_change().dropna()
    idx = labels.index.intersection(rets.index)
    labels, rets = labels.loc[idx], rets.loc[idx]
    if len(labels) < min_train + 30:
        return None, None
    strat, dates = [], []
    for t in range(min_train, len(labels) - 1):
        P_t = build_transition_matrix(labels.iloc[:t])
        position = float(np.sign(signal_from_matrix(P_t, int(labels.iloc[t]))))
        strat.append(position * float(rets.iloc[t + 1]))
        dates.append(rets.index[t + 1])
    strat = pd.Series(strat, index=dates)
    return strat, rets.loc[strat.index]


def sharpe(r: pd.Series) -> float:
    sd = r.std(ddof=1)
    return float(r.mean() / sd * np.sqrt(252)) if sd and np.isfinite(sd) else float("nan")


def max_drawdown(r: pd.Series) -> float:
    eq = (1 + r).cumprod()
    return float(((eq - eq.cummax()) / eq.cummax()).min())


def ticker_figure(name, close, window, threshold, out_dir: Path) -> dict:
    labels = label_regimes(close, window=window, threshold=threshold)
    P = build_transition_matrix(labels)
    pi = stationary_distribution(P)
    strat, bh = strategy_series(close, labels)

    fig = plt.figure(figsize=(13, 9), constrained_layout=True)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 1])

    # 1. price shaded by regime
    ax = fig.add_subplot(gs[0, :])
    ax.plot(close.index, close.values, color="#222", lw=1.1)
    ax.set_yscale("log")
    for k in (0, 1, 2):
        ax.fill_between(
            labels.index, 0, 1, where=(labels.values == k),
            transform=ax.get_xaxis_transform(), color=COLORS[k], alpha=0.35, lw=0,
            label=STATES[k],
        )
    current = STATES[int(labels.iloc[-1])]
    ax.set_title(f"{name} — price by regime (window {window}d, ±{threshold * 100:g}%) · now: {current}")
    ax.legend(loc="upper left", ncol=3, frameon=False)
    ax.set_ylabel("Price (log scale)")
    ax.grid(alpha=0.25)

    # 2. equity curves
    ax2 = fig.add_subplot(gs[1, 0])
    stats = {"ticker": name, "rows": len(close), "start": str(close.index[0].date()),
             "bear": pi[0], "side": pi[1], "bull": pi[2], "sharpe": float("nan"), "maxdd": float("nan")}
    if strat is not None:
        ax2.plot((1 + strat).cumprod(), color="#2E6F57", lw=1.3,
                 label=f"Strategy (Sharpe {sharpe(strat):.2f}, maxDD {max_drawdown(strat) * 100:.0f}%)")
        ax2.plot((1 + bh).cumprod(), color="#888", lw=1.1,
                 label=f"Buy & hold (Sharpe {sharpe(bh):.2f}, maxDD {max_drawdown(bh) * 100:.0f}%)")
        ax2.set_yscale("log")
        ax2.legend(loc="upper left", frameon=False, fontsize=9)
        stats["sharpe"], stats["maxdd"] = sharpe(strat), max_drawdown(strat)
        ref = walk_forward_backtest(close, labels)["sharpe"]
        if np.isfinite(ref) and abs(ref - stats["sharpe"]) > 1e-6:
            print(f"  ! {name}: chart Sharpe {stats['sharpe']:.4f} != package {ref:.4f}", file=sys.stderr)
    else:
        ax2.text(0.5, 0.5, "Not enough history\nfor a walk-forward test", ha="center", va="center")
    ax2.set_title("Walk-forward strategy vs buy & hold (growth of 1, log scale)")
    ax2.grid(alpha=0.25)

    # 3. transition matrix heatmap
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.imshow(P, cmap="Greens", vmin=0, vmax=1)
    ax3.set_xticks(range(3), STATES)
    ax3.set_yticks(range(3), STATES)
    ax3.set_xlabel("Tomorrow")
    ax3.set_ylabel("Today")
    for i in range(3):
        for j in range(3):
            ax3.text(j, i, f"{P[i, j] * 100:.1f}%", ha="center", va="center",
                     color="white" if P[i, j] > 0.55 else "black", fontsize=12,
                     fontweight="bold" if i == j else "normal")
    ax3.set_title("Transition matrix (diagonal = how sticky)")

    fig.suptitle("Backtests are historical, not forward-looking, and exclude trading costs.",
                 fontsize=9, color="#666", y=1.02)
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    fig.savefig(out_dir / f"{safe}.png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return stats


def mix_figure(rows: list[dict], out_dir: Path) -> None:
    rows = sorted(rows, key=lambda r: r["bull"])
    fig, ax = plt.subplots(figsize=(10, 0.42 * len(rows) + 2), constrained_layout=True)
    y = np.arange(len(rows))
    left = np.zeros(len(rows))
    for key, k in (("bear", 0), ("side", 1), ("bull", 2)):
        vals = np.array([r[key] for r in rows])
        ax.barh(y, vals, left=left, color=COLORS[k], label=STATES[k])
        for yi, (v, l) in enumerate(zip(vals, left)):
            if v > 0.07:
                ax.text(l + v / 2, yi, f"{v * 100:.0f}%", ha="center", va="center", fontsize=8)
        left += vals
    ax.set_yticks(y, [r["ticker"] for r in rows])
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share of time in each regime (long-run / stationary distribution)")
    ax.set_title("Long-run regime mix by ticker", pad=28)
    ax.legend(ncol=3, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    fig.savefig(out_dir / "_comparison_long_run_mix.png", dpi=110)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", required=True, help="comma/space separated")
    ap.add_argument("--years", type=int, default=10)
    ap.add_argument("--window", type=int, default=20)
    ap.add_argument("--threshold", type=float, default=0.02)
    ap.add_argument("--out", default="charts")
    a = ap.parse_args()

    from markov_hedge_fund_method.run import _fetch_with_retry

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for t in [x for x in re.split(r"[,\s]+", a.tickers) if x]:
        try:
            df = _fetch_with_retry(t, a.years)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            close = df["Close"].dropna()
            rows.append(ticker_figure(t, close, a.window, a.threshold, out))
            print(f"chart ok: {t}")
        except Exception as exc:  # noqa: BLE001
            print(f"chart FAILED: {t}: {exc}", file=sys.stderr)
    if rows:
        mix_figure(rows, out)
        print(f"{len(rows)} ticker chart(s) + comparison saved to {out}/")
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
