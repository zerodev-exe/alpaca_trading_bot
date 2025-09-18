from alpaca.data.live import CryptoDataStream, StockDataStream
from alpaca.trading.enums import OrderSide
from make_orders import *
import ta
import get_top_gainers
from alpaca.data import StockHistoricalDataClient, StockBarsRequest, CryptoBarsRequest, CryptoHistoricalDataClient
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame
from parameters import API_KEY, SECRET_KEY
from datetime import datetime
import pytz

stock_stream = StockDataStream(API_KEY, SECRET_KEY)
data_client_stock = StockHistoricalDataClient(API_KEY, SECRET_KEY)
crypto_stream = CryptoDataStream(API_KEY, SECRET_KEY)
data_client_crypto = CryptoHistoricalDataClient(API_KEY, SECRET_KEY)

cash_per_trade: float = float(get_account_balance()) / 10 # Allocate 10% of account balance per trade

# Dictionary to store purchase prices
purchase_prices = {}

def is_near_time(target_hour, target_minute, tolerance_seconds=30, timezone_str='US/Eastern'):
    """
    Check if current time is within tolerance of target time
    """
    tz = pytz.timezone(timezone_str)
    now = datetime.now(tz)
    
    target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    time_diff = abs((now - target_time).total_seconds())
    
    return time_diff <= tolerance_seconds

def check_position(symbol):
    """Check if we have an existing position and return position details"""
    try:
        position = get_open_positions(symbol)
        if position is not None and float(position.qty) > 0:
            return True, float(position.qty)
        return False, 0
    except Exception as e:
        if "position does not exist" in str(e):
            return False, 0
        raise e

async def handle_stock_trade(data):
    try:
        # Check existing position
        has_position, qty = check_position(data.symbol)

        # Filter out stocks that are higher than $5
        if data.close > 5.0:
            return


        # Get historical bars
        request_params = StockBarsRequest(
            symbol_or_symbols=data.symbol,
            start=datetime.now() - timedelta(minutes=25),
            timeframe=TimeFrame.Minute
        )

        # Transforming bars into a dataframe
        df = data_client_stock.get_stock_bars(request_params).df

        # Calculate SMA
        if len(df) < 20:
            print(f"Not enough data points for {data.symbol}")
            return

        smma20 = ta.trend.sma_indicator(df['close'], window=20, fillna=True)
        # rsi = ta.momentum.rsi_indicator(df, window=14, fillna=True)
        # print(rsi)
        current_smma = smma20.iloc[-1]

        print(f"{data.symbol} : {data.close} < {current_smma*0.95:.2f} and {data.close} >= {data.vwap}")
        # Trading logic
        if not has_position and (data.close < current_smma*0.95 ): # and data.close >= data.vwap
            # Buy condition - only if we don't have a position
            shares = int(cash_per_trade / data.close)
            if shares > 0:
                # Ensure stop loss is at least $0.01 below the current price
                stop_loss = min(round(data.close*0.95, 2), data.close - 0.02)
                take_profit = round(current_smma*1.02, 2)
                # take_profit = round(data.close*1.02, 2)
                print(f"BOT : {data.symbol} {data.close:.2f} (Stop Loss: {stop_loss:.2f}, Take Profit: {take_profit:.2f})")
                make_market_order(data.symbol, shares, OrderSide.BUY, take_profit, stop_loss)

                # Store the purchase price
                purchase_prices[data.symbol] = data.close

        elif has_position and data.symbol in purchase_prices:
            purchase_price = purchase_prices[data.symbol]
            # Sell only if current price is above purchase price and meets other conditions
            if (data.close > purchase_price and 
                (data.close > current_smma*1.02 or data.close <= data.vwap*0.95)):
                print(f"SOLD : {data.symbol} {data.close:.2f} (Bought at: {purchase_price:.2f})")
                make_sell_order(data.symbol, int(qty), OrderSide.SELL)

                # Remove the symbol from purchase_prices after selling
                del purchase_prices[data.symbol]

        # Check if it's within 30 seconds of 3:59 PM
        if is_near_time(15, 59, tolerance_seconds=30):
            print("It's very close to 3:59 PM!")
            close_all_positions()
            stock_stream.stop()
            exit(0)

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

