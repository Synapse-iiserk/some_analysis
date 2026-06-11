#!/usr/bin/env python3
"""Build comprehensive dataset inventory for the datasets page."""
import json
import os
from pathlib import Path

STATE_DIR = Path('data/raw/state_datasets')
OUT_DIR = Path('data/processed/chart_data')

# Map of filename -> metadata
# Resource IDs from priority_state_ids.json + we use filename as ID
# This is a curated list of all the state datasets we have

DATASET_METADATA = {
    'state_utwise_gross_state_domestic_product_gsdp_and_percen': {
        'title': 'GSDP & Growth (Current/Constant Prices) 2017-18 to 2022-23',
        'category': 'economic',
        'ministry': 'Ministry of Statistics & Programme Implementation',
        'records': 34,
        'states': 34,
        'use': 'Primary GSDP data. Used for state ranking, growth analysis, and per-capita GSDP',
    },
    'statewise_details_of_per_capita_gross_state_domestic_produc': {
        'title': 'Per-Capita GSDP 2019-20 to 2023-24',
        'category': 'economic',
        'ministry': 'Ministry of Statistics & Programme Implementation',
        'records': 28,
        'states': 28,
        'use': 'State income inequality analysis. Used for per-capita ranking and disparity',
    },
    'state_utwise_details_of_share_of_agriculture_and_allied_sec': {
        'title': 'Agriculture & Allied GVA Share in GSDP',
        'category': 'sector',
        'ministry': 'Ministry of Statistics & Programme Implementation',
        'records': 33,
        'states': 33,
        'use': 'Sectoral composition of state economies. Identifies agri-dependent states',
    },
    'state_utwise_indias_export_of_agriculture_products_from_20': {
        'title': 'Agriculture Exports by State 2017-18 to 2022-23',
        'category': 'exports',
        'ministry': 'Ministry of Commerce & Industry',
        'records': 38,
        'states': 38,
        'use': 'State-level agriculture export analysis. Used in state exports breakdown',
    },
    'state_utwise_exports_of_textiles_and_garments_during_20161': {
        'title': 'Textile & Garment Exports by State 2016-17, 2017-18',
        'category': 'exports',
        'ministry': 'Ministry of Textiles',
        'records': 38,
        'states': 38,
        'use': 'State-level textile industry analysis. Used in export composition',
    },
    'statewise_breakup_of_exports_from_sezs_during_201314_to_20': {
        'title': 'SEZ Exports by State 2013-14 to 2015-16',
        'category': 'exports',
        'ministry': 'Ministry of Commerce & Industry',
        'records': 17,
        'states': 17,
        'use': 'Special Economic Zone exports. Identifies export-oriented industrial states',
    },
    'state_utwise_details_of_meat_export_to_world_from_202122_t': {
        'title': 'Meat Exports by State 2021-22 to 2023-24',
        'category': 'exports',
        'ministry': 'Ministry of Commerce & Industry',
        'records': 66,
        'states': 21,
        'use': 'State-level meat export analysis',
    },
    'statewise_marine_products_export_development_authority_mpe': {
        'title': 'Marine Products Exports 2018-19 to 2020-21 (MPEDA)',
        'category': 'exports',
        'ministry': 'Marine Products Export Development Authority',
        'records': 30,
        'states': 12,
        'use': 'Coastal state marine exports',
    },
    'state_utwise_unemployment_rate_in_usual_status_psss_for_': {
        'title': 'Unemployment Rate (PS+SS) by State — Rural/Urban, Male/Female',
        'category': 'employment',
        'ministry': 'MOSPI / PLFS',
        'records': 37,
        'states': 37,
        'use': 'State employment analysis. Used in unemployment visualization and correlations',
    },
    'statewise_worker_population_ratio_per_1000_': {
        'title': 'Worker Population Ratio (per 1000)',
        'category': 'employment',
        'ministry': 'MOSPI / PLFS',
        'records': 39,
        'states': 39,
        'use': 'Labor force participation by state',
    },
    'state_utwise_worker_population_ratio_according_to_usual_sta': {
        'title': 'WPR by Usual Status (Age 15+)',
        'category': 'employment',
        'ministry': 'MOSPI / PLFS',
        'records': 39,
        'states': 39,
        'use': 'Detailed labor force analysis',
    },
    'state_utwise_details_of_lpg_connections_released_as_on_211': {
        'title': 'LPG Connections Released by State (Dec 2017)',
        'category': 'energy',
        'ministry': 'Ministry of Petroleum & Natural Gas',
        'records': 36,
        'states': 36,
        'use': 'State-level LPG penetration. Proxy for energy access and household consumption',
    },
    'state_utwise_lpg_connections_released_under_pradhan_mantri_': {
        'title': 'PMUY LPG Connections Released',
        'category': 'energy',
        'ministry': 'Ministry of Petroleum & Natural Gas',
        'records': 36,
        'states': 36,
        'use': 'PM Ujjwala Yojana adoption by state',
    },
    'state_utwise_details_of_lpg_connections_released_under_prad': {
        'title': 'PMUY Phase-II LPG Connections',
        'category': 'energy',
        'ministry': 'Ministry of Petroleum & Natural Gas',
        'records': 35,
        'states': 35,
        'use': 'Ujjwala 2.0 state coverage',
    },
    'state_utwise_total_new_lpg_connections_including_lpg_conne': {
        'title': 'Total New LPG Connections (including PMUY)',
        'category': 'energy',
        'ministry': 'Ministry of Petroleum & Natural Gas',
        'records': 36,
        'states': 36,
        'use': 'Combined LPG expansion by state',
    },
    'state_utswise_state_government_health_expenditure_sghe_as': {
        'title': 'State Government Health Expenditure (% of GSDP)',
        'category': 'social',
        'ministry': 'National Health Accounts',
        'records': 31,
        'states': 31,
        'use': 'State health spending analysis',
    },
    'state_utwise_details_of_government_health_expenditure_ghe': {
        'title': 'Government Health Expenditure (GHE)',
        'category': 'social',
        'ministry': 'National Health Accounts',
        'records': 31,
        'states': 31,
        'use': 'Combined central+state health spending',
    },
    'statewise_details_of_government_health_expenditure_central': {
        'title': 'Government Health Expenditure (Central+State)',
        'category': 'social',
        'ministry': 'National Health Accounts',
        'records': 31,
        'states': 31,
        'use': 'Total health spending by state',
    },
    'state_utwise_datails_of_expenditure_on_education_and_trainin': {
        'title': 'Education & Training Expenditure by State',
        'category': 'social',
        'ministry': 'Ministry of Education',
        'records': 37,
        'states': 37,
        'use': 'State education spending',
    },
    'state_utwise_details_of_total_outstanding_liabilities_outs': {
        'title': 'Outstanding Liabilities to GSDP',
        'category': 'fiscal',
        'ministry': 'Ministry of Finance',
        'records': 31,
        'states': 31,
        'use': 'State debt analysis',
    },
    'state_utwise_details_of_total_outstanding_liabilities_of_st': {
        'title': 'Outstanding Liabilities of States/UTs (% of GSDP)',
        'category': 'fiscal',
        'ministry': 'Ministry of Finance',
        'records': 31,
        'states': 31,
        'use': 'State debt sustainability',
    },
    'statewise_fiscal_deficit_to_gross_state_domestic_product_g': {
        'title': 'Fiscal Deficit to GSDP',
        'category': 'fiscal',
        'ministry': 'Ministry of Finance',
        'records': 29,
        'states': 29,
        'use': 'State fiscal health',
    },
    'statewise_revenue_deficit_surplus_from_201516_to_201718_': {
        'title': 'Revenue Deficit/Surplus 2015-16 to 2017-18',
        'category': 'fiscal',
        'ministry': 'Ministry of Finance',
        'records': 29,
        'states': 29,
        'use': 'State revenue balance',
    },
    'state_utwise_total_msme_registered_and_classified_under_udya': {
        'title': 'Total MSMEs Registered on Udyam Portal',
        'category': 'industrial',
        'ministry': 'Ministry of MSME',
        'records': 37,
        'states': 37,
        'use': 'MSME count by state. Industrial activity indicator',
    },
    'state_utwise_number_of_total_women_owned_msme_registered_and_': {
        'title': 'Women-Owned MSMEs (Udyam)',
        'category': 'industrial',
        'ministry': 'Ministry of MSME',
        'records': 37,
        'states': 37,
        'use': 'Women entrepreneurship by state',
    },
    'state_utwise_number_of_valid_passports_issued_in_the_countr': {
        'title': 'Valid Passports Issued by State (2023)',
        'category': 'social',
        'ministry': 'Ministry of External Affairs',
        'records': 38,
        'states': 38,
        'use': 'Outbound mobility proxy',
    },
    'statewise_list_of_passports_issued_in_201415_from_minist': {
        'title': 'Passports Issued 2014-15 by State',
        'category': 'social',
        'ministry': 'Ministry of External Affairs',
        'records': 37,
        'states': 37,
        'use': 'Historical passport data',
    },
    'state_utswise_estimated_electrical_energy_requirement_and_p': {
        'title': 'Electrical Energy Requirement & Peak Demand',
        'category': 'energy',
        'ministry': 'Ministry of Power',
        'records': 74,
        'states': 36,
        'use': 'State power demand and consumption',
    },
    'demand_energy_requirementof_power_from_central_generating_': {
        'title': 'Energy Demand from Central Generating Stations 2013-16',
        'category': 'energy',
        'ministry': 'Ministry of Power',
        'records': 35,
        'states': 35,
        'use': 'Central power allocation by state',
    },
    'state_wise_and_month_wise_requirement_and_availability_of_ch': {
        'title': 'Chemical Fertilizer Requirement & Availability (Monthly)',
        'category': 'sector',
        'ministry': 'Department of Fertilizers',
        'records': 100,
        'states': 8,
        'use': 'Fertilizer demand-supply gap by state and month',
    },
    'statewise_and_monthwise_requirement_and_availability_of_ch': {
        'title': 'Chemical Fertilizer Req/Avail 2014 (Monthly)',
        'category': 'sector',
        'ministry': 'Department of Fertilizers',
        'records': 100,
        'states': 8,
        'use': 'Historical fertilizer availability',
    },
    'statewise_monthwise_requirement_and_availability_of_chemic': {
        'title': 'Chemical Fertilizer Req/Avail 2015 (Monthly)',
        'category': 'sector',
        'ministry': 'Department of Fertilizers',
        'records': 100,
        'states': 8,
        'use': 'Fertilizer demand-supply trends',
    },
}

# Group by category
categories = {
    'economic': 'Economic (GSDP, Per-Capita)',
    'exports': 'Exports by State',
    'employment': 'Employment & Labor',
    'sector': 'Sector-Specific (Fertilizer, Agriculture)',
    'energy': 'Energy (LPG, Power)',
    'social': 'Social (Health, Education, Passports)',
    'fiscal': 'Fiscal (Debt, Deficit)',
    'industrial': 'Industrial (MSMEs)',
}

inventory = {}
for cat, label in categories.items():
    inventory[cat] = {
        'label': label,
        'datasets': [],
    }

# Add datasets to categories
for filename, meta in DATASET_METADATA.items():
    cat = meta.get('category', 'economic')
    if cat not in inventory:
        inventory[cat] = {'label': cat, 'datasets': []}
    inventory[cat]['datasets'].append({
        'filename': filename,
        'title': meta['title'],
        'ministry': meta['ministry'],
        'records': meta['records'],
        'states': meta['states'],
        'use': meta['use'],
    })

# Save
with open(OUT_DIR / 'state_datasets_inventory.json', 'w') as f:
    json.dump({
        'total_state_datasets': len(DATASET_METADATA),
        'total_records': sum(m['records'] for m in DATASET_METADATA.values()),
        'categories': inventory,
    }, f, indent=2)

print(f'Saved state_datasets_inventory.json')
print(f'  Total state datasets: {len(DATASET_METADATA)}')
print(f'  Total records: {sum(m["records"] for m in DATASET_METADATA.values())}')
print()
for cat, info in inventory.items():
    print(f'  {info["label"]}: {len(info["datasets"])} datasets')
