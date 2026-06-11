#!/usr/bin/env python3
"""Enrich catalogue using curl with proper rate limiting.

Respects the 1000 req/hr rate limit by using a token bucket.
Uses 5 parallel workers with delays to stay under limit.
Supports resume.
"""

import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque

from tqdm import tqdm

API_KEY = os.getenv("DATA_GOV_API_KEY", "579b464db66ec23bdd000001eb9e9125ad9441cc4b9ea4e1465edbac")
BASE_URL = "https://api.data.gov.in/resource"
INPUT_FILE = "catalogue_basic.jsonl"
OUTPUT_FILE = "catalogue_enriched_v2.jsonl"

MAX_WORKERS = 5
# Rate limit: 1000/hr = ~16.7/min = ~1 req every 3.6s
# With 5 workers, each worker does ~1 req every 18s
RATE_INTERVAL = 3.6  # seconds between requests globally

write_lock = threading.Lock()
request_times = deque()
rate_lock = threading.Lock()


def rate_limit():
    """Simple rate limiter: ensure we don't exceed RATE_LIMIT per hour."""
    with rate_lock:
        now = time.time()
        # Remove timestamps older than 1 hour
        while request_times and request_times[0] < now - 3600:
            request_times.popleft()
        if len(request_times) >= 950:  # leave some buffer
            # Sleep until the oldest request is > 1 hour ago
            sleep_time = request_times[0] + 3600 - now + 1
            if sleep_time > 0:
                tqdm.write(f"  Rate limit: sleeping {sleep_time:.0f}s...")
                time.sleep(sleep_time)
        request_times.append(time.time())


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


def enrich_record(basic_rec):
    rid = basic_rec["id"]
    rate_limit()
    try:
        url = f"{BASE_URL}/{rid}?format=json&api-key={API_KEY}&limit=0"
        data = curl_get(url)
        meta = {
            "org": data.get("org", []),
            "sector": data.get("sector", []),
            "catalog_uuid": data.get("catalog_uuid", ""),
        }
        return {**basic_rec, **meta}, None
    except Exception as e:
        return None, f"{rid}: {e}"


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

    # Estimate time: 1000 req/hr max
    est_hours = len(remaining) / 950  # 950 to leave buffer
    print(f"Estimated time: {est_hours:.1f} hours (respecting 1000 req/hr rate limit)")

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
                    if enriched_count % 100 == 0 and enriched_count > 0:
                        pbar.set_postfix(ok=enriched_count, fail=len(failed))

    print(f"\nDone!")
    print(f"  Enriched: {enriched_count:,}")
    print(f"  Failed: {len(failed):,}")
    if failed:
        with open("enrich_failures_v2.json", "w") as f:
            json.dump(failed, f, indent=2)
        print(f"  Failures saved to enrich_failures_v2.json")


if __name__ == "__main__":
    main()
