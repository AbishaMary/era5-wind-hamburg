"""Tests for src/windtools.py."""

import sys
from pathlib import Path

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
