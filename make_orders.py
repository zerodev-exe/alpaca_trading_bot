from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopLossRequest, TakeProfitRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from parameters import API_KEY, SECRET_KEY


trading_clinet = TradingClient(API_KEY, SECRET_KEY, paper=True)

def get_account():
    return trading_clinet.get_account().portfolio_value

def get_orders():
    return trading_clinet.get_orders()

def get_open_positions(symbol: str):
    return trading_clinet.get_open_position(symbol)

def get_positions():
    return trading_clinet.get_all_positions()

def make_market_order(symbol, qty, side, take_profit=None, stop_loss=None):
    try:
        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(take_profit),
            stop_loss=StopLossRequest(stop_loss)
        )
        market_order = trading_clinet.submit_order(order_data)
        return market_order
    except Exception as e:
        print(f"Error processing trade: {str(e)}")

if __name__ == "__main__":
    print(get_account())
    print(get_orders())
    print(get_positions())