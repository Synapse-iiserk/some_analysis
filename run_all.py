#!/usr/bin/env python3
"""Master runner: executes the full analysis pipeline.

Run with: .venv/bin/python run_all.py

Steps:
1. Download datasets from data.gov.in
2. Scrape external economic data
3. Data engineering (merge, clean, features)
4. EDA and correlation analysis
5. Predictive modeling
6. Scenario forecasting
7. Generate notebook + reports
"""

import subprocess
import sys
import time
from pathlib import Path

VENV_PYTHON = Path(".venv/bin/python")
STEPS = [
    ("1. Download Data", "download_datasets.py"),
    ("2. Scrape External", "scrape_external_data.py"),
    ("3. Data Engineering", "01_data_engineering.py"),
    ("4. EDA & Correlation", "02_eda_correlation.py"),
    ("5. Predictive Models", "03_models.py"),
    ("6. Scenario Forecast", "04_forecast.py"),
    ("7. Generate Notebook", "05_generate_notebook.py"),
]


def run_step(name, script):
    print(f"\n{'='*80}")
    print(f"  {name}")
    print(f"{'='*80}")
    start = time.time()
    try:
        result = subprocess.run(
            [str(VENV_PYTHON), script],
            capture_output=True, text=True, timeout=3600,
        )
        print(result.stdout)
        if result.stderr:
            print(f"STDERR:\n{result.stderr[-2000:]}")
        elapsed = time.time() - start
        print(f"  Completed in {elapsed:.1f}s")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT after 3600s")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    print("=" * 80)
    print("  PETROCHEMICAL TRADE ANALYSIS - FULL PIPELINE")
    print("=" * 80)

    results = {}
    for name, script in STEPS:
        success = run_step(name, script)
        results[name] = success
        if not success:
            print(f"\n  WARNING: {name} failed. Continuing...")

    print(f"\n{'='*80}")
    print("  PIPELINE SUMMARY")
    print(f"{'='*80}")
    for name, success in results.items():
        status = "OK" if success else "FAILED"
        print(f"  [{status}] {name}")

    all_passed = all(results.values())
    print(f"\n  Overall: {'ALL PASSED' if all_passed else 'SOME FAILURES'}")
    print("=" * 80)


if __name__ == "__main__":
    main()
