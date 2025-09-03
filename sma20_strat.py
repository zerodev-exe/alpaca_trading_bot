import os
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetAssetsRequest
from alpaca.trading.enums import OrderSide, TimeInForce, AssetClass
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SMAmeanReversionBot:
    def __init__(self, api_key, secret_key, paper=True):
        """
        Initialize the SMA Mean Reversion trading bot
        
        Args:
            api_key (str): Alpaca API key
            secret_key (str): Alpaca secret key
            paper (bool): Use paper trading (default: True)
        """
        self.trading_client = TradingClient(api_key, secret_key, paper=paper)
        self.data_client = StockHistoricalDataClient(api_key, secret_key)

        # Strategy parameters
        self.sma_period = 20
        self.buy_threshold = -0.05  # Buy when 5% below SMA
        self.sell_threshold = 0.02  # Sell when 2% above SMA
        self.max_position_size = 1000  # Max dollars per position
        self.max_stock_price = 5.0  # Only trade stocks under $5

        # Tracking
        self.positions = {}
        self.watchlist = []

    def get_account_info(self):
        """Get account information"""
        try:
            account = self.trading_client.get_account()
            logger.info(f"Account equity: ${float(account.equity):,.2f}")
            logger.info(f"Buying power: ${float(account.buying_power):,.2f}")
            return account
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None

    def get_tradeable_assets(self):
        """Get list of tradeable stocks under $5"""
        try:
            search_params = GetAssetsRequest(
                status='active',
                asset_class=AssetClass.US_EQUITY
            )
            assets = self.trading_client.get_all_assets(search_params)

            # Filter for tradeable stocks (you might want to add your own screening logic)
            tradeable = []
            for asset in assets:
                if (asset.tradable and
                    asset.shortable and
                    asset.marginable and
                        asset.status == 'active'):
                    tradeable.append(asset.symbol)

            return tradeable[:50]  # Limit to 50 for demo
        except Exception as e:
            logger.error(f"Error getting assets: {e}")
            return []

    def get_stock_data(self, symbol, bars=30):
        """Get recent 1-minute bar data for a symbol"""
        try:
            end_time = datetime.now()
            # Get last 2 hours of data
            start_time = end_time - timedelta(hours=2)

            request_params = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=TimeFrame.Minute,
                start=start_time,
                end=end_time
            )

            bars_data = self.data_client.get_stock_bars(request_params)

            if symbol in bars_data.data:
                df = pd.DataFrame([{
                    'timestamp': bar.timestamp,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume
                } for bar in bars_data.data[symbol]])

                df = df.sort_values('timestamp').reset_index(drop=True)
                return df
            return None

        except Exception as e:
            logger.error(f"Error getting data for {symbol}: {e}")
            return None

    def calculate_sma(self, df, period):
        """Calculate Simple Moving Average"""
        if len(df) < period:
            return None
        return df['close'].rolling(window=period).mean().iloc[-1]

    def calculate_signal(self, symbol):
        """Calculate buy/sell signal based on SMA strategy"""
        try:
            df = self.get_stock_data(symbol)
            if df is None or len(df) < self.sma_period:
                return None, None

            current_price = df['close'].iloc[-1]

            # Skip if stock price is above $5
            if current_price > self.max_stock_price:
                return None, None

            sma_20 = self.calculate_sma(df, self.sma_period)
            if sma_20 is None:
                return None, None

            # Calculate percentage difference from SMA
            price_diff_pct = (current_price - sma_20) / sma_20

            signal = None

            # Buy signal: price is 5% or more below SMA 20
            if price_diff_pct <= self.buy_threshold:
                signal = 'BUY'

            # Sell signal: price is 2% or more above SMA 20
            elif price_diff_pct >= self.sell_threshold:
                signal = 'SELL'

            return signal, {
                'symbol': symbol,
                'current_price': current_price,
                'sma_20': sma_20,
                'price_diff_pct': price_diff_pct * 100
            }

        except Exception as e:
            logger.error(f"Error calculating signal for {symbol}: {e}")
            return None, None

    def get_position_size(self, price):
        """Calculate position size based on max position value"""
        return int(self.max_position_size / price)

    def place_buy_order(self, symbol, quantity):
        """Place a buy order"""
        try:
            market_order_data = MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )

            order = self.trading_client.submit_order(
                order_data=market_order_data)
            logger.info(f"BUY order placed for {symbol}: {quantity} shares")
            return order

        except Exception as e:
            logger.error(f"Error placing buy order for {symbol}: {e}")
            return None

    def place_sell_order(self, symbol, quantity):
        """Place a sell order"""
        try:
            market_order_data = MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )

            order = self.trading_client.submit_order(
                order_data=market_order_data)
            logger.info(f"SELL order placed for {symbol}: {quantity} shares")
            return order

        except Exception as e:
            logger.error(f"Error placing sell order for {symbol}: {e}")
            return None

    def get_current_positions(self):
        """Get current open positions"""
        try:
            positions = self.trading_client.get_all_positions()
            position_dict = {}

            for pos in positions:
                position_dict[pos.symbol] = {
                    'qty': int(pos.qty),
                    'avg_entry_price': float(pos.avg_entry_price),
                    'current_price': float(pos.current_price),
                    'unrealized_pnl': float(pos.unrealized_pnl)
                }

            return position_dict

        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {}

    def scan_and_trade(self, symbols):
        """Main trading logic - scan symbols and execute trades"""
        logger.info(f"Scanning {len(symbols)} symbols...")

        current_positions = self.get_current_positions()

        for symbol in symbols:
            try:
                signal, data = self.calculate_signal(symbol)

                if signal and data:
                    logger.info(f"{symbol}: {signal} - Price: ${data['current_price']:.2f}, "
                                f"SMA20: ${data['sma_20']:.2f}, "
                                f"Diff: {data['price_diff_pct']:.1f}%")

                    # Execute buy signal
                    if signal == 'BUY' and symbol not in current_positions:
                        quantity = self.get_position_size(
                            data['current_price'])
                        if quantity > 0:
                            order = self.place_buy_order(symbol, quantity)
                            if order:
                                logger.info(
                                    f"Bought {quantity} shares of {symbol} at ${data['current_price']:.2f}")

                    # Execute sell signal
                    elif signal == 'SELL' and symbol in current_positions:
                        quantity = current_positions[symbol]['qty']
                        order = self.place_sell_order(symbol, quantity)
                        if order:
                            logger.info(
                                f"Sold {quantity} shares of {symbol} at ${data['current_price']:.2f}")

                # Small delay between API calls
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue

    def run_strategy(self, symbols=None, run_once=False):
        """Run the trading strategy"""
        logger.info("Starting SMA Mean Reversion Bot...")

        # Get account info
        account = self.get_account_info()
        if not account:
            logger.error("Could not get account info. Exiting.")
            return

        # Get symbols if not provided
        if not symbols:
            logger.info("Getting tradeable assets...")
            symbols = self.get_tradeable_assets()

        if not symbols:
            logger.error("No symbols to trade. Exiting.")
            return

        logger.info(f"Trading symbols: {symbols[:10]}...")  # Show first 10

        if run_once:
            self.scan_and_trade(symbols)
        else:
            # Continuous running during market hours
            while True:
                try:
                    current_time = datetime.now()
                    # Check if market is open (basic check - you might want to add holidays)
                    if current_time.weekday() < 5 and 9 <= current_time.hour < 16.5:
                        self.scan_and_trade(symbols)
                    else:
                        logger.info("Market is closed. Waiting...")

                    # Wait 1 minute before next scan
                    time.sleep(60)

                except KeyboardInterrupt:
                    logger.info("Stopping bot...")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    time.sleep(30)  # Wait 30 seconds before retrying


# Example usage
if __name__ == "__main__":
    # Set your Alpaca credentials
    API_KEY = os.getenv('ALPACA_API_KEY')  # Set these as environment variables
    SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')

    if not API_KEY or not SECRET_KEY:
        print("Please set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables")
        exit(1)

    # Initialize bot (paper trading by default)
    bot = SMAmeanReversionBot(API_KEY, SECRET_KEY, paper=True)

    # Example symbols to trade (you can customize this list)
    test_symbols = ['AAPL', 'MSFT', 'TSLA', 'AMD', 'NVDA', 'SPY', 'QQQ']

    # Run the strategy once for testing
    # bot.run_strategy(symbols=test_symbols, run_once=True)

    # Uncomment to run continuously
    bot.run_strategy(symbols=test_symbols, run_once=False)
