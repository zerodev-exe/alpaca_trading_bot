from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from dotenv import load_dotenv
import os

load_dotenv()

# Get API credentials from environment variables
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

trading_clinet = TradingClient(API_KEY, SECRET_KEY, paper=True)

def get_account():
    return trading_clinet.get_account().buying_power

def get_orders():
    return trading_clinet.get_orders()

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

def make_limit_order(symbol, qty, side, limit_price):
    order_data = LimitOrderRequest(
        symbol=symbol,
        qty=qty,
        side=side,
        time_in_force=TimeInForce.DAY,
        limit_price=limit_price,
    )

    limit_order = trading_clinet.submit_order(order_data)
    print(limit_order)

if __name__ == "__main__":
    print(get_account())
    print(get_orders())
    print(get_positions())