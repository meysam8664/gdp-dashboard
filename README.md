# 💰 Professional Arbitrage Opportunity Finder

A comprehensive, intelligent arbitrage detection system that monitors multiple cryptocurrency exchanges in real-time to identify profitable trading opportunities. Built with advanced algorithms, robust error handling, and a modern web interface.

## 🚀 Features

### Core Functionality
- **Multi-Exchange Support**: Binance, Coinbase, Kraken, KuCoin, Bybit, OKX, Gate.io
- **Real-Time Monitoring**: Continuous price monitoring with configurable scan intervals
- **Intelligent Detection**: Advanced algorithms for simple, triangular, and cross-currency arbitrage
- **Risk Management**: Comprehensive risk scoring and confidence analysis
- **Performance Optimization**: High-performance async operations with caching

### Advanced Features
- **Live Dashboard**: Modern Streamlit interface with real-time updates
- **REST API**: Full REST API with WebSocket support for real-time data
- **Comprehensive Logging**: Detailed logging with error tracking and performance monitoring
- **Configuration Management**: Flexible configuration system for different strategies
- **Error Recovery**: Robust error handling with automatic recovery mechanisms
- **Testing Suite**: Comprehensive test coverage for all components

### Analytics & Monitoring
- **Profit Distribution Charts**: Visualize opportunity distribution
- **Exchange Activity Monitoring**: Track exchange health and performance
- **Performance Metrics**: Detailed performance statistics and timing
- **Error Analytics**: Comprehensive error tracking and analysis
- **Real-Time Alerts**: Instant notifications for profitable opportunities

## 📋 Requirements

- Python 3.8+
- Exchange API keys (optional, works in sandbox mode)
- 4GB+ RAM recommended
- Stable internet connection

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd arbitrage-opportunity-finder
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables** (optional):
   ```bash
   # Create .env file
   echo "BINANCE_API_KEY=your_binance_api_key" >> .env
   echo "BINANCE_SECRET=your_binance_secret" >> .env
   echo "COINBASE_API_KEY=your_coinbase_api_key" >> .env
   echo "COINBASE_SECRET=your_coinbase_secret" >> .env
   # Add other exchange keys as needed
   ```

4. **Create logs directory**:
   ```bash
   mkdir -p logs
   ```

## 🚀 Quick Start

### Option 1: Streamlit Dashboard (Recommended)
```bash
streamlit run streamlit_app.py
```
Open your browser to `http://localhost:8501`

### Option 2: REST API
```bash
python api_service.py
```
API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### Option 3: Command Line
```bash
python arbitrage_engine.py
```

## 📊 Usage

### Streamlit Dashboard

1. **Start Monitoring**: Click "Start Monitoring" to begin scanning for opportunities
2. **Configure Settings**: Adjust minimum profit, volume, and risk thresholds
3. **Select Symbols**: Choose which cryptocurrency pairs to monitor
4. **View Opportunities**: Real-time table of profitable opportunities
5. **Analyze Data**: Use charts and analytics to understand market patterns

### API Usage

#### Get Current Opportunities
```bash
curl "http://localhost:8000/opportunities?limit=10&min_profit=0.5"
```

#### Get Statistics
```bash
curl "http://localhost:8000/statistics"
```

#### Start/Stop Monitoring
```bash
curl -X POST "http://localhost:8000/monitoring/start"
curl -X POST "http://localhost:8000/monitoring/stop"
```

#### Update Configuration
```bash
curl -X POST "http://localhost:8000/config" \
  -H "Content-Type: application/json" \
  -d '{"min_profit_percentage": 0.2, "min_volume": 2000}'
```

### WebSocket Real-Time Updates
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/opportunities');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('New opportunities:', data.data);
};
```

## ⚙️ Configuration

### Exchange Configuration
Edit `config.py` to configure exchange settings:

```python
exchanges = {
    "binance": ExchangeConfig(
        name="binance",
        api_key="your_api_key",
        secret="your_secret",
        sandbox=True,  # Set to False for live trading
        enabled=True
    ),
    # ... other exchanges
}
```

### Arbitrage Settings
```python
arbitrage = ArbitrageConfig(
    min_profit_percentage=0.1,  # Minimum 0.1% profit
    min_volume=1000,            # Minimum volume requirement
    max_spread=5.0,             # Maximum spread percentage
    max_risk_score=50.0,        # Maximum risk score
    scan_interval=5             # Scan every 5 seconds
)
```

## 🔧 Advanced Features

### Custom Arbitrage Strategies

1. **Simple Arbitrage**: Same asset, different exchanges
2. **Triangular Arbitrage**: A→B→C→A currency chains
3. **Cross-Currency Arbitrage**: Different base currencies
4. **Futures-Spot Arbitrage**: Futures vs spot price differences

### Risk Management

- **Confidence Scoring**: Based on volume and spread analysis
- **Risk Assessment**: Time-based and volatility risk calculation
- **Exchange Health Monitoring**: Automatic blacklisting of problematic exchanges
- **Execution Time Estimation**: Predicts opportunity viability

### Performance Optimization

- **Async Operations**: Non-blocking exchange API calls
- **Caching**: Intelligent caching of price data
- **Rate Limiting**: Respects exchange API limits
- **Connection Pooling**: Efficient connection management

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest test_arbitrage.py -v

# Run specific test categories
python -m pytest test_arbitrage.py::TestArbitrageDetector -v
python -m pytest test_arbitrage.py::TestAPI -v

# Run with coverage
python -m pytest test_arbitrage.py --cov=arbitrage_engine --cov-report=html
```

## 📈 Monitoring & Logging

### Log Files
- `logs/arbitrage_YYYY-MM-DD.log`: General application logs
- `logs/errors_YYYY-MM-DD.log`: Error-specific logs
- `logs/performance_YYYY-MM-DD.log`: Performance metrics

### Health Monitoring
- Exchange connectivity status
- API rate limit monitoring
- Error rate tracking
- Performance metrics

## 🚨 Error Handling

The system includes comprehensive error handling:

- **Automatic Recovery**: Retries failed operations
- **Exchange Blacklisting**: Temporarily disables problematic exchanges
- **Graceful Degradation**: Continues operating with available exchanges
- **Detailed Logging**: Complete error tracking and analysis

## 🔒 Security Considerations

- **API Key Security**: Store keys in environment variables
- **Sandbox Mode**: Test with sandbox environments first
- **Rate Limiting**: Respects exchange API limits
- **Error Sanitization**: Prevents sensitive data leakage

## 📊 Performance Metrics

Typical performance characteristics:
- **Scan Interval**: 5 seconds (configurable)
- **Memory Usage**: ~100-200MB
- **CPU Usage**: Low (async operations)
- **Network**: Minimal (efficient API usage)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes only. Always verify opportunities before trading and never risk more than you can afford to lose. The authors are not responsible for any financial losses.

## 🆘 Support

For issues and questions:
1. Check the logs in the `logs/` directory
2. Review the API documentation at `/docs`
3. Check the test suite for usage examples
4. Create an issue with detailed error information

## 🔄 Updates

The system is designed to be easily extensible:
- Add new exchanges by implementing the exchange interface
- Create custom arbitrage strategies
- Extend the API with new endpoints
- Add new monitoring and alerting features

---

**Built with ❤️ for the cryptocurrency trading community**
