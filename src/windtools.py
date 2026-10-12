"""Shared helpers: load ERA5 100 m wind, compute speed/direction, convert to capacity factor."""

from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr


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
    numpy array of capacity factor values between 0 and 1.
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
    return np.select(conditions, values)


def add_capacity_factor(df, **curve_kwargs):
    df = df.copy()
    df["cf"] = power_curve(df["ws100"], **curve_kwargs)
    return df


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
        [8784 if pd.Timestamp(year=y, month=12, day=31).dayofyear == 366 else 8760 for y in counts.index],
        index=counts.index,
    )
    good = counts.index[counts / expected >= min_coverage]
    return df[df.index.year.isin(good)]
