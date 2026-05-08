from datetime import datetime, timedelta

import pytz
import ta
from alpaca.data import StockBarsRequest, StockHistoricalDataClient
from alpaca.data.live import StockDataStream
from alpaca.data.timeframe import TimeFrame

import get_top_gainers
from make_orders import *
from parameters import API_KEY, SECRET_KEY

stock_stream = StockDataStream(API_KEY, SECRET_KEY)
data_client_stock = StockHistoricalDataClient(API_KEY, SECRET_KEY)

cash_per_trade: float = (
    float(get_account_balance()) / 10
)  # Allocate 10% of account balance per trade


def is_near_time(
    target_hour, target_minute, tolerance_seconds=30, timezone_str="US/Eastern"
):
    """
    Check if current time is within tolerance of target time
    """
    tz = pytz.timezone(timezone_str)
    now = datetime.now(tz)

    target_time = now.replace(
        hour=target_hour, minute=target_minute, second=0, microsecond=0
    )
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
        # Get historical bars
        request_params = StockBarsRequest(
            symbol_or_symbols=data.symbol,
            start=datetime.now() - timedelta(minutes=15),
            timeframe=TimeFrame.Minute,
        )

        # Transforming bars into a dataframe
        df = data_client_stock.get_stock_bars(request_params).df

        # Calculate SMA
        if len(df) < 20:
            print(f"Not enough data points for {data.symbol}")
            return

        # smma20 = ta.trend.sma_indicator(df["close"], window=20, fillna=True)
        rsi = ta.momentum.RSIIndicator(df["close"], window=14, fillna=True).rsi()

        # current_smma = smma20.iloc[-1]
        current_rsi = rsi.iloc[-1]

        # Check existing position
        has_position, qty = check_position(data.symbol)

        # print(f"{data.symbol} : ({data.close} < {current_smma*0.95:.2f} or {current_rsi:.2f} < 30) and {data.close} >= {data.vwap:.2f} : ({data.close < current_smma*0.95} or {current_rsi < 30}) and {data.close >= data.vwap}")
        # Trading logic
        # if data.close < current_smma * 0.95 or current_rsi < 30:
        if current_rsi < 30:
            # Buy condition - only if we don't have a position and haven't ordered it
            shares = int(cash_per_trade / data.close)
            if shares > 0:
                order = buy_order_trailing_stop(
                    symbol=data.symbol, qty=shares, trailing_percent=2
                )

        # Check if it's near 3:00 PM Eastern Time to close all positions
        if is_near_time(15, 00, tolerance_seconds=30):
            print("It's time to close all positions.")
            close_all_positions()
            print("All positions closed. See you tomorrow ;) Exiting...")
            exit(0)

    except Exception as e:
        print(f"Error processing trade data for {data.symbol}: {str(e)}")


if __name__ == "__main__":
    while True:
        try:
            gainers, losers = get_top_gainers.get_top_stocks_gainers()
            for gainer in gainers:
                print(f"Subscribing to {gainer['symbol']}")
                stock_stream.subscribe_bars(handle_stock_trade, gainer["symbol"])
            for loser in losers:
                print(f"Subscribing to {loser['symbol']}")
                stock_stream.subscribe_bars(handle_stock_trade, loser["symbol"])
            stock_stream.run()

            print("Waiting for next bar...")
        except Exception as e:
            print(f"Error in main: {str(e)}")
