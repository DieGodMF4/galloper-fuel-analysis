# Galloper Fuel Analysis

Analysis of the complete fuel-refill history of a **Hyundai Galloper Exceed
Long 2.5 TCI diesel** (1999–2026), digitised from a 27-year handwritten
logbook kept by its owner. About **530 fill-ups** spanning roughly
**231,600 km** and the peseta-to-euro transition.

## Objective

Extract cost, consumption and refuelling-behaviour patterns from a single
vehicle tracked continuously for almost three decades:

- Evolution of diesel price over 27 years (nominal and inflation-adjusted).
- Fuel economy vs. vehicle ageing and mileage.
- Spending patterns and refuelling frequency over time.
- Market share by fuel brand and by location (several stations in the same
  town are tracked separately).
- Effect of switching to premium diesel (Shell V-Power / BP Ultimate),
  annotated by hand in the log, treated as a natural experiment.

## Methodological note (important)

Fill-ups were done to a **fixed amount of money**, not to a full tank.
Per-leg fuel economy (litres of one fill-up divided by the km since the
previous one) is therefore **noisy** and must not be read in isolation.
Consumption is measured **in aggregate** — total litres over total distance
across a wide window (yearly, or a rolling block of fill-ups) — where the
tank-level boundary effect averages out. The odometer is the reliable
monotonic anchor of the dataset.

## Data

`data/raw/fuel_log_1999_2026.csv`

| Column   | Description                                          |
|----------|------------------------------------------------------|
| ID       | Sequential row id (ordered by odometer)              |
| KM       | Odometer reading (cumulative km, monotonic)          |
| Litros   | Litres refuelled                                     |
| Importe  | Amount paid (raw)                                     |
| Moneda   | Currency: `Pts` (until Jan 2002) or `EUR`            |
| Fecha    | Refuelling date (DD/MM/YYYY)                          |
| Marca    | Station brand (Shell, Cepsa, BP, Repsol, Mobil, ...) |
| Lugar    | Station location                                      |
| Notas    | Correction trail and observations                    |

A few rows have missing litres or odometer readings (never written down in
the logbook); they are kept, not dropped, and handled explicitly downstream.

## Repository structure

```
galloper-fuel-analysis/
├── data/
│   ├── raw/          # immutable source CSV
│   ├── interim/      # intermediate (git-ignored)
│   └── processed/    # analysis-ready parquet (git-ignored)
├── notebooks/
│   ├── 01_cleaning_features.ipynb   # typing, currency, features, QA
│   ├── 02_eda.ipynb                 # distributions, gaps, seasonality
│   ├── 03_fuel_price.ipynb          # price 1999-2026, nominal vs real
│   ├── 04_consumption_usage.ipynb   # aggregate economy, km/year, ageing
│   ├── 05_stations_brands.ipynb     # brand share, price by brand/place
│   └── 06_premium_diesel_impact.ipynb  # change-points + CausalImpact
├── src/galloper/     # reusable code (config, io, cleaning, features, viz)
├── reports/figures/  # generated charts (git-ignored)
├── requirements.txt
└── README.md
```

## Getting started

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
jupyter lab            # start with notebooks/01_cleaning_features.ipynb
```

Notebooks import the helper package via `sys.path.append("../src")`.

## Tech stack

Python · pandas · statsmodels · ruptures · CausalImpact · matplotlib / seaborn

## Status

Work in progress. Notebook 01 (cleaning + feature engineering) is functional;
EDA and modelling notebooks are being developed.

## Author

**Diego Marrero Ferrera** — BSc in Data Science and Engineering (ULPGC, 2026).
GitHub: [DieGodMF4](https://github.com/DieGodMF4)
