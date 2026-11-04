"""Tests for src/windtools.py."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.append(str(Path(__file__).parents[1] / "src"))

import windtools as wt


@pytest.mark.parametrize(
    "year, expected_kwh",
    [
        (2020, 8784),  # leap year
        (2021, 8760),
    ],
)
def test_annual_energy_constant_1_kw(year, expected_kwh):
    hours = pd.date_range(f"{year}-01-01 00:00", f"{year}-12-31 23:00", freq="h")
    power = pd.Series(1.0, index=hours)

    energy = wt.annual_energy(power)

    assert list(energy.index) == [year]
    assert energy.loc[year] == pytest.approx(expected_kwh)


def test_power_curve_returns_nan_for_nan_wind_speed():
    ws = np.array([np.nan, 2.0, 3.0, 7.5, 12.0, 20.0, 25.0, 30.0])

    cf = wt.power_curve(ws)

    expected_cubic = (7.5**3 - 3**3) / (12**3 - 3**3)
    assert np.isnan(cf[0])
    assert cf[1:] == pytest.approx([0.0, 0.0, expected_cubic, 1.0, 1.0, 0.0, 0.0])


def test_find_low_wind_events_does_not_count_nan_hours():
    # 30 low hours + 20 NaN hours + 30 low hours, between windy periods. If NaN
    # hours counted as low wind, this would be one 80-hour event. Without them,
    # neither 30-hour run reaches the 48-hour minimum.
    values = [0.5] * 5 + [0.05] * 30 + [np.nan] * 20 + [0.05] * 30 + [0.5] * 5
    hours = pd.date_range("2020-01-01 00:00", periods=len(values), freq="h")
    cf = pd.Series(values, index=hours)

    events = wt.find_low_wind_events(cf, threshold=0.10, min_hours=48)

    assert len(events) == 0


def test_annual_energy_is_nan_for_year_with_missing_power():
    hours = pd.date_range("2020-01-01 00:00", "2021-12-31 23:00", freq="h")
    power = pd.Series(1.0, index=hours)
    power.loc["2020-06-01 12:00"] = np.nan

    energy = wt.annual_energy(power)

    assert np.isnan(energy.loc[2020])
    assert energy.loc[2021] == pytest.approx(8760)
