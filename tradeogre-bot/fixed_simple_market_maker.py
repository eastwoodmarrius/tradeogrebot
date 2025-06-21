#!/usr/bin/env python3
"""
Simple TradeOgre Market Maker Bot

This bot creates and maintains a grid of buy and sell orders on TradeOgre
following the official API documentation with proper minimum order values.
"""
import os
import time
import json
import logging
import requests
from funcs import generate_grid

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    'market': 'AEGS-USDT',
    'api_key_file': '~/.config/tradeogre/api.key',
    'buy_grid_levels': 3,
    'sell_grid_levels': 3,
    'buy_range': 0.05,  # 5% below current bid
    'sell_range': 0.05,  # 5% above current ask
    'min_order_value_usd': 1.0,     # Minimum $1 USD per order
    'max_quote_per_order': 2.0,     # Maximum USDT per order (increased)
    'max_base_total': 10000,        # Maximum total AEGS to use
    'max_quote_total': 6.0,         # Maximum total USDT to use (increased)
    'api_rate_limit': 1.0,          # Seconds between API calls
    'refresh_interval': 3600,       # Seconds between refreshing orders
    'order_delay': 1.0,             # Seconds between placing orders
    'error_delay': 60               # Seconds to wait after an error
}

class TradeOgreAPI:
    """TradeOgre API wrapper following official documentation"""
    
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
    
    def get_orders(self, market=None):
        """Get open orders for a market"""
        if market:
            data = {"market": market}
        else:
            data = {}
        return self._request("POST", "account/orders", auth=True, data=data)
    
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
    
    def cancel_all_orders(self):
        """Cancel all orders"""
        data = {
            "uuid": "all"
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
            
            # Get available balances
            available = result.get('available', {})
            
            if self.base_currency in available:
                balances['base'] = float(available[self.base_currency])
            
            if self.quote_currency in available:
                balances['quote'] = float(available[self.quote_currency])
            
            return balances
        else:
            logger.error(f"Failed to get balances: {result.get('error')}")
            return None
    
    def get_own_orders(self):
        """Get all open orders for the current market"""
        result = self.api.get_orders(self.market)
        orders = []
        
        if result['success']:
            # Check if there are any orders
            if isinstance(result, list) and len(result) > 0:
                for order in result:
                    if order.get('market') == self.market:
                        orders.append({
                            'uuid': order['uuid'],
                            'type': order['type'],
                            'price': float(order['price']),
                            'quantity': float(order['quantity'])
                        })
            else:
                logger.info("No open orders found")
        else:
            logger.error(f"Failed to get orders: {result.get('error')}")
        
        return orders
    
    def cancel_all_orders(self):
        """Cancel all open orders"""
        result = self.api.cancel_all_orders()
        
        if result['success']:
            logger.info("All orders cancelled successfully")
            return True
        else:
            logger.error(f"Failed to cancel orders: {result.get('error')}")
            return False
    
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
            # Calculate quantity based on price and ensure minimum order value
            quantity = max(
                quote_per_order / price,
                self.config['min_order_value_usd'] / price  # Ensure $1 minimum
            )
            quantity = round(quantity, 8)
            
            order_value = quantity * price
            
            # Only create order if we have enough balance and it meets minimum value
            if order_value >= self.config['min_order_value_usd'] and order_value <= available_quote:
                buy_orders.append({
                    'price': price,
                    'quantity': quantity,
                    'value': order_value
                })
                logger.info(f"Buy order planned: {quantity} AEGS @ ${price:.8f} = ${order_value:.4f}")
        
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
        
        # Create sell orders
        sell_orders = []
        for price in sell_prices:
            # Calculate quantity to ensure minimum $1 order value
            min_quantity = self.config['min_order_value_usd'] / price
            
            # Use a reasonable quantity that meets the minimum value requirement
            quantity = max(min_quantity, min_quantity * 1.5)  # Use 1.5x minimum for safety
            quantity = round(quantity, 8)
            
            order_value = quantity * price
            
            # Only create order if we have enough balance
            if quantity <= available_base and order_value >= self.config['min_order_value_usd']:
                sell_orders.append({
                    'price': price,
                    'quantity': quantity,
                    'value': order_value
                })
                logger.info(f"Sell order planned: {quantity} AEGS @ ${price:.8f} = ${order_value:.4f}")
        
        return sell_orders
    
    def place_orders(self, buy_orders, sell_orders):
        """Place all orders"""
        # Place buy orders
        for order in buy_orders:
            logger.info(f"Placing buy order: {order['quantity']} AEGS @ ${order['price']:.8f} (${order['value']:.4f})")
            result = self.api.place_buy_order(
                self.market,
                f"{order['price']:.8f}",
                f"{order['quantity']:.8f}"
            )
            
            if not result['success']:
                logger.error(f"Failed to place buy order: {result.get('error')}")
            else:
                logger.info(f"Buy order placed successfully: {result.get('uuid', 'No UUID')}")
            
            # Add delay between orders
            time.sleep(self.config['order_delay'])
        
        # Place sell orders
        for order in sell_orders:
            logger.info(f"Placing sell order: {order['quantity']} AEGS @ ${order['price']:.8f} (${order['value']:.4f})")
            result = self.api.place_sell_order(
                self.market,
                f"{order['price']:.8f}",
                f"{order['quantity']:.8f}"
            )
            
            if not result['success']:
                logger.error(f"Failed to place sell order: {result.get('error')}")
            else:
                logger.info(f"Sell order placed successfully: {result.get('uuid', 'No UUID')}")
            
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
            
            logger.info(f"Market info: Bid=${market_info['bid']:.8f}, Ask=${market_info['ask']:.8f}, Last=${market_info['price']:.8f}")
            
            # Get account balances
            balances = self.get_balances()
            if not balances:
                return False
            
            logger.info(f"Balances: {balances['base']} {self.base_currency}, {balances['quote']} {self.quote_currency}")
            
            # Check if we have sufficient balances
            if balances['quote'] < self.config['min_order_value_usd']:
                logger.warning(f"Insufficient {self.quote_currency} balance for buy orders (need at least ${self.config['min_order_value_usd']})")
            
            min_base_needed = self.config['min_order_value_usd'] / market_info['ask']
            if balances['base'] < min_base_needed:
                logger.warning(f"Insufficient {self.base_currency} balance for sell orders (need at least {min_base_needed:.2f})")
            
            # Create buy and sell orders
            buy_orders = self.create_buy_orders(market_info, balances)
            sell_orders = self.create_sell_orders(market_info, balances)
            
            if not buy_orders and not sell_orders:
                logger.warning("No orders to place - insufficient balances or prices don't meet minimum requirements")
                return False
            
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
    # Load API key
    api_key, api_secret = load_api_key(CONFIG['api_key_file'])
    if not api_key or not api_secret:
        logger.error("Failed to load API key, exiting")
        return
    
    logger.info("API credentials loaded successfully")
    
    # Initialize API
    api = TradeOgreAPI(api_key, api_secret, rate_limit=CONFIG['api_rate_limit'])
    
    # Initialize market maker
    market_maker = MarketMaker(api, CONFIG['market'], CONFIG)
    
    logger.info(f"Starting market maker for {CONFIG['market']}")
    logger.info(f"Minimum order value: ${CONFIG['min_order_value_usd']}")
    
    # Run market maker loop
    while True:
        try:
            success = market_maker.run()
            
            if not success:
                logger.warning("Market maker iteration failed, retrying...")
            
            # Wait for next iteration
            logger.info(f"Waiting {CONFIG['refresh_interval']} seconds until next refresh...")
            time.sleep(CONFIG['refresh_interval'])
        
        except KeyboardInterrupt:
            logger.info("Market maker stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            time.sleep(CONFIG['error_delay'])

if __name__ == "__main__":
    main()