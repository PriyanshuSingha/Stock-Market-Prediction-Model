"""
predictor/services/model_trainer.py
Train Linear Regression, Random Forest, and LSTM models.
"""

import logging
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

logger = logging.getLogger(__name__)


def train_linear_regression(X_train, y_train, X_test, y_test):
    """Train Linear Regression and return model + metrics."""
    logger.info("Training Linear Regression model")

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    metrics = _compute_metrics(y_test, y_pred)

    logger.info(f"Linear Regression → R2: {metrics['r2_score']:.4f}, RMSE: {metrics['rmse']:.4f}")
    return model, metrics


def train_random_forest(X_train, y_train, X_test, y_test):
    """Train Random Forest and return model + metrics."""
    logger.info("Training Random Forest model")

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    metrics = _compute_metrics(y_test, y_pred)

    logger.info(f"Random Forest → R2: {metrics['r2_score']:.4f}, RMSE: {metrics['rmse']:.4f}")
    return model, metrics


def train_lstm(X_train, y_train, X_test, y_test):
    """
    Build and train an LSTM model using Keras.
    Falls back gracefully if TensorFlow is unavailable.
    """
    logger.info("Training LSTM model")

    try:
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout
        from tensorflow.keras.callbacks import EarlyStopping

        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=(X_train.shape[1], 1)),
            Dropout(0.2),
            LSTM(64, return_sequences=False),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dense(1),
        ])

        model.compile(optimizer='adam', loss='mean_squared_error')

        early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

        model.fit(
            X_train, y_train,
            epochs=50,
            batch_size=32,
            validation_split=0.1,
            callbacks=[early_stop],
            verbose=0,
        )

        y_pred = model.predict(X_test, verbose=0).flatten()
        metrics = _compute_metrics(y_test, y_pred)

        logger.info(f"LSTM → R2: {metrics['r2_score']:.4f}, RMSE: {metrics['rmse']:.4f}")
        return model, metrics

    except ImportError:
        logger.warning("TensorFlow not available, falling back to Random Forest for LSTM slot")
        raise ImportError("TensorFlow/Keras is required for LSTM. Install it via: pip install tensorflow")


def _compute_metrics(y_true, y_pred) -> dict:
    """Compute R2, MSE, and RMSE."""
    mse  = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    r2   = float(r2_score(y_true, y_pred))
    return {
        'r2_score': round(r2, 6),
        'mse':      round(mse, 6),
        'rmse':     round(rmse, 6),
    }
