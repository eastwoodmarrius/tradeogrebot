# TradeOgre Market Maker Bot - Installation Guide

This guide will help you install and configure the TradeOgre Market Maker Bot.

## Prerequisites

- Python 3.6 or higher
- TradeOgre API key and secret
- Linux, macOS, or Windows with WSL

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/eastwoodmarrius/tradeogrebot.git
   cd tradeogrebot/tradeogre-bot
   ```

2. Run the installation script:
   ```bash
   ./install.sh
   ```

3. Configure your API key:
   ```bash
   nano ~/.config/tradeogre/api.key
   ```
   Replace the placeholder text with your actual API key and secret:
   ```
   YOUR_API_KEY
   YOUR_API_SECRET
   ```

4. Configure the bot settings:
   ```bash
   nano market_maker_config.py
   ```
   Adjust the settings according to your trading strategy.

## Running the Bot

### Manual Execution

To run the bot manually:
```bash
./market_maker_bot.py
```

### Running as a Service (Linux)

1. Edit the service file:
   ```bash
   nano tradeogre-market-maker.service
   ```
   Replace `YOUR_USERNAME` and `/path/to/tradeogrebot` with your actual username and path.

2. Install the service:
   ```bash
   sudo cp tradeogre-market-maker.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable tradeogre-market-maker
   sudo systemctl start tradeogre-market-maker
   ```

3. Check the service status:
   ```bash
   sudo systemctl status tradeogre-market-maker
   ```

## Testing

1. Test the API connection:
   ```bash
   ./test_api.py
   ```

2. Test the market maker in dry run mode:
   ```bash
   ./test_market_maker.py
   ```

## Uninstallation

To uninstall the bot:
```bash
./uninstall.sh
```

## Troubleshooting

- **API Connection Issues**: Verify your API key and internet connection.
- **Permission Denied**: Make sure the scripts are executable (`chmod +x *.py`).
- **Log Files**: Check `market_maker.log` for detailed error messages.

## Support

If you encounter any issues, please open an issue on GitHub or contact the developer.