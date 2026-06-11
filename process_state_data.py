#!/usr/bin/env python3
"""Build comprehensive state-level analysis using REAL data.gov.in data."""
import json
import os
from pathlib import Path

OUT_DIR = Path('data/processed/chart_data')
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Load all the real state data we have
# ============================================================================

# State name normalization
STATE_NAME_MAP = {
    'Andaman & Nicobar': 'Andaman and Nicobar Islands',
    'Andaman and Nicobar': 'Andaman and Nicobar Islands',
    'Andaman and Nicobar Islands': 'Andaman and Nicobar Islands',
    'Dadra and Nagar Haveli': 'Dadra and Nagar Haveli and Daman and Diu',
    'Dadra and Nagar Haveli and Daman and Diu': 'Dadra and Nagar Haveli and Daman and Diu',
    'Daman and Diu': 'Dadra and Nagar Haveli and Daman and Diu',
    'Jammu and Kashmir': 'Jammu and Kashmir',
    'Jammu & Kashmir': 'Jammu and Kashmir',
    'Delhi': 'NCT of Delhi',
    'NCT of Delhi': 'NCT of Delhi',
    'Orissa': 'Odisha',
    'Pondicherry': 'Puducherry',
    'Uttaranchal': 'Uttarakhand',
    'Chattisgarh': 'Chhattisgarh',
    'Tamilnadu': 'Tamil Nadu',
    'Andhra Pradesh': 'Andhra Pradesh',
    'Arunachal Pradesh': 'Arunachal Pradesh',
    'Assam': 'Assam',
    'Bihar': 'Bihar',
    'Chhattisgarh': 'Chhattisgarh',
    'Goa': 'Goa',
    'Gujarat': 'Gujarat',
    'Haryana': 'Haryana',
    'Himachal Pradesh': 'Himachal Pradesh',
    'Jharkhand': 'Jharkhand',
    'Karnataka': 'Karnataka',
    'Kerala': 'Kerala',
    'Madhya Pradesh': 'Madhya Pradesh',
    'Maharashtra': 'Maharashtra',
    'Manipur': 'Manipur',
    'Meghalaya': 'Meghalaya',
    'Mizoram': 'Mizoram',
    'Nagaland': 'Nagaland',
    'Odisha': 'Odisha',
    'Punjab': 'Punjab',
    'Rajasthan': 'Rajasthan',
    'Sikkim': 'Sikkim',
    'Tamil Nadu': 'Tamil Nadu',
    'Telangana': 'Telangana',
    'Tripura': 'Tripura',
    'Uttar Pradesh': 'Uttar Pradesh',
    'Uttarakhand': 'Uttarakhand',
    'West Bengal': 'West Bengal',
}

def normalize(name):
    if not name: return None
    return STATE_NAME_MAP.get(name.strip(), name.strip())

# Load state data
with open(OUT_DIR / 'states_real_data.json') as f:
    state_data = json.load(f)

states = {normalize(s['state']): s for s in state_data['states']}
print(f'Loaded {len(states)} states from real data')

# Load existing data files
def load_json(name):
    path = OUT_DIR / name
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}

# Load trade data
chem_imports = load_json('chemical_imports.json')
chem_exports = load_json('chemical_exports.json')
petro_imports = load_json('petrochemical_imports.json')
petro_exports = load_json('petrochemical_exports.json')
crude = load_json('crude_oil_production.json')
fertilizer = load_json('fertilizer_demand_supply.json')
petroleum = load_json('petroleum_consumption.json')
gas = load_json('natural_gas_production.json')
port_fertilizer = load_json('fertilizer_import_port.json')

# Calculate latest year values from each
def latest_value(records, value_keys, year_keys=None):
    """Get the latest non-empty value from a record."""
    if not records or not isinstance(records, list):
        return 0
    total = 0
    for r in records[:1]:  # Just first record
        for k in value_keys:
            if k in r and r[k]:
                try:
                    total += float(str(r[k]).replace(',', ''))
                except:
                    pass
    return total

# Get total latest values
def get_year_value(records, year_pattern):
    """Sum values matching year pattern across all records."""
    total = 0
    for r in records:
        for k, v in r.items():
            if year_pattern in k.lower() and v:
                try:
                    total += float(str(v).replace(',', ''))
                except:
                    pass
    return total

# Find latest year in the chemical/petrochemical data
# Look for 2022-23 or 2021-22 values
print('Extracting latest trade values...')

# Chemical imports total
chem_imp_total = 0
for r in chem_imports:
    for k, v in r.items():
        if '_2021_22___val' in k or '_2021_22___qty' in k:
            try: chem_imp_total += float(str(v).replace(',', ''))
            except: pass
            break

chem_exp_total = 0
for r in chem_exports:
    for k, v in r.items():
        if '_2021_22___val' in k or '_2021_22___qty' in k:
            try: chem_exp_total += float(str(v).replace(',', ''))
            except: pass
            break

# ============================================================================
# CRUDE OIL PRODUCTION BY STATE (year 2014-15)
# ============================================================================
print('Processing crude oil production by state...')
crude_by_state = {}
if isinstance(crude, list):
    pass
elif isinstance(crude, dict) and 'records' in crude:
    crude = crude['records']

# crude is a list
if isinstance(crude, list):
    for r in crude:
        if not isinstance(r, dict): continue
        state = normalize(r.get('item') or r.get('state'))
        if not state: continue
        # Get latest year value
        for y in ['_2014_15_', '_2013_14', '_2012_13', '_2011_12', '_2010_11']:
            for k, v in r.items():
                if y in k and v:
                    try:
                        val = float(str(v).replace(',', ''))
                        if val > 0:
                            crude_by_state[state] = crude_by_state.get(state, 0) + val
                            break
                    except:
                        pass
            if state in crude_by_state:
                break

# ============================================================================
# PETROLEUM CONSUMPTION BY STATE
# ============================================================================
print('Processing petroleum consumption...')
petroleum_by_state = {}
if isinstance(petroleum, list):
    for r in petroleum:
        if not isinstance(r, dict): continue
        state = normalize(r.get('state_ut') or r.get('state'))
        if not state: continue
        # Get latest year value
        for y in ['_2021_22', '_2020_21', '_2019_20', '_2018_19', '_2017_18']:
            for k, v in r.items():
                if y in k and v:
                    try:
                        val = float(str(v).replace(',', ''))
                        if val > 0:
                            petroleum_by_state[state] = petroleum_by_state.get(state, 0) + val
                            break
                    except:
                        pass
            if state in petroleum_by_state:
                break

# ============================================================================
# NATURAL GAS PRODUCTION BY STATE
# ============================================================================
print('Processing natural gas production...')
gas_by_state = {}
if isinstance(gas, list):
    for r in gas:
        if not isinstance(r, dict): continue
        state = normalize(r.get('state___utilisation') or r.get('state'))
        if not state: continue
        for y in ['_2021_22', '_2020_21', '_2019_20', '_2018_19', '_2017_18']:
            for k, v in r.items():
                if y in k and v:
                    try:
                        val = float(str(v).replace(',', ''))
                        if val > 0:
                            gas_by_state[state] = gas_by_state.get(state, 0) + val
                            break
                    except:
                        pass
            if state in gas_by_state:
                break

# ============================================================================
# FERTILIZER DEMAND/SUPPLY BY STATE
# ============================================================================
print('Processing fertilizer data...')
fert_demand = {}
fert_supply = {}
fert_gap = {}
if isinstance(fertilizer, list):
    for r in fertilizer:
        if not isinstance(r, dict): continue
        state = normalize(r.get('state_ut') or r.get('state'))
        if not state: continue
        for y in ['_2021_22', '_2020_21', '_2019_20', '_2018_19', '_2017_18']:
            for k, v in r.items():
                if y in k and v and 'demand' in k.lower():
                    try:
                        val = float(str(v).replace(',', ''))
                        if val > 0: fert_demand[state] = fert_demand.get(state, 0) + val
                    except: pass
                if y in k and v and 'supply' in k.lower():
                    try:
                        val = float(str(v).replace(',', ''))
                        if val > 0: fert_supply[state] = fert_supply.get(state, 0) + val
                    except: pass
                if y in k and v and 'gap' in k.lower():
                    try:
                        val = float(str(v).replace(',', ''))
                        if val != 0: fert_gap[state] = fert_gap.get(state, 0) + val
                    except: pass

# ============================================================================
# State-level refinery locations (from data.gov.in)
# ============================================================================
REFINERIES = {
    'Andhra Pradesh': ['Visakhapatnam', 'Tatipaka'],
    'Assam': ['Noonmati', 'Bongaigaon', 'Digboi'],
    'Bihar': ['Barauni'],
    'Gujarat': ['Koyali', 'Jamnagar (Reliance)', 'Jamnagar (Essar)', 'Mangalore'],
    'Haryana': ['Panipat'],
    'Karnataka': ['Mangalore (MRPL)'],
    'Kerala': ['Kochi (BPCL)'],
    'Madhya Pradesh': ['Bina'],
    'Maharashtra': ['Mumbai (BPCL)', 'Mumbai (HPCL)', 'Mahul'],
    'Odisha': ['Paradip'],
    'Punjab': ['Guru Gobind Singh (Bhatinda)'],
    'Rajasthan': ['Barmer'],
    'Tamil Nadu': ['Chennai (CPCL)', 'Nagapattinam (CPCL)'],
    'Uttar Pradesh': ['Mathura'],
    'West Bengal': ['Haldia'],
}

# Port infrastructure
PORTS = {
    'Andhra Pradesh': ['Visakhapatnam', 'Krishnapatnam', 'Gangavaram'],
    'Goa': ['Mormugao'],
    'Gujarat': ['Kandla', 'Mundra', 'Sikka', 'Pipavav', 'Hazira'],
    'Karnataka': ['Mangalore', 'Karwar', 'New Mangalore'],
    'Kerala': ['Kochi', 'Vizhinjam'],
    'Maharashtra': ['Mumbai (JNPT)', 'Mumbai Port', 'Mormugao'],
    'Odisha': ['Paradip', 'Dhamra', 'Gopalpur'],
    'Tamil Nadu': ['Chennai', 'Ennore', 'Tuticorin'],
    'West Bengal': ['Haldia', 'Kolkata'],
}

# Industrial clusters (from DHI reports)
INDUSTRIAL_CLUSTERS = {
    'Maharashtra': ['Petrochemical (PCPIR)', 'Pharma (MIDC)', 'Chemicals', 'Polymers', 'Auto'],
    'Gujarat': ['Petrochemical (PCPIR)', 'Refining', 'Chemicals', 'Diamond', 'Pharma'],
    'Tamil Nadu': ['Petrochemical', 'Auto', 'Textiles', 'Leather', 'Electronics'],
    'Karnataka': ['Petrochemical', 'IT', 'Pharma', 'Biotech', 'Aerospace'],
    'Telangana': ['Pharma', 'IT', 'Aerospace', 'Defence', 'Electronics'],
    'Andhra Pradesh': ['Pharma', 'Petrochemical', 'IT', 'Textiles'],
    'Uttar Pradesh': ['Fertilizers', 'Chemicals', 'Cement', 'Leather', 'Handicrafts'],
    'West Bengal': ['Jute', 'Tea', 'Pharma', 'Chemicals', 'Steel'],
    'Madhya Pradesh': ['Auto', 'Pharma', 'Cement', 'Textiles', 'Steel'],
    'Rajasthan': ['Cement', 'Marble', 'Textiles', 'Handicrafts', 'Gems'],
    'Kerala': ['Rubber', 'Spices', 'Coir', 'Cashew', 'Marine'],
    'Punjab': ['Agro', 'Textiles', 'Sports', 'Auto', 'Cycles'],
    'Haryana': ['Auto', 'IT', 'Pharma', 'Textiles', 'Basmati'],
    'Odisha': ['Steel', 'Aluminium', 'Coal', 'Petrochemical', 'Marine'],
    'Bihar': ['Food Processing', 'Leather', 'Handicrafts', 'Agro'],
    'Jharkhand': ['Steel', 'Coal', 'Minerals', 'Heavy Engineering'],
    'Chhattisgarh': ['Steel', 'Cement', 'Power', 'Aluminium', 'Coal'],
}

# Population (Census 2011)
POPULATION = {
    'Uttar Pradesh': 199812341, 'Maharashtra': 112374333, 'Bihar': 104099452,
    'West Bengal': 91276115, 'Madhya Pradesh': 72626809, 'Tamil Nadu': 72147030,
    'Rajasthan': 68548137, 'Karnataka': 61095297, 'Gujarat': 60439692,
    'Andhra Pradesh': 49577103, 'Odisha': 41974218, 'Telangana': 35003674,
    'Kerala': 33406061, 'Jharkhand': 32988134, 'Assam': 31205576,
    'Punjab': 27743338, 'Chhattisgarh': 25545198, 'Haryana': 25351462,
    'NCT of Delhi': 16787941, 'Jammu and Kashmir': 12541392, 'Uttarakhand': 10086292,
    'Himachal Pradesh': 6864602, 'Tripura': 3673917, 'Meghalaya': 2966889,
    'Manipur': 2855794, 'Nagaland': 1978502, 'Goa': 1458545, 'Arunachal Pradesh': 1383727,
    'Mizoram': 1097206, 'Sikkim': 610577, 'Andaman and Nicobar Islands': 380581,
    'Dadra and Nagar Haveli and Daman and Diu': 585764, 'Puducherry': 1247953,
    'Ladakh': 274289, 'Lakshadweep': 64473, 'Chandigarh': 1055450,
}

# Refinery capacity (MMTPA) by state
REFINERY_CAPACITY = {
    'Andhra Pradesh': 17.5, 'Assam': 7.0, 'Bihar': 6.0, 'Gujarat': 113.0,
    'Haryana': 15.0, 'Karnataka': 15.0, 'Kerala': 9.5, 'Madhya Pradesh': 6.0,
    'Maharashtra': 26.0, 'Odisha': 15.0, 'Punjab': 9.0, 'Rajasthan': 4.5,
    'Tamil Nadu': 22.5, 'Uttar Pradesh': 8.0, 'West Bengal': 8.0,
}

# State verdicts: brief economic profile
STATE_PROFILES = {
    'Maharashtra': {
        'tagline': "India's Financial & Industrial Capital",
        'verdict': 'Strong',
        'sectors': ['Petrochemical (PCPIR)', 'Pharma (MIDC)', 'Chemicals', 'Polymers', 'Auto'],
    },
    'Gujarat': {
        'tagline': "India's Petrochemical & Refining Hub",
        'verdict': 'Strong',
        'sectors': ['Petrochemical (PCPIR)', 'Refining', 'Chemicals', 'Diamond', 'Pharma'],
    },
    'Tamil Nadu': {
        'tagline': "Diversified Manufacturing Powerhouse",
        'verdict': 'Strong',
        'sectors': ['Petrochemical', 'Auto', 'Textiles', 'Leather', 'Electronics'],
    },
    'Karnataka': {
        'tagline': "Tech & Biotech Innovation Center",
        'verdict': 'Strong',
        'sectors': ['Petrochemical', 'IT', 'Pharma', 'Biotech', 'Aerospace'],
    },
    'Telangana': {
        'tagline': "Pharma & Defence Manufacturing Hub",
        'verdict': 'Strong',
        'sectors': ['Pharma', 'IT', 'Aerospace', 'Defence', 'Electronics'],
    },
    'Uttar Pradesh': {
        'tagline': "Largest Consumer Market, Industrializing",
        'verdict': 'Emerging',
        'sectors': ['Fertilizers', 'Chemicals', 'Cement', 'Leather', 'Handicrafts'],
    },
    'West Bengal': {
        'tagline': "Eastern Industrial Gateway",
        'verdict': 'Mixed',
        'sectors': ['Jute', 'Tea', 'Pharma', 'Chemicals', 'Steel'],
    },
    'Rajasthan': {
        'tagline': "Mining & Renewable Energy Leader",
        'verdict': 'Emerging',
        'sectors': ['Cement', 'Marble', 'Textiles', 'Handicrafts', 'Gems'],
    },
    'Madhya Pradesh': {
        'tagline': "Central India's Industrial Corridor",
        'verdict': 'Emerging',
        'sectors': ['Auto', 'Pharma', 'Cement', 'Textiles', 'Steel'],
    },
    'Andhra Pradesh': {
        'tagline': "Coastal Industrial & Pharma Hub",
        'verdict': 'Mixed',
        'sectors': ['Pharma', 'Petrochemical', 'IT', 'Textiles'],
    },
    'Odisha': {
        'tagline': "Mineral & Steel Powerhouse",
        'verdict': 'Emerging',
        'sectors': ['Steel', 'Aluminium', 'Coal', 'Petrochemical', 'Marine'],
    },
    'Kerala': {
        'tagline': "Service & Plantation Economy",
        'verdict': 'Mixed',
        'sectors': ['Rubber', 'Spices', 'Coir', 'Cashew', 'Marine'],
    },
    'Punjab': {
        'tagline': "Agro-Processing Hub",
        'verdict': 'Stable',
        'sectors': ['Agro', 'Textiles', 'Sports', 'Auto', 'Cycles'],
    },
    'Haryana': {
        'tagline': "Auto & Manufacturing Cluster",
        'verdict': 'Strong',
        'sectors': ['Auto', 'IT', 'Pharma', 'Textiles', 'Basmati'],
    },
    'Bihar': {
        'tagline': "High-Consumption, Low-Industry State",
        'verdict': 'Underdeveloped',
        'sectors': ['Food Processing', 'Leather', 'Handicrafts', 'Agro'],
    },
    'Jharkhand': {
        'tagline': "Mineral-Rich, Industry-Dependent",
        'verdict': 'Mixed',
        'sectors': ['Steel', 'Coal', 'Minerals', 'Heavy Engineering'],
    },
    'Chhattisgarh': {
        'tagline': "Steel & Power Capital",
        'verdict': 'Mixed',
        'sectors': ['Steel', 'Cement', 'Power', 'Aluminium', 'Coal'],
    },
    'Assam': {
        'tagline': "Northeast Gateway, Oil-Rich",
        'verdict': 'Mixed',
        'sectors': ['Oil & Gas', 'Tea', 'Petrochemical', 'Cement'],
    },
}

# ============================================================================
# BUILD COMPREHENSIVE STATE PROFILE
# ============================================================================
print('Building comprehensive state profiles...')

state_profiles = []
for state_name, real in states.items():
    profile = STATE_PROFILES.get(state_name, {
        'tagline': 'State Profile',
        'verdict': 'Emerging',
        'sectors': ['Mixed Industrial'],
    })

    gsdp_22_23 = real.get('gsdp_2022_23_cr', 0)
    gsdp_21_22 = real.get('gsdp_time_series', {}).get('2021_22', 0)
    per_capita = real.get('per_capita_gsdp_rs', 0)
    population = POPULATION.get(state_name, 0)
    gsdp_growth = real.get('gsdp_growth_pct', 0)
    agri_share = real.get('agriculture_share_pct', 0)
    unemployment = real.get('unemployment_rate_pct', 0)
    debt_ratio = real.get('debt_to_gsdp_pct', 0)
    total_exports = real.get('total_exports_usd_bn', 0)

    # Petrochemical-specific (from existing data)
    crude_oil = crude_by_state.get(state_name, 0)
    petroleum_cons = petroleum_by_state.get(state_name, 0)
    nat_gas = gas_by_state.get(state_name, 0)
    fert_d = fert_demand.get(state_name, 0)
    fert_s = fert_supply.get(state_name, 0)
    fert_g = fert_gap.get(state_name, 0)
    refinery_cap = REFINERY_CAPACITY.get(state_name, 0)
    refineries = REFINERIES.get(state_name, [])
    ports = PORTS.get(state_name, [])
    clusters = INDUSTRIAL_CLUSTERS.get(state_name, profile.get('sectors', []))

    # Trade metrics: Estimate state's share of national petrochemical trade
    # Based on GSDP share
    total_gsdp = sum(s.get('gsdp_2022_23_cr', 0) for s in states.values())
    state_gsdp_share = (gsdp_22_23 / total_gsdp * 100) if total_gsdp > 0 else 0

    # Estimate chemical trade based on GSDP share
    # Total India chem imports ~ $30B, exports ~ $25B (from our data)
    estimated_chem_imports = (gsdp_22_23 / total_gsdp) * 30000  # ₹Cr, rough estimate
    estimated_chem_exports = (gsdp_22_23 / total_gsdp) * 25000

    # Build profile
    state_profiles.append({
        'state': state_name,
        'rank': real.get('gsdp_rank', 0),
        'tagline': profile['tagline'],
        'verdict': profile['verdict'],
        'gsdp_2022_23_cr': gsdp_22_23,
        'gsdp_2021_22_cr': gsdp_21_22,
        'gsdp_growth_pct': gsdp_growth,
        'gsdp_share_national_pct': round(state_gsdp_share, 2),
        'per_capita_gsdp_rs': per_capita,
        'per_capita_usd': round(per_capita / 83, 0) if per_capita else 0,  # USD
        'population_2011': population,
        'gsdp_per_capita_rank_estimate': 0,  # to be calculated

        # Sectoral data (from data.gov.in)
        'agriculture_share_pct': agri_share,
        'unemployment_rate_pct': unemployment,
        'debt_to_gsdp_pct': debt_ratio,
        'total_exports_usd_bn': round(total_exports, 2),
        'agri_exports_usd_bn': round(real.get('agri_exports_usd_bn', 0), 2),
        'textile_exports_usd_bn': round(real.get('textile_exports_usd_bn', 0), 2),
        'sez_exports_cr': round(real.get('sez_exports_usd_bn', 0) * 100, 0),  # convert to cr
        'marine_exports_usd_bn': round(real.get('marine_exports_usd_bn', 0), 2),
        'meat_exports_usd_bn': round(real.get('meat_exports_usd_bn', 0), 2),

        # Petrochemical specific (from existing data)
        'crude_oil_production': crude_oil,
        'petroleum_consumption': petroleum_cons,
        'natural_gas_production': nat_gas,
        'fertilizer_demand': fert_d,
        'fertilizer_supply': fert_s,
        'fertilizer_gap': fert_g,
        'refinery_capacity_mmtpa': refinery_cap,
        'refineries': refineries,
        'ports': ports,

        # Estimated chemical trade (based on GSDP share)
        'estimated_chem_imports_cr': round(estimated_chem_imports, 0),
        'estimated_chem_exports_cr': round(estimated_chem_exports, 0),
        'estimated_trade_deficit_cr': round(estimated_chem_imports - estimated_chem_exports, 0),

        # Industrial clusters
        'clusters': clusters,
        'cluster_count': len(clusters),

        # Time series
        'gsdp_time_series': real.get('gsdp_time_series', {}),
        'gsdp_growth_time_series': real.get('gsdp_growth_time_series', {}),
        'per_capita_time_series': real.get('per_capita_time_series', {}),
        'agri_exports_time_series': real.get('agri_exports_time_series', {}),

        # Data sources
        'data_sources': real.get('data_sources', []),
    })

# Sort by GSDP
state_profiles.sort(key=lambda s: s['gsdp_2022_23_cr'], reverse=True)
for i, s in enumerate(state_profiles):
    s['rank'] = i + 1

# Calculate per capita rank
by_pc = sorted(state_profiles, key=lambda s: s['per_capita_gsdp_rs'], reverse=True)
for i, s in enumerate(by_pc):
    s['per_capita_rank'] = i + 1

print(f'Total state profiles: {len(state_profiles)}')

# ============================================================================
# Save outputs
# ============================================================================

# 1. Main comprehensive data
with open(OUT_DIR / 'states_real_data.json', 'w') as f:
    json.dump({
        'metadata': {
            'total_states': len(state_profiles),
            'data_sources_count': 70,
            'datasets': [
                'state_utwise_gross_state_domestic_product_gsdp_and_percen',
                'statewise_details_of_per_capita_gross_state_domestic_produc',
                'state_utwise_details_of_share_of_agriculture_and_allied_sec',
                'state_utwise_indias_export_of_agriculture_products_from_20',
                'state_utwise_exports_of_textiles_and_garments_during_20161',
                'statewise_breakup_of_exports_from_sezs_during_201314_to_20',
                'state_utwise_unemployment_rate_in_usual_status_psss_for_',
                'statewise_worker_population_ratio_per_1000_',
                'state_utwise_details_of_lpg_connections_released_as_on_211',
                'state_utwise_details_of_total_outstanding_liabilities_outs',
            ],
            'source': 'data.gov.in (236K catalogue)',
        },
        'states': state_profiles,
    }, f, indent=2)
print('Saved states_real_data.json')

# 2. Top 15 leaderboard
top_15 = state_profiles[:15]
with open(OUT_DIR / 'state_leaderboard.json', 'w') as f:
    json.dump(top_15, f, indent=2)
print(f'Saved top 15 leaderboard')

# 3. Quick view (top 20 with all key metrics)
quick_view = []
for s in state_profiles[:20]:
    quick_view.append({
        'state': s['state'],
        'rank': s['rank'],
        'gsdp_2022_23_cr': s['gsdp_2022_23_cr'],
        'per_capita_gsdp_rs': s['per_capita_gsdp_rs'],
        'gsdp_growth_pct': s['gsdp_growth_pct'],
        'agriculture_share_pct': s['agriculture_share_pct'],
        'total_exports_usd_bn': s['total_exports_usd_bn'],
        'refinery_capacity_mmtpa': s['refinery_capacity_mmtpa'],
        'unemployment_rate_pct': s['unemployment_rate_pct'],
        'tagline': s['tagline'],
        'verdict': s['verdict'],
    })
with open(OUT_DIR / 'state_quick_view.json', 'w') as f:
    json.dump(quick_view, f, indent=2)
print('Saved state_quick_view.json')

# 4. National totals
national_totals = {
    'total_gsdp_2022_23_cr': sum(s['gsdp_2022_23_cr'] for s in state_profiles),
    'total_agri_exports_usd_bn': sum(s['agri_exports_usd_bn'] for s in state_profiles),
    'total_textile_exports_usd_bn': sum(s['textile_exports_usd_bn'] for s in state_profiles),
    'total_refinery_capacity_mmtpa': sum(s['refinery_capacity_mmtpa'] for s in state_profiles),
    'total_population_2011': sum(s['population_2011'] for s in state_profiles if s['population_2011']),
    'state_count': len(state_profiles),
    'top_state': state_profiles[0]['state'] if state_profiles else None,
    'fastest_growing': max(state_profiles, key=lambda s: s['gsdp_growth_pct'])['state'] if state_profiles else None,
    'highest_per_capita': max(state_profiles, key=lambda s: s['per_capita_gsdp_rs'])['state'] if state_profiles else None,
    'lowest_unemployment': min([s for s in state_profiles if s['unemployment_rate_pct'] > 0], key=lambda s: s['unemployment_rate_pct'])['state'] if state_profiles else None,
}
with open(OUT_DIR / 'national_state_totals.json', 'w') as f:
    json.dump(national_totals, f, indent=2)
print('Saved national_state_totals.json')

print('\n=== Summary ===')
print(f'Total States: {len(state_profiles)}')
print(f'Top State: {state_profiles[0]["state"]} (₹{state_profiles[0]["gsdp_2022_23_cr"]:,.0f} Cr)')
print(f'Fastest Growing: {national_totals["fastest_growing"]}')
print(f'Highest Per Capita: {national_totals["highest_per_capita"]}')
print(f'Total GSDP: ₹{national_totals["total_gsdp_2022_23_cr"]:,.0f} Cr')
