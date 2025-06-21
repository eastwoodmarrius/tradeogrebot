# TradeOgre Market Maker Bot

A professional market making bot for TradeOgre exchange that provides liquidity on both sides of the market.

## Features

- **Dual-sided Market Making**: Places both buy and sell orders to provide liquidity
- **Configurable Grid Spacing**: Customizable price levels for buy and sell orders
- **Rate Limiting**: Respects API rate limits to avoid being blocked
- **Error Handling**: Robust error handling and logging
- **Balance Management**: Efficiently allocates available funds across orders
- **Order Book Analysis**: Analyzes market depth before placing orders
- **Automatic Rebalancing**: Periodically refreshes orders to adapt to market changes

## Files

- `market_maker_bot.py` - Main market maker bot implementation
- `market_maker_config.py` - Configuration settings
- `funcs.py` - Helper functions
- `test_api.py` - Test script for API connectivity
- `secure_tradeogre.py` - Secure API wrapper (legacy)

## Setup

1. Create a TradeOgre API key with trading permissions
2. Save your API key and secret in a file (default: `~/.config/tradeogre/api.key`)
   ```
   YOUR_API_KEY
   YOUR_API_SECRET
   ```
3. Adjust settings in `market_maker_config.py` to match your trading strategy
4. Run the bot: `python market_maker_bot.py`

## Configuration

Edit `market_maker_config.py` to customize:

- **Market**: Trading pair (default: AEGS-USDT)
- **Grid Levels**: Number of buy/sell orders to place
- **Price Ranges**: How far from market price to place orders
- **Order Sizes**: Maximum amount per order
- **Refresh Interval**: How often to update orders

## Testing

Before running with real funds:

1. Test API connectivity: `python test_api.py`
2. Set small order sizes in config
3. Monitor the first few cycles to ensure proper operation

## Security

- API keys are loaded from a separate file, not hardcoded
- Rate limiting prevents API abuse
- Error handling prevents unexpected behavior

## Requirements

- Python 3.6+
- requests library
- Internet connection to TradeOgre API

## License

This project is licensed under the MIT License - see the LICENSE file for details.