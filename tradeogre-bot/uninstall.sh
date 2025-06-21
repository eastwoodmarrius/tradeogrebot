#!/bin/bash
# Uninstallation script for TradeOgre Market Maker Bot

echo "Uninstalling TradeOgre Market Maker Bot..."

# Remove virtual environment
if [ -d "tradeogre-env" ]; then
    echo "Removing virtual environment..."
    rm -rf tradeogre-env
fi

# Remove log files
echo "Removing log files..."
rm -f market_maker.log

echo "Uninstallation complete!"
echo "Note: Your API key file at ~/.config/tradeogre/api.key has not been removed."
echo "If you want to remove it, use: rm ~/.config/tradeogre/api.key"