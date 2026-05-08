import time

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderClass, OrderSide, TimeInForce
from alpaca.trading.requests import (
    MarketOrderRequest,
    StopLossRequest,
    TakeProfitRequest,
    TrailingStopOrderRequest,
)

from parameters import API_KEY, SECRET_KEY

trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)


def get_account_balance():
    return trading_client.get_account().cash


def get_orders():
    return trading_client.get_orders()


def get_open_positions(symbol: str):
    return trading_client.get_open_position(symbol)


def get_positions():
    return trading_client.get_all_positions()


def make_market_order(
    symbol: str,
    qty: int,
    side,
    take_profit: float,
    stop_loss: float,
    entry_price: float,
):
    try:
        trail_percent = 0.001

        bracket_order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(limit_price=take_profit),
            stop_loss=StopLossRequest(stop_price=stop_loss),
        )

        market_order = trading_client.submit_order(bracket_order_data)

        trailing_stop_data = TrailingStopOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.GTC,
            trail_percent=trail_percent,
        )

        trailing_order = trading_client.submit_order(trailing_stop_data)

        print(
            f"Take Profit: {take_profit:.2f}\nStop Loss: {stop_loss:.2f}\nTrail: {trail_percent * 100}%"
        )
        return market_order
    except Exception as e:
        print(f"Error processing trade: {str(e)}")


def make_sell_order(symbol: str, qty: int, side):
    try:
        bracket_order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.BRACKET,
        )

        market_order = trading_client.submit_order(bracket_order_data)
        print(f"Placing sell order for {qty} shares of {symbol} as a {side} order.")
        return market_order
    except Exception as e:
        print(f"Error processing trade: {str(e)}")


def make_trailing_stop_order(symbol: str, qty: int, side, trail_price: float):
    try:
        trailing_stop_data = TrailingStopOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY,
            trail_price=trail_price,
        )

        order = trading_client.submit_order(trailing_stop_data)
        print(f"Trailing stop order placed with trail: ${trail_price:.2f}")
        return order
    except Exception as e:
        print(f"Error placing trailing stop order: {str(e)}")


def close_all_positions():
    return trading_client.close_all_positions()


def buy_order_trailing_stop(symbol: str, qty: int, trailing_percent: float):
    side = OrderSide.BUY
    bracket_order_data = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=side,
        time_in_force=TimeInForce.DAY,
        order_class=OrderClass.SIMPLE,
    )

    market_order = trading_client.submit_order(bracket_order_data)

    print(f"Placing buy order for {qty} shares of {symbol} as a {side} order.")

    time.sleep(10)  # Wait for the buy order to fill

    try:
        trailing_stop = TrailingStopOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.GTC,
            trail_percent=trailing_percent,
        )
        trailing_order = trading_client.submit_order(trailing_stop)
    except Exception as e:
        if "hard-to-borrow" in str(e).lower():
            print(f"Skipping trailing stop for {symbol} (hard-to-borrow asset)")
        else:
            raise


if __name__ == "__main__":
    # print(get_account_balance())
    # print(get_orders())
    # print(get_positions())
    # print(close_all_positions())
    buy_order_trailing_stop("PLTR", 1, 0.1)
