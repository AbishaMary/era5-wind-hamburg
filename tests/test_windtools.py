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


def test_wind_direction_northerly_is_0_or_360():
    # u=0, v=-5 blows towards the south, so the wind comes from the north.
    direction = wt.wind_direction(0.0, -5.0)

    assert min(direction, 360 - direction) == pytest.approx(0, abs=1e-9)


@pytest.mark.parametrize(
    "u, v, expected_degrees",
    [
        (-5.0, 0.0, 90),   # blowing west, so from the east
        (0.0, 5.0, 180),   # blowing north, so from the south
        (5.0, 0.0, 270),   # blowing east, so from the west
    ],
)
def test_wind_direction_cardinal_points(u, v, expected_degrees):
    assert wt.wind_direction(u, v) == pytest.approx(expected_degrees)


def test_wind_direction_random_values_stay_between_0_and_360():
    rng = np.random.default_rng(42)
    u = rng.uniform(-30, 30, size=10_000)
    v = rng.uniform(-30, 30, size=10_000)

    direction = wt.wind_direction(u, v)

    assert np.all((direction >= 0) & (direction <= 360))
