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

async def handle_stock_trade(data):
    try:
        print(f"Close price: {data.symbol}, {data.close:.2f}, {data.vwap:.2f}")

        # Check for existing position
        try:
            position = get_open_positions(data.symbol)
            has_position = position is not None and float(position.qty) > 0
            if has_position:
                print(f"Position already open for {data.symbol}")
                return
        except Exception as e:
            if "position does not exist" in str(e):
                has_position = False
            else:
                print(f"Error checking position: {str(e)}")
                return

        # Get historical bars
        request_params = StockBarsRequest(
            symbol_or_symbols=data.symbol,
            start=datetime.now() - timedelta(days=1),
            timeframe=TimeFrame.Minute
        )

        # Get the bars data
        bars = data_client_stock.get_stock_bars(request_params)
        df = bars.df

        # Calculate SMA
        if len(df) >= 20:  # Only calculate if we have enough data points
            smma20 = ta.trend.sma_indicator(df['close'], window=20, fillna=True)
            print(f"SMA20: {smma20.iloc[-1]:.2f}")
            current_smma = smma20.iloc[-1]
        else:
            print(f"Not enough data points for {data.symbol}")
            return

        # Buy or sell based on price vs SMMA20
        if data.close < current_smma*0.95 and data.close > data.vwap:
            print(f"Price {data.close:.2f} is under SMMA20 by 5% or more {current_smma:.2f} for {data.symbol}")
            make_market_order(data.symbol, 1, OrderSide.BUY)
        elif data.close > current_smma*1.02 or data.close < data.vwap:
            print(f"Price {data.close:.2f} is over SMMA20 by 2% or more {current_smma:.2f} for {data.symbol}")
            make_market_order(data.symbol, 1, OrderSide.SELL)

    except Exception as e:
        print(f"Error processing trade data for {data.symbol}: {str(e)}")

if __name__ == "__main__":
    try:
        gainers = get_top_gainers.get_top_stocks_gainers()
        for gainer in gainers:
            print(f"Subscribing to {gainer['symbol']}")
            stock_stream.subscribe_bars(handle_stock_trade, gainer['symbol'])
        stock_stream.run()
    except Exception as e:
        print(f"Error in main: {str(e)}")
