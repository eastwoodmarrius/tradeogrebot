#!/usr/bin/env python3
"""
Test the TradeOgre API authenticated endpoints
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

def test_api_endpoint(key, secret, endpoint, method="GET", data=None):
    """Test a specific API endpoint"""
    url = f"https://tradeogre.com/api/v1/{endpoint}"
    auth = (key, secret)
    
    try:
        if method == "GET":
            response = requests.get(url, auth=auth)
        elif method == "POST":
            response = requests.post(url, auth=auth, data=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    """Main function"""
    # Load API key
    logger.info("Enter path to API key file:")
    key_file = input().strip()
    
    api_key, api_secret = load_api_key(key_file)
    if not api_key or not api_secret:
        logger.error("Failed to load API key, exiting")
        return
    
    logger.info("API credentials loaded successfully")
    
    # Test balances endpoint
    logger.info("\nTesting account/balances endpoint...")
    result = test_api_endpoint(api_key, api_secret, "account/balances")
    logger.info(f"Result: {json.dumps(result, indent=2)}")
    
    # Test orders endpoint
    market = "AEGS-USDT"
    logger.info(f"\nTesting account/orders/{market} endpoint...")
    result = test_api_endpoint(api_key, api_secret, f"account/orders/{market}")
    logger.info(f"Result: {json.dumps(result, indent=2)}")
    
    # Test order history endpoint
    logger.info(f"\nTesting account/order_history endpoint...")
    result = test_api_endpoint(api_key, api_secret, "account/order_history")
    logger.info(f"Result: {json.dumps(result, indent=2)}")
    
    logger.info("\nAPI test complete")

if __name__ == "__main__":
    main()