# Model Results

## Model Comparison

| Model | MAE | RMSE | MAPE (%) |
|-------|-----|------|----------|
| SARIMAX | 0.06 | 0.20 | 0.12 |
| XGBoost | 0.14 | 0.24 | 0.30 |
| VAR | 0.34 | 0.42 | 0.72 |
| LightGBM | 1.09 | 1.11 | 2.31 |

## Forecast Summary

- **Best model**: Based on MAE score
- **Ensemble**: Simple average of all model forecasts
- **Confidence interval**: 95% from SARIMAX
