#!/usr/bin/env python3
"""Download all datasets from data.gov.in API and external sources.

Datasets identified from catalogue analysis for petrochemical trade analysis.
Uses curl via subprocess for reliability with the slow API.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

API_KEY = os.getenv("DATA_GOV_API_KEY", "579b464db66ec23bdd000001eb9e9125ad9441cc4b9ea4e1465edbac")
BASE_URL = "https://api.data.gov.in/resource"
RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Datasets to download: (resource_id, label, description)
DATASETS = [
    # Core petrochemical trade
    ("cb525a11-6cb1-4267-aa48-f63eaabe97b7", "petrochemical_exports", "Product-wise Petrochemical Exports 2015-2025"),
    ("b32764bf-dcb1-41c6-b174-61550537e5b6", "petrochemical_imports", "Product-wise Petrochemical Imports 2015-2025"),
    ("179671b5-9e73-462b-86b3-637ea37522ef", "chemical_exports", "Product-wise Chemical Exports 2015-2025"),
    ("1cdd0a0b-2355-47a5-af3f-788c7866c9f4", "chemical_imports", "Product-wise Chemical Imports 2015-2025"),

    # Extended historical chemistry
    ("02c46d80-75d2-4b6a-a688-53a2a2ce437d", "chemical_exports_2010_2018", "Chemical Exports 2010-2018"),
    ("361d5f39-771f-4fd5-94a8-04112f7c7c72", "petrochemical_exports_2009_2017", "Petrochemical Exports 2009-2017"),
    ("7828ade4-d2da-4e5b-93e6-dc92ea584c7b", "petrochemical_exports_2013_2021", "Petrochemical Exports 2013-2021"),
    ("2d1c04e0-8360-49b1-a6d9-1922011acf8b", "petrochemical_imports_2013_2021", "Petrochemical Imports 2013-2021"),

    # Crude oil
    ("44f0d912-df6f-4d51-8043-c3257644bd03", "crude_oil_trade_2012_2017", "Crude Oil Import/Export 2012-2017"),
    ("26136e8d-a085-4f22-b877-e775918b2338", "intl_crude_oil_prices", "International Crude Oil Prices"),
    ("db1b2527-6549-46fb-83c7-eb0b56b6fc2e", "crude_oil_production", "Crude Oil & Gas Production 1980-2015"),
    ("76ae5010-629d-45f2-9bdd-aebda502c1f7", "natural_gas_production", "Natural Gas Production 2013-2020"),
    ("0a1af4a7-c6c8-4818-a47c-95570b3e1dcf", "petroleum_consumption", "State-wise Petroleum Consumption"),

    # Prices & indices
    ("38d8b72c-44d3-49d0-917f-0bd8de1b7e1a", "wpi_petroleum", "WPI Petroleum Products"),
    ("239ac3d0-f08d-40d0-b03c-9b7a426a62d5", "wpi_all_2011_series", "WPI All Commodities 2011 Series"),
    ("578fd3e8-b099-4eb7-9437-3515ef334817", "lpg_retail_price", "LPG Retail Selling Price Monthly"),

    # Macroeconomic
    ("cc473f03-4db1-4c34-949e-481bdb3da490", "eight_core_industries", "Eight Core Industries Index"),
    ("31d53713-46c6-48bd-951a-4d986272fd96", "iip_monthly", "Index of Industrial Production Monthly"),
    ("f338e1f1-b527-454e-b0ee-089f3de3f0fa", "gdp_quarterly_current", "Quarterly GDP at Current Prices"),
    ("a56b86d1-f00e-4ee4-ab08-5b5367b3fab2", "gdp_quarterly_constant", "Quarterly GDP at Constant Prices"),
    ("4a587f38-f69d-4b5f-a463-d378b754d6b8", "gdp_by_economic_activity", "GDP by Economic Activity 1950-2014"),
    ("b0842d7b-2f7d-466d-84b9-5f8b2e7a9e32", "fdi_inflows", "FDI Equity Inflows by Sector 2000-2016"),
    ("8f9755dd-14ea-478b-b7ab-b243a1aa9bdd", "fdi_inflows_v2", "FDI Equity Inflows 2000-2017"),
    ("316ea4dc-aef6-4e87-a2de-b1150ab18d1d", "merchandise_trade_countries", "Export/Import with USA/Russia/UK/China"),

    # Consumer prices
    ("d792b73e-961d-4d7c-babc-c8089acfa0cd", "cpi_state_level", "State Level CPI Rural/Urban"),

    # Steel & cross-industry
    ("93ab92b0-f010-46ea-be17-4bcd3d276c17", "steel_prices", "Steel Prices Delhi Market"),
    ("0be00b95-8871-493b-b4a3-a7e33d52352c", "textile_prices", "Textile Product Prices"),

    # Fertilizer (chemical industry input)
    ("18553bcf-7703-4951-9e15-8d78856f3593", "fertilizer_import_port", "Port-wise Fertilizer Import"),
    ("cd5141b6-b77a-4958-b633-1c25e574e213", "fertilizer_import_country", "Country-wise Fertilizer Import"),
    ("c7c7d147-5635-445c-ae05-cb3dfb68e3c0", "fertilizer_demand_supply", "Fertilizer Demand Supply 2019-2024"),

    # MSME/Industry
    ("4ec8fa64-ec26-4560-8cdc-3117e115756b", "oil_gas_cpsu", "Oil & Gas CPSU Summary"),
]


def curl_get(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                ["curl", "-s", "--max-time", "120", url],
                capture_output=True, text=True, timeout=130,
            )
            if result.returncode != 0:
                raise RuntimeError(f"curl failed (rc={result.returncode})")
            data = json.loads(result.stdout)
            if "error" in data:
                raise RuntimeError(f"API error: {data['error']}")
            return data
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  Retry {attempt+1}/{max_retries}: {e}")
                time.sleep(3)
            else:
                raise


def download_dataset(rid, label, desc, max_records=None):
    print(f"\n[{label}] {desc}")
    print(f"  ID: {rid}")

    # First get metadata with limit=0 to see total
    url = f"{BASE_URL}/{rid}?format=json&api-key={API_KEY}&limit=0"
    try:
        meta = curl_get(url)
    except Exception as e:
        print(f"  SKIPPED (meta fetch failed): {e}")
        return False

    total = meta.get("total", 0)
    fields = meta.get("field", [])
    print(f"  Total records: {total}")
    print(f"  Fields: {[f.get('id','') for f in fields[:10]]}...")

    if max_records and total > max_records:
        total = max_records
        print(f"  Capped to {max_records} records")

    if total == 0:
        print(f"  SKIPPED (no records)")
        return False

    # Paginate and download ALL records
    limit = 5000
    all_records = []
    offset = 0

    while offset < total:
        url = f"{BASE_URL}/{rid}?format=json&api-key={API_KEY}&limit={limit}&offset={offset}"
        try:
            data = curl_get(url)
            batch = data.get("records", [])
            all_records.extend(batch)
            offset += limit
            print(f"  Progress: {len(all_records)}/{total}", end="\r")
            time.sleep(0.5)  # Rate limiting
        except Exception as e:
            print(f"  FAILED at offset={offset}: {e}")
            # Try smaller batch
            if limit > 1000:
                limit = limit // 2
                print(f"  Retrying with limit={limit}")
                continue
            else:
                break

    print(f"  Downloaded: {len(all_records)} records")

    # Save metadata + records
    output = {
        "resource_id": rid,
        "label": label,
        "description": desc,
        "total": len(all_records),
        "fields": fields,
        "records": all_records,
    }

    out_path = RAW_DIR / f"{label}.json"
    with open(out_path, "w") as f:
        json.dump(output, f, ensure_ascii=False, default=str)
    print(f"  Saved to {out_path} ({os.path.getsize(out_path)/1024/1024:.1f} MB)")

    return True


def main():
    print("=" * 80)
    print("DOWNLOADING DATA.GOV.IN DATASETS")
    print("=" * 80)

    success = 0
    failed = 0

    for rid, label, desc in DATASETS:
        out_path = RAW_DIR / f"{label}.json"
        if out_path.exists():
            print(f"\n[{label}] Already exists, skipping ({out_path.stat().st_size/1024/1024:.1f} MB)")
            success += 1
            continue
        try:
            if download_dataset(rid, label, desc):
                success += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1

    print(f"\n{'=' * 80}")
    print(f"Done! Success: {success}, Failed: {failed}")
    print(f"Data saved to {RAW_DIR}")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
