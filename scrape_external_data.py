#!/usr/bin/env python3
"""Scrape external economic data sources for petrochemical analysis.

Sources:
- FRED (Federal Reserve Economic Data) - crude oil prices, USD/INR, etc.
- World Bank API - macroeconomic indicators
- PPAC India - petroleum planning data
- RBI data - interest rates, forex reserves
"""

import json
import os
import subprocess
import time
from pathlib import Path

RAW_DIR = Path("data/raw/external")
RAW_DIR.mkdir(parents=True, exist_ok=True)


def curl_get(url, timeout=60):
    result = subprocess.run(
        ["curl", "-s", "--max-time", str(timeout), url],
        capture_output=True, text=True, timeout=timeout + 10,
    )
    return result.stdout


def fetch_fred_series(series_id, description, api_key="DEMO_KEY"):
    """Fetch a FRED time series via the public API."""
    print(f"  FRED: {series_id} - {description}")
    url = (
        f"https://api.stlouisfed.org/fred/series/observations"
        f"?series_id={series_id}&api_key={api_key}&file_type=json"
        f"&observation_start=2000-01-01"
    )
    try:
        raw = curl_get(url)
        data = json.loads(raw)
        observations = data.get("observations", [])
        records = [{"date": o["date"], "value": o["value"]} for o in observations]
        return records
    except Exception as e:
        print(f"    FAILED: {e}")
        return []


def fetch_world_bank(indicator, country="IND", description=""):
    """Fetch World Bank indicator via API."""
    print(f"  World Bank: {indicator} - {description}")
    url = (
        f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
        f"?format=json&per_page=100&date=2000:2025"
    )
    try:
        raw = curl_get(url)
        data = json.loads(raw)
        if len(data) > 1:
            records = [
                {"date": f"{item['date']}-01-01", "value": item["value"], "indicator": item["indicator"]["id"]}
                for item in data[1] if item["value"] is not None
            ]
            return records
        return []
    except Exception as e:
        print(f"    FAILED: {e}")
        return []


def scrape_ppac_data():
    """Scrape PPAC (Petroleum Planning & Analysis Cell) data."""
    print("  PPAC: Attempting to fetch petroleum data...")
    # PPAC has PDF reports, but we can try their data endpoints
    urls = [
        "https://www.ppac.gov.in/readfiles/files/1563594745_oilbook.pdf",
    ]
    # PPAC data is mostly PDFs - we'll note the URLs for reference
    return {
        "ppac_url": "https://ppac.gov.in",
        "note": "PPAC data is primarily in PDF format. Use specific datasets from data.gov.in instead.",
        "key_reports": [
            "PPAC Journal monthly",
            "Ready Reckoner FY 2025-26",
            "Snapshot of India's Oil & Gas Data (monthly)",
            "All India study on sectoral demand for petrol and diesel",
        ]
    }


def main():
    print("=" * 80)
    print("SCRAPING EXTERNAL ECONOMIC DATA")
    print("=" * 80)

    all_data = {}

    # 1. FRED data (no API key needed for demo, but limited)
    print("\n--- FRED Series ---")
    fred_series = {
        "DCOILWTICO": "WTI Crude Oil Price (Daily)",
        "DCOILBRENTEU": "Brent Crude Oil Price (Daily)",
        "DGS10": "10-Year Treasury Rate",
        "DGS2": "2-Year Treasury Rate",
        "DTWEXBGS": "Trade Weighted USD Index",
        "DEXINUS": "USD to INR Exchange Rate",
        "MABMMYINM189S": "India Industrial Production Index",
    }
    for sid, desc in fred_series.items():
        records = fetch_fred_series(sid, desc)
        all_data[f"fred_{sid}"] = {"series_id": sid, "description": desc, "records": records}
        print(f"    Got {len(records)} observations")
        time.sleep(0.5)

    # 2. World Bank indicators
    print("\n--- World Bank Indicators ---")
    wb_indicators = {
        "NY.GDP.MKTP.KD.ZG": "GDP Growth Rate",
        "BN.CAB.XOKA.CD": "Current Account Balance",
        "BX.KLT.DINV.CD.WD": "FDI Net Inflows",
        "NE.TRD.GNFS.ZS": "Trade (% of GDP)",
        "TM.VAL.PETR.MT.CD": "Petroleum Imports",
        "TX.VAL.PETR.MT.CD": "Petroleum Exports",
        "FP.CPI.TOTL.ZG": "Consumer Price Inflation",
        "SL.UEM.TOTL.ZS": "Unemployment Rate",
        "SP.POP.TOTL": "Population Total",
        "SP.DYN.LE00.IN": "Life Expectancy",
        "SE.ADT.LITR.ZS": "Literacy Rate",
    }
    for indicator, desc in wb_indicators.items():
        records = fetch_world_bank(indicator, "IND", desc)
        all_data[f"wb_{indicator}"] = {"indicator": indicator, "description": desc, "records": records}
        print(f"    Got {len(records)} observations")
        time.sleep(0.3)

    # 3. PPAC info
    print("\n--- PPAC Data ---")
    ppac_info = scrape_ppac_data()
    all_data["ppac_info"] = ppac_info
    print(f"    PPAC note: {ppac_info['note']}")

    # Save all external data
    output_path = RAW_DIR / "external_economic_data.json"
    with open(output_path, "w") as f:
        json.dump(all_data, f, ensure_ascii=False, default=str)
    print(f"\nSaved to {output_path} ({os.path.getsize(output_path)/1024:.1f} KB)")

    # Also save a summary
    summary = {}
    for key, data in all_data.items():
        if isinstance(data, dict) and "records" in data:
            summary[key] = len(data["records"])
        else:
            summary[key] = "info_only"
    print("\nSummary of data collected:")
    for k, v in summary.items():
        print(f"  {k}: {v} records")


if __name__ == "__main__":
    main()
