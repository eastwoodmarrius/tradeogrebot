#!/usr/bin/env python3
"""
Configuration for the AEGS Market Maker Bot
"""

# Market configuration
MARKET = 'AEGS-USDT'
API_KEY_FILE = '~/.config/tradeogre/api.key'

# Grid configuration
BUY_GRID_LEVELS = 3
SELL_GRID_LEVELS = 3
BUY_RANGE = 0.05  # 5% below current bid
SELL_RANGE = 0.05  # 5% above current ask

# Order size configuration
MAX_BASE_PER_ORDER = 100  # Maximum AEGS per order
MAX_QUOTE_PER_ORDER = 0.1  # Maximum USDT per order
MAX_BASE_TOTAL = 300      # Maximum total AEGS to use
MAX_QUOTE_TOTAL = 0.3     # Maximum total USDT to use
MIN_ORDER_VALUE = 0.0001  # Minimum order value in USDT

# API configuration
API_RATE_LIMIT = 1.0  # Seconds between API calls

# Timing configuration
REFRESH_INTERVAL = 3600  # Seconds between refreshing orders
ORDER_DELAY = 1.0        # Seconds between placing orders
ERROR_DELAY = 60         # Seconds to wait after an error

def get_config():
    """Return configuration as a dictionary"""
    return {
        'market': MARKET,
        'api_key_file': API_KEY_FILE,
        'buy_grid_levels': BUY_GRID_LEVELS,
        'sell_grid_levels': SELL_GRID_LEVELS,
        'buy_range': BUY_RANGE,
        'sell_range': SELL_RANGE,
        'max_base_per_order': MAX_BASE_PER_ORDER,
        'max_quote_per_order': MAX_QUOTE_PER_ORDER,
        'max_base_total': MAX_BASE_TOTAL,
        'max_quote_total': MAX_QUOTE_TOTAL,
        'min_order_value': MIN_ORDER_VALUE,
        'api_rate_limit': API_RATE_LIMIT,
        'refresh_interval': REFRESH_INTERVAL,
        'order_delay': ORDER_DELAY,
        'error_delay': ERROR_DELAY
    }