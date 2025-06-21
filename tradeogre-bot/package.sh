#!/bin/bash
# Package the TradeOgre Market Maker Bot for distribution

echo "Packaging TradeOgre Market Maker Bot..."

# Create a temporary directory
TEMP_DIR="tradeogre-market-maker"
mkdir -p $TEMP_DIR

# Copy necessary files
cp market_maker_bot.py $TEMP_DIR/
cp market_maker_config.py $TEMP_DIR/
cp funcs.py $TEMP_DIR/
cp test_api.py $TEMP_DIR/
cp test_market_maker.py $TEMP_DIR/
cp install.sh $TEMP_DIR/
cp uninstall.sh $TEMP_DIR/
cp check_updates.py $TEMP_DIR/
cp requirements.txt $TEMP_DIR/
cp README.md $TEMP_DIR/
cp INSTALL.md $TEMP_DIR/
cp tradeogre-market-maker.service $TEMP_DIR/

# Create a zip file
zip -r tradeogre-market-maker.zip $TEMP_DIR

# Clean up
rm -rf $TEMP_DIR

echo "Package created: tradeogre-market-maker.zip"