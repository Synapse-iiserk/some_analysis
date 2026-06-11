#!/usr/bin/env python3
"""Generate Jupyter Notebook with Interactive Analysis.

Creates a complete .ipynb notebook with all analyses and visualizations.
"""

import json
from pathlib import Path

FIG_DIR = Path("figures")


def make_code_cell(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.split("\n")}


def make_markdown_cell(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.split("\n")}


def build_notebook():
    cells = []

    # Title
    cells.append(make_markdown_cell(
        "# India Petrochemical Trade Analysis & Forecast (2026-2027)\n"
        "\n"
        "## Project Overview\n"
        "This notebook provides a comprehensive analysis of India's petrochemical trade,\n"
        "including data exploration, correlation analysis, predictive modeling, and\n"
        "12-month forecasts under multiple geopolitical scenarios.\n"
        "\n"
        "**Key Context (June 2026):**\n"
        "- Brent Crude: ~$90/barrel (Strait of Hormuz tensions)\n"
        "- USD/INR: ~95.5 (record low)\n"
        "- India GDP: 7.7% (FY2026)\n"
        "- Oil Import Dependency: 85-87%"
    ))

    # Setup
    cells.append(make_code_cell(
        "import warnings\n"
        "warnings.filterwarnings('ignore')\n"
        "\n"
        "import numpy as np\n"
        "import pandas as pd\n"
        "import matplotlib.pyplot as plt\n"
        "import seaborn as sns\n"
        "from pathlib import Path\n"
        "\n"
        "plt.style.use('seaborn-v0_8-whitegrid')\n"
        "sns.set_palette('husl')\n"
        "%matplotlib inline\n"
        "\n"
        "DATA_DIR = Path('data/processed')\n"
        "FIG_DIR = Path('figures')\n"
        "print('Setup complete.')"
    ))

    # Section 1: Data Overview
    cells.append(make_markdown_cell("## 1. Data Overview"))

    cells.append(make_code_cell(
        "# Load processed datasets\n"
        "datasets = {}\n"
        "for f in DATA_DIR.glob('*.csv'):\n"
        "    datasets[f.stem] = pd.read_csv(f)\n"
        "    print(f'Loaded: {f.stem} ({len(datasets[f.stem])} rows)')\n"
        "\n"
        "print(f'\\nTotal datasets: {len(datasets)}')"
    ))

    # Section 2: Trade Balance
    cells.append(make_markdown_cell("## 2. Petrochemical Trade Balance"))

    cells.append(make_code_cell(
        "tb = datasets.get('petrochemical_trade_balance')\n"
        "if tb is not None:\n"
        "    print(tb.to_string(index=False))\n"
        "else:\n"
        "    print('Trade balance data not available')"
    ))

    cells.append(make_code_cell(
        "fig, axes = plt.subplots(2, 2, figsize=(16, 12))\n"
        "\n"
        "# Exports vs Imports\n"
        "ax = axes[0, 0]\n"
        "if tb is not None:\n"
        "    x = range(len(tb))\n"
        "    ax.bar(x, tb['total_export_value']/1000, label='Exports', color='#2ecc71', alpha=0.8)\n"
        "    ax.bar(x, -tb['total_import_value']/1000, label='Imports', color='#e74c3c', alpha=0.8)\n"
        "    ax.set_xticks(x)\n"
        "    ax.set_xticklabels(tb['fiscal_year'], rotation=45)\n"
        "    ax.set_ylabel('Value (thousands crore ₹)')\n"
        "    ax.set_title('Petrochemical Exports vs Imports')\n"
        "    ax.legend()\n"
        "    ax.axhline(y=0, color='black', linewidth=0.5)\n"
        "\n"
        "# Trade Balance\n"
        "ax = axes[0, 1]\n"
        "if tb is not None:\n"
        "    ax.plot(tb['fiscal_year'], tb['trade_balance']/1000, 'o-', color='#3498db', linewidth=2)\n"
        "    ax.fill_between(range(len(tb)), tb['trade_balance']/1000, alpha=0.3, color='#3498db')\n"
        "    ax.set_xticks(range(len(tb)))\n"
        "    ax.set_xticklabels(tb['fiscal_year'], rotation=45)\n"
        "    ax.set_ylabel('Trade Balance (thousands crore ₹)')\n"
        "    ax.set_title('Petrochemical Trade Balance')\n"
        "    ax.axhline(y=0, color='red', linestyle='--', linewidth=1)\n"
        "\n"
        "plt.tight_layout()\n"
        "plt.savefig(FIG_DIR / 'notebook_01_trade_balance.pdf', dpi=150, bbox_inches='tight')\n"
        "plt.show()"
    ))

    # Section 3: Macro Correlations
    cells.append(make_markdown_cell("## 3. Macroeconomic Correlations"))

    cells.append(make_code_cell(
        "# Load macro data\n"
        "macro = {}\n"
        "for name in ['wti_crude', 'usd_inr', 'gdp_growth', 'fdi_inflows', 'cpi_inflation']:\n"
        "    path = DATA_DIR / f'macro_{name}.csv'\n"
        "    if path.exists():\n"
        "        df = pd.read_csv(path)\n"
        "        df['date'] = pd.to_datetime(df['date'])\n"
        "        macro[name] = df.set_index('date')[[name]].resample('M').mean()\n"
        "\n"
        "if macro:\n"
        "    merged = pd.DataFrame()\n"
        "    for name, df in macro.items():\n"
        "        merged = merged.join(df, how='outer') if not merged.empty else df\n"
        "    merged = merged.dropna()\n"
        "    print(f'Merged macro data: {len(merged)} months')\n"
        "    print(merged.describe())\n"
        "else:\n"
        "    print('No macro data available')"
    ))

    cells.append(make_code_cell(
        "if 'merged' in dir() and len(merged) > 10:\n"
        "    fig, axes = plt.subplots(1, 2, figsize=(16, 6))\n"
        "\n"
        "    # Correlation heatmap\n"
        "    corr = merged.corr()\n"
        "    sns.heatmap(corr, annot=True, fmt='.2f', cmap='RdBu_r', center=0,\n"
        "                ax=axes[0], square=True, linewidths=0.5)\n"
        "    axes[0].set_title('Macro Indicator Correlations')\n"
        "\n"
        "    # Rolling correlation\n"
        "    if 'wti_crude' in merged.columns and 'usd_inr' in merged.columns:\n"
        "        rolling_corr = merged['wti_crude'].rolling(12).corr(merged['usd_inr'])\n"
        "        axes[1].plot(merged.index, rolling_corr, color='#9b59b6', linewidth=2)\n"
        "        axes[1].axhline(y=0, color='black', linestyle='--', linewidth=0.5)\n"
        "        axes[1].set_title('Rolling 12M Correlation: Crude vs USD/INR')\n"
        "        axes[1].set_ylabel('Correlation')\n"
        "\n"
        "    plt.tight_layout()\n"
        "    plt.savefig(FIG_DIR / 'notebook_02_correlations.pdf', dpi=150, bbox_inches='tight')\n"
        "    plt.show()"
    ))

    # Section 4: Model Forecasts
    cells.append(make_markdown_cell("## 4. Predictive Model Forecasts"))

    cells.append(make_code_cell(
        "fc_path = DATA_DIR.parent / 'results' / '03_forecasts.csv'\n"
        "if fc_path.exists():\n"
        "    forecasts = pd.read_csv(fc_path, index_col=0, parse_dates=True)\n"
        "    print('Available forecasts:')\n"
        "    print(forecasts.columns.tolist())\n"
        "    print(forecasts.tail(12))\n"
        "else:\n"
        "    print('Run 03_models.py first to generate forecasts.')"
    ))

    cells.append(make_code_cell(
        "metrics_path = DATA_DIR.parent / 'results' / '02_model_metrics.csv'\n"
        "if metrics_path.exists():\n"
        "    metrics = pd.read_csv(metrics_path)\n"
        "    print('\\nModel Comparison:')\n"
        "    print(metrics.to_string(index=False))\n"
        "    \n"
        "    fig, ax = plt.subplots(figsize=(10, 5))\n"
        "    colors = ['#3498db', '#2ecc71', '#e74c3c', '#9b59b6', '#f39c12']\n"
        "    ax.barh(metrics['model'], metrics['mae'], color=colors[:len(metrics)])\n"
        "    ax.set_xlabel('Mean Absolute Error (lower = better)')\n"
        "    ax.set_title('Model Performance Comparison')\n"
        "    plt.tight_layout()\n"
        "    plt.savefig(FIG_DIR / 'notebook_03_model_comparison.pdf', dpi=150, bbox_inches='tight')\n"
        "    plt.show()"
    ))

    # Section 5: Scenario Analysis
    cells.append(make_markdown_cell("## 5. 2026-2027 Scenario Analysis"))

    cells.append(make_code_cell(
        "scenario_path = DATA_DIR.parent / 'results' / '04_scenario_forecasts.csv'\n"
        "if scenario_path.exists():\n"
        "    scenarios = pd.read_csv(scenario_path)\n"
        "    scenarios['date'] = pd.to_datetime(scenarios['date'])\n"
        "    \n"
        "    fig, axes = plt.subplots(1, 2, figsize=(16, 6))\n"
        "    colors = {'base_case': '#3498db', 'bull_case': '#2ecc71', 'bear_case': '#e74c3c'}\n"
        "    \n"
        "    for scenario_id in scenarios['scenario'].unique():\n"
        "        data = scenarios[scenarios['scenario'] == scenario_id]\n"
        "        axes[0].plot(data['date'], data['import_index'], 'o-',\n"
        "                     color=colors.get(scenario_id, 'gray'), linewidth=2, label=scenario_id)\n"
        "        axes[1].plot(data['date'], data['trade_balance'], 'o-',\n"
        "                     color=colors.get(scenario_id, 'gray'), linewidth=2, label=scenario_id)\n"
        "    \n"
        "    axes[0].set_title('Import Index Forecast')\n"
        "    axes[0].set_ylabel('Index')\n"
        "    axes[0].legend()\n"
        "    axes[1].set_title('Trade Balance Forecast')\n"
        "    axes[1].set_ylabel('Balance Index')\n"
        "    axes[1].axhline(y=0, color='black', linestyle='--', linewidth=1)\n"
        "    axes[1].legend()\n"
        "    \n"
        "    plt.tight_layout()\n"
        "    plt.savefig(FIG_DIR / 'notebook_04_scenarios.pdf', dpi=150, bbox_inches='tight')\n"
        "    plt.show()"
    ))

    # Section 6: Conclusions
    cells.append(make_markdown_cell(
        "## 6. Key Conclusions\n"
        "\n"
        "### Findings\n"
        "1. **Structural Deficit**: India runs a persistent trade deficit in petrochemicals\n"
        "2. **Crude Price Sensitivity**: Petrochemical imports are highly sensitive to crude oil prices\n"
        "3. **Currency Impact**: INR depreciation amplifies import costs in domestic terms\n"
        "4. **GDP Correlation**: Industrial growth drives petrochemical demand\n"
        "\n"
        "### 2026 Outlook\n"
        "- **Base Case**: Petrochemical imports remain elevated due to crude prices\n"
        "- **Bull Case**: Peace dividend could reduce import costs by 15-20%\n"
        "- **Bear Case**: Escalation could push import costs up by 20-30%\n"
        "\n"
        "### Policy Recommendations\n"
        "1. Build strategic petrochemical reserves\n"
        "2. Diversify crude sourcing away from Middle East\n"
        "3. Invest in domestic petrochemical capacity\n"
        "4. Implement currency hedging for importers\n"
        "5. Shift toward specialty chemicals with higher value-add"
    ))

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.13.0"}
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }

    path = Path("notebook_petrochemical_analysis.ipynb")
    with open(path, "w") as f:
        json.dump(notebook, f, indent=1)
    print(f"Generated notebook: {path}")
    return path


if __name__ == "__main__":
    build_notebook()
