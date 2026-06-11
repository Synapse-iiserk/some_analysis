#!/usr/bin/env python3
"""Slow enrichment script - run in background over time.

Respects 1000 req/hr rate limit.
Processes ~950 records/hour.
Can be stopped and restarted (resume support).
"""

import json
import os
import subprocess
import sys
import threading
import time

from tqdm import tqdm

API_KEY = os.getenv("DATA_GOV_API_KEY", "579b464db66ec23bdd000001eb9e9125ad9441cc4b9ea4e1465edbac")
BASE_URL = "https://api.data.gov.in/resource"
INPUT_FILE = "catalogue_basic.jsonl"
OUTPUT_FILE = "catalogue_enriched_slow.jsonl"
FAILURES_FILE = "enrich_failures_slow.json"

# 1 request every 3.8 seconds = ~950/hr (under 1000 limit)
REQUEST_INTERVAL = 3.8


def curl_get(url):
    result = subprocess.run(
        ["curl", "-s", "--max-time", "60", url],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed: {result.stderr[:200]}")
    data = json.loads(result.stdout)
    if "error" in data:
        raise RuntimeError(f"API error: {data['error']}")
    return data


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


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
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

    est_hours = len(remaining) * REQUEST_INTERVAL / 3600
    est_days = est_hours / 24
    print(f"Estimated time: {est_hours:.1f} hours ({est_days:.1f} days)")
    print(f"Rate: 1 request every {REQUEST_INTERVAL}s = ~{3600/REQUEST_INTERVAL:.0f} req/hr")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Press Ctrl+C to stop (resume supported)\n")

    failed = []
    enriched_count = 0
    last_request_time = 0

    try:
        with open(OUTPUT_FILE, "a") as out_f:
            pbar = tqdm(total=len(remaining), unit="rec", desc="Enriching")
            for i, rec in enumerate(remaining):
                # Rate limit: wait between requests
                elapsed = time.time() - last_request_time
                if elapsed < REQUEST_INTERVAL:
                    time.sleep(REQUEST_INTERVAL - elapsed)

                rid = rec["id"]
                last_request_time = time.time()

                try:
                    url = f"{BASE_URL}/{rid}?format=json&api-key={API_KEY}&limit=0"
                    data = curl_get(url)
                    enriched = {
                        **rec,
                        "org": data.get("org", []),
                        "sector": data.get("sector", []),
                        "catalog_uuid": data.get("catalog_uuid", ""),
                    }
                    out_f.write(json.dumps(enriched, ensure_ascii=False) + "\n")
                    out_f.flush()
                    enriched_count += 1
                except Exception as e:
                    failed.append(f"{rid}: {e}")

                pbar.update(1)
                if enriched_count % 50 == 0 and enriched_count > 0:
                    pbar.set_postfix(ok=enriched_count, fail=len(failed))

            pbar.close()

    except KeyboardInterrupt:
        print(f"\n\nStopped! Progress saved.")
        print(f"  Enriched so far: {enriched_count:,}")
        print(f"  Failed so far: {len(failed):,}")
        print(f"  Resume by running this script again.")

    if failed:
        with open(FAILURES_FILE, "w") as f:
            json.dump(failed, f, indent=2)

    print(f"\nDone!")
    print(f"  Enriched: {enriched_count:,}")
    print(f"  Failed: {len(failed):,}")
    print(f"  Resume: run again to continue from where you left off")


if __name__ == "__main__":
    main()
