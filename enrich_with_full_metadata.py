#!/usr/bin/env python3
"""Enrich basic catalogue with full metadata from /resource/{UUID}.

Uses curl via subprocess for reliability.
Reads catalogue_basic.jsonl, fetches org/sector/catalog_uuid for each
resource using ThreadPoolExecutor, and saves to catalogue_full.jsonl.

Supports resume: skips UUIDs already present in the output file.
"""

import json
import os
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

API_KEY = os.getenv("DATA_GOV_API_KEY", "579b464db66ec23bdd000001eb9e9125ad9441cc4b9ea4e1465edbac")
BASE_URL = "https://api.data.gov.in/resource"
INPUT_FILE = "catalogue_basic.jsonl"
OUTPUT_FILE = "catalogue_full.jsonl"

MAX_WORKERS = 50
write_lock = threading.Lock()


def curl_get(url):
    result = subprocess.run(
        ["curl", "-s", "--max-time", "30", url],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed: {result.stderr[:200]}")
    return json.loads(result.stdout)


def load_done_ids():
    done = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    done.add(rec["id"])
                except (json.JSONDecodeError, KeyError):
                    pass
    return done


def fetch_resource_meta(resource_id):
    url = f"{BASE_URL}/{resource_id}?format=json&api-key={API_KEY}&limit=0"
    data = curl_get(url)
    return {
        "org": data.get("org", []),
        "sector": data.get("sector", []),
        "catalog_uuid": data.get("catalog_uuid", ""),
    }


def enrich_record(basic_rec):
    rid = basic_rec["id"]
    try:
        meta = fetch_resource_meta(rid)
        return {**basic_rec, **meta}, None
    except Exception as e:
        return None, f"{rid}: {e}"


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Run fetch_basic_catalogue.py first.")
        sys.exit(1)

    print(f"Loading {INPUT_FILE}...")
    with open(INPUT_FILE, "r") as f:
        basic_records = [json.loads(line) for line in f if line.strip()]
    print(f"Loaded {len(basic_records):,} basic records")

    done_ids = load_done_ids()
    remaining = [r for r in basic_records if r["id"] not in done_ids]
    print(f"Already enriched: {len(done_ids):,}")
    print(f"Remaining: {len(remaining):,}")

    if not remaining:
        print("Nothing to enrich. All done!")
        return

    failed = []
    enriched_count = 0

    with open(OUTPUT_FILE, "a") as out_f:
        with tqdm(total=len(remaining), unit="rec", desc="Enriching") as pbar:
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {
                    executor.submit(enrich_record, rec): rec
                    for rec in remaining
                }
                for future in as_completed(futures):
                    result, error = future.result()
                    if error:
                        failed.append(error)
                    elif result:
                        with write_lock:
                            out_f.write(json.dumps(result, ensure_ascii=False) + "\n")
                            out_f.flush()
                        enriched_count += 1
                    pbar.update(1)
                    if enriched_count % 500 == 0 and enriched_count > 0:
                        pbar.set_postfix(ok=enriched_count, fail=len(failed))

    print(f"\nDone!")
    print(f"  Enriched: {enriched_count:,}")
    print(f"  Failed: {len(failed):,}")
    if failed:
        print(f"  First 10 failures:")
        for e in failed[:10]:
            print(f"    {e}")
        with open("enrich_failures.json", "w") as f:
            json.dump(failed, f, indent=2)
        print(f"  All failures saved to enrich_failures.json")


if __name__ == "__main__":
    main()
