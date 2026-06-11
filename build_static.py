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
    "/api/scenarios": "results/04_scenario_forecasts.csv",
    "/api/forecast-csv": "results/03_forecasts.csv",
    "/api/trajectory-crude": "data/processed/chart_data/trajectory_crude.json",
    "/api/trajectory-inr": "data/processed/chart_data/trajectory_inr.json",
    "/api/trajectory-trade": "data/processed/chart_data/trajectory_trade.json",
    "/api/trajectory-deficit": "data/processed/chart_data/trajectory_deficit.json",
    "/api/model-forecast": "data/processed/chart_data/model_forecast.json",
    "/api/milestones": "data/processed/chart_data/milestones.json",
    "/api/cumulative-impact": "data/processed/chart_data/cumulative_impact.json",
}


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
        "datasets.html": {"title": "datasets"},
    }

    DOCS_DIR.mkdir(exist_ok=True)

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
