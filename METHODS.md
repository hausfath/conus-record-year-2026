# Odds of a record-warm 2026 for the contiguous U.S. (data through August 2026)

Run 2026-10-01. Scripts: `record_odds.py` (models + full-record CV), `cv2.py` (2000–2025 CV,
hinge trend, hindcasts), `make_figure.py` (pooled estimate + two-panel figure), `make_figure_simple.py` (single-panel figure). Dependencies in `requirements.txt`.

## Data
- NOAA NCEI Climate at a Glance, contiguous U.S. average temperature, nClimDiv, °F
  (`data/cag_all_months.csv`, all months 1895-01 to 2026-08; `data/cag_annual.csv` 1895–2025; `fetch_data.sh` refreshes both).
  URL pattern: `.../climate-at-a-glance/national/time-series/110/tavg/all/1/1895-2026/data.csv`.
- Checked: NOAA's annual value equals the unweighted mean of the 12 monthly values
  (max discrepancy 0.005 °F, rounding). So annual 2026 = (8 × Jan–Aug mean + 4 × Sep–Dec mean) / 12.
- September 2026 is not yet published (NCEI releases ~8th of the month). nClimDiv values can be
  revised slightly in later releases.

## Known values
| Quantity | °F | °C |
|---|---|---|
| Record annual: 2024 | 55.48 | 13.04 |
| Runner-up: 2012 | 55.27 | 12.93 |
| 2026 Jan–Aug mean (warmest YTD on record; 2012 was 57.90) | 57.98 | 14.43 |
| Sep–Dec mean needed to beat 2024 | 50.50 | 10.28 |
| Sep–Dec mean needed to beat 2012 | 49.87 | 9.93 |
| Historical Sep–Dec mean, 1895–2025 | 48.66 | 9.26 |
| Sep–Dec mean, 2016–2025 | 50.96 | 10.53 |
| Record Sep–Dec: 2024 | 52.71 | 11.51 |

Sep–Dec exceeded 50.50 °F in 12 of 131 years, 8 of them since 2000. JJA 2026 (74.37 °F) and
August 2026 (75.58 °F) are each the warmest on record.

## Models (all predict the Sep–Dec mean; annual follows deterministically)
- A: Sep–Dec ~ year (trend only, baseline).
- B: Sep–Dec ~ Jan–Aug mean + year.
- C: B + August.
- D: B + JJA mean (last three months).
- B2 / D2: B / D with a hinge trend (extra slope after 1980).
- E: AR(1) on standardized monthly anomalies about per-month linear trends, simulated from the
  observed August anomaly (lag-1 month-to-month correlation ≈ 0.2).
- F: trend fit plus the last 30 years' detrended Sep–Dec residuals (smoothed bootstrap in the pool).
OLS predictive intervals use the t distribution with parameter uncertainty (`se_obs`).
Fit windows: 1895+, 1950+, 1980+.

## Cross-validation (rolling origin: predict year t from years < t)
Test years 2000–2025, Sep–Dec mean, °F:

| Window | Model | Bias | RMSE | CRPS | 90% coverage |
|---|---|---|---|---|---|
| 1895+ | B YTD+trend | +0.76 | 1.48 | 0.86 | 0.73 |
| 1895+ | D YTD+JJA+trend | +0.64 | 1.40 | 0.81 | 0.73 |
| 1950+ | D YTD+JJA+trend | +0.51 | 1.35 | 0.79 | 0.69 |
| 1950+ | D2 hinge | +0.06 | 1.28 | 0.74 | 0.88 |
| 1950+ | B2 hinge | +0.19 | 1.27 | 0.73 | 0.81 |
| 1980+ | A trend only | +0.14 | 1.27 | 0.73 | 0.92 |
| 1980+ | B YTD+trend | +0.13 | 1.33 | 0.75 | 0.88 |
| 1980+ | D YTD+JJA+trend | +0.01 | 1.35 | 0.77 | 0.92 |

Bias = observed − predicted. Linear trends fitted from 1895 or 1950 under-predict recent autumns
by 0.5–1 °F (CONUS warming has accelerated and the last five Sep–Dec periods are all in the top
six), with 90% intervals covering only ~70%. The 1980+ window and hinge-trend fits are unbiased
with near-nominal coverage, so the headline pools those. Adding JJA improves CRPS slightly in
every window; adding August alone adds little. Detrended correlation of Sep–Dec with Jan–Aug is
0.25, with JJA 0.39, with August 0.21 (1950–2025).

## Hindcast sanity check (model D, through August of each year)
| Year | Prior record | YTD rank | P(record), 1950+ / 1980+ | Outcome |
|---|---|---|---|---|
| 2012 | 54.24 (2006) | 1 | 0.99 / 1.00 | record (55.27) |
| 2016 | 55.27 (2012) | 3 | 0.01 / 0.05 | no (54.90) |
| 2024 | 55.27 (2012) | 2 | 0.09 / 0.20 | record (55.48), on a record-warm Sep–Dec |
| 2025 | 55.48 (2024) | 11 | 0.00 / 0.00 | no (54.62) |

## 2026 results
| Model | Sep–Dec mean (°F) | SD | P(record) | P(top 2) |
|---|---|---|---|---|
| D 1980+ | 51.90 | 1.22 | 0.87 | 0.95 |
| B 1980+ | 51.88 | 1.23 | 0.87 | 0.95 |
| D2 hinge 1950+ | 51.49 | 1.13 | 0.81 | 0.93 |
| B2 hinge 1950+ | 51.46 | 1.15 | 0.80 | 0.91 |
| E AR(1) 1980+ | 51.28 | 1.18 | 0.75 | 0.88 |
| F empirical 1980+ | 51.15 | 1.40 | 0.67 | 0.80 |
| **Pooled (equal weight)** | **51.53** | **1.26** | **0.79** | **0.90** |

Pooled 2026 annual: median 55.83 °F (13.24 °C), 5–95% range 55.12–56.51 °F.
Biased long-window linear-trend models (not pooled) give 0.62–0.73 for the record.

## Caveats
- The estimate rests on the trend assumption more than on the predictor set: the spread across
  defensible models is roughly 0.65–0.87, so quote ~80% with "roughly three-in-four to nine-in-ten".
- Sep–Dec needs to be only moderately warm relative to recent autumns (below the 2016–2025 mean of
  50.96 °F). A 2012-style autumn (50.03 °F) would leave 2026 second at 55.33 °F.
- No use of seasonal forecasts (CPC outlook, ENSO state). A strong El Niño winter typically favours
  a warm northern tier and cool/wet South in Nov–Dec; the net CONUS-mean effect is small and
  mixed-sign historically, so it was not included.
- Persistence (AR(1)) is weak at monthly scale for CONUS, which is why the autocorrelation
  model adds little over the regression approaches.
