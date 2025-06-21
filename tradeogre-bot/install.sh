#!/bin/bash
# Installation script for TradeOgre Market Maker Bot

echo "Installing TradeOgre Market Maker Bot..."

# Create virtual environment if it doesn't exist
if [ ! -d "tradeogre-env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv tradeogre-env
fi

# Activate virtual environment
source tradeogre-env/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create API key directory if it doesn't exist
mkdir -p ~/.config/tradeogre

# Check if API key file exists
if [ ! -f ~/.config/tradeogre/api.key ]; then
    echo "API key file not found. Creating template..."
    echo "YOUR_API_KEY" > ~/.config/tradeogre/api.key
    echo "YOUR_API_SECRET" >> ~/.config/tradeogre/api.key
    echo "Please edit ~/.config/tradeogre/api.key with your actual API credentials."
fi

# Make scripts executable
chmod +x market_maker_bot.py test_api.py test_market_maker.py

echo "Installation complete!"
echo "To run the bot, use: ./market_maker_bot.py"
echo "To test the API connection, use: ./test_api.py"
echo "To test the market maker in dry run mode, use: ./test_market_maker.py"