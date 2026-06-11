#!/usr/bin/env python3
"""Fetch basic catalogue from data.gov.in /lists endpoint.

Uses curl via subprocess for reliability (Python requests times out on this API).
Paginates through all active resources in batches of 1000,
saving each record as a JSON line to catalogue_basic.jsonl.
"""

import json
import os
import subprocess
import time

from tqdm import tqdm

API_KEY = os.getenv("DATA_GOV_API_KEY", "579b464db66ec23bdd000001eb9e9125ad9441cc4b9ea4e1465edbac")
BASE_URL = "https://api.data.gov.in/lists"
BATCH_SIZE = 1000
OUTPUT_FILE = "catalogue_basic.jsonl"


def curl_get(url):
    """Fetch URL using curl, return parsed JSON."""
    result = subprocess.run(
        ["curl", "-s", "--max-time", "120", url],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed (rc={result.returncode}): {result.stderr}")
    return json.loads(result.stdout)


def build_url(offset, limit):
    return (
        f"{BASE_URL}?format=json&api-key={API_KEY}"
        f"&filters%5Bactive%5D=1&offset={offset}&limit={limit}"
    )


def get_total():
    data = curl_get(build_url(0, 0))
    return data["total"]


def fetch_batch(offset, limit):
    return curl_get(build_url(offset, limit))


def main():
    total = get_total()
    print(f"Total active resources: {total:,}")

    total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"Batches to fetch (size {BATCH_SIZE}): {total_batches}")

    fetched = 0
    failed_batches = []

    with open(OUTPUT_FILE, "w") as f:
        pbar = tqdm(total=total, unit="rec", desc="Fetching catalogue")
        for batch_idx in range(total_batches):
            offset = batch_idx * BATCH_SIZE
            retries = 3
            while retries > 0:
                try:
                    data = fetch_batch(offset, BATCH_SIZE)
                    records = data.get("records", [])
                    for rec in records:
                        compact = {
                            "id": rec.get("index_name"),
                            "title": rec.get("title", ""),
                            "desc": rec.get("desc", ""),
                            "source": rec.get("source", ""),
                            "org_type": rec.get("org_type", ""),
                            "is_public": rec.get("is_public", ""),
                            "visualizable": rec.get("visualizable", 0),
                            "fields": [
                                {"id": fi.get("id"), "name": fi.get("name"), "type": fi.get("type")}
                                for fi in rec.get("field", [])
                            ],
                            "created_date": rec.get("created_date", ""),
                            "updated_date": rec.get("updated_date", ""),
                        }
                        f.write(json.dumps(compact, ensure_ascii=False) + "\n")
                    fetched += len(records)
                    pbar.update(len(records))
                    break
                except Exception as e:
                    retries -= 1
                    if retries > 0:
                        tqdm.write(f"  Retry batch {batch_idx} (offset={offset}): {e}")
                        time.sleep(3)
                    else:
                        tqdm.write(f"  FAILED batch {batch_idx} (offset={offset}): {e}")
                        failed_batches.append(offset)
            time.sleep(0.2)

        pbar.close()

    print(f"\nDone!")
    print(f"  Fetched: {fetched:,} records")
    print(f"  Failed batches: {len(failed_batches)}")
    if failed_batches:
        print(f"  Failed offsets: {failed_batches}")
    print(f"  Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
