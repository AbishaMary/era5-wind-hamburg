"""Topic #4: interannual variability of wind energy yield and P50/P90 at Hamburg.

Converts ERA5 100 m wind to capacity factor with a generic power curve, then computes
annual energy for a hypothetical turbine, year-to-year variability, P50/P90 for
1-year and 10-year horizons, and how the long-term mean converges with record length.

Run from the repo root:
    python analysis/02_yield_variability.py --data "data/raw/*.nc"
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
Z90 = 1.2816  # one-sided 90% exceedance for a normal distribution


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="data/raw/*.nc", help="ERA5 NetCDF file or glob pattern")
    p.add_argument("--lat", type=float, default=53.55)
    p.add_argument("--lon", type=float, default=10.0)
    p.add_argument("--rated-mw", type=float, default=5.0, help="turbine rated power (MW)")
    args = p.parse_args()
    FIG.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)

    df = complete_years(add_capacity_factor(load_era5_wind(args.data, args.lat, args.lon)))

    # Annual statistics. Use mean CF x 8760 h so leap years don't inflate energy.
    annual = df.groupby(df.index.year).agg(mean_ws=("ws100", "mean"), cf=("cf", "mean"))
    annual["energy_gwh"] = annual["cf"] * args.rated_mw * 8760 / 1000
    annual.index.name = "year"
    annual.to_csv(OUT / "annual_yield.csv")

    n = len(annual)
    p50 = annual["energy_gwh"].mean()
    sigma = annual["energy_gwh"].std(ddof=1)
    sigma_rel = sigma / p50
    p90_1y = p50 - Z90 * sigma
    p90_10y = p50 - Z90 * sigma / np.sqrt(10)

    # Sensitivity of energy to wind speed: % change in energy per % change in wind speed
    slope = np.polyfit(np.log(annual["mean_ws"]), np.log(annual["energy_gwh"]), 1)[0]

    print(f"{n} complete years ({annual.index.min()}-{annual.index.max()}), "
          f"{args.rated_mw:.0f} MW generic turbine at 100 m\n")
    print(annual.round(3).to_string())
    print(f"\nLong-term mean CF: {annual['cf'].mean():.3f}")
    print(f"P50 annual energy: {p50:.2f} GWh")
    print(f"Interannual variability: {sigma:.2f} GWh ({sigma_rel:.1%} of P50)")
    print(f"P90, 1-year horizon:  {p90_1y:.2f} GWh ({p90_1y / p50:.1%} of P50)")
    print(f"P90, 10-year horizon: {p90_10y:.2f} GWh ({p90_10y / p50:.1%} of P50)")
    print(f"Energy-to-wind sensitivity: 1% more wind speed -> {slope:.1f}% more energy")
    print(f"Best year {annual['energy_gwh'].idxmax()}, worst year {annual['energy_gwh'].idxmin()} "
          f"({annual['energy_gwh'].min() / p50 - 1:+.1%} vs P50)")
    print("\nNote: only interannual variability is included; a real P90 also adds model, "
          "measurement and loss uncertainties.")

    # Convergence: spread of the N-year mean across all possible N-year windows
    conv = []
    for w in range(1, n + 1):
        means = annual["energy_gwh"].rolling(w).mean().dropna()
        conv.append((w, (means.max() - means.min()) / p50 * 100))
    conv = pd.DataFrame(conv, columns=["years", "range_pct"])

    # --- Figures ---
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))

    ax = axes[0, 0]
    colors = np.where(annual["energy_gwh"] >= p50, "tab:blue", "tab:red")
    ax.bar(annual.index, annual["energy_gwh"], color=colors)
    ax.axhline(p50, color="k", lw=1, label=f"P50 = {p50:.1f} GWh")
    ax.axhline(p90_1y, color="k", ls="--", lw=1, label=f"P90 (1 yr) = {p90_1y:.1f} GWh")
    ax.set(title="Annual energy yield", ylabel="GWh / year")
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.legend(fontsize=8)

    ax = axes[0, 1]
    ax.scatter(annual["mean_ws"], annual["energy_gwh"])
    for y, r in annual.iterrows():
        ax.annotate(str(y)[2:], (r["mean_ws"], r["energy_gwh"]), fontsize=7)
    ax.set(title=f"Energy vs mean wind speed (elasticity ≈ {slope:.1f})",
           xlabel="annual mean wind speed at 100 m (m/s)", ylabel="GWh / year")

    ax = axes[1, 0]
    monthly = df["cf"].groupby([df.index.year, df.index.month]).mean().unstack()
    ax.plot(monthly.columns, monthly.T.values, color="grey", alpha=0.3, lw=0.8)
    ax.plot(monthly.columns, monthly.mean(), color="tab:blue", lw=2.5, label="mean")
    ax.set(title="Monthly capacity factor (each line = one year)", xlabel="month",
           ylabel="capacity factor", xticks=range(1, 13))
    ax.legend(fontsize=8)

    ax = axes[1, 1]
    ax.plot(conv["years"], conv["range_pct"], "o-")
    ax.set(title="How many years for a stable long-term mean?",
           xlabel="averaging window (years)", ylabel="max-min of window means (% of P50)")
    ax.grid(alpha=0.3)

    fig.suptitle("Wind energy yield variability at Hamburg (ERA5 100 m)", fontsize=13)
    fig.tight_layout()
    fig.savefig(FIG / "02_yield_variability.png", dpi=150)
    print(f"\nSaved {FIG / '02_yield_variability.png'} and {OUT / 'annual_yield.csv'}")


if __name__ == "__main__":
    main()
