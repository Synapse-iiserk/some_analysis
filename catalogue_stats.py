#!/usr/bin/env python3
"""Generate summary statistics from the catalogue."""

import json
import os
import sys
from collections import Counter

INPUT_BASIC = "catalogue_basic.jsonl"
INPUT_ENRICHED = "catalogue_full.jsonl"
OUTPUT = "catalogue_summary.json"


def load_records():
    for fname in [INPUT_ENRICHED, INPUT_BASIC]:
        if os.path.exists(fname):
            print(f"Loading {fname}...")
            records = []
            with open(fname, "r") as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
            print(f"Loaded {len(records):,} records")
            return records, fname
    print("Error: No catalogue file found.")
    sys.exit(1)


def main():
    records, source_file = load_records()
    total = len(records)

    org_type_counter = Counter()
    source_counter = Counter()
    org_counter = Counter()
    sector_counter = Counter()
    field_type_counter = Counter()
    year_counter = Counter()
    public_count = 0
    visualizable_count = 0
    has_fields = 0
    total_fields = 0

    for rec in records:
        ot = rec.get("org_type", "unknown")
        if isinstance(ot, list):
            ot = ", ".join(ot) if ot else "unknown"
        org_type_counter[ot] += 1

        src = rec.get("source", "unknown")
        if isinstance(src, list):
            src = ", ".join(src) if src else "unknown"
        source_counter[src] += 1

        if rec.get("is_public") == "1":
            public_count += 1
        if str(rec.get("visualizable", "0")) == "1":
            visualizable_count += 1

        cd = rec.get("created_date", "")
        if cd and len(cd) >= 4:
            year_counter[cd[:4]] += 1

        fields = rec.get("fields", [])
        if fields:
            has_fields += 1
            total_fields += len(fields)
            for fi in fields:
                field_type_counter[fi.get("type", "unknown")] += 1

        # Enriched fields
        orgs = rec.get("org", [])
        if orgs:
            for o in (orgs if isinstance(orgs, list) else [orgs]):
                org_counter[o] += 1

        sectors = rec.get("sector", [])
        if sectors:
            for s in (sectors if isinstance(sectors, list) else [sectors]):
                sector_counter[s] += 1

    summary = {
        "source_file": source_file,
        "total_resources": total,
        "public_resources": public_count,
        "visualizable_resources": visualizable_count,
        "resources_with_fields": has_fields,
        "total_field_definitions": total_fields,
        "avg_fields_per_resource": round(total_fields / max(has_fields, 1), 1),
        "by_org_type": dict(org_type_counter.most_common()),
        "top_30_sources": dict(source_counter.most_common(30)),
        "top_50_organizations": dict(org_counter.most_common(50)),
        "top_50_sectors": dict(sector_counter.most_common(50)),
        "field_type_distribution": dict(field_type_counter.most_common()),
        "by_year": dict(sorted(year_counter.items())),
    }

    with open(OUTPUT, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"DATA.GOV.IN CATALOGUE SUMMARY")
    print(f"{'='*60}")
    print(f"Total resources:       {total:,}")
    print(f"Public resources:      {public_count:,}")
    print(f"Visualizable:          {visualizable_count:,}")
    print(f"With field defs:       {has_fields:,}")
    print(f"Total field defs:      {total_fields:,}")
    print(f"Avg fields/resource:   {round(total_fields/max(has_fields,1),1)}")
    print(f"\nBy org type:")
    for k, v in org_type_counter.most_common():
        print(f"  {k or '(empty)':30s} {v:>8,}")
    print(f"\nTop 20 sources:")
    for k, v in source_counter.most_common(20):
        print(f"  {k or '(empty)':40s} {v:>8,}")
    print(f"\nTop 15 organizations (enriched):")
    for k, v in org_counter.most_common(15):
        print(f"  {str(k):55s} {v:>6,}")
    print(f"\nTop 15 sectors (enriched):")
    for k, v in sector_counter.most_common(15):
        print(f"  {str(k):40s} {v:>6,}")
    print(f"\nField types:")
    for k, v in field_type_counter.most_common():
        print(f"  {str(k or '(none)'):20s} {v:>10,}")
    print(f"\nBy year (creation):")
    for k, v in sorted(year_counter.items(), key=lambda x: str(x[0])):
        bar = "#" * min(v // 1000, 50)
        print(f"  {str(k or '(none)'):8s}: {v:>8,}  {bar}")
    print(f"\n{'='*60}")
    print(f"Summary saved to {OUTPUT}")


if __name__ == "__main__":
    main()
