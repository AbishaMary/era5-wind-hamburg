"""Topic #3: low-wind ("Dunkelflaute"-style) events at Hamburg from 20 years of ERA5.

A low-wind event = a run of consecutive hours with capacity factor below a threshold,
lasting at least a minimum duration. Outputs event statistics and figures.

Run from the repo root:
    python analysis/01_low_wind_events.py --data "data/raw/*.nc"
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from windtools import add_capacity_factor, complete_years, load_era5_wind  # noqa: E402

FIG = Path("figures")
OUT = Path("results")


def find_events(cf, threshold, min_hours):
    """Return a DataFrame of events: start, end, duration (h), mean CF."""
    below = cf < threshold
    run_id = (below != below.shift()).cumsum()  # new id each time state flips
    runs = cf[below].groupby(run_id[below])
    events = pd.DataFrame({
        "start": runs.apply(lambda s: s.index[0]),
        "end": runs.apply(lambda s: s.index[-1]),
        "duration_h": runs.size(),
        "mean_cf": runs.mean(),
    })
    events = events[events["duration_h"] >= min_hours].reset_index(drop=True)
    return events


def empirical_return_periods(annual_max):
    """Weibull plotting position: T = (n + 1) / rank, rank 1 = largest."""
    s = annual_max.sort_values(ascending=False).reset_index(drop=True)
    n = len(s)
    return pd.DataFrame({"duration_h": s, "return_period_yr": (n + 1) / (s.index + 1)})


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="data/raw/*.nc", help="ERA5 NetCDF file or glob pattern")
    p.add_argument("--lat", type=float, default=53.55)
    p.add_argument("--lon", type=float, default=10.0)
    p.add_argument("--threshold", type=float, default=0.10, help="CF threshold for 'low wind'")
    p.add_argument("--min-hours", type=int, default=48, help="minimum event duration (h)")
    args = p.parse_args()
    FIG.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)

    df = complete_years(add_capacity_factor(load_era5_wind(args.data, args.lat, args.lon)))
    years = sorted(df.index.year.unique())
    print(f"Data: {df.index[0]} to {df.index[-1]}, {len(years)} complete years")
    print(f"Mean wind speed at 100 m: {df['ws100'].mean():.2f} m/s, mean CF: {df['cf'].mean():.3f}")

    events = find_events(df["cf"], args.threshold, args.min_hours)
    events["year"] = events["start"].dt.year
    events["month"] = events["start"].dt.month
    events.to_csv(OUT / "low_wind_events.csv", index=False)

    per_year = events.groupby("year").size().reindex(years, fill_value=0)
    annual_max = events.groupby("year")["duration_h"].max().reindex(years, fill_value=0)
    rp = empirical_return_periods(annual_max)

    print(f"\nEvents (CF < {args.threshold:.0%} for >= {args.min_hours} h): {len(events)} total, "
          f"{per_year.mean():.1f} per year (range {per_year.min()}-{per_year.max()})")
    print(f"Median duration: {events['duration_h'].median():.0f} h, longest: {events['duration_h'].max()} h "
          f"starting {events.loc[events['duration_h'].idxmax(), 'start']:%Y-%m-%d}")
    print(f"Share of all hours spent in such events: {events['duration_h'].sum() / len(df):.1%}")
    print("\nLongest event per year, empirical return periods:")
    print(rp.head(5).to_string(index=False))

    # --- Figures ---
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))

    ax = axes[0, 0]
    per_year.plot.bar(ax=ax, color="tab:blue")
    ax.set(title="Low-wind events per year", xlabel="", ylabel="count")

    ax = axes[0, 1]
    by_month = events.groupby("month").size().reindex(range(1, 13), fill_value=0)
    ax.bar(by_month.index, by_month.values / len(years), color="tab:orange")
    ax.set(title="Seasonality (events starting per month, per year)", xlabel="month",
           ylabel="events / year", xticks=range(1, 13))

    ax = axes[1, 0]
    ax.hist(events["duration_h"] / 24, bins=20, color="tab:green")
    ax.set(title="Event duration distribution", xlabel="duration (days)", ylabel="count")

    ax = axes[1, 1]
    ax.semilogx(rp["return_period_yr"], rp["duration_h"] / 24, "o-")
    ax.set(title="Longest event per year vs return period", xlabel="return period (years)",
           ylabel="duration (days)")
    ax.grid(True, which="both", alpha=0.3)

    fig.suptitle(f"Low-wind events at Hamburg (ERA5 100 m): CF < {args.threshold:.0%} "
                 f"for ≥ {args.min_hours} h", fontsize=13)
    fig.tight_layout()
    fig.savefig(FIG / "01_low_wind_events.png", dpi=150)
    print(f"\nSaved {FIG / '01_low_wind_events.png'} and {OUT / 'low_wind_events.csv'}")


if __name__ == "__main__":
    main()
