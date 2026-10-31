# Window and threshold sensitivity test

Updated 2026-10-31 12:28 UTC · 10 years of daily data · walk-forward (no lookahead) · costs: 5 basis points per unit of position change

Each row re-runs the regime model with a different rolling window and threshold. **Sharpe (net)** subtracts trading costs. **Changes/yr** is how often the position flips. The **out-of-sample** line picks the best setting on the first half of the period and then shows how that same setting did on the second half.

## SPY

| Window | Threshold | Bear | Sideways | Bull | Sharpe | Sharpe (net) | Max DD | Changes/yr |
|---|---|---|---|---|---|---|---|---|
| 10d | ±1% | 22% | 30% | 48% | 0.36 | 0.23 | -26% | 25 |
| 10d | ±2% | 15% | 55% | 30% | 0.28 | 0.18 | -42% | 19 |
| 10d | ±5% | 4% | 91% | 4% | 0.20 | 0.15 | -38% | 9 |
| 20d | ±1% | 22% | 18% | 60% | 0.41 | 0.34 | -27% | 14 |
| 20d **(default)** | ±2% | 18% | 35% | 47% | 0.17 | 0.10 | -33% | 14 |
| 20d | ±5% | 7% | 79% | 13% | 0.24 | 0.19 | -34% | 10 |
| 60d | ±1% | 19% | 8% | 73% | 0.31 | 0.26 | -32% | 9 |
| 60d | ±2% | 17% | 14% | 69% | 0.19 | 0.15 | -43% | 8 |
| 60d | ±5% | 10% | 46% | 44% | 0.06 | 0.02 | -58% | 7 |
| **Buy & hold** | | | | | **0.82** | | **-34%** | 0 |

**Out-of-sample** (split 2022-05-02): best on the first half was 10d / ±1% (Sharpe 0.59). On the second half it scored **0.10** (-0.07 after costs), vs 0.28 for the 20d / ±2% default and **0.97** for buy & hold.

## TLT

| Window | Threshold | Bear | Sideways | Bull | Sharpe | Sharpe (net) | Max DD | Changes/yr |
|---|---|---|---|---|---|---|---|---|
| 10d | ±1% | 35% | 32% | 33% | -0.25 | -0.46 | -53% | 33 |
| 10d | ±2% | 22% | 59% | 19% | -0.31 | -0.49 | -49% | 28 |
| 10d | ±5% | 3% | 94% | 3% | -0.71 | -0.75 | -68% | 7 |
| 20d | ±1% | 40% | 23% | 37% | -0.22 | -0.38 | -51% | 26 |
| 20d **(default)** | ±2% | 28% | 44% | 27% | -0.13 | -0.27 | -43% | 22 |
| 20d | ±5% | 8% | 84% | 8% | -0.26 | -0.32 | -50% | 10 |
| 60d | ±1% | 42% | 18% | 40% | -0.10 | -0.21 | -46% | 18 |
| 60d | ±2% | 36% | 31% | 33% | 0.05 | -0.05 | -39% | 16 |
| 60d | ±5% | 19% | 62% | 19% | -0.28 | -0.33 | -43% | 9 |
| **Buy & hold** | | | | | **-0.04** | | **-48%** | 0 |

**Out-of-sample** (split 2022-05-02): best on the first half was 60d / ±2% (Sharpe 0.61). On the second half it scored **-0.49** (-0.63 after costs), vs -0.45 for the 20d / ±2% default and **-0.22** for buy & hold.

## HYG

| Window | Threshold | Bear | Sideways | Bull | Sharpe | Sharpe (net) | Max DD | Changes/yr |
|---|---|---|---|---|---|---|---|---|
| 10d | ±1% | 12% | 69% | 19% | 0.06 | -0.15 | -29% | 17 |
| 10d | ±2% | 4% | 90% | 6% | 0.21 | 0.13 | -19% | 8 |
| 10d | ±5% | 1% | 99% | 1% | -0.09 | -0.10 | -26% | 2 |
| 20d | ±1% | 15% | 52% | 32% | 0.19 | 0.05 | -22% | 12 |
| 20d **(default)** | ±2% | 8% | 82% | 11% | -0.01 | -0.12 | -31% | 10 |
| 20d | ±5% | 1% | 97% | 2% | 0.57 | 0.55 | -18% | 2 |
| 60d | ±1% | 15% | 29% | 56% | 0.00 | -0.06 | -23% | 6 |
| 60d | ±2% | 10% | 58% | 32% | 0.02 | -0.04 | -32% | 6 |
| 60d | ±5% | 5% | 89% | 6% | -0.11 | -0.15 | -31% | 4 |
| **Buy & hold** | | | | | **0.50** | | **-22%** | 0 |

**Out-of-sample** (split 2022-05-02): best on the first half was 20d / ±5% (Sharpe 0.49). On the second half it scored **0.68** (0.65 after costs), vs 0.18 for the 20d / ±2% default and **0.77** for buy & hold.

## TSLA

| Window | Threshold | Bear | Sideways | Bull | Sharpe | Sharpe (net) | Max DD | Changes/yr |
|---|---|---|---|---|---|---|---|---|
| 10d | ±1% | 41% | 7% | 51% | 0.46 | 0.41 | -67% | 35 |
| 10d | ±2% | 38% | 14% | 48% | 0.56 | 0.51 | -73% | 32 |
| 10d | ±5% | 27% | 37% | 36% | 0.29 | 0.25 | -82% | 31 |
| 20d | ±1% | 41% | 6% | 52% | 0.35 | 0.31 | -87% | 23 |
| 20d **(default)** | ±2% | 39% | 11% | 50% | 0.34 | 0.30 | -84% | 24 |
| 20d | ±5% | 32% | 27% | 41% | 0.35 | 0.31 | -80% | 26 |
| 60d | ±1% | 40% | 5% | 55% | -0.00 | -0.03 | -95% | 15 |
| 60d | ±2% | 38% | 8% | 54% | -0.10 | -0.12 | -95% | 14 |
| 60d | ±5% | 34% | 17% | 49% | 0.22 | 0.20 | -87% | 13 |
| **Buy & hold** | | | | | **0.84** | | **-74%** | 0 |

**Out-of-sample** (split 2022-05-02): best on the first half was 20d / ±1% (Sharpe 0.59). On the second half it scored **0.09** (0.04 after costs), vs 0.13 for the 20d / ±2% default and **0.41** for buy & hold.

## VXUS

| Window | Threshold | Bear | Sideways | Bull | Sharpe | Sharpe (net) | Max DD | Changes/yr |
|---|---|---|---|---|---|---|---|---|
| 10d | ±1% | 27% | 30% | 43% | -0.01 | -0.20 | -44% | 33 |
| 10d | ±2% | 17% | 54% | 28% | 0.00 | -0.13 | -42% | 24 |
| 10d | ±5% | 4% | 92% | 4% | 0.20 | 0.16 | -48% | 8 |
| 20d | ±1% | 28% | 19% | 52% | 0.20 | 0.08 | -33% | 22 |
| 20d **(default)** | ±2% | 21% | 39% | 40% | 0.30 | 0.21 | -35% | 16 |
| 20d | ±5% | 7% | 81% | 12% | 0.17 | 0.12 | -31% | 10 |
| 60d | ±1% | 25% | 13% | 62% | 0.33 | 0.26 | -36% | 13 |
| 60d | ±2% | 21% | 23% | 56% | 0.19 | 0.13 | -33% | 11 |
| 60d | ±5% | 12% | 52% | 36% | 0.33 | 0.29 | -29% | 7 |
| **Buy & hold** | | | | | **0.50** | | **-36%** | 0 |

**Out-of-sample** (split 2022-05-02): best on the first half was 60d / ±1% (Sharpe 0.40). On the second half it scored **0.25** (0.16 after costs), vs 0.57 for the 20d / ±2% default and **0.80** for buy & hold.

_Backtests are historical, not forward-looking._
