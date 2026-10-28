# Wind energy variability and low-wind risk at Hamburg (ERA5, 2005–2025)

How often does wind power "go quiet" near Hamburg, how much does annual
wind energy vary, and what yield can be relied on? This project uses
21 years of hourly reanalysis data to quantify low-wind events and
interannual yield variability (P50/P90), relevant for energy system
planning, project financing and power trading.

## Key findings

### Low-wind events (notebook 1)

- **Frequency:** Periods where a wind turbine produces less than 10% of its rated capacity for at least two days occur about 16 times per year (range 11–23 across years).
- **Season:** They are most common in July, August and September likely because weaker storm activity in summer.
- **Duration:** A typical event lasts 66 hours (2 days, 18 hours); the longest lasted 11 days (January 2017). An event of 9 days occurs roughly once every 10 years.

### Energy yield variability (notebook 2)

- **Typical year and spread:** A generic 5 MW turbine would produce about
  9.25 GWh per year (P50, capacity factor ≈ 21%); individual years vary
  by about ±9%.
- **Bankable estimate:** In 9 out of 10 years, output exceeds 8.21 GWh
  (P90, 89% of P50). Averaged over 10 years, P90 rises to 96% of P50.
- **Why long records matter:** A single year can misrepresent the
  long-term yield by up to 28%; a decade of data narrows this to about 4%.
  1% more wind speed gives about 3% more energy.

## Data

- ERA5 hourly reanalysis (ECMWF / Copernicus), 100 m wind components
  u100 and v100, 2005–2024
  (Contains modified Copernicus Climate Change Service information (2025). Hersbach et al. (2020), ERA5 hourly data on single levels, Copernicus Climate Data Store.)
- Grid point nearest Hamburg: [53.5]°N, [10]°E
- Raw data is not included in this repository (download from the
  Copernicus Climate Data Store).

## Method

**Notebook 1 – Low wind events**

1. Wind speed and direction from u100/v100; Weibull fit of the speed distribution.
2. Hourly capacity factor from a generic turbine power curve
   (cut-in 3 m/s, rated 12 m/s, cut-out 25 m/s).
3. Low-wind event: hourly capacity factor < 10% for ≥ 48 consecutive hours.
4. Event statistics: frequency, seasonality, duration distribution.
5. Empirical return periods of the longest event per year.
6. Sensitivity of results to the event definition (threshold and minimum duration).

**Notebook 2 – Yield variability**
1. Annual energy for a 5 MW turbine from mean capacity factor.
2. P50 (mean) and P90 for 1- and 10-year horizons (normal assumption,
   checked with a Q–Q plot and empirical percentile).
3. Energy–wind speed elasticity from a log–log fit.
4. Seasonal cycle and month-to-month variability.
5. Convergence of multi-year averages, lag-1 autocorrelation, and trend test.


## Limitations

**Notebook 1 – Low wind events**

- ERA5 (~30 km grid) tends to underestimate onshore wind speeds;
  absolute capacity factors are indicative, relative patterns more robust.
- Generic power curve; no air-density correction, wake or availability losses.
- 20 years limits return-period estimates to roughly 10–20 years.

**Notebook 2 – Yield variability**

- P90 includes interannual variability only; real assessments add
  measurement, modelling and loss uncertainties.
- Normal distribution and independent years are assumed (supported by
  the data, but tested with only 21 years).

## Repository structure

notebooks/01_low_wind_events.ipynb     low-wind event analysis
notebooks/02_yield_variability.ipynb   yield variability and P50/P90
src/windtools.py                       reusable functions
figures/                               saved figures
requirements.txt                       Python dependencies

## How to run

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

Place the ERA5 NetCDF file in `data/raw/` and run the notebook.

## Next steps

- Wind power forecasting against observed generation data
- Link low-frequency variability to the NAO using EEMD