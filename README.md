# India Petrochemical Trade Analysis & Forecast

A comprehensive analysis of India's petrochemical trade patterns, macroeconomic correlations, and 12-month forecasts under three geopolitical scenarios.

**Live Site:** https://synapse-iiserk.github.io/some_analysis/

## What's Inside

- **31 datasets** from data.gov.in (petrochemicals, chemicals, crude oil, GDP, IIP, FDI, CPI)
- **9 World Bank indicators** (GDP, FDI, trade, CPI, population, etc.)
- **4 predictive models** (SARIMAX, XGBoost, LightGBM, VAR) trained on 12 CPU cores
- **3 scenario forecasts** (Base/Bull/Bear) for Jul 2026 – Jun 2027
- **6 verdicts** with evidence, recommendations, and projected impact
- **8 actionable insights** with data sources
- **Interactive Plotly.js charts** with hover effects, zoom, and scenario comparisons

## Pages

| Page | Content |
|------|---------|
| [Overview](/) | Executive summary, key metrics, trade balance chart, model performance |
| [Trade](/trade) | Product-level import/export analysis, sector breakdowns |
| [Forecast](/forecast) | 12-month scenario analysis (Base/Bull/Bear), monthly data tables |
| [Models](/models) | Model comparison, feature importance, architecture details |
| [Deep Analysis](/analysis) | Investment gaps, risk matrix, trajectory projections, actionable insights |
| [Data Sources](/datasets) | All 31 datasets, World Bank indicators, API endpoints, methodology |

## Project Structure

```
├── .github/workflows/deploy.yml   # GitHub Pages deployment
├── docs/                           # Static site (GitHub Pages)
│   ├── index.html                  # Home page
│   ├── trade.html                  # Trade analysis
│   ├── forecast.html               # Forecast & scenarios
│   ├── models.html                 # Model performance
│   ├── analysis.html               # Deep analysis
│   ├── datasets.html               # Data sources
│   ├── data/                       # JSON/CSV data files
│   ├── figures/                    # PNG chart images
│   └── results/                    # Model results
├── templates/                      # Jinja2 templates (source)
├── *.py                            # Analysis scripts
├── app.py                          # Flask dev server
├── build_static.py                 # Renders templates → docs/
└── pyproject.toml                  # Python dependencies
```

## Local Development

```bash
# Install dependencies
pip install flask pandas jinja2

# Run Flask dev server
python app.py
# → http://localhost:5000

# Or build static site and serve
python build_static.py
python -m http.server 8000 -d docs/
# → http://localhost:8000
```

## Data Pipeline

1. `download_datasets.py` — Fetch 31 datasets from data.gov.in API
2. `scrape_external_data.py` — Scrape World Bank indicators
3. `01_data_engineering.py` — Clean, merge, feature-engineer
4. `02_eda_correlation.py` — Exploratory analysis
5. `03_models.py` — Train 4 models (12 CPU cores)
6. `04_forecast.py` — Generate scenario forecasts
7. `generate_analysis_content.py` — Create verdicts and insights
8. `build_static.py` — Render static HTML for GitHub Pages

## Key Findings

- **Trade Deficit**: ₹29,370 Cr (FY2024-25), growing 4% annually
- **Middle East Dependency**: 52.3% of imports from one region
- **Best Model**: SARIMAX (MAE 0.06, MAPE 0.12%)
- **Base Case Deficit (Jun 2027)**: ₹39,780 Cr
- **Bull Case Deficit (Jun 2027)**: ₹7,830 Cr
- **Investment Gap**: ₹141,000 Cr across 7 sectors

## License

Data sourced from India's Open Government Data Platform (data.gov.in) under open data policy.
