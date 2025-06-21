#!/usr/bin/env python3
"""
TradeOgre Market Maker Bot

This bot creates and maintains a grid of buy and sell orders on TradeOgre
to provide liquidity and potentially profit from the spread.
"""
import os
import time
import json
import logging
import datetime
import requests
from funcs import generate_grid
from market_maker_config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradeOgreAPI:
    """TradeOgre API wrapper"""
    
    def __init__(self, key=None, secret=None, rate_limit=1.0):
        """Initialize the API with optional credentials"""
        self.key = key
        self.secret = secret
        self.rate_limit = rate_limit  # Minimum seconds between API calls
        self.last_request_time = 0
        self.base_url = "https://tradeogre.com/api/v1"
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _request(self, method, endpoint, auth=False, params=None, data=None):
        """Make a request to the TradeOgre API"""
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        auth_tuple = None
        
        if auth:
            if not self.key or not self.secret:
                return {"success": False, "error": "API credentials not set"}
            auth_tuple = (self.key, self.secret)
        
        try:
            if method == "GET":
                response = requests.get(url, params=params, auth=auth_tuple, headers=headers)
            elif method == "POST":
                response = requests.post(url, params=params, data=data, auth=auth_tuple, headers=headers)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_ticker(self, market):
        """Get ticker information for a market"""
        return self._request("GET", f"ticker/{market}")
    
    def get_order_book(self, market):
        """Get order book for a market"""
        return self._request("GET", f"orders/{market}")
    
    def get_balances(self):
        """Get account balances"""
        return self._request("GET", "account/balances", auth=True)
    
    def get_balance(self, currency):
        """Get balance for a specific currency"""
        return self._request("GET", f"account/balance/{currency}", auth=True)
    
    def get_orders(self, market):
        """Get open orders for a market"""
        return self._request("GET", f"account/orders/{market}", auth=True)
    
    def place_buy_order(self, market, price, quantity):
        """Place a buy order"""
        data = {
            "market": market,
            "price": price,
            "quantity": quantity
        }
        return self._request("POST", "order/buy", auth=True, data=data)
    
    def place_sell_order(self, market, price, quantity):
        """Place a sell order"""
        data = {
            "market": market,
            "price": price,
            "quantity": quantity
        }
        return self._request("POST", "order/sell", auth=True, data=data)
    
    def cancel_order(self, order_id):
        """Cancel an order"""
        data = {
            "uuid": order_id
        }
        return self._request("POST", "order/cancel", auth=True, data=data)

class MarketMaker:
    """Market maker for TradeOgre"""
    
    def __init__(self, api, market, config):
        """Initialize the market maker"""
        self.api = api
        self.market = market
        self.config = config
        self.base_currency, self.quote_currency = market.split('-')
    
    def get_market_info(self):
        """Get current market information"""
        result = self.api.get_ticker(self.market)
        
        if result['success']:
            return {
                'bid': float(result['bid']),
                'ask': float(result['ask']),
                'price': float(result['price'])
            }
        else:
            logger.error(f"Failed to get market info: {result.get('error')}")
            return None
    
    def get_balances(self):
        """Get account balances for the trading pair"""
        result = self.api.get_balances()
        
        if result['success']:
            balances = {
                'base': 0.0,
                'quote': 0.0
            }
            
            for currency, balance in result.items():
                if currency.upper() == self.base_currency:
                    balances['base'] = float(balance['available'])
                elif currency.upper() == self.quote_currency:
                    balances['quote'] = float(balance['available'])
            
            return balances
        else:
            logger.error(f"Failed to get balances: {result.get('error')}")
            return None
    
    def get_own_orders(self):
        """Get all open orders for the current market"""
        result = self.api.get_orders(self.market)
        orders = []
        
        if result['success']:
            # Check if data is a dictionary (has orders) or an integer (0, no orders)
            if isinstance(result, dict) and not isinstance(result, int):
                for uuid, order in result.items():
                    if uuid != 'success':  # Skip the success flag
                        orders.append({
                            'uuid': uuid,
                            'type': order['type'],
                            'price': float(order['price']),
                            'quantity': float(order['quantity'])
                        })
            else:
                # No orders, API returns 0
                logger.info("No open orders found")
        else:
            logger.error(f"Failed to get orders: {result.get('error')}")
        
        return orders
    
    def cancel_all_orders(self):
        """Cancel all open orders for the current market"""
        orders = self.get_own_orders()
        
        if not orders:
            logger.info("No orders to cancel")
            return True
        
        success = True
        for order in orders:
            logger.info(f"Cancelling {order['type']} order: {order['quantity']} @ {order['price']}")
            result = self.api.cancel_order(order['uuid'])
            if not result['success']:
                logger.error(f"Failed to cancel order {order['uuid']}: {result.get('error')}")
                success = False
        
        return success
    
    def create_buy_orders(self, market_info, balances):
        """Create a grid of buy orders"""
        if not market_info or not balances:
            return []
        
        # Calculate price range for buy orders
        buy_lower = market_info['bid'] * (1 - self.config['buy_range'])
        buy_upper = market_info['bid'] * 0.99  # Just below current bid
        
        # Generate grid of prices
        buy_prices = generate_grid(buy_lower, buy_upper, self.config['buy_grid_levels'])
        
        # Calculate available quote currency for buy orders
        available_quote = min(
            balances['quote'],
            self.config['max_quote_total']
        )
        
        # Calculate amount per order
        quote_per_order = min(
            available_quote / self.config['buy_grid_levels'],
            self.config['max_quote_per_order']
        )
        
        # Create buy orders
        buy_orders = []
        for price in buy_prices:
            # Calculate quantity based on price
            quantity = round(quote_per_order / price, 8)
            
            if quantity * price >= self.config['min_order_value']:
                buy_orders.append({
                    'price': price,
                    'quantity': quantity
                })
        
        return buy_orders
    
    def create_sell_orders(self, market_info, balances):
        """Create a grid of sell orders"""
        if not market_info or not balances:
            return []
        
        # Calculate price range for sell orders
        sell_lower = market_info['ask'] * 1.01  # Just above current ask
        sell_upper = market_info['ask'] * (1 + self.config['sell_range'])
        
        # Generate grid of prices
        sell_prices = generate_grid(sell_lower, sell_upper, self.config['sell_grid_levels'])
        
        # Calculate available base currency for sell orders
        available_base = min(
            balances['base'],
            self.config['max_base_total']
        )
        
        # Calculate amount per order
        base_per_order = min(
            available_base / self.config['sell_grid_levels'],
            self.config['max_base_per_order']
        )
        
        # Create sell orders
        sell_orders = []
        for price in sell_prices:
            # Use fixed quantity for sell orders
            quantity = round(base_per_order, 8)
            
            if quantity * price >= self.config['min_order_value']:
                sell_orders.append({
                    'price': price,
                    'quantity': quantity
                })
        
        return sell_orders
    
    def place_orders(self, buy_orders, sell_orders):
        """Place all orders"""
        # Place buy orders
        for order in buy_orders:
            logger.info(f"Placing buy order: {order['quantity']} @ {order['price']}")
            result = self.api.place_buy_order(
                self.market,
                f"{order['price']:.8f}",
                f"{order['quantity']:.8f}"
            )
            
            if not result['success']:
                logger.error(f"Failed to place buy order: {result.get('error')}")
            
            # Add delay between orders
            time.sleep(self.config['order_delay'])
        
        # Place sell orders
        for order in sell_orders:
            logger.info(f"Placing sell order: {order['quantity']} @ {order['price']}")
            result = self.api.place_sell_order(
                self.market,
                f"{order['price']:.8f}",
                f"{order['quantity']:.8f}"
            )
            
            if not result['success']:
                logger.error(f"Failed to place sell order: {result.get('error')}")
            
            # Add delay between orders
            time.sleep(self.config['order_delay'])
    
    def run(self):
        """Run one iteration of the market maker"""
        try:
            # Cancel existing orders
            self.cancel_all_orders()
            
            # Get market information
            market_info = self.get_market_info()
            if not market_info:
                return False
            
            logger.info(f"Market info: Bid={market_info['bid']}, Ask={market_info['ask']}, Last={market_info['price']}")
            
            # Get account balances
            balances = self.get_balances()
            if not balances:
                return False
            
            logger.info(f"Balances: {balances['base']} {self.base_currency}, {balances['quote']} {self.quote_currency}")
            
            # Create buy and sell orders
            buy_orders = self.create_buy_orders(market_info, balances)
            sell_orders = self.create_sell_orders(market_info, balances)
            
            # Place orders
            self.place_orders(buy_orders, sell_orders)
            
            return True
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

def load_api_key(key_file):
    """Load API key from file"""
    try:
        # Expand the tilde to the home directory
        expanded_path = os.path.expanduser(key_file)
        with open(expanded_path, 'r') as f:
            lines = f.read().strip().split('\n')
            if len(lines) >= 2:
                return lines[0], lines[1]
            else:
                logger.error(f"Invalid API key file format: {key_file}")
                return None, None
    except Exception as e:
        logger.error(f"Failed to load API key: {e}")
        return None, None

def main():
    """Main function"""
    # Load configuration
    config = get_config()
    
    # Load API key
    api_key, api_secret = load_api_key(config['api_key_file'])
    if not api_key or not api_secret:
        logger.error("Failed to load API key, exiting")
        return
    
    logger.info("API credentials loaded successfully")
    
    # Initialize API
    api = TradeOgreAPI(api_key, api_secret, rate_limit=config['api_rate_limit'])
    
    # Initialize market maker
    market_maker = MarketMaker(api, config['market'], config)
    
    logger.info(f"Starting market maker for {config['market']}")
    
    # Run market maker loop
    while True:
        try:
            success = market_maker.run()
            
            if not success:
                logger.warning("Market maker iteration failed, retrying...")
            
            # Wait for next iteration
            logger.info(f"Waiting {config['refresh_interval']} seconds until next refresh...")
            time.sleep(config['refresh_interval'])
        
        except KeyboardInterrupt:
            logger.info("Market maker stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            time.sleep(config['error_delay'])

if __name__ == "__main__":
    main()