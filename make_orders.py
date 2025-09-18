from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, StopLossRequest, TakeProfitRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from parameters import API_KEY, SECRET_KEY

trading_clinet = TradingClient(API_KEY, SECRET_KEY, paper=True)

def get_account_balance():
    return trading_clinet.get_account().cash

def get_orders():
    return trading_clinet.get_orders()

def get_open_positions(symbol: str):
    return trading_clinet.get_open_position(symbol)

def get_positions():
    return trading_clinet.get_all_positions()

def make_market_order(symbol: str, qty: int, side, take_profit: float, stop_loss: float):
    print(f"Take Profit: {take_profit:.2f}\nStop Loss: {stop_loss:.2f}")
    try:
        bracket__order_data = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    time_in_force=TimeInForce.DAY,
                    order_class=OrderClass.BRACKET,
                    take_profit=TakeProfitRequest(limit_price=take_profit),
                    stop_loss=StopLossRequest(stop_price=stop_loss)
                    )

        market_order = trading_clinet.submit_order(bracket__order_data)
        return market_order
    except Exception as e:
        print(f"Error processing trade: {str(e)}")

def make_sell_order(symbol: str, qty: int, side):
    print(f"Placing market order for {qty} shares of {symbol} as a {side} order.")
    try:
        bracket__order_data = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    time_in_force=TimeInForce.DAY,
                    order_class=OrderClass.BRACKET,
                    )

        market_order = trading_clinet.submit_order(bracket__order_data)
        return market_order
    except Exception as e:
        print(f"Error processing trade: {str(e)}")

def close_all_positions():
    return trading_clinet.close_all_positions(True)

if __name__ == "__main__":
    print(get_account_balance())
    print(get_orders())
    print(get_positions())
    print(close_all_positions())