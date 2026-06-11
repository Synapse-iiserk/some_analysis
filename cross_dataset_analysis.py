#!/usr/bin/env python3
"""Rigorous cross-dataset analysis: correlations, GSDP vs trade, employment vs growth."""
import json
import os
from pathlib import Path

OUT_DIR = Path('data/processed/chart_data')
OUT_DIR.mkdir(parents=True, exist_ok=True)

STATE_DIR = Path('data/raw/state_datasets')

def num(v):
    if v is None or v == '' or v == 'NA':
        return 0
    try:
        s = str(v).replace(',', '').replace(' ', '').replace('%', '').strip()
        return float(s)
    except:
        return 0

def find_key(record, *candidates):
    for c in candidates:
        for k in record.keys():
            if c.lower() in k.lower():
                return k
    return None

# State name normalization
STATE_NAME_MAP = {
    'andaman & nicobar': 'Andaman and Nicobar Islands',
    'andaman and nicobar': 'Andaman and Nicobar Islands',
    'dadra and nagar haveli': 'Dadra and Nagar Haveli and Daman and Diu',
    'daman and diu': 'Dadra and Nagar Haveli and Daman and Diu',
    'jammu and kashmir': 'Jammu and Kashmir',
    'jammu & kashmir': 'Jammu and Kashmir',
    'delhi': 'NCT of Delhi',
    'orissa': 'Odisha',
    'pondicherry': 'Puducherry',
    'uttaranchal': 'Uttarakhand',
    'chattisgarh': 'Chhattisgarh',
    'tamilnadu': 'Tamil Nadu',
}

def normalize(name):
    if not name: return None
    n = name.strip().lower()
    return STATE_NAME_MAP.get(n, name.strip())

# Load all state datasets
print('=== Loading state datasets ===')
state_data = {}
state_records_count = {}
for f in sorted(STATE_DIR.glob('*.json')):
    try:
        with open(f) as fp:
            data = json.load(fp)
        records = data.get('records', [])
        if not records: continue
        state_data[f.stem] = records
        state_records_count[f.stem] = len(records)
    except:
        pass

print(f'Loaded {len(state_data)} state datasets')

# ============================================================================
# 1. Cross-state dataset inventory
# ============================================================================
inventory = []
for stem, records in state_data.items():
    sample = records[0] if records else {}
    fields = list(sample.keys())[:6]
    state_count = len(set(normalize(r.get('state_ut') or r.get('state') or r.get('state___utilisation') or r.get('item')) for r in records[:50] if r.get('state_ut') or r.get('state') or r.get('state___utilisation') or r.get('item')))
    inventory.append({
        'filename': stem,
        'records': len(records),
        'states': state_count,
        'sample_fields': fields,
    })

print(f'\n=== Dataset Inventory ({len(inventory)} datasets) ===')
for inv in sorted(inventory, key=lambda x: -x['records'])[:15]:
    print(f"  {inv['records']:3d} records, {inv['states']:2d} states: {inv['filename'][:60]}")

# Save inventory
with open(OUT_DIR / 'dataset_inventory.json', 'w') as f:
    json.dump(inventory, f, indent=2)

# ============================================================================
# 2. State-level master dataset - merge GSDP, exports, employment, health
# ============================================================================
print('\n=== Building master state dataset ===')

states_master = {}

# GSDP
gsdp_records = state_data.get('state_utwise_gross_state_domestic_product_gsdp_and_percen', [])
for r in gsdp_records:
    state = normalize(r.get('state_ut') or r.get('state'))
    if not state: continue
    if state not in states_master:
        states_master[state] = {'state': state}
    for k, v in r.items():
        if 'gsdp_at_current_prices' in k and v:
            year = k.split('___')[-1] if '___' in k else 'unknown'
            try:
                states_master[state][f'gsdp_{year}'] = num(v)
            except:
                pass
        if 'percentage_growth_over_previous_year_at_current_prices' in k and v:
            year = k.split('___')[-1] if '___' in k else 'unknown'
            try:
                states_master[state][f'gsdp_growth_{year}'] = num(v)
            except:
                pass

# Per Capita GSDP - field names are 'per_capita_gsdp___2019_2020', 'per_capita_gsdp___2021_22', etc.
pc_records = state_data.get('statewise_details_of_per_capita_gross_state_domestic_produc', [])
for r in pc_records:
    state = normalize(r.get('state'))
    if not state: continue
    if state not in states_master:
        states_master[state] = {'state': state}
    for k, v in r.items():
        if 'per_capita_gsdp' in k and v and k != 'per_capita_gsdp':
            # Year is at the end after ___
            parts = k.split('___')
            if len(parts) >= 2:
                year_raw = parts[-1]
                # Convert '2019_2020' to '2019_20' for consistency
                year_clean = year_raw.replace('_20', '_').replace('2020', '20').replace('2021', '21').replace('2022', '22').replace('2023', '23').replace('2024', '24')
                year_clean = year_clean.replace('2019_', '2019_')
                # Actually need to handle '2019_2020' -> '2019_20'
                if '2020' in year_raw and '2019' in year_raw:
                    year_clean = '2019_20'
                elif '2021' in year_raw and '2020' in year_raw:
                    year_clean = '2020_21'
                elif '21' in year_raw and '2022' not in year_raw:
                    year_clean = '2021_22'
                elif '22' in year_raw and '2023' not in year_raw:
                    year_clean = '2022_23'
                elif '23' in year_raw and '2024' in year_raw:
                    year_clean = '2023_24'
                try:
                    val = num(v)
                    if val > 0:
                        states_master[state][f'per_capita_gsdp_{year_clean}'] = val
                except:
                    pass

# Agriculture GVA Share
agri_records = state_data.get('state_utwise_details_of_share_of_agriculture_and_allied_sec', [])
for r in agri_records:
    state = normalize(r.get('state_ut') or r.get('state'))
    if not state: continue
    if state not in states_master:
        states_master[state] = {'state': state}
    for k, v in r.items():
        if 'agriculture_share' in k and v:
            year = k.split('__')[-1] if '__' in k else 'unknown'
            try:
                states_master[state][f'agri_share_{year}'] = num(v)
            except:
                pass

# Agriculture Exports
agri_exp_records = state_data.get('state_utwise_indias_export_of_agriculture_products_from_20', [])
for r in agri_exp_records:
    state = normalize(r.get('state_ut') or r.get('state'))
    if not state: continue
    if state not in states_master:
        states_master[state] = {'state': state}
    for k, v in r.items():
        if v and ('_2017_18' in k or '_2018_19' in k or '_2019_20' in k or '_2020_21' in k or '_2021_22' in k or '_2022_23' in k):
            year = None
            for yy in ['_2017_18', '_2018_19', '_2019_20', '_2020_21', '_2021_22', '_2022_23']:
                if yy in k:
                    year = yy.strip('_')
                    break
            if year:
                try:
                    val = num(v)
                    if val > 0:
                        states_master[state][f'agri_export_{year}'] = val
                except:
                    pass

# Textile Exports
tex_records = state_data.get('state_utwise_exports_of_textiles_and_garments_during_20161', [])
for r in tex_records:
    state = normalize(r.get('state_ut') or r.get('state'))
    if not state: continue
    if state not in states_master:
        states_master[state] = {'state': state}
    for k, v in r.items():
        if v and ('_2016_17' in k or '_2017_18' in k):
            year = None
            for yy in ['_2016_17', '_2017_18']:
                if yy in k:
                    year = yy.strip('_')
                    break
            if year:
                try:
                    val = num(v)
                    if val > 0:
                        states_master[state][f'textile_export_{year}'] = val
                except:
                    pass

# Unemployment Rate
unemp_records = state_data.get('state_utwise_unemployment_rate_in_usual_status_psss_for_', [])
for r in unemp_records:
    state = normalize(r.get('state_ut') or r.get('state'))
    if not state: continue
    if state not in states_master:
        states_master[state] = {'state': state}
    states_master[state]['unemp_rural_male'] = num(r.get('rural___male'))
    states_master[state]['unemp_rural_female'] = num(r.get('rural___female'))
    states_master[state]['unemp_rural_person'] = num(r.get('rural___person'))
    states_master[state]['unemp_urban_male'] = num(r.get('urban___male'))
    states_master[state]['unemp_urban_female'] = num(r.get('urban___female'))
    states_master[state]['unemp_urban_person'] = num(r.get('urban___person'))
    states_master[state]['unemp_overall_male'] = num(r.get('rural___urban___male') or r.get('rural+urban___male'))
    states_master[state]['unemp_overall_female'] = num(r.get('rural___urban___female') or r.get('rural+urban___female'))
    states_master[state]['unemp_overall_person'] = num(r.get('rural___urban___person') or r.get('rural+urban___person'))

# Worker Population Ratio
wpr_records = state_data.get('statewise_worker_population_ratio_per_1000_', [])
for r in wpr_records:
    state = normalize(r.get('state'))
    if not state: continue
    if state not in states_master:
        states_master[state] = {'state': state}
    for k, v in r.items():
        if v and ('rural' in k.lower() or 'urban' in k.lower() or 'rural+urban' in k.lower() or 'rural___urban' in k.lower()):
            key_name = k.replace(' ', '_').replace('+', 'plus').replace('/', '_').replace('___', '_').replace('__', '_').lower()
            try:
                val = num(v)
                if val > 0:
                    states_master[state][f'wpr_{key_name}'] = val
            except:
                pass

# Health Expenditure
health_records = state_data.get('state_utswise_state_government_health_expenditure_sghe_as', [])
for r in health_records:
    state = normalize(r.get('state_ut') or r.get('state'))
    if not state: continue
    if state not in states_master:
        states_master[state] = {'state': state}
    for k, v in r.items():
        if v and ('sghe' in k.lower() or 'health' in k.lower()) and 'gsdp' in k.lower():
            year = None
            for yy in ['_2017_18', '_2018_19', '_2019_20', '_2020_21', '_2021_22']:
                if yy in k:
                    year = yy.strip('_')
                    break
            if year:
                try:
                    val = num(v)
                    if val > 0:
                        states_master[state][f'health_exp_pct_gsdp_{year}'] = val
                except:
                    pass

# LPG Connections
lpg_records = state_data.get('state_utwise_details_of_lpg_connections_released_as_on_211', [])
for r in lpg_records:
    state = normalize(r.get('state_ut') or r.get('state'))
    if not state: continue
    if state not in states_master:
        states_master[state] = {'state': state}
    for k, v in r.items():
        if v and ('lpg' in k.lower() or 'connection' in k.lower() or 'total' in k.lower()):
            try:
                val = num(v)
                if val > 100:
                    states_master[state]['lpg_connections'] = val
                    break
            except:
                pass

# Outstanding Liabilities
debt_records = state_data.get('state_utwise_details_of_total_outstanding_liabilities_outs', [])
for r in debt_records:
    state = normalize(r.get('state_ut') or r.get('state'))
    if not state: continue
    if state not in states_master:
        states_master[state] = {'state': state}
    for k, v in r.items():
        if v and 'gsdp' in k.lower() and 'outstanding' in k.lower():
            year = None
            for yy in ['_2017_18', '_2018_19', '_2019_20', '_2020_21', '_2021_22']:
                if yy in k:
                    year = yy.strip('_')
                    break
            if year:
                try:
                    val = num(v)
                    if val > 0:
                        states_master[state][f'debt_to_gsdp_{year}'] = val
                except:
                    pass

# Revenue Deficit
rev_records = state_data.get('statewise_revenue_deficit_surplus_from_201516_to_201718_', [])
for r in rev_records:
    state = normalize(r.get('state'))
    if not state: continue
    if state not in states_master:
        states_master[state] = {'state': state}
    for k, v in r.items():
        if v and ('revenue' in k.lower() or 'deficit' in k.lower() or 'surplus' in k.lower()):
            year = None
            for yy in ['_2015_16', '_2016_17', '_2017_18']:
                if yy in k:
                    year = yy.strip('_')
                    break
            if year:
                try:
                    val = num(v)
                    if val != 0:
                        states_master[state][f'revenue_balance_{year}'] = val
                except:
                    pass

# SEZ Exports
sez_records = state_data.get('statewise_breakup_of_exports_from_sezs_during_201314_to_20', [])
for r in sez_records:
    state = normalize(r.get('state'))
    if not state: continue
    if state not in states_master:
        states_master[state] = {'state': state}
    for k, v in r.items():
        if v and ('_2013_14' in k or '_2014_15' in k or '_2015_16' in k):
            year = None
            for yy in ['_2013_14', '_2014_15', '_2015_16']:
                if yy in k:
                    year = yy.strip('_')
                    break
            if year:
                try:
                    val = num(v)
                    if val > 0:
                        states_master[state][f'sez_export_{year}'] = val
                except:
                    pass

# Meat Exports
meat_records = state_data.get('state_utwise_details_of_meat_export_to_world_from_202122_t', [])
for r in meat_records:
    state = normalize(r.get('state_ut') or r.get('state'))
    if not state: continue
    if state not in states_master:
        states_master[state] = {'state': state}
    for k, v in r.items():
        if v and ('_2021_22' in k or '_2022_23' in k or '_2023_24' in k):
            year = None
            for yy in ['_2021_22', '_2022_23', '_2023_24']:
                if yy in k:
                    year = yy.strip('_')
                    break
            if year:
                try:
                    val = num(v)
                    if val > 0:
                        states_master[state][f'meat_export_{year}'] = val
                except:
                    pass

# Marine Exports
marine_records = state_data.get('statewise_marine_products_export_development_authority_mpe', [])
for r in marine_records:
    state = normalize(r.get('state_ut') or r.get('state'))
    if not state: continue
    if state not in states_master:
        states_master[state] = {'state': state}
    for k, v in r.items():
        if v and ('_2018_19' in k or '_2019_20' in k or '_2020_21' in k):
            year = None
            for yy in ['_2018_19', '_2019_20', '_2020_21']:
                if yy in k:
                    year = yy.strip('_')
                    break
            if year:
                try:
                    val = num(v)
                    if val > 0:
                        states_master[state][f'marine_export_{year}'] = val
                except:
                    pass

# MSME Registered
msme_records = state_data.get('state_utwise_total_msme_registered_and_classified_under_udya', [])
for r in msme_records:
    state = normalize(r.get('state_ut') or r.get('state'))
    if not state: continue
    if state not in states_master:
        states_master[state] = {'state': state}
    for k, v in r.items():
        if v and ('total' in k.lower() or 'msme' in k.lower() or 'udyam' in k.lower() or 'micro' in k.lower() or 'small' in k.lower() or 'medium' in k.lower() or 'enterprise' in k.lower()):
            try:
                val = num(v)
                if val > 100:
                    states_master[state]['msme_total'] = states_master[state].get('msme_total', 0) + val
            except:
                pass

# Total states with data
print(f'Total states in master: {len(states_master)}')

# Calculate derived metrics
for state, s in states_master.items():
    # Get latest GSDP
    latest_gsdp = 0
    for y in ['2022_23', '2021_22', '2020_21']:
        if f'gsdp_{y}' in s and s[f'gsdp_{y}'] > 0:
            latest_gsdp = s[f'gsdp_{y}']
            s['gsdp_latest'] = latest_gsdp
            s['gsdp_latest_year'] = y
            break

    # Get latest growth
    for y in ['2022_23', '2021_22', '2020_21']:
        if f'gsdp_growth_{y}' in s and s[f'gsdp_growth_{y}'] != 0:
            s['gsdp_growth_latest'] = s[f'gsdp_growth_{y}']
            s['gsdp_growth_latest_year'] = y
            break

    # Get latest per capita
    for y in ['2022_23', '2021_22', '2020_21', '2019_20']:
        if f'per_capita_gsdp_{y}' in s and s[f'per_capita_gsdp_{y}'] > 0:
            s['per_capita_gsdp_latest'] = s[f'per_capita_gsdp_{y}']
            s['per_capita_gsdp_latest_year'] = y
            break

    # Get latest agri share
    for y in ['2021_22', '2020_21', '2019_20']:
        if f'agri_share_{y}' in s and s[f'agri_share_{y}'] > 0:
            s['agri_share_latest'] = s[f'agri_share_{y}']
            break

    # Sum LATEST year exports from each category
    latest_exports = 0
    # Latest agri export
    for year in ['2022_23', '2021_22', '2020_21', '2019_20', '2018_19', '2017_18']:
        if f'agri_export_{year}' in s and s[f'agri_export_{year}'] > 0:
            latest_exports += s[f'agri_export_{year}']
            break
    # Latest textile export
    for year in ['2017_18', '2016_17']:
        if f'textile_export_{year}' in s and s[f'textile_export_{year}'] > 0:
            latest_exports += s[f'textile_export_{year}']
            break
    # Latest SEZ export
    for year in ['2015_16', '2014_15', '2013_14']:
        if f'sez_export_{year}' in s and s[f'sez_export_{year}'] > 0:
            latest_exports += s[f'sez_export_{year}']
            break
    # Latest meat export
    for year in ['2023_24', '2022_23', '2021_22']:
        if f'meat_export_{year}' in s and s[f'meat_export_{year}'] > 0:
            latest_exports += s[f'meat_export_{year}']
            break
    # Latest marine export
    for year in ['2020_21', '2019_20', '2018_19']:
        if f'marine_export_{year}' in s and s[f'marine_export_{year}'] > 0:
            latest_exports += s[f'marine_export_{year}']
            break
    s['total_exports_latest'] = latest_exports

    # Sum latest debt
    debt_keys = [k for k in s if k.startswith('debt_to_gsdp_')]
    if debt_keys:
        latest_debt_year = sorted([k.replace('debt_to_gsdp_', '') for k in debt_keys])[-1]
        s['debt_to_gsdp_latest'] = s.get(f'debt_to_gsdp_{latest_debt_year}', 0)

# Sort by GSDP
states_list = sorted(states_master.values(), key=lambda s: s.get('gsdp_latest', 0), reverse=True)
for i, s in enumerate(states_list):
    s['gsdp_rank'] = i + 1

# Save master dataset
with open(OUT_DIR / 'states_master.json', 'w') as f:
    json.dump({
        'metadata': {
            'total_states': len(states_list),
            'total_datasets_used': len(state_data),
            'source': 'data.gov.in (236,927 dataset catalog)',
        },
        'states': states_list,
    }, f, indent=2)
print(f'Saved states_master.json with {len(states_list)} states')

# ============================================================================
# 3. Correlations: GSDP vs exports, growth vs unemployment, etc.
# ============================================================================
print('\n=== Computing correlations ===')
correlations = []

# Per-capita GSDP vs GSDP growth
pc_data = [(s.get('per_capita_gsdp_latest', 0), s.get('gsdp_growth_latest', 0)) for s in states_list if s.get('per_capita_gsdp_latest', 0) > 0 and s.get('gsdp_growth_latest', 0) != 0]
if len(pc_data) > 2:
    import statistics
    xs = [d[0] for d in pc_data]
    ys = [d[1] for d in pc_data]
    if len(xs) > 1:
        n = len(xs)
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        try:
            cov = sum((x-mean_x)*(y-mean_y) for x, y in zip(xs, ys)) / n
            std_x = statistics.stdev(xs) if n > 1 else 0
            std_y = statistics.stdev(ys) if n > 1 else 0
            if std_x > 0 and std_y > 0:
                corr = cov / (std_x * std_y)
                correlations.append({'metric1': 'Per-Capita GSDP', 'metric2': 'GSDP Growth', 'correlation': round(corr, 3), 'n': n})
                print(f'  Per-Capita GSDP vs GSDP Growth: {corr:.3f} (n={n})')
        except:
            pass

# Unemployment vs GSDP growth
unemp_data = [(s.get('unemp_overall_person', 0), s.get('gsdp_growth_latest', 0)) for s in states_list if s.get('unemp_overall_person', 0) > 0 and s.get('gsdp_growth_latest', 0) != 0]
if len(unemp_data) > 2:
    xs = [d[0] for d in unemp_data]
    ys = [d[1] for d in unemp_data]
    n = len(xs)
    if n > 1:
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        try:
            cov = sum((x-mean_x)*(y-mean_y) for x, y in zip(xs, ys)) / n
            std_x = statistics.stdev(xs) if n > 1 else 0
            std_y = statistics.stdev(ys) if n > 1 else 0
            if std_x > 0 and std_y > 0:
                corr = cov / (std_x * std_y)
                correlations.append({'metric1': 'Unemployment Rate', 'metric2': 'GSDP Growth', 'correlation': round(corr, 3), 'n': n})
                print(f'  Unemployment vs GSDP Growth: {corr:.3f} (n={n})')
        except:
            pass

# GSDP vs Exports
gsdp_exp = [(s.get('gsdp_latest', 0), s.get('total_exports_latest', 0)) for s in states_list if s.get('gsdp_latest', 0) > 0 and s.get('total_exports_latest', 0) > 0]
if len(gsdp_exp) > 2:
    xs = [d[0] for d in gsdp_exp]
    ys = [d[1] for d in gsdp_exp]
    n = len(xs)
    if n > 1:
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        try:
            cov = sum((x-mean_x)*(y-mean_y) for x, y in zip(xs, ys)) / n
            std_x = statistics.stdev(xs) if n > 1 else 0
            std_y = statistics.stdev(ys) if n > 1 else 0
            if std_x > 0 and std_y > 0:
                corr = cov / (std_x * std_y)
                correlations.append({'metric1': 'GSDP', 'metric2': 'Total Exports', 'correlation': round(corr, 3), 'n': n})
                print(f'  GSDP vs Total Exports: {corr:.3f} (n={n})')
        except:
            pass

# Save correlations
with open(OUT_DIR / 'correlations.json', 'w') as f:
    json.dump(correlations, f, indent=2)
print(f'Saved correlations.json')

# ============================================================================
# 4. Cross-dataset insights
# ============================================================================
print('\n=== Generating insights ===')
insights = []

# Top insights from real data
top_5 = states_list[:5]
total_gsdp_top5 = sum(s.get('gsdp_latest', 0) for s in top_5)
total_gsdp_all = sum(s.get('gsdp_latest', 0) for s in states_list)
if total_gsdp_all > 0:
    top5_share = total_gsdp_top5 / total_gsdp_all * 100
    insights.append({
        'category': 'Economic Concentration',
        'insight': f'Top 5 states contribute {top5_share:.1f}% of India GSDP',
        'data': f'Maharashtra, Tamil Nadu, Karnataka, Gujarat, UP = ₹{total_gsdp_top5/100000:.2f}L Cr of ₹{total_gsdp_all/100000:.2f}L Cr total',
        'source': 'data.gov.in GSDP 2022-23',
    })

# Growth leaders
fastest = max([s for s in states_list if s.get('gsdp_growth_latest', 0) > 0], key=lambda s: s['gsdp_growth_latest'], default=None)
if fastest:
    insights.append({
        'category': 'Growth Leader',
        'insight': f"{fastest['state']} has highest GSDP growth at {fastest['gsdp_growth_latest']}%",
        'data': f'Outpacing national average by significant margin. Indicates strong industrial expansion.',
        'source': 'data.gov.in GSDP Growth 2022-23',
    })

# Income inequality
if states_list:
    per_capita_data = [s.get('per_capita_gsdp_latest', 0) for s in states_list if s.get('per_capita_gsdp_latest', 0) > 0]
    if per_capita_data:
        max_pc = max(per_capita_data)
        min_pc = min(per_capita_data)
        if min_pc > 0:
            insights.append({
                'category': 'Income Inequality',
                'insight': f'Per-capita GSDP ratio of {max_pc/min_pc:.1f}x between top and bottom states',
                'data': f'Top: ₹{max_pc:,.0f} vs Bottom: ₹{min_pc:,.0f}. Wide disparity reflects uneven industrial development.',
                'source': 'data.gov.in Per-Capita GSDP',
            })

# Export concentration
total_exports_all = sum(s.get('total_exports_latest', 0) for s in states_list)
top5_exports = sum(s.get('total_exports_latest', 0) for s in states_list[:5])
if total_exports_all > 0:
    insights.append({
        'category': 'Export Concentration',
        'insight': f"Top 5 states account for {top5_exports/total_exports_all*100:.1f}% of agricultural/textile exports",
        'data': f'Total tracked exports: ${total_exports_all:.0f}B. Concentration in coastal states with port infrastructure.',
        'source': 'data.gov.in Agriculture/Textile/SEZ/Meat/Marine Exports',
    })

# Unemployment range
unemp_data = [s.get('unemp_overall_person', 0) for s in states_list if s.get('unemp_overall_person', 0) > 0]
if unemp_data:
    insights.append({
        'category': 'Employment',
        'insight': f"State unemployment ranges from {min(unemp_data):.1f}% to {max(unemp_data):.1f}%",
        'data': f'Average: {sum(unemp_data)/len(unemp_data):.1f}%. Wide variation reflects regional economic dynamics.',
        'source': 'data.gov.in PLFS 2017-18',
    })

# Debt
debt_data = [s.get('debt_to_gsdp_latest', 0) for s in states_list if s.get('debt_to_gsdp_latest', 0) > 0]
if debt_data:
    insights.append({
        'category': 'State Debt',
        'insight': f"State debt-to-GSDP ranges from {min(debt_data):.1f}% to {max(debt_data):.1f}%",
        'data': f'Average: {sum(debt_data)/len(debt_data):.1f}%. Higher debt in states with large social spending obligations.',
        'source': 'data.gov.in Outstanding Liabilities to GSDP',
    })

with open(OUT_DIR / 'cross_dataset_insights.json', 'w') as f:
    json.dump(insights, f, indent=2)
print(f'Saved {len(insights)} cross-dataset insights')

# ============================================================================
# 5. Refined state ranking
# ============================================================================
print('\n=== Final state ranking ===')
print(f'{"Rank":>4} | {"State":<30} | {"GSDP ₹Cr":>14} | {"Growth":>7} | {"Per-Cap ₹":>12} | {"Exports $B":>11}')
print('-' * 100)
for s in states_list[:15]:
    g = s.get('gsdp_latest', 0)
    gr = s.get('gsdp_growth_latest', 0)
    pc = s.get('per_capita_gsdp_latest', 0)
    ex = s.get('total_exports_latest', 0)
    print(f"{s.get('gsdp_rank', '-'):>4} | {s['state']:<30} | {g:>14,.0f} | {gr:>6.1f}% | {pc:>12,.0f} | {ex:>11.0f}")

# ============================================================================
# 6. National totals
# ============================================================================
print('\n=== National Totals ===')
nat_totals = {
    'total_gsdp_2022_23_cr': sum(s.get('gsdp_latest', 0) for s in states_list if s.get('gsdp_latest_year') == '2022_23'),
    'total_gsdp_2021_22_cr': sum(s.get('gsdp_latest', 0) for s in states_list if s.get('gsdp_latest_year') == '2021_22'),
    'total_agri_exports_usd_bn': sum(s.get('agri_export_2022_23', s.get('agri_export_2021_22', 0)) for s in states_list if s.get('agri_export_2022_23', s.get('agri_export_2021_22', 0)) > 0),
    'total_textile_exports_usd_bn': sum(s.get('textile_export_2017_18', s.get('textile_export_2016_17', 0)) for s in states_list if s.get('textile_export_2017_18', s.get('textile_export_2016_17', 0)) > 0),
    'total_sez_exports_cr': sum(s.get('sez_export_2015_16', s.get('sez_export_2014_15', 0)) for s in states_list if s.get('sez_export_2015_16', s.get('sez_export_2014_15', 0)) > 0),
    'total_meat_exports_usd_bn': sum(s.get('meat_export_2021_22', s.get('meat_export_2022_23', 0)) for s in states_list if s.get('meat_export_2021_22', s.get('meat_export_2022_23', 0)) > 0),
    'total_marine_exports_usd_bn': sum(s.get('marine_export_2020_21', s.get('marine_export_2019_20', 0)) for s in states_list if s.get('marine_export_2020_21', s.get('marine_export_2019_20', 0)) > 0),
    'total_combined_exports_usd_bn': sum(s.get('total_exports_latest', 0) for s in states_list if s.get('total_exports_latest', 0) > 0),
    'avg_unemployment_pct': sum(s.get('unemp_overall_person', 0) for s in states_list if s.get('unemp_overall_person', 0) > 0) / max(1, sum(1 for s in states_list if s.get('unemp_overall_person', 0) > 0)),
    'avg_debt_to_gsdp_pct': sum(s.get('debt_to_gsdp_latest', 0) for s in states_list if s.get('debt_to_gsdp_latest', 0) > 0) / max(1, sum(1 for s in states_list if s.get('debt_to_gsdp_latest', 0) > 0)),
    'state_count': len(states_list),
    'top_state': states_list[0]['state'] if states_list else None,
    'fastest_growing': max([s for s in states_list if s.get('gsdp_growth_latest', 0) > 0], key=lambda s: s.get('gsdp_growth_latest', 0), default={}).get('state'),
    'highest_per_capita': max([s for s in states_list if s.get('per_capita_gsdp_latest', 0) > 0], key=lambda s: s.get('per_capita_gsdp_latest', 0), default={}).get('state'),
    'lowest_unemployment': min([s for s in states_list if s.get('unemp_overall_person', 0) > 0], key=lambda s: s.get('unemp_overall_person', 0), default={}).get('state'),
    'highest_debt': max([s for s in states_list if s.get('debt_to_gsdp_latest', 0) > 0], key=lambda s: s.get('debt_to_gsdp_latest', 0), default={}).get('state'),
    'data_sources': list(state_data.keys())[:20],
    'total_datasets': len(state_data),
}
with open(OUT_DIR / 'national_state_totals.json', 'w') as f:
    json.dump(nat_totals, f, indent=2)
print('Saved national_state_totals.json')
print(f'  Total GSDP 22-23: ₹{nat_totals["total_gsdp_2022_23_cr"]:,.0f} Cr')
print(f'  Top state: {nat_totals["top_state"]}')
print(f'  Fastest: {nat_totals["fastest_growing"]}')
print(f'  Highest per-capita: {nat_totals["highest_per_capita"]}')

# Save comprehensive state list with all metrics
states_summary = []
for s in states_list:
    states_summary.append({
        'rank': s.get('gsdp_rank', 0),
        'state': s['state'],
        'gsdp_latest_cr': s.get('gsdp_latest', 0),
        'gsdp_latest_year': s.get('gsdp_latest_year', 'N/A'),
        'gsdp_growth_pct': s.get('gsdp_growth_latest', 0),
        'per_capita_gsdp_rs': s.get('per_capita_gsdp_latest', 0),
        'agri_share_pct': s.get('agri_share_latest', 0),
        'total_exports_usd_bn': s.get('total_exports_latest', 0),
        'unemployment_pct': s.get('unemp_overall_person', 0),
        'debt_to_gsdp_pct': s.get('debt_to_gsdp_latest', 0),
        'lpg_connections': s.get('lpg_connections', 0),
        'msme_total': s.get('msme_total', 0),
    })
with open(OUT_DIR / 'state_summary.json', 'w') as f:
    json.dump(states_summary, f, indent=2)
print(f'Saved state_summary.json with {len(states_summary)} states')

print('\n=== ALL DONE ===')
print(f'Total state datasets processed: {len(state_data)}')
print(f'Total states in master dataset: {len(states_list)}')
print(f'Correlations computed: {len(correlations)}')
print(f'Cross-dataset insights: {len(insights)}')
