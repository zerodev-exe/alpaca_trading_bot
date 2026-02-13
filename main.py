import argparse
import asyncio
from alpaca.data.live import StockDataStream, CryptoDataStream
from alpaca.trading.enums import OrderSide
from make_orders import *
import ta
import get_top_gainers
from alpaca.data import (
    StockHistoricalDataClient,
    CryptoHistoricalDataClient,
    StockBarsRequest,
    CryptoBarsRequest,
)
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame
from parameters import API_KEY, SECRET_KEY
import pytz

stock_stream = StockDataStream(API_KEY, SECRET_KEY)
crypto_stream = CryptoDataStream(API_KEY, SECRET_KEY)
data_client_stock = StockHistoricalDataClient(API_KEY, SECRET_KEY)
data_client_crypto = CryptoHistoricalDataClient(API_KEY, SECRET_KEY)

cash_per_trade: float = (
    float(get_account_balance()) / 10
)  # Allocate 10% of account balance per trade

# Dictionary to store purchase prices
purchase_prices = {}


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


async def handle_crypto_trade(data):
    try:
        if not data.symbol.endswith("/USD"):
            return

        # Get historical bars
        request_params = CryptoBarsRequest(
            symbol_or_symbols=data.symbol,
            start=datetime.now() - timedelta(minutes=60),
            timeframe=TimeFrame.Minute,
        )

        # Transforming bars into a dataframe
        df = data_client_crypto.get_crypto_bars(request_params).df

        # Calculate SMA
        if len(df) < 20:
            print(f"Not enough data points for {data.symbol}")
            return

        smma20 = ta.trend.sma_indicator(df["close"], window=20, fillna=True)
        rsi = ta.momentum.RSIIndicator(df["close"], window=14, fillna=True).rsi()

        current_smma = smma20.iloc[-1]
        current_rsi = rsi.iloc[-1]

        print(
            f"{data.symbol} : ({data.close} < {current_smma * 0.95:.2f} or {current_rsi:.2f} < 30) and {data.close} >= {data.vwap:.2f} : ({data.close < current_smma * 0.95} or {current_rsi < 30}) and {data.close >= data.vwap}"
        )
        # Trading logic
        if (
            data.close < current_smma * 0.95 or current_rsi < 30
        ) and data.close >= data.vwap:
            # Buy condition - only if we don't have a position
            shares = int(cash_per_trade / data.close)
            if shares > 0:
                # Ensure stop loss is at least $0.01 below the current price
                stop_loss = round(min(data.close * 0.95, data.close - 0.01), 2)
                take_profit = round(max(data.close * 1.02, data.close + 0.01), 2)
                print(
                    f"BOT : {data.symbol} {data.close:.2f} (Stop Loss: {stop_loss:.2f}, Take Profit: {take_profit:.2f})"
                )
                order = make_market_order(
                    data.symbol, shares, OrderSide.BUY, take_profit, stop_loss
                )
                print(order)
                # Store the purchase price
                purchase_prices[data.symbol] = data.close

        # Check if it's within 30 seconds of 3:59 PM
        if data.timestamp.astimezone(pytz.timezone("US/Eastern")).hour == 15:
            print("It's very close to 3:59 PM!")
            close_all_positions()
            crypto_stream.stop()

    except Exception as e:
        print(f"Error processing trade data for {data.symbol}: {str(e)}")


async def handle_stock_trade(data):
    try:
        # Filter out stocks that are above $5 or below $1
        if data.close > 5.0 or data.close < 1.0:
            return

        # Get historical bars
        request_params = StockBarsRequest(
            symbol_or_symbols=data.symbol,
            start=datetime.now() - timedelta(minutes=25),
            timeframe=TimeFrame.Minute,
        )

        # Transforming bars into a dataframe
        df = data_client_stock.get_stock_bars(request_params).df

        # Calculate SMA
        if len(df) < 20:
            print(f"Not enough data points for {data.symbol}")
            return

        smma20 = ta.trend.sma_indicator(df["close"], window=20, fillna=True)
        rsi = ta.momentum.RSIIndicator(df["close"], window=14, fillna=True).rsi()

        current_smma = smma20.iloc[-1]
        current_rsi = rsi.iloc[-1]

        # Check existing position
        has_position, qty = check_position(data.symbol)

        # Trading logic
        if data.close < current_smma * 0.95 or current_rsi < 30:
            # Buy condition - only if we don't have a position
            shares = int(cash_per_trade / data.close)
            if shares > 0:
                # Ensure stop loss is at least $0.02 below the current price
                stop_loss = round(min(data.close * 0.98, data.close - 0.02), 2)
                take_profit = round(max(data.close * 1.02, data.close + 0.01), 2)
                print(
                    f"BOT : {data.symbol} {data.close:.2f} (Stop Loss: {stop_loss:.2f}, Take Profit: {take_profit:.2f})"
                )
                order = make_market_order(
                    data.symbol, shares, OrderSide.BUY, take_profit, stop_loss
                )
                # Store the purchase price
                purchase_prices[data.symbol] = data.close

        elif has_position and data.symbol in purchase_prices:
            purchase_price = purchase_prices[data.symbol]
            # Sell only if current price is above purchase price and meets other conditions
            if data.close > purchase_price and (
                data.close > current_smma * 1.02 or data.close <= data.vwap * 0.95
            ):
                print(
                    f"SOLD : {data.symbol} {data.close:.2f} (Bought at: {purchase_price:.2f})"
                )
                make_sell_order(data.symbol, int(qty), OrderSide.SELL)
                # Remove the symbol from purchase_prices after selling
                del purchase_prices[data.symbol]

        # Check if it's near 3:00 PM Eastern Time to close all positions
        if is_near_time(15, 00, tolerance_seconds=30):
            print("It's time to close all positions.")
            close_all_positions()
            print("All positions closed. See you tomorrow ;) Exiting...")
            exit(0)

    except Exception as e:
        print(f"Error processing trade data for {data.symbol}: {str(e)}")


def run_crypto_trading():
    try:
        gainers, losers = get_top_gainers.get_top_crypto_gainers()
        for gainer in gainers:
            crypto_stream.subscribe_bars(handle_crypto_trade, gainer["symbol"])
        for loser in losers:
            crypto_stream.subscribe_bars(handle_crypto_trade, loser["symbol"])
        crypto_stream.run()
        while True:
            print("Waiting for next bar...")
    except Exception as e:
        print(f"Error in crypto trading: {str(e)}")


def run_stock_trading():
    try:
        gainers, losers = get_top_gainers.get_top_stocks_gainers()
        for gainer in gainers:
            print(f"Subscribing to {gainer['symbol']}")
            stock_stream.subscribe_bars(handle_stock_trade, gainer["symbol"])
        for loser in losers:
            print(f"Subscribing to {loser['symbol']}")
            stock_stream.subscribe_bars(handle_stock_trade, loser["symbol"])
        stock_stream.run()
        while True:
            print("Waiting for next bar...")
    except Exception as e:
        print(f"Error in stock trading: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trading bot for stocks and crypto")
    parser.add_argument(
        "market_type",
        choices=["crypto", "stock"],
        help="Type of market to trade: crypto or stock",
    )
    args = parser.parse_args()

    if args.market_type == "crypto":
        print("Starting crypto trading bot...")
        run_crypto_trading()
    elif args.market_type == "stock":
        print("Starting stock trading bot...")
        run_stock_trading()
