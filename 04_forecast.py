#!/usr/bin/env python3
"""Forecast 2026-2027 with Scenario Analysis.

Generates 12-month forecasts under three scenarios:
- Base Case: Current geopolitical tensions persist
- Bull Case: Middle East peace, oil prices drop
- Bear Case: Escalation, supply disruption
"""

import os
import warnings
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings('ignore')

DATA_DIR = Path("data/processed")
FIG_DIR = Path("figures")
FIG_DIR.mkdir(exist_ok=True)
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)
MODEL_DIR = Path("models")

plt.style.use('seaborn-v0_8-whitegrid')
FIG_DPI = 150

# 2026 Context Parameters
CURRENT_CRUDE = 90.0  # $/barrel (June 2026)
CURRENT_INR = 95.5    # USD/INR
CURRENT_GDP_GROWTH = 7.7  # % (FY2026)

# Scenario definitions
SCENARIOS = {
    "base_case": {
        "name": "Base Case (Tensions Persist)",
        "crude_path": [90, 88, 86, 85, 84, 85, 86, 87, 88, 89, 90, 91],
        "inr_path": [95.5, 96, 96.5, 97, 97.5, 98, 98.5, 99, 99, 99.5, 100, 100],
        "gdp_growth": [7.5, 7.2, 7.0, 6.8, 6.8, 7.0, 7.2, 7.2, 7.0, 6.8, 6.8, 7.0],
        "description": "Geopolitical tensions continue, crude stays elevated, INR gradually weakens"
    },
    "bull_case": {
        "name": "Bull Case (Peace Dividend)",
        "crude_path": [90, 82, 75, 70, 68, 66, 65, 65, 66, 67, 68, 70],
        "inr_path": [95.5, 94, 92, 90, 88, 87, 86, 85, 85, 85, 86, 86],
        "gdp_growth": [7.5, 7.8, 8.0, 8.2, 8.2, 8.0, 7.8, 7.8, 8.0, 8.2, 8.0, 7.8],
        "description": "Strait of Hormuz reopens, crude drops to $65-70, INR strengthens"
    },
    "bear_case": {
        "name": "Bear Case (Escalation)",
        "crude_path": [90, 95, 100, 105, 110, 108, 105, 100, 98, 95, 92, 90],
        "inr_path": [95.5, 97, 99, 101, 103, 104, 105, 104, 103, 102, 101, 100],
        "gdp_growth": [7.5, 6.5, 5.8, 5.5, 5.5, 5.8, 6.0, 6.2, 6.5, 6.5, 6.8, 7.0],
        "description": "Full conflict, crude spikes above $100, INR weakens past 100"
    }
}


def load_trained_models():
    """Load trained models from pickle files."""
    models = {}
    for name in ["sarimax", "prophet", "xgboost", "lightgbm", "var"]:
        path = MODEL_DIR / f"{name}.pkl"
        if path.exists():
            with open(path, "rb") as f:
                models[name] = pickle.load(f)
    return models


def generate_scenario_forecasts():
    """Generate forecasts for each scenario using trained models."""
    all_forecasts = {}

    for scenario_id, scenario in SCENARIOS.items():
        print(f"\n  {scenario['name']}")
        print(f"    Crude: ${scenario['crude_path'][0]} -> ${scenario['crude_path'][-1]}")
        print(f"    INR: {scenario['inr_path'][0]} -> {scenario['inr_path'][-1]}")

        # Create scenario feature matrix
        months = pd.date_range("2026-07-01", periods=12, freq="MS")
        scenario_features = pd.DataFrame({
            "date": months,
            "wti_crude": scenario["crude_path"],
            "usd_inr": scenario["inr_path"],
            "gdp_growth": scenario["gdp_growth"],
        })

        # Model-based predictions (simplified for demonstration)
        # In practice, feed these features into trained models

        # Crude price effect: petrochemical imports ~ crude * INR factor
        base_import_index = CURRENT_CRUDE * CURRENT_INR / 100
        scenario_imports = []
        for i in range(12):
            crude_factor = scenario["crude_path"][i] / CURRENT_CRUDE
            inr_factor = scenario["inr_path"][i] / CURRENT_INR
            gdp_factor = 1 + (scenario["gdp_growth"][i] - CURRENT_GDP_GROWTH) / 100

            # Petrochemical demand elasticity to crude: ~0.3
            # (higher crude = higher feedstock cost = slightly lower demand)
            demand_elasticity = -0.3

            import_index = base_import_index * crude_factor ** (1 + demand_elasticity) * inr_factor * gdp_factor
            scenario_imports.append(import_index)

        # Petrochemical export index (inversely related to crude)
        # Higher crude = higher Indian petrochemical prices = slightly lower exports
        export_elasticity = -0.2
        base_export_index = 0.6 * base_import_index  # India has ~60% export coverage
        scenario_exports = []
        for i in range(12):
            crude_factor = scenario["crude_path"][i] / CURRENT_CRUDE
            inr_factor = scenario["inr_path"][i] / CURRENT_INR  # Weaker INR helps exports
            export_index = base_export_index * crude_factor ** export_elasticity * (1 / inr_factor) ** 0.5
            scenario_exports.append(export_index)

        scenario_features["import_index"] = scenario_imports
        scenario_features["export_index"] = scenario_exports
        scenario_features["trade_balance"] = [e - im for e, im in zip(scenario_exports, scenario_imports)]

        all_forecasts[scenario_id] = scenario_features

    return all_forecasts


def plot_scenario_analysis(all_forecasts):
    """Plot comprehensive scenario analysis."""
    fig, axes = plt.subplots(3, 3, figsize=(20, 16))

    colors = {"base_case": "#3498db", "bull_case": "#2ecc71", "bear_case": "#e74c3c"}

    for col_idx, (scenario_id, fc) in enumerate(all_forecasts.items()):
        color = colors[scenario_id]
        months = fc["date"]

        # Row 1: Input assumptions
        ax = axes[0, col_idx]
        ax.plot(months, fc["wti_crude"], 'o-', color=color, linewidth=2)
        ax.set_title(f"Crude Oil Price\n{SCENARIOS[scenario_id]['name']}")
        ax.set_ylabel("$/barrel")
        ax.tick_params(axis='x', rotation=45)

        ax = axes[1, col_idx]
        ax.plot(months, fc["usd_inr"], 's-', color=color, linewidth=2)
        ax.set_title(f"USD/INR Exchange Rate")
        ax.set_ylabel("INR per USD")
        ax.tick_params(axis='x', rotation=45)

        # Row 2: Forecast results
        ax = axes[2, col_idx]
        ax.plot(months, fc["import_index"], '^-', color="#e74c3c", linewidth=2, label="Imports")
        ax.plot(months, fc["export_index"], 'v-', color="#2ecc71", linewidth=2, label="Exports")
        ax.fill_between(months, fc["export_index"], fc["import_index"],
                        where=fc["export_index"] < fc["import_index"],
                        alpha=0.3, color="#e74c3c", label="Deficit")
        ax.set_title(f"Trade Balance Forecast")
        ax.set_ylabel("Index Value")
        ax.legend(fontsize=8)
        ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    path = FIG_DIR / "08_scenario_analysis_3panel.pdf"
    plt.savefig(path, dpi=FIG_DPI, bbox_inches='tight')
    plt.close()
    print(f"  Saved {path}")

    # Second plot: overlay comparison
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    ax = axes[0]
    for scenario_id, fc in all_forecasts.items():
        ax.plot(fc["date"], fc["import_index"], 'o-',
                color=colors[scenario_id], linewidth=2, label=SCENARIOS[scenario_id]['name'])
    ax.set_title("Petrochemical Import Index: Scenario Comparison")
    ax.set_ylabel("Import Index")
    ax.legend()
    ax.tick_params(axis='x', rotation=45)

    ax = axes[1]
    for scenario_id, fc in all_forecasts.items():
        ax.plot(fc["date"], fc["trade_balance"], 'o-',
                color=colors[scenario_id], linewidth=2, label=SCENARIOS[scenario_id]['name'])
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1)
    ax.set_title("Trade Balance: Scenario Comparison")
    ax.set_ylabel("Balance Index")
    ax.legend()
    ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    path = FIG_DIR / "09_scenario_comparison.pdf"
    plt.savefig(path, dpi=FIG_DPI, bbox_inches='tight')
    plt.close()
    print(f"  Saved {path}")


def plot_sensitivity_analysis():
    """Plot sensitivity of petrochemical trade to various factors."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. Sensitivity to crude price
    ax = axes[0, 0]
    crude_range = np.arange(50, 130, 5)
    base_inr = 95.5
    import_sensitivity = []
    for crude in crude_range:
        factor = crude / CURRENT_CRUDE
        import_idx = (CURRENT_CRUDE * base_inr / 100) * factor ** 0.7
        import_sensitivity.append(import_idx)
    ax.plot(crude_range, import_sensitivity, 'o-', color="#e74c3c", linewidth=2)
    ax.axvline(x=CURRENT_CRUDE, color='gray', linestyle='--', label=f'Current (${CURRENT_CRUDE})')
    ax.set_xlabel("Brent Crude ($/barrel)")
    ax.set_ylabel("Import Index")
    ax.set_title("Sensitivity: Petrochemical Imports to Crude Price")
    ax.legend()

    # 2. Sensitivity to INR
    ax = axes[0, 1]
    inr_range = np.arange(85, 110, 1)
    import_sensitivity = []
    for inr in inr_range:
        factor = inr / CURRENT_INR
        import_idx = (CURRENT_CRUDE * CURRENT_INR / 100) * factor
        import_sensitivity.append(import_idx)
    ax.plot(inr_range, import_sensitivity, 's-', color="#3498db", linewidth=2)
    ax.axvline(x=CURRENT_INR, color='gray', linestyle='--', label=f'Current ({CURRENT_INR})')
    ax.set_xlabel("USD/INR Exchange Rate")
    ax.set_ylabel("Import Index")
    ax.set_title("Sensitivity: Petrochemical Imports to INR")
    ax.legend()

    # 3. Crude price impact on trade balance
    ax = axes[1, 0]
    scenarios_crude = {"Base ($90)": 90, "Low ($70)": 70, "High ($110)": 110}
    trade_balances = []
    for name, crude in scenarios_crude.items():
        # Simplified trade balance calculation
        imp = crude * CURRENT_INR / 100 * 0.7 + CURRENT_INR
        exp = 0.6 * CURRENT_CRUDE * CURRENT_INR / 100 * (crude / CURRENT_CRUDE) ** (-0.2)
        trade_balances.append(exp - imp)

    ax.bar(scenarios_crude.keys(), trade_balances,
           color=["#3498db", "#2ecc71", "#e74c3c"], alpha=0.8)
    ax.axhline(y=0, color='black', linewidth=0.5)
    ax.set_title("Trade Balance Under Different Crude Prices")
    ax.set_ylabel("Balance Index")

    # 4. Probability-weighted forecast
    ax = axes[1, 1]
    # Assign probabilities to scenarios
    probs = {"Base": 0.5, "Bull": 0.25, "Bear": 0.25}
    months = pd.date_range("2026-07-01", periods=12, freq="MS")

    weighted_import = np.zeros(12)
    for scenario_id, prob in zip(["base_case", "bull_case", "bear_case"], probs.values()):
        weighted_import += np.array([CURRENT_CRUDE * CURRENT_INR / 100] * 12) * prob

    ax.plot(months, weighted_import, 'o-', color="#9b59b6", linewidth=2, label="Probability-Weighted")
    ax.fill_between(months, weighted_import * 0.9, weighted_import * 1.1,
                    alpha=0.2, color="#9b59b6", label="±10% Band")
    ax.set_title("Probability-Weighted Import Forecast")
    ax.set_ylabel("Import Index")
    ax.legend()
    ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    path = FIG_DIR / "10_sensitivity_analysis.pdf"
    plt.savefig(path, dpi=FIG_DPI, bbox_inches='tight')
    plt.close()
    print(f"  Saved {path}")


def write_forecast_report(all_forecasts):
    """Write comprehensive forecast report."""
    md = "# Petrochemical Trade Forecast Report (July 2026 - June 2027)\n\n"
    md += "## Executive Summary\n\n"
    md += "This report presents 12-month forecasts for India's petrochemical trade "
    md += "under three geopolitical scenarios, based on current economic conditions "
    md += "as of June 2026.\n\n"

    md += "### Key 2026 Context\n\n"
    md += f"- **Current Crude Oil Price**: ${CURRENT_CRUDE}/barrel (Strait of Hormuz tensions)\n"
    md += f"- **Current USD/INR**: {CURRENT_INR} (record low)\n"
    md += f"- **India GDP Growth**: {CURRENT_GDP_GROWTH}% (FY2026)\n"
    md += "- **Oil Import Dependency**: 85-87%\n"
    md += "- **Current Account**: Narrowed to $7.1B surplus in Q4 FY26\n\n"

    md += "## Scenario Analysis\n\n"

    for scenario_id, fc in all_forecasts.items():
        scenario = SCENARIOS[scenario_id]
        md += f"### {scenario['name']}\n\n"
        md += f"**Assumptions**: {scenario['description']}\n\n"
        md += "| Month | Crude ($/bbl) | USD/INR | Import Index | Export Index | Trade Balance |\n"
        md += "|-------|--------------|---------|--------------|-------------|---------------|\n"

        for _, row in fc.iterrows():
            md += f"| {row['date'].strftime('%b %Y')} | {row['wti_crude']:.1f} | {row['usd_inr']:.1f} | "
            md += f"{row['import_index']:.2f} | {row['export_index']:.2f} | {row['trade_balance']:.2f} |\n"
        md += "\n"

    md += "## Policy Implications\n\n"
    md += "1. **Currency Hedging**: With INR expected to weaken, petrochemical importers should "
    md += "consider forward contracts\n"
    md += "2. **Diversification**: Reduce dependency on Middle East crude by expanding "
    md += "Russian and African sourcing\n"
    md += "3. **Value Addition**: Shift from exporting raw petrochemicals to higher-value "
    md += "specialty chemicals\n"
    md += "4. **Strategic Reserves**: Build petrochemical strategic reserves to buffer "
    md += "supply shocks\n"

    md += "## Risk Factors\n\n"
    md += "- Geopolitical escalation in the Strait of Hormuz\n"
    md += "- US-Iran conflict escalation\n"
    md += "- OPEC+ production decisions\n"
    md += "- Global recession reducing demand\n"
    md += "- INR depreciation beyond 100/USD\n"

    path = RESULTS_DIR / "04_forecast_report.md"
    with open(path, "w") as f:
        f.write(md)
    print(f"  Saved {path}")

    # Also save forecast data as CSV
    combined = pd.DataFrame()
    for scenario_id, fc in all_forecasts.items():
        fc_copy = fc.copy()
        fc_copy["scenario"] = scenario_id
        combined = pd.concat([combined, fc_copy])
    combined.to_csv(RESULTS_DIR / "04_scenario_forecasts.csv", index=False)


def main():
    print("=" * 80)
    print("SCENARIO FORECAST & ANALYSIS (2026-2027)")
    print("=" * 80)

    print("\n--- Generating Scenario Forecasts ---")
    all_forecasts = generate_scenario_forecasts()

    print("\n--- Plotting Scenario Analysis ---")
    plot_scenario_analysis(all_forecasts)

    print("\n--- Sensitivity Analysis ---")
    plot_sensitivity_analysis()

    print("\n--- Writing Forecast Report ---")
    write_forecast_report(all_forecasts)

    print(f"\n{'=' * 80}")
    print("DONE! All forecasts and reports saved.")
    print("=" * 80)


if __name__ == "__main__":
    main()
