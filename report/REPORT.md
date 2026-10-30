# Markov regime report

Updated 2026-10-30 12:44 UTC · 10 years of daily data · 20-day window · ±2% threshold

Each day is labelled **Bull**, **Bear** or **Sideways** from the trailing return. *Long-run mix* is the share of time the model expects in each regime. *Stays* is the chance a regime continues the next day. *Strategy* goes long in Bull-leaning states and short in Bear-leaning ones, re-fitted every day with no lookahead; *B&H* is simply holding the asset over the same days. Backtests are historical, not forward-looking, and exclude trading costs.

![Long-run regime mix](charts/_comparison_long_run_mix.png)

## Table

| Ticker | Now | Bear | Sideways | Bull | Bear stays | Bull stays | Sharpe: strategy | Sharpe: B&H | Max DD: strategy | Max DD: B&H | Data from |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [VOO](#voo) | Sideways | 17.6% | 34.9% | 47.5% | 86.0% | 89.0% | 0.26 | 0.83 | -33% | -34% | 2016-10-31 |
| [VTI](#vti) | Sideways | 18.3% | 35.0% | 46.7% | 86.5% | 87.9% | 0.32 | 0.79 | -38% | -35% | 2016-10-31 |
| [EWT](#ewt) | Bear | 24.6% | 27.5% | 47.9% | 84.8% | 89.8% | 0.34 | 0.85 | -53% | -39% | 2016-10-31 |
| [SHY](#shy) | Sideways | 0.0% | 99.8% | 0.2% | 0.0% | 40.0% | 0.76 | 1.14 | -6% | -6% | 2016-10-31 |
| [SGOV](#sgov) | Sideways | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | – | 14.78 | 0% | -0% | 2020-06-01 |
| [SCHP](#schp) | Bull | 5.4% | 88.5% | 6.1% | 73.5% | 69.8% | -0.13 | 0.49 | -25% | -14% | 2016-10-31 |
| [IEF](#ief) | Bull | 11.8% | 76.0% | 12.2% | 80.5% | 79.1% | -0.14 | 0.14 | -23% | -24% | 2016-10-31 |
| [VXUS](#vxus) | Sideways | 20.7% | 38.8% | 40.5% | 86.4% | 87.1% | 0.31 | 0.51 | -35% | -36% | 2016-10-31 |
| [QQQM](#qqqm) | Bear | 25.1% | 26.7% | 48.1% | 86.4% | 88.7% | 0.41 | 0.73 | -27% | -35% | 2020-10-13 |
| [AAPL](#aapl) | Bull | 26.4% | 19.2% | 54.4% | 88.9% | 91.8% | 0.61 | 0.96 | -39% | -39% | 2016-10-31 |
| [GOOG](#goog) | Bear | 27.0% | 21.5% | 51.5% | 85.9% | 90.7% | 0.31 | 0.77 | -64% | -45% | 2016-10-31 |
| [AAAU](#aaau) | Bear | 21.6% | 38.3% | 40.1% | 79.9% | 87.7% | 0.08 | 0.84 | -47% | -26% | 2018-08-15 |
| [MSFT](#msft) | Bull | 23.0% | 24.9% | 52.0% | 81.8% | 89.5% | -0.34 | 0.90 | -82% | -37% | 2016-10-31 |
| [NVDA](#nvda) | Bear | 28.8% | 13.5% | 57.7% | 84.7% | 91.3% | 0.23 | 1.08 | -75% | -66% | 2016-10-31 |
| [TSLA](#tsla) | Bull | 39.2% | 11.0% | 49.7% | 88.6% | 90.0% | 0.34 | 0.84 | -84% | -74% | 2016-10-31 |
| [SPOT](#spot) | Bull | 37.9% | 13.5% | 48.6% | 88.0% | 90.2% | -0.13 | 0.62 | -91% | -81% | 2018-04-03 |
| [SNDK](#sndk) | Bear | 25.3% | 7.1% | 67.6% | 90.2% | 95.6% | 1.76 | 1.59 | -43% | -56% | 2025-02-13 |
| [NKE](#nke) | Bull | 36.4% | 21.7% | 41.9% | 86.6% | 87.1% | -0.07 | 0.09 | -70% | -79% | 2016-10-31 |
| [MA](#ma) | Bull | 24.3% | 26.0% | 49.8% | 82.8% | 90.2% | -0.34 | 0.74 | -80% | -41% | 2016-10-31 |
| [XLE](#xle) | Bull | 30.6% | 25.7% | 43.7% | 86.0% | 89.7% | 0.06 | 0.54 | -68% | -67% | 2016-10-31 |
| [RSP](#rsp) | Bull | 19.8% | 36.3% | 43.8% | 88.4% | 87.9% | 0.36 | 0.67 | -37% | -39% | 2016-10-31 |
| [VTV](#vtv) | Bull | 17.5% | 38.6% | 44.0% | 84.1% | 89.3% | 0.31 | 0.75 | -31% | -37% | 2016-10-31 |
| [SCHD](#schd) | Bull | 18.8% | 37.5% | 43.7% | 84.6% | 88.9% | 0.21 | 0.78 | -35% | -33% | 2016-10-31 |
| [HYG](#hyg) | Sideways | 7.6% | 81.5% | 10.8% | 78.1% | 80.5% | -0.00 | 0.50 | -31% | -22% | 2016-10-31 |
| [TLT](#tlt) | Bull | 28.4% | 44.3% | 27.3% | 85.3% | 84.6% | -0.13 | -0.05 | -43% | -48% | 2016-10-31 |
| [VGIT](#vgit) | Sideways | 4.8% | 89.4% | 5.9% | 77.5% | 78.9% | 0.33 | 0.32 | -14% | -16% | 2016-10-31 |
| [XLU](#xlu) | Bull | 24.7% | 33.2% | 42.1% | 84.4% | 88.0% | 0.04 | 0.51 | -57% | -36% | 2016-10-31 |

## Charts

### VOO

![VOO](charts/VOO.png)

### VTI

![VTI](charts/VTI.png)

### EWT

![EWT](charts/EWT.png)

### SHY

![SHY](charts/SHY.png)

### SGOV

![SGOV](charts/SGOV.png)

### SCHP

![SCHP](charts/SCHP.png)

### IEF

![IEF](charts/IEF.png)

### VXUS

![VXUS](charts/VXUS.png)

### QQQM

![QQQM](charts/QQQM.png)

### AAPL

![AAPL](charts/AAPL.png)

### GOOG

![GOOG](charts/GOOG.png)

### AAAU

![AAAU](charts/AAAU.png)

### MSFT

![MSFT](charts/MSFT.png)

### NVDA

![NVDA](charts/NVDA.png)

### TSLA

![TSLA](charts/TSLA.png)

### SPOT

![SPOT](charts/SPOT.png)

### SNDK

![SNDK](charts/SNDK.png)

### NKE

![NKE](charts/NKE.png)

### MA

![MA](charts/MA.png)

### XLE

![XLE](charts/XLE.png)

### RSP

![RSP](charts/RSP.png)

### VTV

![VTV](charts/VTV.png)

### SCHD

![SCHD](charts/SCHD.png)

### HYG

![HYG](charts/HYG.png)

### TLT

![TLT](charts/TLT.png)

### VGIT

![VGIT](charts/VGIT.png)

### XLU

![XLU](charts/XLU.png)
