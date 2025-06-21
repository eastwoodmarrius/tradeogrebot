#!/usr/bin/env python3
"""
Test TradeOgre API connection and fetch market data
"""
import logging
import json
from market_maker_bot import TradeOgreAPI

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Initialize API
    api = TradeOgreAPI()
    
    # Test public API endpoints (no authentication required)
    logger.info("Testing public API endpoints...")
    
    # Get ticker for AEGS-USDT
    logger.info("Fetching AEGS-USDT ticker...")
    ticker_result = api.get_ticker('AEGS-USDT')
    if ticker_result['success']:
        logger.info(f"Ticker: {json.dumps(ticker_result['data'], indent=2)}")
    else:
        logger.error(f"Failed to get ticker: {ticker_result.get('error')}")
    
    # Get order book for AEGS-USDT
    logger.info("Fetching AEGS-USDT order book...")
    orderbook_result = api._request('get', 'orders/AEGS-USDT', auth=False)
    if orderbook_result['success']:
        # Just show summary to avoid too much output
        book = orderbook_result['data']
        buy_count = len(book.get('buy', {}))
        sell_count = len(book.get('sell', {}))
        logger.info(f"Order book: {buy_count} buy orders, {sell_count} sell orders")
    else:
        logger.error(f"Failed to get order book: {orderbook_result.get('error')}")
    
    # Test authenticated endpoints if API key is provided
    logger.info("\nDo you want to test authenticated endpoints? (y/n)")
    choice = input().strip().lower()
    
    if choice == 'y':
        # Load API key
        logger.info("Enter path to API key file:")
        key_file = input().strip()
        
        if api.load_key(key_file):
            # Get account balances
            logger.info("Fetching account balances...")
            balances_result = api.get_balances()
            if balances_result['success']:
                logger.info(f"Balances: {json.dumps(balances_result['data'], indent=2)}")
            else:
                logger.error(f"Failed to get balances: {balances_result.get('error')}")
            
            # Get active orders
            logger.info("Fetching active orders...")
            orders_result = api.get_orders()
            if orders_result['success']:
                orders = orders_result['data']
                logger.info(f"Active orders: {len(orders)}")
                for uuid, order in orders.items():
                    logger.info(f"  {uuid}: {order['type']} {order['quantity']} {order['market']} @ {order['price']}")
            else:
                logger.error(f"Failed to get orders: {orders_result.get('error')}")
        else:
            logger.error("Failed to load API key")
    
    logger.info("API test complete")

if __name__ == "__main__":
    main()