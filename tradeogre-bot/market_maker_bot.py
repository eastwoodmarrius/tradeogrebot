#!/usr/bin/env python3
"""
AEGS Market Maker Bot - Provides liquidity on both sides of the market
"""
import time
import logging
import os
import json
from datetime import datetime
import requests
from funcs import generate_grid
from market_maker_config import get_config

# Setup logging will be configured in main() after loading config

logger = logging.getLogger(__name__)

class TradeOgreAPI:
    """TradeOgre API wrapper with enhanced error handling"""
    
    def __init__(self, rate_limit=1.0):
        self.base_url = "https://tradeogre.com/api/v1"
        self.api_key = None
        self.api_secret = None
        self.last_request_time = 0
        self.min_request_interval = rate_limit  # seconds between API calls
    
    def load_key(self, key_file):
        """Load API key from file"""
        try:
            with open(key_file, 'r') as f:
                lines = f.read().strip().split('\n')
                self.api_key = lines[0].strip()
                self.api_secret = lines[1].strip()
            logger.info("API credentials loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load API key: {str(e)}")
            return False
    
    def _rate_limit(self):
        """Ensure we don't exceed API rate limits"""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _request(self, method, endpoint, data=None, auth=True):
        """Make API request with rate limiting and error handling"""
        self._rate_limit()
        url = f"{self.base_url}/{endpoint}"
        
        headers = {}
        auth_tuple = (self.api_key, self.api_secret) if auth else None
        
        try:
            if method.lower() == 'get':
                response = requests.get(url, params=data, auth=auth_tuple, timeout=10)
            elif method.lower() == 'post':
                response = requests.post(url, data=data, auth=auth_tuple, timeout=10)
            else:
                return {'success': False, 'error': f"Unsupported method: {method}"}
            
            # Check if response is valid JSON
            try:
                result = response.json()
            except json.JSONDecodeError:
                return {'success': False, 'error': f"Invalid JSON response: {response.text}"}
            
            # Check for API error responses
            if isinstance(result, dict) and 'error' in result:
                return {'success': False, 'error': result['error']}
            
            return {'success': True, 'data': result}
        
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f"Request failed: {str(e)}"}
        except Exception as e:
            return {'success': False, 'error': f"Unexpected error: {str(e)}"}
    
    def get_ticker(self, market):
        """Get market ticker data"""
        return self._request('get', f"ticker/{market}", auth=False)
    
    def get_balances(self):
        """Get account balances"""
        return self._request('get', "account/balances")
    
    def get_order_book(self, market):
        """Get market order book"""
        return self._request('get', f"orders/{market}", auth=False)
    
    def get_orders(self):
        """Get all active orders for the account"""
        return self._request('get', "account/orders")
    
    def buy(self, market, quantity, price):
        """Place buy order"""
        data = {
            'market': market,
            'quantity': str(quantity),
            'price': str(price)
        }
        return self._request('post', "order/buy", data=data)
    
    def sell(self, market, quantity, price):
        """Place sell order"""
        data = {
            'market': market,
            'quantity': str(quantity),
            'price': str(price)
        }
        return self._request('post', "order/sell", data=data)
    
    def cancel_order(self, order_id):
        """Cancel an order by UUID"""
        data = {'uuid': order_id}
        return self._request('post', "order/cancel", data=data)


class MarketMaker:
    """Market maker that provides liquidity on both sides of the market"""
    
    def __init__(self, api, market, config):
        self.api = api
        self.market = market
        self.config = config
        self.base_currency = market.split('-')[0]  # e.g., AEGS
        self.quote_currency = market.split('-')[1]  # e.g., USDT
        self.own_orders = {}  # Track our own orders
    
    def get_market_info(self):
        """Get current market information"""
        ticker_result = self.api.get_ticker(self.market)
        if not ticker_result['success']:
            logger.error(f"Failed to get ticker: {ticker_result.get('error')}")
            return None
        
        ticker = ticker_result['data']
        return {
            'bid': float(ticker['bid']),
            'ask': float(ticker['ask']),
            'price': float(ticker['price']),
            'high': float(ticker['high']),
            'low': float(ticker['low']),
            'volume': float(ticker['volume'])
        }
    
    def get_balances(self):
        """Get account balances"""
        result = self.api.get_balances()
        if not result['success']:
            logger.error(f"Failed to get balances: {result.get('error')}")
            return None
        
        balances = result['data']
        return {
            'base': float(balances.get(self.base_currency, {}).get('available', 0)),
            'quote': float(balances.get(self.quote_currency, {}).get('available', 0))
        }
    
    def get_order_book(self):
        """Get market order book"""
        result = self.api.get_order_book(self.market)
        if not result['success']:
            logger.error(f"Failed to get order book: {result.get('error')}")
            return None
        
        return result['data']
    
    def get_own_orders(self):
        """Get our own active orders"""
        result = self.api.get_orders()
        if not result['success']:
            logger.error(f"Failed to get orders: {result.get('error')}")
            return None
        
        # Filter orders for our market
        market_orders = {}
        for uuid, order in result['data'].items():
            if order['market'] == self.market:
                market_orders[uuid] = order
        
        return market_orders
    
    def cancel_all_orders(self):
        """Cancel all active orders for our market"""
        orders = self.get_own_orders()
        if not orders:
            return
        
        logger.info(f"Cancelling {len(orders)} active orders")
        for uuid in orders:
            result = self.api.cancel_order(uuid)
            if result['success']:
                logger.info(f"Cancelled order {uuid}")
            else:
                logger.error(f"Failed to cancel order {uuid}: {result.get('error')}")
            time.sleep(0.5)  # Rate limiting
    
    def create_buy_orders(self, market_info, balances):
        """Create buy orders below current bid price"""
        if not market_info or not balances:
            return []
        
        bid_price = market_info['bid']
        available_quote = balances['quote']
        
        # Calculate buy grid
        buy_levels = generate_grid(
            bid_price * (1 - self.config['buy_range']),
            bid_price * 0.99,  # Just below current bid
            self.config['buy_grid_levels']
        )
        
        if not buy_levels:
            logger.error("Failed to generate buy grid")
            return []
        
        # Calculate quantity per order
        quote_per_order = min(
            available_quote / self.config['buy_grid_levels'],
            self.config['max_quote_per_order']
        )
        
        orders_placed = []
        for price in buy_levels:
            # Calculate quantity in base currency
            quantity = round(quote_per_order / price, 8)
            
            if quantity * price < self.config['min_order_value']:
                logger.warning(f"Order value too small: {quantity * price} {self.quote_currency}")
                continue
            
            logger.info(f"Placing buy order: {quantity} {self.base_currency} @ {price} {self.quote_currency}")
            result = self.api.buy(self.market, quantity, price)
            
            if result['success']:
                uuid = result['data'].get('uuid')
                logger.info(f"Buy order placed: {uuid}")
                orders_placed.append(uuid)
            else:
                logger.error(f"Failed to place buy order: {result.get('error')}")
            
            time.sleep(1)  # Rate limiting
        
        return orders_placed
    
    def create_sell_orders(self, market_info, balances):
        """Create sell orders above current ask price"""
        if not market_info or not balances:
            return []
        
        ask_price = market_info['ask']
        available_base = balances['base']
        
        # Calculate sell grid
        sell_levels = generate_grid(
            ask_price * 1.01,  # Just above current ask
            ask_price * (1 + self.config['sell_range']),
            self.config['sell_grid_levels']
        )
        
        if not sell_levels:
            logger.error("Failed to generate sell grid")
            return []
        
        # Calculate quantity per order
        base_per_order = min(
            available_base / self.config['sell_grid_levels'],
            self.config['max_base_per_order']
        )
        
        orders_placed = []
        for price in sell_levels:
            if base_per_order * price < self.config['min_order_value']:
                logger.warning(f"Order value too small: {base_per_order * price} {self.quote_currency}")
                continue
            
            logger.info(f"Placing sell order: {base_per_order} {self.base_currency} @ {price} {self.quote_currency}")
            result = self.api.sell(self.market, base_per_order, price)
            
            if result['success']:
                uuid = result['data'].get('uuid')
                logger.info(f"Sell order placed: {uuid}")
                orders_placed.append(uuid)
            else:
                logger.error(f"Failed to place sell order: {result.get('error')}")
            
            time.sleep(1)  # Rate limiting
        
        return orders_placed
    
    def run(self):
        """Run the market maker"""
        logger.info(f"Starting market maker for {self.market}")
        
        # Get market info
        market_info = self.get_market_info()
        if not market_info:
            logger.error("Failed to get market info, exiting")
            return False
        
        logger.info(f"Market info: Bid={market_info['bid']}, Ask={market_info['ask']}, Last={market_info['price']}")
        
        # Get balances
        balances = self.get_balances()
        if not balances:
            logger.error("Failed to get balances, exiting")
            return False
        
        logger.info(f"Balances: {balances['base']} {self.base_currency}, {balances['quote']} {self.quote_currency}")
        
        # Cancel existing orders
        self.cancel_all_orders()
        
        # Create buy orders
        buy_orders = self.create_buy_orders(market_info, balances)
        logger.info(f"Placed {len(buy_orders)} buy orders")
        
        # Create sell orders
        sell_orders = self.create_sell_orders(market_info, balances)
        logger.info(f"Placed {len(sell_orders)} sell orders")
        
        logger.info("Market maker setup complete")
        return True


def main():
    # Load configuration
    config = get_config()
    
    # Setup logging
    log_level = getattr(logging, config['log_level'])
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(config['log_file'])
        ]
    )
    global logger
    logger = logging.getLogger(__name__)
    
    # Initialize API
    api = TradeOgreAPI(rate_limit=config['api_rate_limit'])
    if not api.load_key(config['api_key_file']):
        logger.error("Failed to load API key, exiting")
        return
    
    # Initialize market maker
    market_maker = MarketMaker(api, config['market'], config)
    
    # Run market maker
    try:
        while True:
            start_time = time.time()
            
            success = market_maker.run()
            if not success:
                logger.error("Market maker failed, retrying in 60 seconds")
                time.sleep(60)
                continue
            
            # Wait for refresh interval
            elapsed = time.time() - start_time
            sleep_time = max(0, config['refresh_interval'] - elapsed)
            
            logger.info(f"Sleeping for {sleep_time:.0f} seconds until next refresh")
            time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        logger.info("Market maker stopped by user")
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
    finally:
        # Clean up on exit
        try:
            market_maker.cancel_all_orders()
            logger.info("All orders cancelled")
        except:
            pass


if __name__ == "__main__":
    main()