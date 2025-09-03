from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from dotenv import load_dotenv
import os

load_dotenv()

# Get API credentials from environment variables
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

trading_clinet = TradingClient(API_KEY, SECRET_KEY, paper=True)

print(trading_clinet.get_account().buying_power)

makert_oder_data = MarketOrderRequest(
    symbol="SPY",
    qty=1,
    side=OrderSide.SELL,
    time_in_force=TimeInForce.DAY,
)

limit_oder_data = LimitOrderRequest(
    symbol="SPY",
    qty=1,
    side=OrderSide.BUY,
    time_in_force=TimeInForce.DAY,
    limit_price=640.00,
)

limit_order = trading_clinet.submit_order(limit_oder_data)
print(limit_order)