#!/usr/bin/env python3
"""Predictive Models for Petrochemical Trade Forecasting.

Models implemented:
1. SARIMAX - Time series with exogenous variables
2. Prophet - Facebook's forecasting tool
3. XGBoost - Gradient boosting regression
4. LightGBM - Light gradient boosting
5. VAR - Vector autoregression
6. Ensemble - Stacking of top models
"""

import os
import warnings
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
from sklearn.model_selection import TimeSeriesSplit

# Use all CPU cores
os.environ["OMP_NUM_THREADS"] = str(os.cpu_count())
os.environ["OPENBLAS_NUM_THREADS"] = str(os.cpu_count())
os.environ["MKL_NUM_THREADS"] = str(os.cpu_count())
os.environ["VECLIB_MAXIMUM_THREADS"] = str(os.cpu_count())
os.environ["NUMEXPR_NUM_THREADS"] = str(os.cpu_count())
warnings.filterwarnings('ignore')

DATA_DIR = Path("data/processed")
FIG_DIR = Path("figures")
FIG_DIR.mkdir(exist_ok=True)
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

plt.style.use('seaborn-v0_8-whitegrid')
FIG_DPI = 150


def load_macro_series():
    """Load and align macro time series."""
    series = {}
    for name in ["wti_crude", "usd_inr", "gdp_growth", "fdi_inflows", "cpi_inflation"]:
        path = DATA_DIR / f"macro_{name}.csv"
        if path.exists():
            df = pd.read_csv(path)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
                df = df.set_index("date")
            else:
                df.index = pd.to_datetime(df.index)
            series[name] = df[name]

    # Resample all to monthly
    aligned = pd.DataFrame(series).resample("ME").mean()
    aligned = aligned.ffill()  # Forward fill only, no backfill to avoid garbage
    aligned = aligned.dropna()  # Drop rows with any NaN
    return aligned


def prepare_target_variable():
    """Create target variable from trade balance or import data."""
    # Use WTI crude as proxy for petrochemical price if trade data is limited
    # In practice, we'd use actual petrochemical trade values

    # Try to build from macro data
    macro = load_macro_series()

    # Create synthetic target: petrochemical import index
    # Based on: imports = f(crude_price, usd_inr, gdp, fdi)
    if "wti_crude" in macro.columns and "usd_inr" in macro.columns:
        # Simple model: petrochemical imports ~ crude * exchange_rate * gdp_factor
        target = macro["wti_crude"] * macro["usd_inr"] / 100
        if "gdp_growth" in macro.columns:
            gdp_factor = 1 + macro["gdp_growth"].fillna(0) / 100
            target = target * gdp_factor
        target.name = "petrochemical_import_index"
        return target, macro

    return None, macro


def train_sarimax(target, exog, forecast_steps=12):
    """Train SARIMAX model."""
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    print("  Training SARIMAX...")
    try:
        # Use auto-arima to find best order
        from pmdarima import auto_arima
        auto_model = auto_arima(
            target, exog=exog,
            seasonal=True, m=12,
            suppress_warnings=True,
            stepwise=True,
            error_action='ignore'
        )
        order = auto_model.order
        seasonal_order = auto_model.seasonal_order
        print(f"    Best order: {order}, seasonal: {seasonal_order}")
    except Exception as e:
        print(f"    Auto-ARIMA failed: {e}, using default (1,1,1)")
        order = (1, 1, 1)
        seasonal_order = (1, 1, 1, 12)

    model = SARIMAX(target, exog=exog, order=order, seasonal_order=seasonal_order)
    results = model.fit(disp=False, maxiter=200)

    # Forecast
    last_exog = exog.iloc[-1:] if exog is not None else None
    forecast = results.get_forecast(steps=forecast_steps, exog=pd.DataFrame(
        np.tile(last_exog.values, (forecast_steps, 1)),
        columns=exog.columns
    ))
    forecast_mean = forecast.predicted_mean
    forecast_ci = forecast.conf_int()

    return results, forecast_mean, forecast_ci


def train_prophet(target, exog=None, forecast_steps=12):
    """Train Prophet model."""
    try:
        from prophet import Prophet
    except ImportError:
        print("  Prophet not installed, skipping...")
        return None, None, None

    print("  Training Prophet...")
    df_prophet = pd.DataFrame({
        'ds': target.index,
        'y': target.values
    })

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10,
    )

    # Add regressors
    if exog is not None:
        for col in exog.columns:
            df_prophet[col] = exog[col].values
            model.add_regressor(col)

    model.fit(df_prophet)

    # Make future dataframe
    future = model.make_future_dataframe(periods=forecast_steps, freq='MS')
    if exog is not None:
        # For future periods, repeat the last known exog values
        last_vals = exog.iloc[-1]
        for i in range(1, forecast_steps + 1):
            future_date = target.index[-1] + pd.DateOffset(months=i)
            future.loc[len(future)] = [future_date] + list(last_vals.values)

    forecast = model.predict(future)
    forecast_set = forecast.tail(forecast_steps)

    return model, forecast_set, forecast


def train_xgboost(target, features, forecast_steps=12):
    """Train XGBoost model."""
    try:
        from xgboost import XGBRegressor
    except ImportError:
        print("  XGBoost not installed, skipping...")
        return None, None, None

    print("  Training XGBoost...")

    # Create lag features
    df = pd.DataFrame({'target': target})
    for lag in [1, 2, 3, 6, 12]:
        df[f'lag_{lag}'] = df['target'].shift(lag)

    if features is not None:
        for col in features.columns:
            df[col] = features[col]
            for lag in [1, 3]:
                df[f'{col}_lag_{lag}'] = features[col].shift(lag)

    df['month'] = df.index.month
    df['quarter'] = df.index.quarter
    df = df.dropna()

    X = df.drop('target', axis=1)
    y = df['target']

    model = XGBRegressor(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,  # Use all cores
        tree_method='hist',  # Fast histogram-based method
    )
    model.fit(X, y, eval_set=[(X, y)], verbose=False)

    # Feature importance
    importance = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)

    # Forecast (recursive)
    last_row = df.iloc[-1:].copy()
    forecasts = []
    for _ in range(forecast_steps):
        pred = model.predict(last_row.drop('target', axis=1))[0]
        forecasts.append(pred)
        new_row = last_row.copy()
        new_row['target'] = pred
        lag_map = {1: 'target', 2: 'lag_1', 3: 'lag_2', 6: 'lag_3', 12: 'lag_6'}
        for lag, src_col in lag_map.items():
            col = f'lag_{lag}'
            if col in new_row.columns and src_col in last_row.columns:
                new_row[col] = last_row[src_col].values[0]
        last_row = new_row

    forecast_index = pd.date_range(start=target.index[-1] + pd.DateOffset(months=1),
                                   periods=forecast_steps, freq='ME')
    forecast_series = pd.Series(forecasts, index=forecast_index)

    return model, forecast_series, importance


def train_lightgbm(target, features, forecast_steps=12):
    """Train LightGBM model."""
    try:
        from lightgbm import LGBMRegressor
    except ImportError:
        print("  LightGBM not installed, skipping...")
        return None, None

    print("  Training LightGBM...")

    df = pd.DataFrame({'target': target})
    for lag in [1, 2, 3, 6, 12]:
        df[f'lag_{lag}'] = df['target'].shift(lag)

    if features is not None:
        for col in features.columns:
            df[col] = features[col]

    df['month'] = df.index.month
    df = df.dropna()

    X = df.drop('target', axis=1)
    y = df['target']

    model = LGBMRegressor(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbose=-1,
        n_jobs=-1,  # Use all cores
    )
    model.fit(X, y)

    # Recursive forecast
    last_row = df.iloc[-1:].copy()
    forecasts = []
    for _ in range(forecast_steps):
        pred = model.predict(last_row.drop('target', axis=1))[0]
        forecasts.append(pred)
        new_row = last_row.copy()
        new_row['target'] = pred
        lag_map = {1: 'target', 2: 'lag_1', 3: 'lag_2', 6: 'lag_3', 12: 'lag_6'}
        for lag, src_col in lag_map.items():
            col = f'lag_{lag}'
            if col in new_row.columns and src_col in last_row.columns:
                new_row[col] = last_row[src_col].values[0]
        last_row = new_row

    forecast_index = pd.date_range(start=target.index[-1] + pd.DateOffset(months=1),
                                   periods=forecast_steps, freq='ME')
    forecast_series = pd.Series(forecasts, index=forecast_index)

    return model, forecast_series


def train_var(target, features, forecast_steps=12):
    """Train Vector Autoregression model."""
    from statsmodels.tsa.api import VAR

    print("  Training VAR...")

    df = pd.DataFrame({'target': target})
    if features is not None:
        for col in features.columns[:3]:  # Limit to 3 exog vars
            df[col] = features[col]

    # Drop constant columns and convert to numeric
    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.loc[:, df.nunique() > 1]  # Remove constant columns
    df = df.dropna()

    model = VAR(df)
    try:
        results = model.fit(maxlags=4, ic='aic')
    except:
        results = model.fit(maxlags=2)

    # Forecast
    forecast = results.forecast(df.values[-results.k_ar:], steps=forecast_steps)
    forecast_index = pd.date_range(start=df.index[-1] + pd.DateOffset(months=1),
                                   periods=forecast_steps, freq='ME')
    forecast_df = pd.DataFrame(forecast, index=forecast_index, columns=df.columns)

    return results, forecast_df["target"]


def evaluate_forecast(actual, predicted, model_name):
    """Calculate evaluation metrics."""
    # Align
    common_idx = actual.index.intersection(predicted.index)
    if len(common_idx) == 0:
        return {"model": model_name, "mae": np.nan, "rmse": np.nan, "mape": np.nan}

    a = actual.loc[common_idx].values
    p = predicted.loc[common_idx].values

    mae = mean_absolute_error(a, p)
    rmse = np.sqrt(mean_squared_error(a, p))
    try:
        mape = mean_absolute_percentage_error(a, p) * 100
    except:
        mape = np.nan

    return {"model": model_name, "mae": mae, "rmse": rmse, "mape": mape}


def plot_forecasts(target, forecasts_dict, model_metrics):
    """Plot all model forecasts."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    colors = ["#3498db", "#2ecc71", "#e74c3c", "#9b59b6", "#f39c12", "#1abc9c"]

    # 1. All forecasts overlay
    ax = axes[0, 0]
    ax.plot(target.index, target.values, 'k-', linewidth=2, label='Actual', alpha=0.8)
    for i, (name, fc) in enumerate(forecasts_dict.items()):
        if isinstance(fc, pd.Series):
            ax.plot(fc.index, fc.values, '--', color=colors[i % len(colors)], linewidth=1.5, label=name)
    ax.set_title("All Model Forecasts vs Actual")
    ax.legend(fontsize=8)
    ax.set_ylabel("Value")

    # 2. Model comparison (MAE)
    ax = axes[0, 1]
    if model_metrics:
        models = [m["model"] for m in model_metrics]
        maes = [m["mae"] for m in model_metrics]
        ax.barh(models, maes, color=colors[:len(models)])
        ax.set_title("Model Comparison (MAE - lower is better)")
        ax.set_xlabel("Mean Absolute Error")

    # 3. Ensemble forecast
    ax = axes[1, 0]
    ax.plot(target.index, target.values, 'k-', linewidth=2, label='Actual')
    # Simple average ensemble
    ensemble_fc = None
    count = 0
    for name, fc in forecasts_dict.items():
        if isinstance(fc, pd.Series):
            if ensemble_fc is None:
                ensemble_fc = fc.copy()
            else:
                ensemble_fc = ensemble_fc.add(fc, fill_value=0)
            count += 1
    if ensemble_fc is not None and count > 0:
        ensemble_fc = ensemble_fc / count
        ax.plot(ensemble_fc.index, ensemble_fc.values, 'r--', linewidth=2, label='Ensemble')
    ax.set_title("Ensemble Forecast (Simple Average)")
    ax.legend()
    ax.set_ylabel("Value")

    # 4. Residuals distribution
    ax = axes[1, 1]
    if "sarimax" in forecasts_dict and isinstance(forecasts_dict["sarimax"], pd.Series):
        common = target.index.intersection(forecasts_dict["sarimax"].index)
        if len(common) > 0:
            residuals = target.loc[common].values - forecasts_dict["sarimax"].loc[common].values
            ax.hist(residuals, bins=20, color="#3498db", alpha=0.7, edgecolor='black')
            ax.set_title("SARIMAX Residuals Distribution")
            ax.set_xlabel("Residual")
            ax.set_ylabel("Frequency")

    plt.tight_layout()
    path = FIG_DIR / "06_model_forecasts.pdf"
    plt.savefig(path, dpi=FIG_DPI, bbox_inches='tight')
    plt.close()
    print(f"  Saved {path}")


def plot_feature_importance(importance):
    """Plot XGBoost feature importance."""
    if importance is None or len(importance) == 0:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    importance.head(15).plot(kind="barh", ax=ax, color="#3498db", alpha=0.8)
    ax.set_title("XGBoost Feature Importance (Top 15)")
    ax.set_xlabel("Importance Score")
    plt.tight_layout()
    path = FIG_DIR / "07_feature_importance.pdf"
    plt.savefig(path, dpi=FIG_DPI, bbox_inches='tight')
    plt.close()
    print(f"  Saved {path}")


def write_model_results(metrics, forecasts_dict):
    """Write model results to files."""
    # CSV of metrics
    if metrics:
        df = pd.DataFrame(metrics)
        df.to_csv(RESULTS_DIR / "02_model_metrics.csv", index=False)

    # CSV of forecasts
    fc_df = pd.DataFrame()
    for name, fc in forecasts_dict.items():
        if isinstance(fc, pd.Series):
            fc_df[name] = fc
    if not fc_df.empty:
        fc_df.to_csv(RESULTS_DIR / "03_forecasts.csv")

    # Markdown summary
    md = "# Model Results\n\n"
    md += "## Model Comparison\n\n"
    md += "| Model | MAE | RMSE | MAPE (%) |\n"
    md += "|-------|-----|------|----------|\n"
    if metrics:
        for m in sorted(metrics, key=lambda x: x.get("mae", 999)):
            md += f"| {m['model']} | {m['mae']:.2f} | {m['rmse']:.2f} | {m.get('mape', 'N/A'):.2f} |\n"

    md += "\n## Forecast Summary\n\n"
    md += "- **Best model**: Based on MAE score\n"
    md += "- **Ensemble**: Simple average of all model forecasts\n"
    md += "- **Confidence interval**: 95% from SARIMAX\n"

    path = RESULTS_DIR / "02_model_summary.md"
    with open(path, "w") as f:
        f.write(md)
    print(f"  Saved {path}")


def main():
    import multiprocessing
    ncpu = multiprocessing.cpu_count()
    print("=" * 80)
    print("PREDICTIVE MODELING")
    print(f"  CPU Cores Available: {ncpu}")
    print(f"  Using: ALL cores (n_jobs=-1)")
    print("=" * 80)

    # 1. Prepare data
    print("\n--- Preparing Data ---")
    target, macro = prepare_target_variable()
    if target is None:
        print("ERROR: Could not create target variable")
        return

    print(f"  Target: {target.name}, {len(target)} observations")
    print(f"  Date range: {target.index.min()} to {target.index.max()}")
    print(f"  Features: {list(macro.columns)}")

    # Train/test split: last 24 months for test
    TEST_SIZE = min(24, len(target) // 4)
    train_target = target.iloc[:-TEST_SIZE]
    test_target = target.iloc[-TEST_SIZE:]
    train_macro = macro.loc[macro.index.isin(train_target.index)]
    test_macro = macro.loc[macro.index.isin(test_target.index)]

    print(f"  Train: {len(train_target)} obs, Test: {len(test_target)} obs")

    # 2. Train models
    forecasts = {}
    metrics = []
    FORECAST_STEPS = 12

    # SARIMAX
    print("\n--- SARIMAX ---")
    try:
        sarimax_model, sarimax_fc, sarimax_ci = train_sarimax(train_target, train_macro, FORECAST_STEPS)
        forecasts["sarimax"] = sarimax_fc
        m = evaluate_forecast(test_target, sarimax_fc, "SARIMAX")
        metrics.append(m)
        print(f"    MAE: {m['mae']:.2f}, RMSE: {m['rmse']:.2f}")

        with open(MODEL_DIR / "sarimax.pkl", "wb") as f:
            pickle.dump(sarimax_model, f)
    except Exception as e:
        print(f"    FAILED: {e}")

    # Prophet
    print("\n--- Prophet ---")
    try:
        prophet_model, prophet_fc, prophet_full = train_prophet(train_target, train_macro, FORECAST_STEPS)
        if prophet_fc is not None:
            prophet_series = prophet_fc.set_index('ds')['yhat']
            forecasts["prophet"] = prophet_series
            m = evaluate_forecast(test_target, prophet_series, "Prophet")
            metrics.append(m)
            print(f"    MAE: {m['mae']:.2f}, RMSE: {m['rmse']:.2f}")

            with open(MODEL_DIR / "prophet.pkl", "wb") as f:
                pickle.dump(prophet_model, f)
    except Exception as e:
        print(f"    FAILED: {e}")

    # XGBoost
    print("\n--- XGBoost ---")
    try:
        xgb_model, xgb_fc, xgb_importance = train_xgboost(train_target, train_macro, FORECAST_STEPS)
        if xgb_fc is not None:
            forecasts["xgboost"] = xgb_fc
            m = evaluate_forecast(test_target, xgb_fc, "XGBoost")
            metrics.append(m)
            print(f"    MAE: {m['mae']:.2f}, RMSE: {m['rmse']:.2f}")

            with open(MODEL_DIR / "xgboost.pkl", "wb") as f:
                pickle.dump(xgb_model, f)

            if xgb_importance is not None:
                plot_feature_importance(xgb_importance)
    except Exception as e:
        print(f"    FAILED: {e}")

    # LightGBM
    print("\n--- LightGBM ---")
    try:
        lgbm_model, lgbm_fc = train_lightgbm(train_target, train_macro, FORECAST_STEPS)
        if lgbm_fc is not None:
            forecasts["lightgbm"] = lgbm_fc
            m = evaluate_forecast(test_target, lgbm_fc, "LightGBM")
            metrics.append(m)
            print(f"    MAE: {m['mae']:.2f}, RMSE: {m['rmse']:.2f}")

            with open(MODEL_DIR / "lightgbm.pkl", "wb") as f:
                pickle.dump(lgbm_model, f)
    except Exception as e:
        print(f"    FAILED: {e}")

    # VAR
    print("\n--- VAR ---")
    try:
        var_model, var_fc = train_var(train_target, train_macro, FORECAST_STEPS)
        if var_fc is not None:
            forecasts["var"] = var_fc
            m = evaluate_forecast(test_target, var_fc, "VAR")
            metrics.append(m)
            print(f"    MAE: {m['mae']:.2f}, RMSE: {m['rmse']:.2f}")

            with open(MODEL_DIR / "var.pkl", "wb") as f:
                pickle.dump(var_model, f)
    except Exception as e:
        print(f"    FAILED: {e}")

    # 3. Plot forecasts (show full history + forecast)
    print("\n--- Plotting Forecasts ---")
    plot_forecasts(target, forecasts, metrics)

    # 4. Write results
    print("\n--- Writing Results ---")
    write_model_results(metrics, forecasts)

    print(f"\nModels saved to {MODEL_DIR}/")
    print("=" * 80)


if __name__ == "__main__":
    main()
