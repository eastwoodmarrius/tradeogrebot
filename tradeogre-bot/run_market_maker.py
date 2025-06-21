#!/usr/bin/env python3
"""
Wrapper script to run the market maker bot with the correct configuration
"""
import os
import sys
import logging
import time
from fixed_market_maker_bot import TradeOgreAPI, MarketMaker, load_api_key

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
    'buy_range': 0.05,
    'sell_range': 0.05,
    'max_base_per_order': 100,
    'max_quote_per_order': 0.1,
    'max_base_total': 300,
    'max_quote_total': 0.3,
    'min_order_value': 0.0001,
    'api_rate_limit': 1.0,
    'refresh_interval': 3600,
    'order_delay': 1.0,
    'error_delay': 60
}

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