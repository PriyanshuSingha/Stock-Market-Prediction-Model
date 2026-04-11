"""
predictor/services/predictor.py
Orchestrates the full prediction pipeline.
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from .data_fetcher import fetch_stock_data
from .preprocessing import preprocess_for_regression, preprocess_for_lstm
from .model_trainer import train_linear_regression, train_random_forest, train_lstm

logger = logging.getLogger(__name__)

SUPPORTED_MODELS = ('linear', 'random_forest', 'lstm')


def run_prediction(symbol: str, model_type: str = 'linear', prediction_days: int = 7) -> dict:
    """
    Full prediction pipeline:
      1. Fetch historical data
      2. Preprocess
      3. Train selected model
      4. Predict future N days
      5. Return structured JSON-serialisable dict

    Args:
        symbol: Ticker symbol (e.g. 'AAPL')
        model_type: 'linear' | 'random_forest' | 'lstm'
        prediction_days: How many future days to forecast

    Returns:
        Complete prediction result dict
    """
    if model_type not in SUPPORTED_MODELS:
        raise ValueError(f"Model '{model_type}' not supported. Choose from: {SUPPORTED_MODELS}")

    logger.info(f"Starting prediction → symbol={symbol}, model={model_type}, days={prediction_days}")

    # ── 1. Fetch data ─────────────────────────────────────────────────────────
    stock_data = fetch_stock_data(symbol)
    df = stock_data['df']

    # ── 2 & 3. Preprocess + Train ────────────────────────────────────────────
    if model_type == 'lstm':
        result = _predict_lstm(df, prediction_days)
    else:
        result = _predict_regression(df, model_type, prediction_days)

    # ── 4. Historical prices for chart (last 180 days) ────────────────────────
    hist_df = df['Close'].tail(180)
    historical_prices = [
        {'date': str(d.date()), 'price': round(float(p), 4)}
        for d, p in zip(hist_df.index, hist_df.values)
    ]

    # ── 5. Assemble response ─────────────────────────────────────────────────
    return {
        'symbol': symbol.upper(),
        'company_name': stock_data['company_name'],
        'sector': stock_data['sector'],
        'currency': stock_data['currency'],
        'current_price': stock_data['current_price'],
        'price_change_pct': stock_data['price_change_pct'],
        'model_used': model_type,
        'historical_prices': historical_prices,
        'predicted_prices': result['predicted_prices'],
        'metrics': result['metrics'],
        'prediction_days': prediction_days,
        'last_updated': datetime.utcnow().isoformat() + 'Z',
    }


# ─── Private helpers ──────────────────────────────────────────────────────────

def _predict_regression(df, model_type, prediction_days):
    X_train, X_test, y_train, y_test, scaler, feature_cols, last_features, data = \
        preprocess_for_regression(df)

    if model_type == 'linear':
        model, metrics = train_linear_regression(X_train, y_train, X_test, y_test)
    else:  # random_forest
        model, metrics = train_random_forest(X_train, y_train, X_test, y_test)

    # ── Iterative future forecasting ─────────────────────────────────────────
    last_row = data.tail(1).copy()
    predictions = []
    last_date = df.index[-1]

    for i in range(prediction_days):
        features = scaler.transform(last_row[feature_cols].values)
        pred_price = float(model.predict(features)[0])
        predictions.append(pred_price)

        # Roll the row forward by 1 day
        next_date = last_date + timedelta(days=i + 1)
        new_row = _build_next_row(last_row, pred_price, next_date, data)
        last_row = new_row
        data = pd.concat([data, new_row])

    predicted_prices = _format_predictions(df.index[-1], predictions, prediction_days)
    return {'predicted_prices': predicted_prices, 'metrics': metrics}


def _predict_lstm(df, prediction_days):
    LOOK_BACK = 60
    X_train, X_test, y_train, y_test, price_scaler, last_sequence = \
        preprocess_for_lstm(df, look_back=LOOK_BACK)

    model, metrics = train_lstm(X_train, y_train, X_test, y_test)

    # ── Rolling forecast ──────────────────────────────────────────────────────
    current_seq = last_sequence.copy()
    predictions_scaled = []

    for _ in range(prediction_days):
        pred = model.predict(current_seq, verbose=0)[0, 0]
        predictions_scaled.append(pred)
        current_seq = np.roll(current_seq, -1, axis=1)
        current_seq[0, -1, 0] = pred

    predictions = price_scaler.inverse_transform(
        np.array(predictions_scaled).reshape(-1, 1)
    ).flatten().tolist()

    predicted_prices = _format_predictions(df.index[-1], predictions, prediction_days)
    return {'predicted_prices': predicted_prices, 'metrics': metrics}


def _format_predictions(last_date, predictions, days):
    result = []
    for i, price in enumerate(predictions):
        future_date = last_date + timedelta(days=i + 1)
        # Skip weekends
        while future_date.weekday() >= 5:
            future_date += timedelta(days=1)
        result.append({'date': str(future_date.date()), 'price': round(float(price), 4)})
    return result


def _build_next_row(last_row, pred_price, next_date, data):
    """Reconstruct a feature row for the next predicted day."""
    history = data['Close'].values
    new_row = pd.DataFrame(index=[next_date])
    new_row['Close']       = pred_price
    new_row['lag_1']       = pred_price
    new_row['lag_3']       = float(np.mean(history[-3:])) if len(history) >= 3 else pred_price
    new_row['lag_7']       = float(np.mean(history[-7:])) if len(history) >= 7 else pred_price
    new_row['lag_14']      = float(np.mean(history[-14:])) if len(history) >= 14 else pred_price
    new_row['ma_7']        = float(np.mean(history[-7:])) if len(history) >= 7 else pred_price
    new_row['ma_21']       = float(np.mean(history[-21:])) if len(history) >= 21 else pred_price
    new_row['std_7']       = float(np.std(history[-7:])) if len(history) >= 7 else 0.0
    new_row['ema_12']      = float(history[-1])
    new_row['day_of_week'] = next_date.weekday()
    new_row['month']       = next_date.month
    return new_row
