#!/usr/bin/env python3
"""
Test the TradeOgre API
"""
import os
import json
import logging
import requests
import time

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
    market = "AEGS-USDT"
    api = TradeOgreAPI()
    
    # Test public endpoints
    logger.info("Testing public API endpoints...")
    
    # Test ticker
    logger.info(f"Fetching {market} ticker...")
    ticker = api.get_ticker(market)
    logger.info(f"Ticker: {json.dumps(ticker, indent=2)}")
    
    # Test order book
    logger.info(f"Fetching {market} order book...")
    order_book = api.get_order_book(market)
    
    if order_book['success']:
        buy_orders = order_book.get('buy', {})
        sell_orders = order_book.get('sell', {})
        logger.info(f"Order book: {len(buy_orders)} buy orders, {len(sell_orders)} sell orders")
    else:
        logger.error(f"Failed to get order book: {order_book.get('error')}")
    
    # Test authenticated endpoints
    logger.info("\nDo you want to test authenticated endpoints? (y/n)")
    choice = input().strip().lower()
    
    if choice == 'y':
        logger.info("Enter path to API key file:")
        key_file = input().strip()
        
        api_key, api_secret = load_api_key(key_file)
        if not api_key or not api_secret:
            logger.error("Failed to load API key, exiting")
            return
        
        # Create new API instance with credentials
        api = TradeOgreAPI(api_key, api_secret)
        
        # Test balances
        logger.info("Fetching account balances...")
        balances = api.get_balances()
        logger.info(f"Balances: {json.dumps(balances, indent=2)}")
        
        # Test orders
        logger.info(f"Fetching open orders for {market}...")
        orders = api.get_orders(market)
        logger.info(f"Orders: {json.dumps(orders, indent=2)}")
    
    logger.info("API test complete")

if __name__ == "__main__":
    main()