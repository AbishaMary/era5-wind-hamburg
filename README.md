# Wind energy variability and low-wind risk at Hamburg (ERA5, 2005–2024)

How often does wind power "go quiet" near Hamburg, for how long, and when?
This project uses 20 years of hourly reanalysis data to quantify low-wind events relevant for energy system planning, storage sizing and power trading.

## Key findings

- **Frequency:** Periods where a wind turbine produces less than 10% of its capacity for at least two days occur about 16 times per year (range 11–23 across years).
- **Season:** They are most common in July, Augut and Sepetember because the winds are calmer during summer.
- **Duration:** A typical event lasts 66 hours (2 days, 18 hours); the longest lasted 11 days (January 2017). An event of 9 days occurs roughly once every 10 years.

![Low-wind events at Hamburg](figures/low_wind.png)

## Data

- ERA5 hourly reanalysis (ECMWF / Copernicus), 100 m wind components
  u100 and v100, 2005–2024
- Grid point nearest Hamburg: [lat]°N, [lon]°E
- Raw data is not included in this repository (download from the
  Copernicus Climate Data Store).

## Method

1. Wind speed and direction from u100/v100; Weibull fit of the speed distribution.
2. Hourly capacity factor from a generic turbine power curve
   (cut-in 3 m/s, rated 12 m/s, cut-out 25 m/s).
3. Low-wind event: hourly capacity factor < 10% for ≥ 48 consecutive hours.
4. Event statistics: frequency, seasonality, duration distribution.
5. Empirical return periods of the longest event per year.
6. Sensitivity of results to the event definition (threshold and minimum duration).

Definitions and details: [docs/methods.md](docs/methods.md)

## Limitations

- ERA5 (~30 km grid) tends to underestimate onshore wind speeds;
  absolute capacity factors are indicative, relative patterns more robust.
- Generic power curve; no air-density correction, wake or availability losses.
- 20 years limits return-period estimates to roughly 10–20 years.

## Repository structure

    notebooks/01_low_wind_events.ipynb   analysis of low-wind events
    src/windtools.py                     reusable functions (power curve, event detection)
    figures/                             saved figures
    docs/methods.md                      definitions and methods

## How to run

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

Place the ERA5 NetCDF file in `data/raw/` and run the notebook.

## Next steps

- Notebook 2: interannual variability of energy yield and P50/P90 estimates (in progress)
- Wind power forecasting against observed generation data