"""
predictor/services/data_fetcher.py
Fetches historical stock data using yfinance and enriches with company info.
"""

import logging
import yfinance as yf
import pandas as pd

logger = logging.getLogger(__name__)


def fetch_stock_data(symbol: str, period: str = "2y") -> dict:
    """
    Fetch historical OHLCV data + company info for a given ticker symbol.

    Args:
        symbol: Stock ticker (e.g. 'AAPL', 'RELIANCE.NS')
        period: yfinance period string — '1y', '2y', '5y', 'max'

    Returns:
        dict with keys: df, company_name, current_price, price_change_pct, sector, currency

    Raises:
        ValueError: If symbol is invalid or data is empty
    """
    logger.info(f"Fetching data for symbol: {symbol}")

    try:
        ticker = yf.Ticker(symbol.upper())
        df = ticker.history(period=period)

        if df is None or df.empty:
            raise ValueError(f"No data found for symbol '{symbol}'. Please verify the ticker.")

        # ── Clean data ────────────────────────────────────────────────────────
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        df.dropna(inplace=True)
        df.index = pd.to_datetime(df.index)
        df.index = df.index.tz_localize(None)  # Remove timezone for JSON serialization

        # ── Company metadata ─────────────────────────────────────────────────
        info = ticker.info or {}
        company_name = info.get('longName') or info.get('shortName') or symbol.upper()
        currency = info.get('currency', 'USD')
        sector = info.get('sector', 'N/A')

        # ── Price change % (last 2 days) ──────────────────────────────────────
        if len(df) >= 2:
            prev_close = float(df['Close'].iloc[-2])
            current_price = float(df['Close'].iloc[-1])
            price_change_pct = ((current_price - prev_close) / prev_close) * 100
        else:
            current_price = float(df['Close'].iloc[-1])
            price_change_pct = 0.0

        logger.info(f"Successfully fetched {len(df)} rows for {symbol} | Price: {current_price:.2f}")

        return {
            'df': df,
            'company_name': company_name,
            'current_price': round(current_price, 4),
            'price_change_pct': round(price_change_pct, 4),
            'sector': sector,
            'currency': currency,
        }

    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        raise ValueError(f"Could not fetch data for '{symbol}': {str(e)}")
