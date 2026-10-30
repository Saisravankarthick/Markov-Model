"""Render markov_regime.py --json output as a Markdown report.

Standard library only, so it runs anywhere Python does. Used by the GitHub
Actions workflow to fill the run's job summary page.

    python scripts/summarize.py regime.json >> "$GITHUB_STEP_SUMMARY"

Exits non-zero if the JSON holds an {"error": ...} object.
"""

from __future__ import annotations

import json
import math
import sys

STATES = ("bear", "sideways", "bull")


def pct(x: float) -> str:
    return "n/a" if x is None or not math.isfinite(x) else f"{x * 100:.2f}%"


def render(a: dict) -> str:
    p = a["params"]
    lines = [
        f"## Markov regime — `{a['source']}`",
        "",
        f"{a['rows']} rows, {a['date_start']} → {a['date_end']} · "
        f"window {p['window']} · threshold ±{p['threshold'] * 100:g}%",
        "",
        f"**Current regime:** {a['current_regime']} · "
        f"**Signal** (bull − bear prob): `{a['signal']:+.4f}`",
        "",
        "### Next-step probabilities",
        "",
        "| Bear | Sideways | Bull |",
        "|---|---|---|",
        "| " + " | ".join(pct(a["next_state_probabilities"][s]) for s in STATES) + " |",
        "",
        "### Transition matrix (row = today, column = tomorrow)",
        "",
        "| | Bear | Sideways | Bull |",
        "|---|---|---|---|",
    ]
    for name, row in zip(a["states"], a["transition_matrix"]):
        lines.append(f"| **{name}** | " + " | ".join(pct(x) for x in row) + " |")

    sd = a["stationary_distribution"]
    wf = a["walk_forward"]
    lines += [
        "",
        "### Long-run regime mix (stationary distribution)",
        "",
        "| Bear | Sideways | Bull |",
        "|---|---|---|",
        "| " + " | ".join(pct(sd[s]) for s in STATES) + " |",
        "",
        "### Walk-forward backtest (no lookahead, no trading costs)",
        "",
        "| Sharpe | Max drawdown | Days evaluated |",
        "|---|---|---|",
        f"| {wf['sharpe']:.3f} | {pct(wf['max_drawdown'])} | {wf['n_trades']} |"
        if math.isfinite(wf["sharpe"])
        else f"| n/a | n/a | {wf['n_trades']} |",
    ]

    hmm = a.get("hmm", {})
    lines += ["", "### Hidden Markov Model", ""]
    if hmm.get("available"):
        lines += ["| Label | Latent state | Mean daily return |", "|---|---|---|"]
        for r in hmm["regimes"]:
            lines.append(
                f"| {r['label']} | {r['latent_state']} | {r['mean_daily_return'] * 100:+.3f}% |"
            )
    else:
        lines.append(f"Skipped: {hmm.get('reason', 'unavailable')}")

    lines += ["", f"_{a['disclaimer']}_", ""]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: summarize.py REGIME_JSON", file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8") as f:
        a = json.loads(f.read().strip().splitlines()[-1])
    if "error" in a:
        print(f"## Markov regime — failed\n\n```\n{a['error']}\n```\n")
        return 1
    print(render(a))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
