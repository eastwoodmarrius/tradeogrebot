#!/usr/bin/env python3
import requests
import time
import logging
from requests.auth import HTTPBasicAuth

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TradeOgreAPI:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://tradeogre.com/api/v1"
        self.auth = HTTPBasicAuth(api_key, api_secret)
    
    def sell_order(self, market, quantity, price):
        """Place a sell order using correct TradeOgre API endpoint"""
        url = f"{self.base_url}/order/sell"
        data = {
            'market': market,
            'quantity': str(quantity),
            'price': str(price)
        }
        try:
            response = requests.post(url, data=data, auth=self.auth, timeout=10)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_ticker(self, market):
        """Get ticker data"""
        url = f"{self.base_url}/ticker/{market}"
        try:
            response = requests.get(url, timeout=10)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}

def main():
    # Load API credentials
    with open('/home/daimondsteel259/.config/tradeogre/api.key', 'r') as f:
        lines = f.read().strip().split('\n')
        api_key = lines[0].strip()
        api_secret = lines[1].strip()
    
    api = TradeOgreAPI(api_key, api_secret)
    
    logger.info("🚀 Starting AEGS Grid Bot - LIVE TRADING")
    
    # Get market data
    ticker = api.get_ticker('AEGS-USDT')
    if not ticker.get('success', True):
        logger.error(f"Failed to get ticker: {ticker.get('error', 'Unknown error')}")
        return
    
    ask_price = float(ticker['ask'])
    current_price = float(ticker['price'])
    
    logger.info(f"📊 AEGS Price: ${current_price:.8f}, Ask: ${ask_price:.8f}")
    
    # Place 3 sell orders
    orders = [
        {'quantity': 3000, 'price': ask_price + 0.00001},
        {'quantity': 3000, 'price': ask_price + 0.0005},
        {'quantity': 3000, 'price': ask_price + 0.001}
    ]
    
    for i, order in enumerate(orders, 1):
        logger.info(f"🔄 Placing order {i}: {order['quantity']} AEGS @ ${order['price']:.8f}")
        
        result = api.sell_order('AEGS-USDT', order['quantity'], order['price'])
        
        if result.get('success'):
            uuid = result.get('uuid', 'N/A')
            logger.info(f"✅ Order {i} placed successfully! UUID: {uuid}")
        else:
            error = result.get('error', 'Unknown error')
            logger.error(f"❌ Order {i} failed: {error}")
        
        time.sleep(1)  # Rate limiting
    
    logger.info("🎉 Grid placement completed!")

if __name__ == "__main__":
    main()
