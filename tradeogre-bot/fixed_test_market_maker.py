#!/usr/bin/env python3
"""
Test the market maker bot in dry run mode
"""
import logging
import json
from fixed_market_maker_bot import TradeOgreAPI, MarketMaker
from fixed_market_maker_config import get_config
from funcs import generate_grid

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Load configuration
    config = get_config()
    
    # Override config for testing
    config['max_base_per_order'] = 100  # Smaller test amount
    config['max_quote_per_order'] = 0.1  # Smaller test amount
    
    # Mock market data
    market_info = {
        'bid': 0.00060001,
        'ask': 0.00081642,
        'price': 0.00060001
    }
    
    # Simulate balances
    balances = {
        'base': 1000,  # 1000 AEGS
        'quote': 10    # 10 USDT
    }
    
    logger.info(f"Testing with mock market data: Bid=${market_info['bid']}, Ask=${market_info['ask']}")
    
    # Test grid generation
    logger.info("\nTesting buy grid generation...")
    buy_lower = market_info['bid'] * (1 - config['buy_range'])
    buy_upper = market_info['bid'] * 0.99
    buy_levels = generate_grid(buy_lower, buy_upper, config['buy_grid_levels'])
    
    if buy_levels:
        logger.info(f"Generated {len(buy_levels)} buy levels:")
        for i, price in enumerate(buy_levels):
            quantity = round(config['max_quote_per_order'] / price, 8)
            logger.info(f"  Buy {i+1}: {quantity} AEGS @ ${price:.8f}")
    else:
        logger.error("Failed to generate buy grid")
    
    logger.info("\nTesting sell grid generation...")
    sell_lower = market_info['ask'] * 1.01
    sell_upper = market_info['ask'] * (1 + config['sell_range'])
    sell_levels = generate_grid(sell_lower, sell_upper, config['sell_grid_levels'])
    
    if sell_levels:
        logger.info(f"Generated {len(sell_levels)} sell levels:")
        for i, price in enumerate(sell_levels):
            quantity = min(config['max_base_per_order'], balances['base'] / config['sell_grid_levels'])
            logger.info(f"  Sell {i+1}: {quantity} AEGS @ ${price:.8f}")
    else:
        logger.error("Failed to generate sell grid")
    
    logger.info("\nTest completed successfully!")

if __name__ == "__main__":
    main()