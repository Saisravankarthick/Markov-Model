"""Monte Carlo simulation for a buy-and-hold portfolio, plus regime-day distributions.

Two ingredients, deliberately separate so each can check the other:

  1. DOLLARS: blocks of real daily returns (all funds on the same dates, so their
     correlation and fat tails are kept) are resampled to build many possible
     futures for the portfolio. Run twice: "history repeats", and with a yearly
     return haircut as a stress case.
  2. REGIMES: Bear / Sideways / Bull days are counted (a) on those resampled
     futures with the same 20-day +/-2% rule, and (b) by simulating each fund's
     own Markov transition table, with the table fixed and with the table
     re-drawn each path (Dirichlet) to show estimation uncertainty.

    uv run python scripts/montecarlo.py --tickers "EQAL, VXUS" --amounts "14000, 14500" \
        --out report/MONTE_CARLO.md --charts report/mc

Not a forecast: it assumes the sampled decade is representative, ignores taxes,
costs and cash flows, and the portfolio is buy-and-hold (no rebalancing).
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

from markov_hedge_fund_method.regime import label_regimes  # noqa: E402

WINDOW, THRESHOLD = 20, 0.02
TD = 252  # trading days per year
PCTS = (5, 25, 50, 75, 95)
NAMES = ["Bear", "Sideways", "Bull"]


# ----------------------------------------------------------------------------- engine
def block_bootstrap(R: np.ndarray, n_days: int, block: int, n_paths: int, rng, haircut: float, chunk: int = 1000):
    """Yield (m, n_days, k) arrays of resampled daily returns, built from blocks of real days."""
    T = len(R)
    adj = R - haircut / TD
    n_blocks = -(-n_days // block)
    for s in range(0, n_paths, chunk):
        m = min(chunk, n_paths - s)
        starts = rng.integers(0, T - block + 1, size=(m, n_blocks))
        idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(m, -1)[:, :n_days]
        yield adj[idx]


def simulate_portfolio(R, amounts, n_days, n_paths, block, haircut, rng, liab_day=None, sample_every=21):
    k = R.shape[1]
    sample_idx = np.arange(0, n_days + 1, sample_every)
    fan = np.empty((n_paths, len(sample_idx)))
    end = np.empty(n_paths)
    mdd = np.empty(n_paths)
    at_liab = np.empty(n_paths) if liab_day else None
    counts = np.zeros((n_paths, k, 3), dtype=int)  # per fund: Bear, Sideways, Bull days
    done = 0
    for chunk in block_bootstrap(R, n_days, block, n_paths, rng, haircut):
        m = chunk.shape[0]
        g = np.concatenate([np.ones((m, 1, k)), np.cumprod(1 + chunk, axis=1)], axis=1)  # (m, n+1, k)
        V = (g * amounts[None, None, :]).sum(axis=2)
        sl = slice(done, done + m)
        fan[sl] = V[:, sample_idx]
        end[sl] = V[:, -1]
        mdd[sl] = (V / np.maximum.accumulate(V, axis=1) - 1).min(axis=1)
        if liab_day:
            at_liab[sl] = V[:, liab_day]
        r20 = g[:, WINDOW:, :] / g[:, :-WINDOW, :] - 1
        bear = (r20 < -THRESHOLD).sum(axis=1)
        bull = (r20 > THRESHOLD).sum(axis=1)
        counts[sl, :, 0] = bear
        counts[sl, :, 2] = bull
        counts[sl, :, 1] = r20.shape[1] - bear - bull
        done += m
    return {"fan": fan, "end": end, "mdd": mdd, "at_liab": at_liab, "counts": counts, "sample_idx": sample_idx,
            "n_label_days": n_days - WINDOW + 1}


def transition_counts(labels: np.ndarray) -> np.ndarray:
    C = np.zeros((3, 3))
    for a, b in zip(labels[:-1], labels[1:]):
        C[a, b] += 1
    return C


def markov_counts(C: np.ndarray, n_steps: int, n_paths: int, rng, redraw: bool, s0: int) -> np.ndarray:
    """Simulate regime days from a transition table. redraw=True draws a fresh table per path (Dirichlet)."""
    if redraw:
        P = np.stack([rng.dirichlet(C[i] + 1.0, size=n_paths) for i in range(3)], axis=1)  # (paths, 3, 3)
    else:
        rs = C.sum(axis=1, keepdims=True)
        P0 = np.where(rs > 0, C / np.where(rs == 0, 1, rs), 1 / 3)
        P = np.broadcast_to(P0, (n_paths, 3, 3))
    cum = np.cumsum(P, axis=2)
    cum[:, :, -1] = 1.0
    state = np.full(n_paths, s0)
    out = np.zeros((n_paths, 3), dtype=int)
    ar = np.arange(n_paths)
    for _ in range(n_steps):
        u = rng.random(n_paths)
        state = (u[:, None] > cum[ar, state]).sum(axis=1)
        out[ar, state] += 1
    return out


def historical_reference(R: np.ndarray, amounts: np.ndarray) -> dict:
    g = np.concatenate([np.ones((1, R.shape[1])), np.cumprod(1 + R, axis=0)], axis=0)
    V = (g * amounts[None, :]).sum(axis=1)
    return {"cagr": (V[-1] / V[0]) ** (TD / len(R)) - 1, "mdd": float((V / np.maximum.accumulate(V) - 1).min()),
            "end": float(V[-1])}


def run_simulation(returns: pd.DataFrame, amounts, horizon_years, n_paths, block, haircut, seed, liability=0.0, liab_years=4.0):
    rng = np.random.default_rng(seed)
    R = returns.to_numpy(dtype=float)
    amounts = np.asarray(amounts, dtype=float)
    n_days = int(round(horizon_years * TD))
    liab_day = int(round(liab_years * TD)) if liability and liab_years * TD <= n_days else None
    out = {"tickers": list(returns.columns), "amounts": amounts, "n_days": n_days, "n_paths": n_paths, "block": block,
           "haircut": haircut, "seed": seed, "liability": liability, "liab_years": liab_years, "liab_day": liab_day,
           "hist": historical_reference(R, amounts), "hist_days": len(R),
           "hist_start": str(returns.index[0].date()) if hasattr(returns.index[0], "date") else "", "hist_end": str(returns.index[-1].date()) if hasattr(returns.index[-1], "date") else ""}
    out["scenarios"] = {
        "history": simulate_portfolio(R, amounts, n_days, n_paths, block, 0.0, rng, liab_day),
        "haircut": simulate_portfolio(R, amounts, n_days, n_paths, block, haircut, rng, liab_day),
    }
    out["markov"] = {}
    n_steps = n_days - WINDOW + 1
    for j, t in enumerate(returns.columns):
        close = (1 + returns.iloc[:, j]).cumprod()
        labels = label_regimes(close, window=WINDOW, threshold=THRESHOLD).to_numpy(dtype=int)
        C = transition_counts(labels)
        s0 = int(labels[-1])
        out["markov"][t] = {"C": C, "s0": s0,
                            "fixed": markov_counts(C, n_steps, n_paths, rng, False, s0),
                            "redraw": markov_counts(C, n_steps, n_paths, rng, True, s0)}
    return out


# ----------------------------------------------------------------------------- report
def usd(x):
    return f"${x:,.0f}"


def pct_str(a, scale=1.0, fmt="{:,.0f}"):
    p = np.percentile(a, PCTS) * scale
    return " – ".join(fmt.format(v) for v in (p[0], p[2], p[4]))


def render(res: dict) -> str:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    tk, am = res["tickers"], res["amounts"]
    tot = am.sum()
    yrs = res["n_days"] / TD
    out = [f"# Monte Carlo: {' + '.join(tk)}", "",
           f"Updated {now} · {res['n_paths']:,} simulated futures of {yrs:g} years ({res['n_days']:,} trading days) · "
           f"seed {res['seed']} · blocks of {res['block']} real days resampled from {res['hist_start']} to {res['hist_end']}", "",
           "## Setup", "",
           "| Fund | Amount | Share of total |", "|---|---|---|"]
    for t, a in zip(tk, am):
        out.append(f"| {t} | {usd(a)} | {a / tot * 100:.1f}% |")
    out += [f"| **Total** | **{usd(tot)}** | 100% |", "",
            "Buy-and-hold: no rebalancing, no contributions or withdrawals, no taxes or costs. Prices are dividend-adjusted (total return). "
            f"**Scenario A: history repeats.** **Scenario B: {res['haircut'] * 100:g}% a year is subtracted from every fund's return**, a stress case "
            "(my assumption, not a forecast).", "",
            f"For reference, the actual last {res['hist_days'] / TD:.1f} years of this exact mix: **{res['hist']['cagr'] * 100:.1f}% a year**, "
            f"worst fall **{res['hist']['mdd'] * 100:.0f}%**, {usd(tot)} became {usd(res['hist']['end'])}.", "",
            f"## 1. Where {usd(tot)} could end up", ""]
    A, B = res["scenarios"]["history"], res["scenarios"]["haircut"]

    def row(label, fa, fb):
        return f"| {label} | {fa} | {fb} |"

    cagr = lambda s: (s["end"] / tot) ** (1 / yrs) - 1  # noqa: E731
    out += [f"| After {yrs:g} years | A: history repeats | B: −{res['haircut'] * 100:g}%/yr stress |", "|---|---|---|"]
    for p in PCTS:
        out.append(row(f"{p}th percentile value" + (" (median)" if p == 50 else ""), usd(np.percentile(A["end"], p)), usd(np.percentile(B["end"], p))))
    out += [row("Median growth per year", f"{np.median(cagr(A)) * 100:.1f}%", f"{np.median(cagr(B)) * 100:.1f}%"),
            row(f"Chance of ending below {usd(tot)} (the amount invested)", f"{(A['end'] < tot).mean() * 100:.1f}%", f"{(B['end'] < tot).mean() * 100:.1f}%"),
            row("Median worst fall along the way", f"{np.median(A['mdd']) * 100:.0f}%", f"{np.median(B['mdd']) * 100:.0f}%"),
            row("Chance of a fall worse than −20%", f"{(A['mdd'] < -0.20).mean() * 100:.0f}%", f"{(B['mdd'] < -0.20).mean() * 100:.0f}%"),
            row("Chance of a fall worse than −30%", f"{(A['mdd'] < -0.30).mean() * 100:.0f}%", f"{(B['mdd'] < -0.30).mean() * 100:.0f}%"),
            row("Chance of a fall worse than −40%", f"{(A['mdd'] < -0.40).mean() * 100:.0f}%", f"{(B['mdd'] < -0.40).mean() * 100:.0f}%"), ""]
    if res["liab_day"]:
        y = res["liab_years"]
        out += [f"### The liability: {usd(res['liability'])} needed in {y:g} years", "",
                f"| After {y:g} years | A: history repeats | B: −{res['haircut'] * 100:g}%/yr stress |", "|---|---|---|"]
        for p in PCTS:
            out.append(row(f"{p}th percentile value", usd(np.percentile(A["at_liab"], p)), usd(np.percentile(B["at_liab"], p))))
        out += [row(f"**Chance the portfolio is below {usd(res['liability'])}**", f"**{(A['at_liab'] < res['liability']).mean() * 100:.1f}%**",
                    f"**{(B['at_liab'] < res['liability']).mean() * 100:.1f}%**"), ""]
    else:
        out += ["*No liability was entered. Add its amount and timing (for example $20,000 in 4 years) and rerun to get the chance of falling short.*", ""]
    out += ["![Portfolio value over time](mc/mc_fan.png)", "",
            "## 2. How many days in each regime", "",
            f"Over {res['n_days']:,} trading days, how many would be Bear, Sideways and Bull. Each cell is the **5th – median – 95th** percentile, in days "
            f"(out of {A['n_label_days']:,} days that can be labelled).", ""]
    for j, t in enumerate(tk):
        M = res["markov"][t]
        out += [f"### {t}  ·  today: {NAMES[M['s0']]}", "", "| Method | Bear days | Sideways days | Bull days |", "|---|---|---|---|"]
        n = A["n_label_days"]
        for label, c in [("Resampled real returns, labelled with the 20-day ±2% rule", A["counts"][:, j, :]),
                         ("Markov chain, table fixed", M["fixed"]), ("Markov chain, table re-drawn each path", M["redraw"])]:
            out.append(f"| {label} | " + " | ".join(pct_str(c[:, s]) for s in range(3)) + " |")
        out.append("")
    out += ["![Bear days](mc/mc_regimes.png)", "",
            "**How to read the checks.** If the Markov-chain rows are close to the resampled-returns row, the transition table is a consistent summary of the "
            "data. The *re-drawn* row is wider because it admits that the table was estimated from only about ten years. "
            "Differences also come from the Markov chain forgetting any longer memory in real returns.", "",
            "## 3. What this does and does not tell you", "",
            "- It assumes the sampled decade is representative of the next ten years. A decade of strong stock returns will make Scenario A look good almost by construction; that is why Scenario B exists.",
            "- Resampling blocks of 20 days keeps short-term momentum and the funds' co-movement, but not anything longer than a block.",
            "- Results are ranges, not predictions. The extreme percentiles depend on rare events that a decade of data barely contains.",
            "- No rebalancing, taxes, trading costs, currency effects on VXUS beyond what is in its price, withdrawals or contributions.", "",
            "_Historical, not forward-looking._", ""]
    return "\n".join(out)


def make_charts(res: dict, outdir: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    outdir.mkdir(parents=True, exist_ok=True)
    tk, am = res["tickers"], res["amounts"]
    tot = am.sum()
    col = {"Bear": "#C57F86", "Sideways": "#A4ABB7", "Bull": "#84BBA1"}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True, constrained_layout=True)
    for ax, (key, title) in zip(axes, [("history", "A: history repeats"), ("haircut", f"B: −{res['haircut'] * 100:g}% a year stress")]):
        S = res["scenarios"][key]
        x = S["sample_idx"] / TD
        q = np.percentile(S["fan"], [5, 25, 50, 75, 95], axis=0)
        ax.fill_between(x, q[0], q[4], color="#84BBA1", alpha=0.25, label="5th–95th percentile")
        ax.fill_between(x, q[1], q[3], color="#84BBA1", alpha=0.45, label="25th–75th percentile")
        ax.plot(x, q[2], color="#2E6F57", lw=2, label="Median")
        ax.axhline(tot, color="#444", ls=":", lw=1.2, label=f"Invested {usd(tot)}")
        if res["liab_day"]:
            ax.scatter([res["liab_years"]], [res["liability"]], color="#9A4750", zorder=5, s=45, label=f"Liability {usd(res['liability'])}")
        ax.set_title(title, fontweight="bold")
        ax.set_xlabel("years from today")
        ax.grid(alpha=0.25)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].set_ylabel("portfolio value ($)")
    axes[0].legend(frameon=False, fontsize=8.5, loc="upper left")
    fig.savefig(outdir / "mc_fan.png", dpi=110, bbox_inches="tight")
    plt.close(fig)

    n = len(tk)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 3.8), constrained_layout=True, squeeze=False)
    for j, (ax, t) in enumerate(zip(axes[0], tk)):
        M = res["markov"][t]
        n_lab = res["scenarios"]["history"]["n_label_days"]
        for label, c, color, ls in [("Resampled real returns", res["scenarios"]["history"]["counts"][:, j, 0], "#2E6F57", "-"),
                                    ("Markov chain, table fixed", M["fixed"][:, 0], "#5F6673", "--"),
                                    ("Markov chain, table re-drawn", M["redraw"][:, 0], "#9A4750", "-")]:
            ax.hist(c / n_lab * 100, bins=60, histtype="step", density=True, color=color, ls=ls, lw=1.8, label=label)
        ax.set_title(f"{t}: share of days in Bear", fontweight="bold")
        ax.set_xlabel("% of days in Bear over the period")
        ax.set_yticks([])
        ax.legend(frameon=False, fontsize=8)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
    fig.savefig(outdir / "mc_regimes.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------------- CLI
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", default="EQAL, VXUS")
    ap.add_argument("--amounts", default="14000, 14500")
    ap.add_argument("--years", type=int, default=10, help="years of history to resample")
    ap.add_argument("--horizon", type=float, default=10, help="years to simulate")
    ap.add_argument("--paths", type=int, default=10000)
    ap.add_argument("--block", type=int, default=20)
    ap.add_argument("--haircut", type=float, default=0.03)
    ap.add_argument("--liability", type=float, default=0.0)
    ap.add_argument("--liability-years", type=float, default=4.0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="report/MONTE_CARLO.md")
    ap.add_argument("--charts", default="report/mc")
    a = ap.parse_args()
    tickers = [x for x in re.split(r"[,\s]+", a.tickers) if x]
    amounts = [float(x) for x in re.split(r"[,\s]+", a.amounts) if x]
    if len(tickers) != len(amounts):
        print("tickers and amounts must have the same length", file=sys.stderr)
        return 2
    from markov_hedge_fund_method.run import _fetch_with_retry

    closes = {}
    for t in tickers:
        df = _fetch_with_retry(t, a.years)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        closes[t] = df["Close"].dropna()
    px = pd.DataFrame(closes).dropna()
    returns = px.pct_change().dropna()
    res = run_simulation(returns, amounts, a.horizon, a.paths, a.block, a.haircut, a.seed, a.liability, a.liability_years)
    make_charts(res, Path(a.charts))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(render(res))
    print("monte carlo ok:", tickers, a.paths, "paths")
    return 0


if __name__ == "__main__":
    sys.exit(main())
