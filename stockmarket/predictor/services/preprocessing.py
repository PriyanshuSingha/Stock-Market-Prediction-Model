"""
predictor/services/preprocessing.py
Data preprocessing and feature engineering for ML models.
"""

import logging
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger(__name__)


def preprocess_for_regression(df: pd.DataFrame):
    """
    Prepare features/target for Linear Regression and Random Forest.
    Uses lag features, rolling averages, and day-of-week encoding.

    Returns:
        X_train, X_test, y_train, y_test, scaler, feature_cols, last_features
    """
    logger.debug("Preprocessing for regression models")

    data = df[['Close']].copy()

    # ── Feature engineering ───────────────────────────────────────────────────
    data['lag_1']  = data['Close'].shift(1)
    data['lag_3']  = data['Close'].shift(3)
    data['lag_7']  = data['Close'].shift(7)
    data['lag_14'] = data['Close'].shift(14)
    data['ma_7']   = data['Close'].rolling(7).mean()
    data['ma_21']  = data['Close'].rolling(21).mean()
    data['std_7']  = data['Close'].rolling(7).std()
    data['ema_12'] = data['Close'].ewm(span=12).mean()
    data['day_of_week'] = data.index.dayofweek
    data['month']        = data.index.month

    data.dropna(inplace=True)

    feature_cols = ['lag_1', 'lag_3', 'lag_7', 'lag_14',
                    'ma_7', 'ma_21', 'std_7', 'ema_12',
                    'day_of_week', 'month']

    X = data[feature_cols].values
    y = data['Close'].values

    # ── Scale features ────────────────────────────────────────────────────────
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # ── Train/test split (80/20) ──────────────────────────────────────────────
    split = int(len(X_scaled) * 0.8)
    X_train, X_test = X_scaled[:split], X_scaled[split:]
    y_train, y_test = y[:split], y[split:]

    # ── Last row for forecasting ──────────────────────────────────────────────
    last_features = scaler.transform(data[feature_cols].values[-1:])

    logger.debug(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
    return X_train, X_test, y_train, y_test, scaler, feature_cols, last_features, data


def preprocess_for_lstm(df: pd.DataFrame, look_back: int = 60):
    """
    Prepare sequences for LSTM model.

    Returns:
        X_train, X_test, y_train, y_test, price_scaler, last_sequence
    """
    logger.debug("Preprocessing for LSTM model")

    prices = df['Close'].values.reshape(-1, 1)

    price_scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = price_scaler.fit_transform(prices)

    # ── Build sequences ───────────────────────────────────────────────────────
    X, y = [], []
    for i in range(look_back, len(scaled)):
        X.append(scaled[i - look_back:i, 0])
        y.append(scaled[i, 0])

    X, y = np.array(X), np.array(y)
    X = X.reshape(X.shape[0], X.shape[1], 1)

    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    last_sequence = scaled[-look_back:].reshape(1, look_back, 1)

    logger.debug(f"LSTM Train: {X_train.shape}, Test: {X_test.shape}")
    return X_train, X_test, y_train, y_test, price_scaler, last_sequence
