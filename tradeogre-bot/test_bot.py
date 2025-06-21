#!/usr/bin/env python3

from secure_tradeogre import SecureTradeOgre
import time

# Initialize API
api = SecureTradeOgre()
api.load_key('/home/daimondsteel259/.config/tradeogre/api.key')

print("🚀 Testing AEGS-USDT Grid Bot Setup")
print("=" * 50)

# Test market data
print("📊 Getting AEGS-USDT market data...")
ticker = api.ticker('AEGS-USDT')
if ticker.success:
    data = ticker.data
    print(f"✅ Current price: {data['price']}")
    print(f"✅ Ask price: {data['ask']}")
    print(f"✅ Bid price: {data['bid']}")
    print(f"✅ 24h volume: {data['volume']}")
else:
    print(f"❌ Error: {ticker.error}")
    exit(1)

# Test account balances
print("\n💰 Getting account balances...")
balances = api.balances()
if balances.success:
    data = balances.data
    usdt_balance = float(data['available']['USDT'])
    aegs_balance = float(data['available']['AEGS'])
    print(f"✅ USDT available: {usdt_balance}")
    print(f"✅ AEGS available: {aegs_balance}")
    
    if aegs_balance >= 1000:
        print(f"✅ Sufficient AEGS for trading (have {aegs_balance}, need 1000)")
    else:
        print(f"⚠️  Low AEGS balance (have {aegs_balance}, recommended 1000+)")
        
else:
    print(f"❌ Error: {balances.error}")
    exit(1)

# Calculate grid parameters
ask_price = float(ticker.data['ask'])
buffer = 0.00001
lower_bound = ask_price + buffer
upper_bound = 0.002
grid_count = 10
trade_size = 1000.0 / grid_count

print(f"\n📈 Grid Trading Parameters:")
print(f"✅ Lower bound: {lower_bound:.8f} USDT")
print(f"✅ Upper bound: {upper_bound:.8f} USDT")
print(f"✅ Grid levels: {grid_count}")
print(f"✅ AEGS per level: {trade_size}")
print(f"✅ Total AEGS to trade: 1000")

# Generate grid levels
from funcs import generate_grid
grid_levels = generate_grid(lower_bound, upper_bound, grid_count)

print(f"\n🎯 Grid Levels (DRY RUN):")
for i, price in enumerate(grid_levels):
    print(f"Level {i+1}: Sell {trade_size} AEGS @ {price:.8f} USDT")

print(f"\n🎉 Setup Complete!")
print(f"Your bot is ready to trade AEGS-USDT")
print(f"Current spread: {((ask_price - float(ticker.data['bid'])) / float(ticker.data['bid']) * 100):.2f}%")
print(f"\n⚠️  This was a DRY RUN - no real orders placed")
print(f"To go live, you'll need to fix the balance checking in secure_run.py")
