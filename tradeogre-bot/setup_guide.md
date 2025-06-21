# TradeOgre Grid Bot - Complete Setup Guide

## 🚀 Quick Start for AEGS-USDT Trading

### Prerequisites
- Python 3.7 or higher
- TradeOgre account with API access
- Initial USDT balance for trading

### Step 1: Install Dependencies
```bash
pip install requests
```

### Step 2: Create API Credentials
1. Log into TradeOgre → Account → Settings → API Keys
2. Create new API key with trading permissions
3. Create secure credential file:
```bash
mkdir -p ~/.config/tradeogre
echo "YOUR_API_KEY" > ~/.config/tradeogre/api.key
echo "YOUR_API_SECRET" >> ~/.config/tradeogre/api.key
chmod 600 ~/.config/tradeogre/api.key
```

### Step 3: Generate Configuration
```bash
python3 config.py
```
This creates a sample configuration file. Copy and modify it:
```bash
cp ~/.config/tradeogre/config.json.sample ~/.config/tradeogre/config.json
```

### Step 4: Configure for AEGS-USDT
Edit `~/.config/tradeogre/config.json`:
```json
{
  "trading": {
    "bot_ticker": "AEGS-USDT",
    "bot_balance": 100.0,
    "buffer": 0.00001,
    "upper_bound": 0.001,
    "grid_count": 10,
    "pulse_interval": 5,
    "max_position": 1000.0,
    "max_orders_per_side": 10,
    "emergency_stop_price_deviation": 0.5,
    "max_consecutive_failures": 5,
    "max_daily_loss": 100.0,
    "dry_run": true
  }
}
```

### Step 5: Test in Dry Run Mode
```bash
python3 secure_run.py
```

### Step 6: Go Live (After Testing)
Set `"dry_run": false` in config and restart the bot.

## 📊 Recommended Parameters for AEGS-USDT

### Conservative Setup:
- **Grid Count**: 8-10 levels
- **Buffer**: 0.00001 USDT
- **Upper Bound**: 20% above current ask
- **Trade Size**: 10-50 AEGS per level
- **Max Position**: 500 AEGS

### Aggressive Setup:
- **Grid Count**: 15-20 levels
- **Buffer**: 0.000005 USDT
- **Upper Bound**: 50% above current ask
- **Trade Size**: 20-100 AEGS per level
- **Max Position**: 2000 AEGS

## 🛡️ Safety Features

### Automatic Risk Controls:
- ✅ Emergency stop on large price movements (>50%)
- ✅ Daily loss limits
- ✅ Maximum position limits
- ✅ API failure protection
- ✅ Rate limiting
- ✅ Comprehensive logging

### Manual Controls:
- ✅ Graceful shutdown (Ctrl+C)
- ✅ Dry run mode for testing
- ✅ Order cancellation on exit
- ✅ Real-time monitoring

## 📈 Monitoring Your Bot

### Log Files:
- Main log: `~/.config/tradeogre/bot.log`
- Rotated automatically when size exceeds 10MB

### Key Metrics to Watch:
- Total trades executed
- Current spread and market conditions
- Active order count
- P&L tracking
- API response times

### Alerts to Set Up:
- Price deviation alerts
- Order fill notifications
- API failure warnings
- Daily P&L summaries

## 🔧 Troubleshooting

### Common Issues:

**"API key file not found"**
- Ensure file exists at `~/.config/tradeogre/api.key`
- Check file permissions (should be 600)

**"Invalid market format"**
- Verify AEGS-USDT is available on TradeOgre
- Check spelling and case sensitivity

**"Insufficient balance"**
- Ensure you have enough USDT for initial orders
- Check minimum order sizes

**"Rate limit exceeded"**
- Bot has built-in rate limiting
- Reduce pulse_interval if needed

**"Connection errors"**
- Check internet connectivity
- Verify TradeOgre API status

### Debug Mode:
Add logging level to see more details:
```python
import logging
logging.getLogger('tradeogre_bot').setLevel(logging.DEBUG)
```

## 🎯 Optimization Tips

### Grid Spacing:
- Tighter grids = more trades, higher fees
- Wider grids = fewer trades, better profit per trade
- Monitor spread to optimize spacing

### Position Sizing:
- Start small and scale up gradually
- Never risk more than you can afford to lose
- Consider market volatility

### Market Timing:
- Avoid major news events
- Monitor volume and liquidity
- Consider time zones and trading hours

## 🚨 Important Warnings

### Financial Risks:
- ⚠️ Grid trading can result in losses during trending markets
- ⚠️ Always use stop losses and position limits
- ⚠️ Start with small amounts for testing
- ⚠️ Never invest more than you can afford to lose

### Technical Risks:
- ⚠️ Ensure stable internet connection
- ⚠️ Monitor bot regularly
- ⚠️ Keep API credentials secure
- ⚠️ Regular backups of configuration

### Legal Considerations:
- ⚠️ Check local regulations regarding automated trading
- ⚠️ Understand tax implications
- ⚠️ Comply with exchange terms of service

## 📞 Support

### Getting Help:
1. Check logs for error messages
2. Review configuration settings
3. Test with dry run mode
4. Verify API connectivity

### Useful Commands:
```bash
# Check API connectivity
python3 -c "from secure_tradeogre import SecureTradeOgre; api = SecureTradeOgre(); print(api.get_connection_status())"

# View current AEGS-USDT market data
curl -s "https://tradeogre.com/api/v1/ticker/AEGS-USDT"

# Check bot logs
tail -f ~/.config/tradeogre/bot.log
```

## 🔄 Updates and Maintenance

### Regular Tasks:
- [ ] Review and adjust grid parameters weekly
- [ ] Monitor market conditions daily
- [ ] Check log files for errors
- [ ] Update configuration as needed
- [ ] Backup important data

### Security Maintenance:
- [ ] Rotate API keys monthly
- [ ] Review file permissions
- [ ] Update dependencies
- [ ] Monitor for security advisories

---

**Remember**: This bot is a tool to assist with trading, but it requires active monitoring and management. Always understand the risks involved and never trade with money you cannot afford to lose.