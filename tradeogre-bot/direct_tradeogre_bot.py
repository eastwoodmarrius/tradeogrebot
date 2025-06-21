#!/usr/bin/env python3
import requests
import base64
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DirectTradeOgre:
    def __init__(self, api_key, secret):
        self.api_key = api_key
        self.secret = secret
        self.base_url = "https://tradeogre.com/api/v1"
        
        # Create auth header
        credentials = f"{api_key}:{secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    
    def sell_order(self, market, quantity, price):
        """Place sell order using exact TradeOgre API format"""
        url = f"{self.base_url}/order/sell"
        data = {
            'market': market,
            'quantity': str(quantity),
            'price': str(price)
        }
        
        try:
            response = requests.post(url, data=data, headers=self.headers)
            result = response.json()
            logger.info(f"API Response: {result}")
            return result
        except Exception as e:
            logger.error(f"API Error: {e}")
            return {"success": False, "error": str(e)}

# Load API keys
with open('/home/daimondsteel259/.config/tradeogre/api.key', 'r') as f:
    lines = f.read().strip().split('\n')
    api_key = lines[0]
    secret = lines[1]

# Initialize API
api = DirectTradeOgre(api_key, secret)

# Test sell order
logger.info("🚀 Testing direct TradeOgre API sell order")
result = api.sell_order("AEGS-USDT", "1000", "0.001")

if result.get("success"):
    logger.info("✅ SUCCESS! Order placed")
    logger.info(f"UUID: {result.get('uuid')}")
else:
    logger.error(f"❌ FAILED: {result.get('error')}")
