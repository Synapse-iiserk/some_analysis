#!/usr/bin/env python3
"""Retry failed batches from the basic catalogue fetch."""

import json
import os
import subprocess
import time

from tqdm import tqdm

API_KEY = os.getenv("DATA_GOV_API_KEY", "579b464db66ec23bdd000001eb9e9125ad9441cc4b9ea4e1465edbac")
BASE_URL = "https://api.data.gov.in/lists"
OUTPUT_FILE = "catalogue_basic.jsonl"

# The 5 failed offsets
FAILED_OFFSETS = [22000, 70000, 114000, 165000, 204000]
RETRY_BATCH = 500  # smaller batches for retries


def curl_get(url):
    result = subprocess.run(
        ["curl", "-s", "--max-time", "120", url],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed: {result.stderr[:200]}")
    return json.loads(result.stdout)


def main():
    # Load existing IDs
    existing_ids = set()
    with open(OUTPUT_FILE, "r") as f:
        for line in f:
            try:
                rec = json.loads(line)
                existing_ids.add(rec["id"])
            except (json.JSONDecodeError, KeyError):
                pass
    print(f"Existing records: {len(existing_ids):,}")

    added = 0
    with open(OUTPUT_FILE, "a") as f:
        for offset in FAILED_OFFSETS:
            print(f"\nRetrying offset {offset} in batches of {RETRY_BATCH}...")
            # Figure out how many records at this offset (fetch total first)
            total_url = (
                f"{BASE_URL}?format=json&api-key={API_KEY}"
                f"&filters%5Bactive%5D=1&offset={offset}&limit=0"
            )
            try:
                data = curl_get(total_url)
                remaining = min(data["total"] - offset, 1000)
            except Exception as e:
                print(f"  Can't get count: {e}")
                remaining = 1000

            sub_offset = 0
            while sub_offset < remaining:
                batch_size = min(RETRY_BATCH, remaining - sub_offset)
                url = (
                    f"{BASE_URL}?format=json&api-key={API_KEY}"
                    f"&filters%5Bactive%5D=1&offset={offset + sub_offset}&limit={batch_size}"
                )
                retries = 3
                while retries > 0:
                    try:
                        data = curl_get(url)
                        records = data.get("records", [])
                        new_count = 0
                        for rec in records:
                            rid = rec.get("index_name")
                            if rid and rid not in existing_ids:
                                compact = {
                                    "id": rid,
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
                                existing_ids.add(rid)
                                new_count += 1
                        added += new_count
                        print(f"  offset={offset + sub_offset}: +{new_count} records")
                        break
                    except Exception as e:
                        retries -= 1
                        if retries > 0:
                            print(f"  Retry: {e}")
                            time.sleep(3)
                        else:
                            print(f"  FAILED: {e}")
                sub_offset += batch_size
                time.sleep(0.3)

    print(f"\nDone! Added {added} records")
    print(f"Total now: {len(existing_ids):,}")


if __name__ == "__main__":
    main()
