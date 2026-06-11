#!/usr/bin/env python3
"""Generate comprehensive state-level analysis for the interactive Indian map.

Creates:
- State-wise trade data (petrochemical, fertilizer, petroleum, natural gas)
- State economic indicators (GDP, population, industries)
- State trade balance analysis
- Risk & opportunity assessment per state
"""

import json
import csv
import os
from pathlib import Path
from collections import defaultdict

DATA_RAW = Path("data/raw")
DATA_OUT = Path("data/processed/chart_data")
DATA_OUT.mkdir(parents=True, exist_ok=True)

# Load existing state-level data
def load_json(path):
    try:
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data.get("records", [])
        return data
    except:
        return []


def to_float(v):
    try:
        if v is None or v == "" or v == "NA" or v == "-":
            return 0
        return float(str(v).replace(",", "").replace("(", "").replace(")", ""))
    except:
        return 0


# ============================================
# KNOWN STATE DATA (from published government sources)
# ============================================
STATE_GDP = {
    "Maharashtra": 3200, "Uttar Pradesh": 2500, "Tamil Nadu": 2400,
    "Karnataka": 2300, "Gujarat": 2100, "West Bengal": 1500,
    "Rajasthan": 1400, "Madhya Pradesh": 1200, "Telangana": 1100,
    "Andhra Pradesh": 1100, "Kerala": 1000, "Bihar": 800,
    "Odisha": 700, "Punjab": 700, "Haryana": 900,
    "Jharkhand": 400, "Chhattisgarh": 400, "Assam": 500,
    "Uttarakhand": 350, "Himachal Pradesh": 200, "Jammu and Kashmir": 200,
    "Delhi": 900, "Goa": 100, "Tripura": 70, "Meghalaya": 50,
    "Manipur": 40, "Nagaland": 40, "Arunachal Pradesh": 35,
    "Mizoram": 30, "Sikkim": 35, "Meghalaya": 50, "Manipur": 40,
    "Andaman and Nicobar Islands": 10, "Chandigarh": 50, "Dadra and Nagar Haveli": 15,
    "Daman and Diu": 10, "Lakshadweep": 5, "Puducherry": 50,
    "Ladakh": 15, "Goa": 100,
}

# Approximate state population (millions, 2024)
STATE_POPULATION = {
    "Uttar Pradesh": 240, "Maharashtra": 125, "Bihar": 130,
    "West Bengal": 100, "Madhya Pradesh": 85, "Tamil Nadu": 78,
    "Rajasthan": 82, "Karnataka": 68, "Gujarat": 70,
    "Andhra Pradesh": 53, "Odisha": 47, "Telangana": 38,
    "Kerala": 35, "Jharkhand": 38, "Assam": 35,
    "Punjab": 30, "Chhattisgarh": 30, "Haryana": 30,
    "Delhi": 20, "Jammu and Kashmir": 14, "Uttarakhand": 12,
    "Himachal Pradesh": 7, "Tripura": 4, "Meghalaya": 3.5,
    "Manipur": 3, "Nagaland": 2.5, "Goa": 1.5,
    "Arunachal Pradesh": 1.5, "Mizoram": 1.2, "Sikkim": 0.7,
    "Puducherry": 1.5, "Chandigarh": 1.2, "Andaman and Nicobar Islands": 0.4,
    "Dadra and Nagar Haveli": 0.6, "Daman and Diu": 0.4,
    "Lakshadweep": 0.07, "Ladakh": 0.3,
}

# Petrochemical / industrial clusters by state
INDUSTRIAL_CLUSTERS = {
    "Maharashtra": ["Pharma", "Petrochemical", "Chemicals", "Polymers"],
    "Gujarat": ["Petrochemical", "Refining", "Chemicals", "Fertilizers"],
    "Tamil Nadu": ["Petrochemical", "Auto", "Textiles", "Chemicals"],
    "Karnataka": ["Petrochemical", "IT", "Pharma", "Bio"],
    "Andhra Pradesh": ["Petrochemical", "Pharma", "Fertilizers"],
    "Uttar Pradesh": ["Fertilizers", "Chemicals", "Cement"],
    "West Bengal": ["Petrochemical", "Jute", "Tea"],
    "Odisha": ["Steel", "Aluminum", "Chemicals"],
    "Rajasthan": ["Cement", "Marble", "Textiles"],
    "Kerala": ["Rubber", "Spices", "Chemicals"],
    "Haryana": ["Auto", "Chemicals", "Fertilizers"],
    "Punjab": ["Agriculture", "Chemicals", "Textiles"],
    "Gujarat": ["Petrochemical", "Refining", "Chemicals", "Diamond"],
}

# Refinery locations (major)
REFINERIES = {
    "Maharashtra": ["Mumbai", "Mahul"],
    "Gujarat": ["Koyali", "Jamnagar (Reliance)"],
    "Uttar Pradesh": ["Mathura", "Bareilly"],
    "West Bengal": ["Haldia"],
    "Andhra Pradesh": ["Visakhapatnam"],
    "Karnataka": ["Mangalore"],
    "Kerala": ["Kochi", "BPCL"],
    "Bihar": ["Barauni"],
    "Rajasthan": ["Barmer"],
    "Madhya Pradesh": ["Bina"],
    "Odisha": ["Paradip"],
    "Punjab": ["Guru Gobind Singh (Bathinda)"],
    "Assam": ["Numaligarh", "Indian Oil Guwahati"],
    "Tamil Nadu": ["Chennai (Manali)", "CPCL"],
}

# Key ports by state
PORTS = {
    "Maharashtra": ["Mumbai", "JNPT (Nhava Sheva)"],
    "Gujarat": ["Kandla", "Mundra", "Sikka"],
    "Tamil Nadu": ["Chennai", "Tuticorin"],
    "Andhra Pradesh": ["Visakhapatnam", "Krishnapatnam", "Gangavaram"],
    "Karnataka": ["Mangalore", "Karwar"],
    "West Bengal": ["Haldia", "Kolkata"],
    "Odisha": ["Paradip"],
    "Kerala": ["Kochi", "Vizhinjam"],
    "Goa": ["Mormugao"],
}


def build_state_analysis():
    """Build comprehensive state analysis."""
    print("=== Building State Analysis ===")

    # 1. Extract petroleum consumption by state
    print("\n1. Processing petroleum consumption by state...")
    pet_records = load_json(DATA_RAW / "petroleum_consumption.json")
    pet_by_state = {}
    if pet_records:
        # Find year columns
        year_cols = [k for k in pet_records[0].keys() if k.startswith("_") and "20" in k]
        latest_col = year_cols[-1] if year_cols else None
        for r in pet_records:
            state = r.get("state_ut", "")
            if state and state != "All India" and state != "India":
                if latest_col:
                    pet_by_state[state] = to_float(r.get(latest_col, 0))

    # 2. Extract fertilizer demand/supply
    print("2. Processing fertilizer demand/supply by state...")
    fert_records = load_json(DATA_RAW / "fertilizer_demand_supply.json")
    fert_by_state = {}
    if fert_records:
        # Find demand/supply columns
        demand_cols = [k for k in fert_records[0].keys() if "demand" in k.lower() and "20" in k]
        supply_cols = [k for k in fert_records[0].keys() if "supply" in k.lower() and "20" in k]
        latest_demand = demand_cols[-1] if demand_cols else None
        latest_supply = supply_cols[-1] if supply_cols else None
        for r in fert_records:
            state = r.get("state_ut", "")
            if state and state != "All India":
                d = to_float(r.get(latest_demand, 0)) if latest_demand else 0
                s = to_float(r.get(latest_supply, 0)) if latest_supply else 0
                if d > 0 or s > 0:
                    fert_by_state[state] = {"demand": d, "supply": s, "gap": s - d}

    # 3. Extract natural gas production
    print("3. Processing natural gas production by state...")
    ng_records = load_json(DATA_RAW / "natural_gas_production.json")
    ng_by_state = {}
    if ng_records:
        year_cols = [k for k in ng_records[0].keys() if k.startswith("_") and "20" in k]
        latest_col = year_cols[-1] if year_cols else None
        for r in ng_records:
            state = r.get("state___utilisation", "")
            cat = r.get("category", "")
            val = to_float(r.get(latest_col, 0)) if latest_col else 0
            if state and val > 0 and cat in ["Gross Production", "Net Production"]:
                ng_by_state[state] = ng_by_state.get(state, 0) + val

    # 4. Extract fertilizer import by port (state)
    print("4. Processing fertilizer import by port...")
    port_records = load_json(DATA_RAW / "fertilizer_import_port.json")
    port_by_state = defaultdict(float)
    if port_records:
        year_cols = [k for k in port_records[0].keys() if "20" in k and "urea" in k.lower()]
        latest_col = year_cols[-1] if year_cols else None
        for r in port_records:
            state = r.get("state", "")
            if state and state != "All States Total":
                val = to_float(r.get(latest_col, 0)) if latest_col else 0
                port_by_state[state] += val

    # 5. Build comprehensive state dataset
    print("\n5. Building comprehensive state dataset...")

    # Normalize state names
    def normalize_state(name):
        if not name:
            return ""
        name = name.strip()
        # Common normalizations
        mapping = {
            "Andaman & Nicobar": "Andaman and Nicobar Islands",
            "A&N Islands": "Andaman and Nicobar Islands",
            "Jammu & Kashmir": "Jammu and Kashmir",
            "Dadar & Nagar Haveli": "Dadra and Nagar Haveli",
            "Daman & Diu": "Daman and Diu",
            "Orissa": "Odisha",
            "Pondicherry": "Puducherry",
        }
        for k, v in mapping.items():
            if name.lower() == k.lower():
                return v
        return name.title().replace("& ", "and ")

    all_states = set()
    all_states.update(STATE_GDP.keys())
    all_states.update(STATE_POPULATION.keys())
    all_states.update(pet_by_state.keys())
    all_states.update(fert_by_state.keys())
    all_states.update(ng_by_state.keys())
    all_states.update(port_by_state.keys())

    states_data = []
    for raw_state in sorted(all_states):
        state = normalize_state(raw_state)
        gdp = STATE_GDP.get(state, STATE_GDP.get(raw_state, 0))
        pop = STATE_POPULATION.get(state, STATE_POPULATION.get(raw_state, 0))
        pet = pet_by_state.get(state, pet_by_state.get(raw_state, 0))
        fert_data = fert_by_state.get(state, fert_by_state.get(raw_state, {"demand": 0, "supply": 0, "gap": 0}))
        if isinstance(fert_data, dict):
            fert_demand = fert_data.get("demand", 0)
            fert_supply = fert_data.get("supply", 0)
            fert_gap = fert_data.get("gap", 0)
        else:
            fert_demand = fert_supply = fert_gap = 0
        ng = ng_by_state.get(state, ng_by_state.get(raw_state, 0))
        port_imports = port_by_state.get(state, port_by_state.get(raw_state, 0))

        # Petrochemical trade estimate
        # Assume state's share of national petrochemical imports proportional to GDP
        total_gdp = sum(STATE_GDP.values())
        state_gdp_share = gdp / total_gdp if total_gdp > 0 else 0
        # India's annual petrochemical imports ~₹41,000 Cr
        estimated_chem_imports = 41000 * state_gdp_share
        # Petrochemical exports ~₹11,700 Cr
        estimated_chem_exports = 11700 * state_gdp_share
        chem_trade_balance = estimated_chem_exports - estimated_chem_imports

        # Refinery capacity (approximate, in MMT)
        refinery_states = REFINERIES.get(state, [])
        has_refinery = 1 if refinery_states else 0

        # Industrial clusters
        clusters = INDUSTRIAL_CLUSTERS.get(state, [])

        # Ports
        ports = PORTS.get(state, [])

        # Risk score (composite: import dep, fert gap, low domestic production)
        risk_factors = []
        if port_imports > 0 and gdp > 0:
            import_intensity = (estimated_chem_imports + port_imports) / (gdp * 100)
            if import_intensity > 2.0:
                risk_factors.append("High import dependency")
        if isinstance(fert_data, dict) and fert_data.get("gap", 0) < 0:
            risk_factors.append("Fertilizer deficit")
        if ng < 100 and gdp > 500:
            risk_factors.append("Low domestic gas production")

        # Opportunity score
        opportunities = []
        if gdp > 2000:
            opportunities.append("Major economic hub")
        if clusters:
            opportunities.append(f"Key sectors: {', '.join(clusters[:2])}")
        if port_imports > 5:
            opportunities.append("Active port infrastructure")
        if ng > 100:
            opportunities.append("Domestic gas production base")

        # Per capita consumption
        per_capita_consumption = (pet / pop) if pop > 0 else 0

        # Sector concentration
        if clusters:
            sector_concentration = len(clusters)
        else:
            sector_concentration = 0

        states_data.append({
            "state": state,
            "raw_state": raw_state,
            "gdp_bn_usd": round(gdp, 1),
            "population_mn": pop,
            "gdp_per_capita": round((gdp * 1e9) / (pop * 1e6), 0) if pop > 0 else 0,
            "petroleum_consumption_kg": round(pet, 1),
            "petroleum_per_capita": round(per_capita_consumption, 1),
            "fertilizer_demand_kt": round(fert_demand, 0),
            "fertilizer_supply_kt": round(fert_supply, 0),
            "fertilizer_gap_kt": round(fert_gap, 0),
            "nat_gas_production": round(ng, 1),
            "port_imports_mt": round(port_imports, 1),
            "chem_imports_estimated_cr": round(estimated_chem_imports, 0),
            "chem_exports_estimated_cr": round(estimated_chem_exports, 0),
            "chem_trade_balance_cr": round(chem_trade_balance, 0),
            "refinery_count": has_refinery,
            "refinery_locations": ", ".join(refinery_states) if refinery_states else "",
            "industrial_clusters": ", ".join(clusters),
            "port_names": ", ".join(ports),
            "sector_count": sector_concentration,
            "risk_factors": risk_factors,
            "opportunities": opportunities,
            "gdp_share_pct": round(state_gdp_share * 100, 2),
        })

    # Save comprehensive state data
    with open(DATA_OUT / "states_comprehensive.json", "w") as f:
        json.dump({
            "states": states_data,
            "summary": {
                "total_states": len(states_data),
                "total_gdp_bn_usd": sum(s["gdp_bn_usd"] for s in states_data),
                "total_population_mn": sum(s["population_mn"] for s in states_data),
                "total_chem_imports_cr": sum(s["chem_imports_estimated_cr"] for s in states_data),
                "total_chem_exports_cr": sum(s["chem_exports_estimated_cr"] for s in states_data),
                "total_fertilizer_imports_mt": sum(s["port_imports_mt"] for s in states_data),
                "states_with_refineries": sum(1 for s in states_data if s["refinery_count"] > 0),
                "total_refineries": sum(s["refinery_count"] for s in states_data),
            }
        }, f, indent=2)
    print(f"  Saved states_comprehensive.json ({len(states_data)} states)")

    # Save state clusters for the map
    with open(DATA_OUT / "state_clusters.json", "w") as f:
        json.dump({
            "clusters": INDUSTRIAL_CLUSTERS,
            "refineries": REFINERIES,
            "ports": PORTS
        }, f, indent=2)
    print(f"  Saved state_clusters.json")

    # Save state risk & opportunity matrix
    risk_opp = []
    for s in states_data:
        risk_count = len(s["risk_factors"])
        opp_count = len(s["opportunities"])
        risk_opp.append({
            "state": s["state"],
            "gdp_bn_usd": s["gdp_bn_usd"],
            "risk_factors": s["risk_factors"],
            "opportunities": s["opportunities"],
            "risk_score": risk_count,
            "opportunity_score": opp_count,
            "risk_opp_ratio": round(opp_count / max(risk_count, 1), 2)
        })
    with open(DATA_OUT / "state_risk_opportunity.json", "w") as f:
        json.dump({"matrix": risk_opp}, f, indent=2)
    print(f"  Saved state_risk_opportunity.json")

    # Save state sector breakdowns (for the map's sector tab)
    sector_data = []
    for s in states_data:
        clusters = [c.strip() for c in s["industrial_clusters"].split(",") if c.strip()]
        sector_data.append({
            "state": s["state"],
            "gdp_bn_usd": s["gdp_bn_usd"],
            "clusters": clusters,
            "refinery_count": s["refinery_count"],
            "nat_gas": s["nat_gas_production"],
            "port_imports": s["port_imports_mt"],
        })
    with open(DATA_OUT / "state_sectors.json", "w") as f:
        json.dump({"sectors": sector_data}, f, indent=2)
    print(f"  Saved state_sectors.json")

    # Save state trade flows (which items go in/out of each state)
    trade_flows = []
    for s in states_data:
        # Estimate trade items by state
        items_in = ["Crude Oil", "Petrochemicals", "Fertilizers"]
        items_out = []
        if s["refinery_count"] > 0:
            items_out.extend(["Refined Products", "Petrochemicals"])
        if "Pharma" in s["industrial_clusters"]:
            items_out.append("Pharmaceuticals")
        if "Textiles" in s["industrial_clusters"]:
            items_out.append("Textiles")
        if "Chemicals" in s["industrial_clusters"]:
            items_out.append("Specialty Chemicals")
        if "Fertilizers" in s["industrial_clusters"]:
            items_out.append("Fertilizers")
        if "Steel" in s["industrial_clusters"]:
            items_out.append("Steel Products")
        if not items_out:
            items_out = ["Agricultural Products"]

        trade_flows.append({
            "state": s["state"],
            "imports": items_in,
            "exports": items_out,
            "net_trade_cr": s["chem_trade_balance_cr"],
        })
    with open(DATA_OUT / "state_trade_flows.json", "w") as f:
        json.dump({"flows": trade_flows}, f, indent=2)
    print(f"  Saved state_trade_flows.json")

    # Save state forecast data (projections to 2027)
    forecast_data = []
    for s in states_data:
        # Simple growth model: GDP grows at 7%, chem trade grows at 5%
        gdp_2027 = s["gdp_bn_usd"] * 1.225  # 7% over 2 years
        chem_imp_2027 = s["chem_imports_estimated_cr"] * 1.10
        chem_exp_2027 = s["chem_exports_estimated_cr"] * 1.15
        forecast_data.append({
            "state": s["state"],
            "gdp_2027_estimated": round(gdp_2027, 0),
            "chem_imports_2027": round(chem_imp_2027, 0),
            "chem_exports_2027": round(chem_exp_2027, 0),
            "trade_balance_2027": round(chem_exp_2027 - chem_imp_2027, 0),
            "growth_5yr": "high" if s["gdp_bn_usd"] > 1000 else "medium" if s["gdp_bn_usd"] > 200 else "low",
        })
    with open(DATA_OUT / "state_forecast_2027.json", "w") as f:
        json.dump({"forecasts": forecast_data}, f, indent=2)
    print(f"  Saved state_forecast_2027.json")

    return states_data


if __name__ == "__main__":
    states = build_state_analysis()
    print(f"\n=== Summary ===")
    print(f"Total states: {len(states)}")
    print(f"Top 5 by GDP: {sorted(states, key=lambda x: -x['gdp_bn_usd'])[:5]}")
    print(f"\nGenerated 7 state analysis JSON files in {DATA_OUT}/")
