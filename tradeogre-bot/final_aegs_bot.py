#!/usr/bin/env python3
"""
Final Working AEGS Grid Bot
"""
import time
import logging
from secure_tradeogre import SecureTradeOgre
from funcs import generate_grid

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
MARKET = "AEGS-USDT"
TOTAL_AEGS = 9000.0  # Use 9000 AEGS (90% of your balance)
GRID_LEVELS = 3      # 3 levels = 3000 AEGS each = $1.80 per order
DRY_RUN = False      # Set to True for testing

def main():
    # Initialize API
    api = SecureTradeOgre()
    api.load_key('/home/daimondsteel259/.config/tradeogre/api.key')
    
    logger.info(f"🚀 Starting AEGS Grid Bot - {'DRY RUN' if DRY_RUN else 'LIVE TRADING'}")
    
    # Get market data
    ticker = api.ticker(MARKET)
    if not ticker.success:
        logger.error(f"Failed to get ticker: {ticker.error}")
        return
    
    ask_price = float(ticker.data['ask'])
    current_price = float(ticker.data['price'])
    
    logger.info(f"📊 AEGS Price: ${current_price:.8f}, Ask: ${ask_price:.8f}")
    
    # Generate grid
    lower_bound = ask_price + 0.00001
    upper_bound = 0.003
    grid_levels = generate_grid(lower_bound, upper_bound, GRID_LEVELS)
    
    if not grid_levels:
        logger.error("Failed to generate grid")
        return
    
    aegs_per_order = TOTAL_AEGS / GRID_LEVELS
    
    logger.info(f"📈 Placing {GRID_LEVELS} sell orders, {aegs_per_order:,.0f} AEGS each")
    
    # Place orders
    for i, price in enumerate(grid_levels):
        order_value = aegs_per_order * price
        
        if DRY_RUN:
            logger.info(f"[DRY RUN] Order {i+1}: Sell {aegs_per_order:,.0f} AEGS @ ${price:.8f} (${order_value:.2f})")
        else:
            logger.info(f"🔄 Placing order {i+1}: {aegs_per_order:,.0f} AEGS @ ${price:.8f}")
            
            # Place real sell order
            response = api.sell(MARKET, aegs_per_order, price)
            
            if response.success:
                logger.info(f"✅ Order placed! UUID: {response.data.get('uuid', 'N/A')}")
            else:
                logger.error(f"❌ Order failed: {response.error}")
        
        time.sleep(1)  # Rate limiting
    
    logger.info("🎉 Grid placement completed!")

if __name__ == "__main__":
    main()
