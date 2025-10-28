# 🚀 Advanced Features Guide

## راهنمای ویژگی‌های پیشرفته | Advanced Features Guide

این راهنما ویژگی‌های پیشرفته نسخه کامل را توضیح می‌دهد.
This guide explains the advanced features of the complete version.

---

## 📑 Table of Contents

1. [Real Exchange Integration (CCXT)](#1-real-exchange-integration)
2. [Historical Database](#2-historical-database)
3. [Multi-Channel Notifications](#3-notifications)
4. [Backtesting Engine](#4-backtesting)
5. [Advanced Analytics & ML](#5-advanced-analytics)
6. [Data Export](#6-data-export)
7. [Configuration](#7-configuration)

---

## 1. Real Exchange Integration

### CCXT Connector

The system now supports real exchange connections using the CCXT library.

#### Installation
```bash
pip install ccxt
```

#### Usage

```python
from core.ccxt_connector import CCXTConnector

# Initialize connector
connector = CCXTConnector(
    api_keys={
        'binance': {
            'apiKey': 'YOUR_API_KEY',
            'secret': 'YOUR_SECRET'
        }
    },
    use_testnet=True  # Use testnet for safety
)

# Initialize exchanges
await connector.initialize_exchanges(['binance', 'coinbase', 'kraken'])

# Fetch real data
ticker = await connector.fetch_ticker('binance', 'BTC/USDT')
```

#### Supported Exchanges

- Binance
- Coinbase
- Kraken
- KuCoin
- Bitfinex
- **100+ more via CCXT**

#### Features

✅ Real-time price data  
✅ Order book depth  
✅ Account balance  
✅ Order placement (with API keys)  
✅ Rate limit management  
✅ Testnet support  

#### Safety

⚠️ **Always use testnet first!**
⚠️ **Never share API keys**
⚠️ **Start with read-only keys**

---

## 2. Historical Database

### SQLite Database Storage

All opportunities and scans are automatically stored in a database for historical analysis.

#### Database Location
```
data/arbitrage.db
```

#### Tables

1. **opportunities** - All detected opportunities
2. **scans** - Scan history and statistics
3. **exchange_health** - Exchange status tracking
4. **preferences** - User settings

#### Usage

```python
from core.database import ArbitrageDatabase

# Initialize database
db = ArbitrageDatabase()

# Get recent opportunities
recent = db.get_recent_opportunities(limit=100, min_profit=1.0)

# Get statistics
stats = db.get_statistics(days=7)

# Export to CSV
db.export_to_csv('opportunities.csv', days=30)
```

#### Statistics Available

- Total opportunities
- Average/max/min profit
- Opportunities by type
- Opportunities by risk level
- Time-based analysis

---

## 3. Multi-Channel Notifications

### Notification System

Get alerts for high-profit opportunities via multiple channels.

#### Supported Channels

1. **Telegram** - Instant messages
2. **Email** - SMTP email alerts
3. **Discord** - Webhook notifications
4. **Custom Webhook** - Your own API

#### Setup

##### Telegram

1. Create bot with [@BotFather](https://t.me/botfather)
2. Get bot token
3. Get your chat ID from [@userinfobot](https://t.me/userinfobot)

```python
from core.notifications import NotificationManager, NotificationConfig

config = NotificationConfig(
    telegram_enabled=True,
    telegram_bot_token='YOUR_BOT_TOKEN',
    telegram_chat_id='YOUR_CHAT_ID',
    min_profit_for_notification=2.0
)

notifier = NotificationManager(config)

# Send test
await notifier.test_notifications()
```

##### Email

```python
config = NotificationConfig(
    email_enabled=True,
    smtp_server='smtp.gmail.com',
    smtp_port=587,
    email_from='your@email.com',
    email_password='YOUR_APP_PASSWORD',
    email_to=['recipient@email.com'],
    min_profit_for_notification=2.0
)
```

⚠️ **Gmail**: Use [App Password](https://support.google.com/accounts/answer/185833), not regular password

##### Discord

1. Create webhook in Discord server settings
2. Copy webhook URL

```python
config = NotificationConfig(
    discord_enabled=True,
    discord_webhook_url='YOUR_WEBHOOK_URL',
    min_profit_for_notification=2.0
)
```

#### Alert Features

- 🚨 Instant high-profit alerts
- 📊 Daily summary reports
- ⏰ Cooldown to prevent spam
- 🎯 Customizable profit threshold
- 📝 Detailed opportunity information

---

## 4. Backtesting Engine

### Strategy Backtesting

Test your arbitrage strategy on historical data before using real money.

#### Usage

```python
from core.backtesting import BacktestEngine

# Initialize engine
engine = BacktestEngine(
    initial_capital=10000.0,
    max_position_size=0.1,  # 10% max per trade
    slippage=0.001  # 0.1% slippage
)

# Run backtest
result = engine.run_backtest(
    opportunities=historical_opportunities,
    strategy_config={
        'min_profit': 1.0,
        'max_risk': 'MEDIUM',
        'min_confidence': 0.6,
        'enabled_types': ['spatial', 'triangular']
    }
)

# View results
print(f"Net Profit: ${result.net_profit:.2f}")
print(f"Win Rate: {result.win_rate*100:.1f}%")
print(f"ROI: {result.roi:.2f}%")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
```

#### Metrics Calculated

- **Total/Net Profit** - Profit after fees
- **Win Rate** - % of successful trades
- **ROI** - Return on investment
- **Sharpe Ratio** - Risk-adjusted returns
- **Max Drawdown** - Largest capital decline
- **Avg Profit per Trade**

#### Parameter Optimization

```python
# Optimize parameters
param_ranges = {
    'min_profit': [0.5, 1.0, 1.5, 2.0],
    'max_risk': ['LOW', 'MEDIUM', 'HIGH'],
    'min_confidence': [0.5, 0.6, 0.7, 0.8]
}

best = engine.optimize_parameters(opportunities, param_ranges)

print(f"Best Parameters: {best['best_parameters']}")
print(f"Best ROI: {best['best_roi']:.2f}%")
```

---

## 5. Advanced Analytics & ML

### AI-Powered Analysis

Machine learning and statistical analysis for better decision-making.

#### Features

##### 1. Opportunity Scoring

Composite score (0-100) based on multiple factors:

```python
from core.analytics import AdvancedAnalytics

analytics = AdvancedAnalytics()

score = analytics.calculate_opportunity_score(opportunity)
# Score combines: profit (40%), confidence (30%), risk (20%), history (10%)
```

##### 2. Best Trading Time Prediction

Find the best hours to trade each asset:

```python
predictions = analytics.predict_best_trading_time('BTC')

# Output:
# {
#   0: {'hour': 0, 'opportunity_count': 12, 'avg_profit': 1.5, 'recommendation': 'Medium'},
#   1: {'hour': 1, 'opportunity_count': 8, 'avg_profit': 2.1, 'recommendation': 'High'},
#   ...
# }
```

##### 3. Exchange Pair Efficiency

Discover which exchange pairs have the best arbitrage:

```python
efficiency = analytics.analyze_exchange_pair_efficiency()

# Returns top 10 exchange pairs by average profit
```

##### 4. Trend Detection

Detect if opportunities are increasing or decreasing:

```python
trend = analytics.detect_trend('ETH', days=7)

# Output:
# {
#   'trend': 'increasing',  # or 'decreasing' or 'stable'
#   'change_percentage': 15.2,
#   'avg_opportunities_per_day': 8.5,
#   'avg_profit': 1.8
# }
```

##### 5. Volatility Index

Measure market volatility (more volatility = more opportunities):

```python
volatility = analytics.calculate_volatility_index('BTC', window=20)
# Returns 0-100 index
```

##### 6. Profit Probability

Predict probability of different profit outcomes:

```python
probabilities = analytics.predict_profit_probability(opportunity)

# Output:
# {
#   'profit_0_1_pct': 0.25,
#   'profit_1_2_pct': 0.35,
#   'profit_2_5_pct': 0.20,
#   'profit_above_5_pct': 0.10,
#   'loss': 0.10
# }
```

##### 7. AI Recommendations

Get intelligent recommendations:

```python
recommendations = analytics.generate_recommendations(opportunities)

# Returns list of actionable recommendations:
# - High profit alerts
# - Safe opportunity suggestions
# - Asset focus recommendations
```

---

## 6. Data Export

### Multi-Format Export

Export your data for external analysis or record-keeping.

#### Supported Formats

1. **CSV** - Spreadsheet compatible
2. **JSON** - API/programmatic use
3. **Excel** - Formatted spreadsheets
4. **Text Report** - Summary report

#### Usage

```python
from utils.export import DataExporter

exporter = DataExporter(output_dir='exports')

# Export to CSV
exporter.export_opportunities_to_csv(opportunities)

# Export to Excel (with formatting)
exporter.export_opportunities_to_excel(opportunities)

# Export to JSON
exporter.export_opportunities_to_json(opportunities)

# Export summary report
exporter.export_summary_report(opportunities, statistics)

# Export all formats at once
results = exporter.export_all_formats(opportunities, statistics)
```

#### Output Location

```
exports/
├── opportunities_20251022_153045.csv
├── opportunities_20251022_153045.json
├── opportunities_20251022_153045.xlsx
└── report_20251022_153045.txt
```

---

## 7. Configuration

### Environment Variables

Create `.env` file for configuration:

```env
# Arbitrage Settings
MIN_PROFIT_PCT=1.0
HIGH_PROFIT_THRESHOLD=3.0

# Exchange Settings
MAX_RETRIES=3
RATE_LIMIT_PER_SECOND=10

# Notification Settings
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id
EMAIL_FROM=your@email.com
EMAIL_PASSWORD=your_app_password
DISCORD_WEBHOOK=your_webhook_url

# Database
DATABASE_PATH=data/arbitrage.db

# Export
EXPORT_DIR=exports
```

### Configuration Management

```python
from config import ArbitrageConfig

# Load from environment
config = ArbitrageConfig.from_env()

# Or create manually
config = ArbitrageConfig(
    min_profit_percentage=1.5,
    max_retries=5,
    auto_scan_enabled=True
)

# Use in engine
engine = ArbitrageEngine(
    min_profit_percentage=config.min_profit_percentage
)
```

---

## 🎯 Complete Workflow Example

### End-to-End Usage

```python
import asyncio
from core import *
from utils import *

async def main():
    # 1. Setup
    config = ArbitrageConfig.from_env()
    db = ArbitrageDatabase()
    analytics = AdvancedAnalytics()
    exporter = DataExporter()
    
    # 2. Initialize components
    engine = ArbitrageEngine(min_profit_percentage=config.min_profit_percentage)
    connector = ExchangeConnector()
    
    # 3. Setup notifications
    notify_config = NotificationConfig(
        telegram_enabled=True,
        telegram_bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
        telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID'),
        min_profit_for_notification=3.0
    )
    notifier = NotificationManager(notify_config)
    
    # 4. Scan markets
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    all_data = await connector.fetch_all_exchanges(symbols)
    
    exchange_data = {
        'exchange_prices': connector.get_exchange_prices(all_data),
        'pair_prices': connector.get_pair_prices(all_data)
    }
    
    # 5. Find opportunities
    opportunities = await engine.scan_all_opportunities(exchange_data)
    
    # 6. Store in database
    for opp in opportunities:
        db.save_opportunity(opp)
        analytics.add_opportunity(opp)
        
        # Send notification for high-profit
        if opp.profit_percentage >= 3.0:
            await notifier.send_opportunity_alert(opp)
    
    # 7. Analyze
    recommendations = analytics.generate_recommendations(opportunities)
    for rec in recommendations:
        print(f"{rec['title']}: {rec['message']}")
    
    # 8. Export
    exporter.export_all_formats(opportunities, db.get_statistics())
    
    # 9. Backtest
    historical = db.get_recent_opportunities(limit=500)
    if len(historical) >= 10:
        backtest_engine = BacktestEngine(initial_capital=10000)
        result = backtest_engine.run_backtest(historical)
        print(f"Backtest ROI: {result.roi:.2f}%")
    
    print(f"✅ Found {len(opportunities)} opportunities")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📚 API Reference

### Core Classes

#### ArbitrageEngine
- `scan_all_opportunities()` - Main scanning method
- `detect_spatial_arbitrage()` - Spatial arbitrage
- `detect_triangular_arbitrage()` - Triangular arbitrage

#### ExchangeConnector
- `fetch_all_exchanges()` - Fetch from all exchanges
- `get_health_status()` - Exchange health

#### CCXTConnector
- `initialize_exchanges()` - Connect to real exchanges
- `fetch_ticker()` - Get real-time price
- `place_order()` - Execute trade

#### ArbitrageDatabase
- `save_opportunity()` - Store opportunity
- `get_recent_opportunities()` - Query database
- `get_statistics()` - Get analytics
- `export_to_csv()` - Export data

#### NotificationManager
- `send_opportunity_alert()` - Send alert
- `send_daily_summary()` - Daily report
- `test_notifications()` - Test setup

#### BacktestEngine
- `run_backtest()` - Run backtest
- `optimize_parameters()` - Find best params
- `get_equity_curve()` - Get performance curve

#### AdvancedAnalytics
- `calculate_opportunity_score()` - Score opportunities
- `predict_best_trading_time()` - Time predictions
- `detect_trend()` - Trend analysis
- `generate_recommendations()` - AI recommendations

#### DataExporter
- `export_opportunities_to_csv()` - CSV export
- `export_opportunities_to_excel()` - Excel export
- `export_opportunities_to_json()` - JSON export
- `export_all_formats()` - Export all

---

## 🔒 Security Best Practices

1. **API Keys**
   - Use environment variables
   - Never commit to git
   - Use read-only keys when possible
   - Enable IP whitelist

2. **Testnet First**
   - Always test with testnet
   - Verify logic before production
   - Start with small amounts

3. **Data Protection**
   - Encrypt sensitive data
   - Regular database backups
   - Secure notification credentials

4. **Rate Limits**
   - Respect exchange limits
   - Use built-in rate limiting
   - Monitor API usage

---

## 🆘 Troubleshooting

### Common Issues

#### "CCXT not installed"
```bash
pip install ccxt
```

#### "Database locked"
```python
# Close existing connections
db.close()
```

#### "Notification failed"
```python
# Test each channel separately
results = await notifier.test_notifications()
print(results)
```

#### "Backtest insufficient data"
```python
# Need at least 10 opportunities
opportunities = db.get_recent_opportunities(limit=500)
print(f"Available: {len(opportunities)}")
```

---

## 📞 Support

For issues or questions:
1. Check this guide
2. Review code documentation
3. Test with examples
4. Open GitHub issue

---

**تبریک! شما اکنون دسترسی به یک سیستم آربیتراژ کامل و حرفه‌ای دارید!**

**Congratulations! You now have access to a complete professional arbitrage system!**
