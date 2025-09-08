from alpaca.data.live import CryptoDataStream, StockDataStream
from alpaca.trading.enums import OrderSide
from make_orders import *
import ta
import os
from dotenv import load_dotenv
import get_top_gainers
from alpaca.data import StockHistoricalDataClient, StockBarsRequest, CryptoBarsRequest, CryptoHistoricalDataClient
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame
import pandas as pd
import numpy as np

# Load environment variables
load_dotenv()

# Get API credentials from environment variables
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

stock_stream = StockDataStream(API_KEY, SECRET_KEY)
crypto_stream = CryptoDataStream(API_KEY, SECRET_KEY)
data_client_stock = StockHistoricalDataClient(API_KEY, SECRET_KEY)
data_client_crypto = CryptoHistoricalDataClient(API_KEY, SECRET_KEY)

cash_per_trade: float = float(get_account()) / 10

def check_position(symbol):
    """Check if we have an existing position and return position details"""
    try:
        position = get_open_positions(symbol)
        if position is not None and float(position.qty) > 0:
            return True, float(position.qty), position.side
        return False, 0, None
    except Exception as e:
        if "position does not exist" in str(e):
            return False, 0, None
        raise e

async def handle_stock_trade(data):
    try:
        print(f"Close price: {data.symbol}, {data.close:.2f}, {data.vwap:.2f}")

        # Check existing position
        has_position, qty, side = check_position(data.symbol)

        # Get historical bars
        request_params = StockBarsRequest(
            symbol_or_symbols=data.symbol,
            start=datetime.now() - timedelta(days=1),
            timeframe=TimeFrame.Minute
        )

        bars = data_client_stock.get_stock_bars(request_params)
        df = bars.df

        # Calculate SMA
        if len(df) < 20:
            print(f"Not enough data points for {data.symbol}")
            return

        smma20 = ta.trend.sma_indicator(df['close'], window=20, fillna=True)
        current_smma = smma20.iloc[-1]
        print(f"SMA20: {current_smma:.2f}")

        # Trading logic
        if not has_position and (data.close < current_smma*0.95 and data.close > data.vwap):
            # Buy condition - only if we don't have a position
            print(f"Buy signal: Price {data.close:.2f} is under SMMA20 {current_smma:.2f} for {data.symbol}")
            shares = int(cash_per_trade / data.close)
            if shares > 0:
                make_market_order(data.symbol, shares, OrderSide.BUY)
                # make_stop_order(data.symbol, shares, OrderSide.SELL, data.close*0.98)
                # make_take_order(data.symbol, shares, OrderSide.SELL, data.close*1.02)

        elif has_position and (data.close > current_smma*1.02 or data.close <= data.vwap*1):
            # Sell condition - only if we have a long position
            print(f"Sell signal: Price {data.close:.2f} vs SMMA20 {current_smma:.2f} for {data.symbol}")
            make_market_order(data.symbol, int(qty), OrderSide.SELL)

    except Exception as e:
        print(f"Error processing trade data for {data.symbol}: {str(e)}")

if __name__ == "__main__":
    try:
        gainers = get_top_gainers.get_top_stocks_gainers()
        for gainer in gainers:
            print(f"Subscribing to {gainer['symbol']}")
            stock_stream.subscribe_bars(handle_stock_trade, gainer['symbol'])
        while True:
            stock_stream.run()
            print("Waiting for next bar...")
    except Exception as e:
        print(f"Error in main: {str(e)}")
