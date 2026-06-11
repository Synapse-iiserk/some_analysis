#!/usr/bin/env python3
"""Render Jinja2 templates to static HTML for GitHub Pages.

Generates docs/ directory with all static files.
Replaces API fetch URLs with relative file paths.
"""

import json
import os
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(".")
DOCS_DIR = BASE_DIR / "docs"
DATA_DIR = BASE_DIR / "data" / "processed"
CHART_DATA_DIR = DATA_DIR / "chart_data"
RESULTS_DIR = BASE_DIR / "results"

# Map API endpoints to relative file paths
API_TO_FILE = {
    "/api/trade-balance": "data/processed/petrochemical_trade_balance.csv",
    "/api/temporal-trends": "data/processed/chart_data/temporal_trends.json",
    "/api/product-flows": "data/processed/chart_data/product_trade_flows.json",
    "/api/investment-gaps": "data/processed/chart_data/investment_gaps.json",
    "/api/geographic-trade": "data/processed/chart_data/geographic_trade.json",
    "/api/sensitivity": "data/processed/chart_data/price_sensitivity.json",
    "/api/sectors": "data/processed/chart_data/sector_breakdown.json",
    "/api/insights": "data/processed/chart_data/key_insights.json",
    "/api/model-performance": "data/processed/chart_data/model_performance.json",
    "/api/scenarios": "data/processed/chart_data/scenarios.json",
    "/api/forecast-csv": "results/03_forecasts.csv",
    "/api/trajectory-crude": "data/processed/chart_data/trajectory_crude.json",
    "/api/trajectory-inr": "data/processed/chart_data/trajectory_inr.json",
    "/api/trajectory-trade": "data/processed/chart_data/trajectory_trade.json",
    "/api/trajectory-deficit": "data/processed/chart_data/trajectory_deficit.json",
    "/api/model-forecast": "data/processed/chart_data/model_forecast.json",
    "/api/milestones": "data/processed/chart_data/milestones.json",
    "/api/cumulative-impact": "data/processed/chart_data/cumulative_impact.json",
    "/api/states": "data/processed/chart_data/states_comprehensive.json",
    "/api/state-clusters": "data/processed/chart_data/state_clusters.json",
    "/api/state-risk": "data/processed/chart_data/state_risk_opportunity.json",
    "/api/state-sectors": "data/processed/chart_data/state_sectors.json",
    "/api/state-trade-flows": "data/processed/chart_data/state_trade_flows.json",
    "/api/state-forecast": "data/processed/chart_data/state_forecast_2027.json",
}


def convert_csv_to_json():
    """Convert CSV files used in JS fetches to JSON."""
    import csv
    
    csv_to_convert = {
        RESULTS_DIR / "04_scenario_forecasts.csv": CHART_DATA_DIR / "scenarios.json",
    }
    
    for csv_path, json_path in csv_to_convert.items():
        if not csv_path.exists():
            print(f"  WARN: {csv_path} not found")
            continue
        try:
            with open(csv_path) as f:
                reader = csv.DictReader(f)
                records = list(reader)
            with open(json_path, "w") as f:
                json.dump(records, f, default=str)
            print(f"  Converted {csv_path.name} -> {json_path.name} ({len(records)} records)")
        except Exception as e:
            print(f"  ERROR converting {csv_path.name}: {e}")


def replace_fetch_urls(html):
    """Replace API fetch URLs with relative file paths."""
    for api_url, file_path in API_TO_FILE.items():
        html = html.replace(f"fetch('{api_url}')", f"fetch('{file_path}')")
        html = html.replace(f'fetch("{api_url}")', f'fetch("{file_path}")')
    # Fix figure paths
    html = html.replace('src="/figures/', 'src="figures/')
    return html


def render_templates():
    """Render all templates to static HTML."""
    env = Environment(loader=FileSystemLoader("templates"))

    pages = {
        "index.html": {"title": "home"},
        "trade.html": {"title": "trade"},
        "forecast.html": {"title": "forecast"},
        "models.html": {"title": "models"},
        "analysis.html": {"title": "analysis"},
        "states.html": {"title": "states"},
        "datasets.html": {"title": "datasets"},
    }

    # Convert CSV files to JSON for JavaScript fetches
    print("Converting CSV files to JSON...")
    convert_csv_to_json()

    DOCS_DIR.mkdir(exist_ok=True)
    (DOCS_DIR / "data" / "processed" / "chart_data").mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "figures").mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "results").mkdir(parents=True, exist_ok=True)

    # Add .nojekyll to prevent Jekyll processing on GitHub Pages
    (DOCS_DIR / ".nojekyll").touch()

    # Copy data files
    import shutil
    for src_dir, dst_dir in [
        (DATA_DIR, DOCS_DIR / "data" / "processed"),
        (CHART_DATA_DIR, DOCS_DIR / "data" / "processed" / "chart_data"),
        (BASE_DIR / "figures", DOCS_DIR / "figures"),
        (RESULTS_DIR, DOCS_DIR / "results"),
    ]:
        if src_dir.exists():
            for f in src_dir.iterdir():
                if f.is_file():
                    shutil.copy2(f, dst_dir)
                    print(f"  Copied {f.name} -> {dst_dir}")

    for filename, context in pages.items():
        print(f"Rendering {filename}...")
        try:
            template = env.get_template(filename)
            html = template.render(active_page=context["title"])
            html = replace_fetch_urls(html)
            output_path = DOCS_DIR / filename
            with open(output_path, "w") as f:
                f.write(html)
            print(f"  -> {output_path} ({os.path.getsize(output_path) // 1024}KB)")
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\nStatic site generated in {DOCS_DIR}/")


if __name__ == "__main__":
    render_templates()
