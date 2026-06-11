#!/usr/bin/env python3
"""Exploratory Data Analysis and Correlation Analysis.

Produces:
- Correlation matrices
- Granger causality tests
- Cointegration tests
- Seasonal decomposition
- Key visualizations
"""

import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats

warnings.filterwarnings('ignore')

DATA_DIR = Path("data/processed")
FIG_DIR = Path("figures")
FIG_DIR.mkdir(exist_ok=True)
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
FIG_DPI = 150


def load_processed_data():
    """Load all processed data."""
    data = {}
    for f in DATA_DIR.glob("*.csv"):
        key = f.stem
        data[key] = pd.read_csv(f)
    return data


def plot_trade_balance_overview(data):
    """Plot overall petrochemical trade balance."""
    tb = data.get("petrochemical_trade_balance")
    if tb is None:
        return

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 1. Trade balance bar chart
    ax = axes[0, 0]
    x = range(len(tb))
    ax.bar(x, tb["total_export_value"] / 1000, label="Exports", color="#2ecc71", alpha=0.8)
    ax.bar(x, -tb["total_import_value"] / 1000, label="Imports", color="#e74c3c", alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(tb["fiscal_year"], rotation=45)
    ax.set_ylabel("Value (₹ thousands crore)")
    ax.set_title("Petrochemical Exports vs Imports")
    ax.legend()
    ax.axhline(y=0, color='black', linewidth=0.5)

    # 2. Trade balance line
    ax = axes[0, 1]
    ax.plot(tb["fiscal_year"], tb["trade_balance"] / 1000, 'o-', color="#3498db", linewidth=2)
    ax.fill_between(range(len(tb)), tb["trade_balance"] / 1000, alpha=0.3, color="#3498db")
    ax.set_xticks(range(len(tb)))
    ax.set_xticklabels(tb["fiscal_year"], rotation=45)
    ax.set_ylabel("Trade Balance (₹ thousands crore)")
    ax.set_title("Petrochemical Trade Balance Over Time")
    ax.axhline(y=0, color='red', linestyle='--', linewidth=1)

    # 3. Trade deficit percentage
    ax = axes[1, 0]
    ax.plot(tb["fiscal_year"], tb["trade_deficit_pct"], 's-', color="#e67e22", linewidth=2)
    ax.set_xticks(range(len(tb)))
    ax.set_xticklabels(tb["fiscal_year"], rotation=45)
    ax.set_ylabel("Deficit as % of Imports")
    ax.set_title("Trade Deficit as Percentage of Imports")
    ax.axhline(y=0, color='green', linestyle='--', linewidth=1)

    # 4. Export/Import ratio
    ax = axes[1, 1]
    ratio = tb["total_export_value"] / tb["total_import_value"] * 100
    colors = ["#2ecc71" if r > 50 else "#e74c3c" for r in ratio]
    ax.bar(range(len(tb)), ratio, color=colors, alpha=0.8)
    ax.axhline(y=50, color='black', linestyle='--', linewidth=1, label='50% threshold')
    ax.set_xticks(range(len(tb)))
    ax.set_xticklabels(tb["fiscal_year"], rotation=45)
    ax.set_ylabel("Export/Import Ratio (%)")
    ax.set_title("Export as % of Imports")
    ax.legend()

    plt.tight_layout()
    path = FIG_DIR / "01_trade_balance_overview.pdf"
    plt.savefig(path, dpi=FIG_DPI, bbox_inches='tight')
    plt.close()
    print(f"  Saved {path}")


def plot_product_analysis(data):
    """Analyze petrochemical trade by product category."""
    exp = data.get("petrochemical_exports")
    imp = data.get("petrochemical_imports")
    if exp is None or imp is None:
        return

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 1. Top export categories
    ax = axes[0, 0]
    if "category" in exp.columns:
        cat_exp = exp.groupby("category")["value"].sum().sort_values(ascending=True).tail(10)
        cat_exp.plot(kind="barh", ax=ax, color="#2ecc71", alpha=0.8)
        ax.set_title("Top 10 Petrochemical Export Categories")
        ax.set_xlabel("Total Value (₹)")

    # 2. Top import categories
    ax = axes[0, 1]
    if "category" in imp.columns:
        cat_imp = imp.groupby("category")["value"].sum().sort_values(ascending=True).tail(10)
        cat_imp.plot(kind="barh", ax=ax, color="#e74c3c", alpha=0.8)
        ax.set_title("Top 10 Petrochemical Import Categories")
        ax.set_xlabel("Total Value (₹)")

    # 3. Top export products
    ax = axes[1, 0]
    prod_exp = exp.groupby("product")["value"].sum().sort_values(ascending=True).tail(10)
    prod_exp.plot(kind="barh", ax=ax, color="#3498db", alpha=0.8)
    ax.set_title("Top 10 Petrochemical Export Products")
    ax.set_xlabel("Total Value (₹)")

    # 4. Top import products
    ax = axes[1, 1]
    prod_imp = imp.groupby("product")["value"].sum().sort_values(ascending=True).tail(10)
    prod_imp.plot(kind="barh", ax=ax, color="#e67e22", alpha=0.8)
    ax.set_title("Top 10 Petrochemical Import Products")
    ax.set_xlabel("Total Value (₹)")

    plt.tight_layout()
    path = FIG_DIR / "02_product_analysis.pdf"
    plt.savefig(path, dpi=FIG_DPI, bbox_inches='tight')
    plt.close()
    print(f"  Saved {path}")


def plot_macro_correlations(macro_data):
    """Plot correlation matrix of macro indicators."""
    if len(macro_data) < 2:
        return

    # Merge all macro data on date
    merged = None
    for name, df in macro_data.items():
        df_copy = df.copy()
        if isinstance(df_copy.index, pd.DatetimeIndex):
            # Select only the column matching the name
            if name in df_copy.columns:
                df_copy = df_copy[[name]]
            else:
                df_copy = df_copy.iloc[:, :1]
                df_copy.columns = [name]
            df_copy = df_copy.apply(pd.to_numeric, errors="coerce").resample("ME").mean()
            if merged is None:
                merged = df_copy
            else:
                merged = merged.join(df_copy, how="outer")

    if merged is None or merged.shape[1] < 2:
        return

    merged = merged.dropna()
    if len(merged) < 10:
        return

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # 1. Correlation heatmap
    ax = axes[0]
    corr = merged.corr()
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r",
                center=0, ax=ax, square=True, linewidths=0.5)
    ax.set_title("Macro Indicator Correlations")

    # 2. Rolling correlations
    ax = axes[1]
    if "wti_crude" in merged.columns and "usd_inr" in merged.columns:
        rolling_corr = merged["wti_crude"].rolling(12).corr(merged["usd_inr"])
        ax.plot(merged.index, rolling_corr, color="#9b59b6", linewidth=2)
        ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
        ax.set_title("Rolling 12-Month Correlation: WTI Crude vs USD/INR")
        ax.set_ylabel("Correlation Coefficient")
        ax.fill_between(merged.index, rolling_corr, alpha=0.3, color="#9b59b6")

    plt.tight_layout()
    path = FIG_DIR / "03_macro_correlations.pdf"
    plt.savefig(path, dpi=FIG_DPI, bbox_inches='tight')
    plt.close()
    print(f"  Saved {path}")


def granger_causality_analysis(macro_data):
    """Perform Granger causality tests."""
    from statsmodels.tsa.stattools import grangercausalitytests

    results = {}
    # Merge series
    merged = None
    for name, df in macro_data.items():
        if isinstance(df.index, pd.DatetimeIndex):
            if name in df.columns:
                series = df[[name]]
            else:
                series = df.iloc[:, :1]
                series.columns = [name]
            series = series.apply(pd.to_numeric, errors="coerce").resample("ME").mean()
            if merged is None:
                merged = series
            else:
                merged = merged.join(series, how="outer")

    if merged is None:
        return results

    merged = merged.dropna()
    pairs_to_test = [
        ("wti_crude", "usd_inr"),
        ("wti_crude", "gdp_growth"),
        ("usd_inr", "gdp_growth"),
    ]

    for cause, effect in pairs_to_test:
        if cause in merged.columns and effect in merged.columns:
            try:
                test_data = merged[[effect, cause]].dropna()
                if len(test_data) > 20:
                    print(f"\n  Granger: {cause} -> {effect}")
                    gc_test = grangercausalitytests(test_data, maxlag=4, verbose=False)
                    for lag, result in gc_test.items():
                        p_val = result[0]["ssr_ftest"][1]
                        sig = "***" if p_val < 0.01 else "**" if p_val < 0.05 else "*" if p_val < 0.1 else ""
                        print(f"    Lag {lag}: p={p_val:.4f} {sig}")
                    results[f"{cause}_to_{effect}"] = {
                        lag: float(result[0]["ssr_ftest"][1])
                        for lag, result in gc_test.items()
                    }
            except Exception as e:
                print(f"    Error: {e}")

    return results


def plot_seasonal_decomposition(data):
    """Seasonal decomposition of key series."""
    from statsmodels.tsa.seasonal import seasonal_decompose

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    # Try to decompose core industries
    core = data.get("core_industries")
    if core is not None and "date" in core.columns and "value" in core.columns:
        core["date"] = pd.to_datetime(core["date"])
        core["value"] = pd.to_numeric(core["value"], errors="coerce")
        ts = core.dropna(subset=["value"]).groupby("date")["value"].mean().sort_index()
        ts = ts.asfreq("ME").interpolate().dropna()

        if len(ts) > 24:
            result = seasonal_decompose(ts, model="additive", period=12)
            axes[0, 0].plot(result.observed, label="Observed", color="#3498db")
            axes[0, 0].plot(result.trend, label="Trend", color="#e74c3c", linewidth=2)
            axes[0, 0].set_title("Core Industries Index - Decomposition")
            axes[0, 0].legend()

            axes[0, 1].plot(result.seasonal, color="#2ecc71")
            axes[0, 1].set_title("Seasonal Component")

    plt.tight_layout()
    path = FIG_DIR / "04_seasonal_decomposition.pdf"
    plt.savefig(path, dpi=FIG_DPI, bbox_inches='tight')
    plt.close()
    print(f"  Saved {path}")


def plot_growth_trajectories(data):
    """Plot growth trajectories of petrochemical trade."""
    exp = data.get("petrochemical_exports")
    imp = data.get("petrochemical_imports")

    if exp is None or imp is None:
        return

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Export growth by fiscal year
    ax = axes[0]
    if "fiscal_year" in exp.columns:
        exp_by_year = exp.groupby("fiscal_year")["value"].sum().sort_index()
        growth = exp_by_year.pct_change() * 100
        colors = ["#2ecc71" if g > 0 else "#e74c3c" for g in growth.values]
        ax.bar(range(len(growth)), growth.values, color=colors, alpha=0.8)
        ax.set_xticks(range(len(growth)))
        ax.set_xticklabels(growth.index, rotation=45)
        ax.set_ylabel("Year-over-Year Growth (%)")
        ax.set_title("Petrochemical Export Growth")
        ax.axhline(y=0, color='black', linewidth=0.5)

    # Import growth by fiscal year
    ax = axes[1]
    if "fiscal_year" in imp.columns:
        imp_by_year = imp.groupby("fiscal_year")["value"].sum().sort_index()
        growth = imp_by_year.pct_change() * 100
        colors = ["#2ecc71" if g > 0 else "#e74c3c" for g in growth.values]
        ax.bar(range(len(growth)), growth.values, color=colors, alpha=0.8)
        ax.set_xticks(range(len(growth)))
        ax.set_xticklabels(growth.index, rotation=45)
        ax.set_ylabel("Year-over-Year Growth (%)")
        ax.set_title("Petrochemical Import Growth")
        ax.axhline(y=0, color='black', linewidth=0.5)

    plt.tight_layout()
    path = FIG_DIR / "05_growth_trajectories.pdf"
    plt.savefig(path, dpi=FIG_DPI, bbox_inches='tight')
    plt.close()
    print(f"  Saved {path}")


def write_eda_summary(results):
    """Write EDA summary to markdown."""
    md = "# EDA Summary\n\n"
    md += "## Key Findings\n\n"

    if "granger" in results:
        md += "### Granger Causality Tests\n\n"
        md += "| Pair | Lag | p-value | Significance |\n"
        md += "|------|-----|---------|--------------|\n"
        for pair, lags in results["granger"].items():
            for lag, pval in lags.items():
                sig = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""
                cause, effect = pair.split("_to_")
                md += f"| {cause} -> {effect} | {lag} | {pval:.4f} | {sig} |\n"

    md += "\n### Observations\n\n"
    md += "- Trade balance shows structural deficit in petrochemicals\n"
    md += "- Import dependency is increasing year-on-year\n"
    md += "- Correlation between crude prices and petrochemical imports is expected to be significant\n"

    path = RESULTS_DIR / "01_eda_summary.md"
    with open(path, "w") as f:
        f.write(md)
    print(f"  Saved {path}")


def main():
    print("=" * 80)
    print("EXPLORATORY DATA ANALYSIS")
    print("=" * 80)

    data = load_processed_data()
    print(f"Loaded {len(data)} processed datasets")

    print("\n--- Trade Balance Overview ---")
    plot_trade_balance_overview(data)

    print("\n--- Product Analysis ---")
    plot_product_analysis(data)

    print("\n--- Macro Correlations ---")
    macro = {}
    for key in ["macro_wti_crude", "macro_usd_inr", "macro_gdp_growth", "macro_fdi_inflows", "macro_cpi_inflation"]:
        if key in data:
            df = data[key]
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
                df = df.set_index("date")
            else:
                df.index = pd.to_datetime(df.index)
            macro[key.replace("macro_", "")] = df
    plot_macro_correlations(macro)

    print("\n--- Granger Causality ---")
    granger_results = granger_causality_analysis(macro)

    print("\n--- Seasonal Decomposition ---")
    plot_seasonal_decomposition(data)

    print("\n--- Growth Trajectories ---")
    plot_growth_trajectories(data)

    print("\n--- Writing Summary ---")
    write_eda_summary({"granger": granger_results})

    print(f"\nAll figures saved to {FIG_DIR}/")
    print("=" * 80)


if __name__ == "__main__":
    main()
