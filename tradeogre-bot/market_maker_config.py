#!/usr/bin/env python3
"""
Configuration for the AEGS Market Maker Bot
"""

# Market configuration
MARKET = 'AEGS-USDT'
API_KEY_FILE = 'test_api.key'  # For testing, use local file

# Grid configuration
BUY_GRID_LEVELS = 3
SELL_GRID_LEVELS = 3
BUY_RANGE = 0.05   # 5% range below current bid
SELL_RANGE = 0.10  # 10% range above current ask

# Order size limits
MAX_BASE_PER_ORDER = 3000.0  # Max AEGS per order
MAX_QUOTE_PER_ORDER = 3.0    # Max USDT per order
MIN_ORDER_VALUE = 0.5        # Minimum order value in USDT

# Timing
REFRESH_INTERVAL = 3600  # Refresh orders every hour (in seconds)
API_RATE_LIMIT = 1.0     # Minimum seconds between API calls

# Logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'market_maker.log'

# Load configuration
def get_config():
    return {
        'market': MARKET,
        'api_key_file': API_KEY_FILE,
        'buy_grid_levels': BUY_GRID_LEVELS,
        'sell_grid_levels': SELL_GRID_LEVELS,
        'buy_range': BUY_RANGE,
        'sell_range': SELL_RANGE,
        'max_base_per_order': MAX_BASE_PER_ORDER,
        'max_quote_per_order': MAX_QUOTE_PER_ORDER,
        'min_order_value': MIN_ORDER_VALUE,
        'refresh_interval': REFRESH_INTERVAL,
        'api_rate_limit': API_RATE_LIMIT,
        'log_level': LOG_LEVEL,
        'log_file': LOG_FILE
    }