"""Shared helpers for wind energy analysis.

- power_curve, add_capacity_factor: wind speed to capacity factor
- wind_direction: meteorological wind direction from u and v components
- annual_energy, p_values: energy per calendar year and P50/P90 statistics
- find_low_wind_events: consecutive low-capacity-factor periods
- complete_years: remove years with too few hourly values
"""

import numpy as np
import pandas as pd


def power_curve(ws, cut_in=3.0, rated=12.0, cut_out=25.0):
    """Normalised power output (0-1) of a generic wind turbine.

    Parameters
    ----------
    ws : float, array or pandas Series
        Wind speed at hub height (m/s).
    cut_in, rated, cut_out : float
        Turbine speeds (m/s).

    Returns
    -------
    numpy array of capacity factor values between 0 and 1, with NaN where the
    wind speed is NaN.
    """
    ws = np.asarray(ws, dtype=float)

    conditions = [
        ws < cut_in,                      # too little wind
        (ws >= cut_in) & (ws < rated),    # cubic rise
        (ws >= rated) & (ws < cut_out),   # full power
        ws >= cut_out,                    # shut down for safety
    ]
    values = [
        0.0,
        (ws**3 - cut_in**3) / (rated**3 - cut_in**3),
        1.0,
        0.0,
    ]
    return np.select(conditions, values, default=np.nan)   # NaN meets no condition


def wind_direction(u, v):
    """Meteorological wind direction: where the wind comes from.

    Parameters
    ----------
    u, v : float, array or pandas Series
        Eastward and northward wind components (m/s).

    Returns
    -------
    Direction in degrees clockwise from north, between 0 and 360
    (0 = from the north, 90 = from the east), with the same type as the input.
    """
    return np.degrees(np.arctan2(-u, -v)) % 360


def add_capacity_factor(df, **curve_kwargs):
    df = df.copy()
    df["cf"] = power_curve(df["ws100"], **curve_kwargs)
    return df


def annual_energy(power):
    """Calculate energy per calendar year from a power time series.

    Parameters
    ----------
    power : pandas Series
        Power in kW, with a sorted, duplicate-free DatetimeIndex.

    Returns
    -------
    pandas Series of energy in kWh, indexed by year. A year containing a NaN
    power value is NaN.

    The time step is the median spacing of the index. Each value counts for one
    time step, so timestamps absent from the index add no energy.
    """
    if not isinstance(power.index, pd.DatetimeIndex):
        raise TypeError("power must have a DatetimeIndex")
    if len(power) < 2:
        raise ValueError("power must contain at least two values to infer the time step")
    if not power.index.is_monotonic_increasing or not power.index.is_unique:
        raise ValueError("power index must be sorted and contain no duplicates")

    step_hours = power.index.to_series().diff().median() / pd.Timedelta(hours=1)
    energy = (power * step_hours).groupby(power.index.year).apply(
        lambda values: values.sum(skipna=False)
    )
    energy.index.name = "year"
    return energy.rename("energy_kwh")


def p_values(annual_energy, horizon_years=1):
    """Calculate P50, sample standard deviation, and horizon-adjusted P90.

    Returns a Series containing energy values in the input units and the
    standard deviation and P90 as percentages of P50.
    """
    if horizon_years < 1:
        raise ValueError("horizon_years must be at least 1")

    annual_energy = pd.Series(annual_energy).dropna()
    if len(annual_energy) < 2:
        raise ValueError("annual_energy must contain at least two valid values")

    p50 = annual_energy.mean()
    if p50 == 0:
        raise ValueError("P50 must be non-zero to calculate percentages of P50")

    sigma_annual = annual_energy.std(ddof=1)
    sigma = sigma_annual / np.sqrt(horizon_years)   # spread of the N-year average
    p90 = p50 - 1.282 * sigma
    return pd.Series({
        "p50": p50,
        "sigma": sigma,
        "sigma_pct_p50": sigma / p50 * 100,
        "p90": p90,
        "p90_pct_p50": p90 / p50 * 100,
    })


def find_low_wind_events(cf, threshold=0.10, min_hours=48):
    """Find consecutive low-capacity-factor events in a time-indexed Series."""
    below = cf.lt(threshold) & cf.notna()
    run_id = below.ne(below.shift(fill_value=False)).cumsum()
    runs = cf[below].groupby(run_id[below])
    events = pd.DataFrame({
        "start": runs.apply(lambda values: values.index[0]),
        "end": runs.apply(lambda values: values.index[-1]),
        "duration_h": runs.size(),
        "mean_cf": runs.mean(),
    })
    return events[events["duration_h"] >= min_hours].reset_index(drop=True)


def complete_years(df, min_coverage=0.95):
    """Keep only calendar years with at least `min_coverage` of hourly data present."""
    counts = df.groupby(df.index.year).size()
    expected = pd.Series(
        [8784 if pd.Timestamp(year=y, month=12, day=31).day_of_year == 366 else 8760 for y in counts.index],
        index=counts.index,
    )
    good = counts.index[counts / expected >= min_coverage]
    return df[df.index.year.isin(good)]
