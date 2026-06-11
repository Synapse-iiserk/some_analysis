#!/usr/bin/env python3
"""India Petrochemical Trade Analysis — Web Dashboard v2.

Interactive dashboard with Plotly.js charts, proper data APIs,
and comprehensive analysis pages.
"""

import json
import os
from pathlib import Path

from flask import Flask, render_template, send_from_directory, jsonify

app = Flask(__name__, static_folder="static", template_folder="templates")

BASE_DIR = Path(".")
FIGURES_DIR = BASE_DIR / "figures"
RESULTS_DIR = BASE_DIR / "results"
DATA_DIR = BASE_DIR / "data" / "processed"
CHART_DATA_DIR = DATA_DIR / "chart_data"


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return None


def load_csv(path):
    try:
        import pandas as pd
        return pd.read_csv(path).to_dict(orient="records")
    except:
        return []


# ============ PAGES ============

@app.route("/")
def index():
    """Home page — Executive Summary with interactive charts."""
    trade_balance = load_csv(DATA_DIR / "petrochemical_trade_balance.csv")
    temporal = load_json(CHART_DATA_DIR / "temporal_trends.json")
    insights = load_json(CHART_DATA_DIR / "key_insights.json")
    metrics = load_csv(RESULTS_DIR / "02_model_metrics.csv")
    geo = load_json(CHART_DATA_DIR / "geographic_trade.json")

    return render_template("index.html",
                         trade_balance=trade_balance,
                         temporal=temporal,
                         insights=insights,
                         metrics=metrics,
                         geo=geo)


@app.route("/trade")
def trade():
    """Trade Analysis — Product flows, category breakdowns."""
    trade_balance = load_csv(DATA_DIR / "petrochemical_trade_balance.csv")
    flows = load_json(CHART_DATA_DIR / "product_trade_flows.json")
    sectors = load_json(CHART_DATA_DIR / "sector_breakdown.json")
    temporal = load_json(CHART_DATA_DIR / "temporal_trends.json")

    return render_template("trade.html",
                         trade_balance=trade_balance,
                         flows=flows,
                         sectors=sectors,
                         temporal=temporal)


@app.route("/forecast")
def forecast():
    """Forecast & Scenarios page."""
    scenarios = load_csv(RESULTS_DIR / "04_scenario_forecasts.csv")
    sensitivity = load_json(CHART_DATA_DIR / "price_sensitivity.json")
    insights = load_json(CHART_DATA_DIR / "key_insights.json")

    return render_template("forecast.html",
                         scenarios=scenarios,
                         sensitivity=sensitivity,
                         insights=insights)


@app.route("/models")
def models():
    """Model Analysis page."""
    metrics = load_csv(RESULTS_DIR / "02_model_metrics.csv")
    model_data = load_json(CHART_DATA_DIR / "model_performance.json")

    return render_template("models.html",
                         metrics=metrics,
                         model_data=model_data)


@app.route("/analysis")
def analysis():
    """Deep Analysis — Investment gaps, sector breakdowns, verdicts."""
    insights = load_json(CHART_DATA_DIR / "key_insights.json")
    investment = load_json(CHART_DATA_DIR / "investment_gaps.json")
    sectors = load_json(CHART_DATA_DIR / "sector_breakdown.json")
    geo = load_json(CHART_DATA_DIR / "geographic_trade.json")
    sensitivity = load_json(CHART_DATA_DIR / "price_sensitivity.json")

    return render_template("analysis.html",
                         insights=insights,
                         investment=investment,
                         sectors=sectors,
                         geo=geo,
                         sensitivity=sensitivity)


@app.route("/datasets")
def datasets():
    """Data Sources page — lists all datasets used."""
    return render_template("datasets.html")


# ============ API ENDPOINTS ============

@app.route("/api/trade-balance")
def api_trade_balance():
    return jsonify(load_csv(DATA_DIR / "petrochemical_trade_balance.csv"))


@app.route("/api/temporal-trends")
def api_temporal_trends():
    return jsonify(load_json(CHART_DATA_DIR / "temporal_trends.json"))


@app.route("/api/product-flows")
def api_product_flows():
    return jsonify(load_json(CHART_DATA_DIR / "product_trade_flows.json"))


@app.route("/api/investment-gaps")
def api_investment_gaps():
    return jsonify(load_json(CHART_DATA_DIR / "investment_gaps.json"))


@app.route("/api/geographic-trade")
def api_geographic_trade():
    return jsonify(load_json(CHART_DATA_DIR / "geographic_trade.json"))


@app.route("/api/sensitivity")
def api_sensitivity():
    return jsonify(load_json(CHART_DATA_DIR / "price_sensitivity.json"))


@app.route("/api/sectors")
def api_sectors():
    return jsonify(load_json(CHART_DATA_DIR / "sector_breakdown.json"))


@app.route("/api/insights")
def api_insights():
    return jsonify(load_json(CHART_DATA_DIR / "key_insights.json"))


@app.route("/api/model-performance")
def api_model_performance():
    return jsonify(load_json(CHART_DATA_DIR / "model_performance.json"))


@app.route("/api/scenarios")
def api_scenarios():
    return jsonify(load_csv(RESULTS_DIR / "04_scenario_forecasts.csv"))


@app.route("/api/forecast-csv")
def api_forecast_csv():
    return jsonify(load_csv(RESULTS_DIR / "03_forecasts.csv"))

@app.route("/api/trajectory-crude")
def api_trajectory_crude():
    return jsonify(load_json(CHART_DATA_DIR / "trajectory_crude.json"))

@app.route("/api/trajectory-inr")
def api_trajectory_inr():
    return jsonify(load_json(CHART_DATA_DIR / "trajectory_inr.json"))

@app.route("/api/trajectory-trade")
def api_trajectory_trade():
    return jsonify(load_json(CHART_DATA_DIR / "trajectory_trade.json"))

@app.route("/api/trajectory-deficit")
def api_trajectory_deficit():
    return jsonify(load_json(CHART_DATA_DIR / "trajectory_deficit.json"))

@app.route("/api/model-forecast")
def api_model_forecast():
    return jsonify(load_json(CHART_DATA_DIR / "model_forecast.json"))

@app.route("/api/milestones")
def api_milestones():
    return jsonify(load_json(CHART_DATA_DIR / "milestones.json"))

@app.route("/api/cumulative-impact")
def api_cumulative_impact():
    return jsonify(load_json(CHART_DATA_DIR / "cumulative_impact.json"))


# ============ STATIC FILES ============

@app.route("/figures/<path:filename>")
def serve_figure(filename):
    return send_from_directory(FIGURES_DIR, filename)


@app.route("/data/<path:filename>")
def serve_data(filename):
    return send_from_directory(DATA_DIR, filename)


@app.route("/chart-data/<path:filename>")
def serve_chart_data(filename):
    return send_from_directory(CHART_DATA_DIR, filename)


if __name__ == "__main__":
    print("=" * 60)
    print("  India Petrochemical Trade Analysis Dashboard v2")
    print("  Starting server on http://0.0.0.0:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False)
