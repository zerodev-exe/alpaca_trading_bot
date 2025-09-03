from alpaca.data.live import CryptoDataStream, StockDataStream
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

async def handle_crypto_trade(data):
    try:
        print(f"Close price: {data.symbol}, {data.close:.2f}, {data.vwap:.2f}")
        
        # Get historical bars
        request_params = CryptoBarsRequest(
            symbol_or_symbols=data.symbol,
            start=datetime.now() - timedelta(days=1),
            timeframe=TimeFrame.Minute
        )
        
        # Get the bars data
        bars = data_client_crypto.get_crypto_bars(request_params)
        df = bars.df
        
        print(df)
        
        # Calculate SMA
        if len(df) >= 20:  # Only calculate if we have enough data points
            smma20 = ta.trend.sma_indicator(df['close'], window=20, fillna=True)
            print(f"SMA20: {smma20.iloc[-1]:.2f}")

        current_smma = smma20.iloc[-1] if len(df) >= 20 else None
        

    except Exception as e:
        print(f"Error processing trade data: {str(e)}")

if __name__ == "__main__":
    while True:
        try:
            gainers = get_top_gainers.get_top_crypto_gainers()
            for gainer in gainers:
                print(gainer)
                crypto_stream.subscribe_bars(handle_crypto_trade, gainer['symbol'])
            crypto_stream.run()
        except Exception as e:
            print(f"Error in main: {str(e)}")
