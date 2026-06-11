#!/usr/bin/env python3
"""Sync full metadata from data.gov.in using the datagovindia library.

Downloads metadata for all ~237k resources to a local SQLite database,
then exports enriched catalogue to JSONL.
"""

import json
import os
import sqlite3
import time

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DATA_GOV_API_KEY", "579b464db66ec23bdd000001eb9e9125ad9441cc4b9ea4e1465edbac")
DB_PATH = os.path.expanduser("~/datagovindia.db")
OUTPUT_FILE = "catalogue_enriched.jsonl"


def main():
    from datagovindia import DataGovIndia

    print("Initializing DataGovIndia client...")
    d = DataGovIndia(api_key=API_KEY)

    print("Syncing metadata to SQLite (this downloads metadata for all ~237k resources)...")
    print("This may take 1-5 minutes...")
    start = time.time()
    d.sync_metadata()
    elapsed = time.time() - start
    print(f"Sync completed in {elapsed:.1f}s")

    # Now query the SQLite database directly for richer metadata
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found after sync")
        return

    print(f"\nQuerying {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables: {tables}")

    # Check schema of main resource table
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [(row[1], row[2]) for row in cursor.fetchall()]
        print(f"\n{table} columns: {cols}")
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  Row count: {count:,}")

    conn.close()


if __name__ == "__main__":
    main()
