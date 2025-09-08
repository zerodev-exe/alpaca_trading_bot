from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopLossRequest, TakeProfitRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from dotenv import load_dotenv
import os

load_dotenv()

# Get API credentials from environment variables
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

trading_clinet = TradingClient(API_KEY, SECRET_KEY, paper=True)

def get_account():
    return trading_clinet.get_account().portfolio_value

def get_orders():
    return trading_clinet.get_orders()

def get_open_positions(symbol: str):
    return trading_clinet.get_open_position(symbol)

def get_positions():
    return trading_clinet.get_all_positions()

def make_market_order(symbol, qty, side):
    try:
        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY,

        )
        market_order = trading_clinet.submit_order(order_data)
        print(market_order)
        return trading_clinet.submit_order(order_data)
    except Exception as e:
        print(f"Error processing trade: {str(e)}")

def make_stop_order(symbol, qty, side, stop_price):
    try:
        order_data = StopLossRequest(
            symbol=symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY,
            stop_price=stop_price,
        )

        stop_order = trading_clinet.submit_order(order_data)
    except Exception as e:
        print(f"Error processing trade: {str(e)}")
        print(stop_order)

def make_take_order(symbol, qty, side, take_price):
    try:
        order_data = TakeProfitRequest(
            symbol=symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY,
            take_price=take_price,
        )
        take_order = trading_clinet.submit_order(order_data)
    except Exception as e:
        print(f"Error processing trade: {str(e)}")
        print(take_order)

if __name__ == "__main__":
    print(get_account())
    print(get_orders())
    print(get_positions())