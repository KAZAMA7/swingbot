# Stock Trading Bot

A comprehensive cross-platform stock swing trading bot that automatically fetches global equity data, performs technical analysis using RSI, Bollinger Bands, and EMA indicators, and generates actionable buy/sell signals with room for improvement and extensibility.

![Trading Bot Demo](https://img.shields.io/badge/Status-Production%20Ready-green)
![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey)

## 🚀 Features

### Core Functionality
- **📊 Technical Analysis**: RSI, Bollinger Bands, and EMA indicators
- **🎯 Signal Generation**: Configurable swing trading buy/sell signals
- **📈 Data Fetching**: Yahoo Finance API integration with rate limiting
- **💾 Data Storage**: SQLite database for historical data and signals
- **⏰ Automated Scheduling**: Periodic updates with market hours support
- **📋 Multiple Output Formats**: CSV files, database, and visual charts

### Advanced Features
- **🔧 Extensible Architecture**: Plugin-based system for new indicators and strategies
- **📱 Cross-Platform**: Single executable for Windows, Mac, and Linux
- **🎨 Visualization**: matplotlib-based technical analysis charts
- **⚙️ Configuration Management**: YAML-based configuration with validation
- **🧪 Comprehensive Testing**: Full test suite with performance benchmarks
- **📝 Detailed Logging**: Structured logging with rotation and retention

## 📦 Quick Start

### Option 1: Simple Trading Bot (Recommended for Testing)

```bash
# Install dependencies
pip install yfinance pandas numpy matplotlib pyyaml

# Run the simple version
python simple_trading_bot.py
```

### Option 2: Full System

```bash
# Install all dependencies
pip install -r requirements.txt

# Test the system
python test_bot.py

# Run the full trading bot
python src/main.py --test
```

### Option 3: Pre-built Binary

```bash
# Build the binary
python build_binary.py

# Run the executable (Windows example)
.\dist\trading-bot-windows-amd64.exe --help
```

## 🎯 Trading Strategy

The bot implements a swing trading strategy based on three technical indicators:

### Buy Signal Conditions
- **RSI < 30** (Oversold condition)
- **Price closes below Bollinger Band lower** (Price compression)
- **Price is above EMA** (Trend confirmation)

### Sell Signal Conditions
- **RSI > 70** (Overbought condition)
- **Price closes above Bollinger Band upper** (Price extension)
- **Price is below EMA** (Trend confirmation)

## 📊 Sample Output

```
Stock Trading Bot
========================================
2025-09-17 17:54:16 - INFO - Analyzing AAPL...
2025-09-17 17:54:17 - INFO - AAPL: 11281 records from 1980-12-12 to 2025-09-16 (44.8 years)
2025-09-17 17:54:17 - INFO - AAPL: NO_SIGNAL - Price: $238.15, RSI: 62.2
2025-09-17 17:54:17 - INFO - GOOGL: 5303 records from 2004-08-19 to 2025-09-16 (21.1 years)
2025-09-17 17:54:17 - INFO - GOOGL: NO_SIGNAL - Price: $251.16, RSI: 91.6
2025-09-17 17:54:18 - INFO - NVDA: 6704 records from 1999-01-22 to 2025-09-16 (26.6 years)
2025-09-17 17:54:18 - INFO - NVDA: NO_SIGNAL - Price: $174.88, RSI: 48.8

Analysis Complete!
Processed: 5 symbols
Signals found: 0
```

**📈 Comprehensive Historical Data:**
- **AAPL**: 44.8 years of data (11,281 records)
- **GOOGL**: 21.1 years of data (5,303 records)  
- **MSFT**: 39.5 years of data (9,955 records)
- **TSLA**: 15.2 years of data (3,828 records)
- **NVDA**: 26.6 years of data (6,704 records)

## ⚙️ Configuration

The bot uses a `config.yaml` file for configuration:

```yaml
# Watchlist of stocks to analyze
watchlist:
  - "AAPL"
  - "GOOGL" 
  - "MSFT"
  - "TSLA"
  - "NVDA"

# Technical indicator parameters
indicators:
  rsi:
    period: 14
  bollinger_bands:
    period: 20
    std_dev: 2
  ema:
    period: 20

# Trading strategy parameters
strategy:
  swing_trading:
    rsi_oversold: 30
    rsi_overbought: 70

# Scheduling configuration
scheduling:
  update_interval: 300  # 5 minutes
  market_hours_only: true

# Output configuration
output:
  csv_file: "signals.csv"
  database: "trading_data.db"
  charts_enabled: false
```

## 🖥️ Usage Examples

### Basic Usage
```bash
# Verify data availability (recommended first step)
python verify_data.py

# Run with default settings (downloads comprehensive historical data)
python simple_trading_bot.py

# Run full system with test mode
python src/main.py --test

# Initialize comprehensive historical data for all symbols
python src/main.py --init-data

# Check data availability for all symbols
python src/main.py --check-data

# Run manual update (no scheduling)
python src/main.py --manual

# Enable verbose logging
python src/main.py --verbose

# Use custom configuration
python src/main.py --config my_config.yaml
```

### Advanced Usage
```bash
# Verify comprehensive data availability
python verify_data.py

# Force complete data refresh
python src/main.py --init-data --force-refresh

# Run tests
python run_tests.py

# Build binary for distribution
python build_binary.py

# Generate performance charts
python src/main.py --plot
```

## 📁 Project Structure

```
stock-trading-bot/
├── 📄 README.md                    # This file
├── 📄 requirements.txt             # Python dependencies
├── 📄 simple_trading_bot.py        # Standalone simple version
├── 📄 build_binary.py              # Binary builder script
├── 📄 run_tests.py                 # Test runner
├── 📁 src/                         # Main source code
│   ├── 📄 main.py                  # Application entry point
│   ├── 📁 config/                  # Configuration management
│   ├── 📁 data/                    # Data fetching and storage
│   ├── 📁 analysis/                # Technical indicators
│   ├── 📁 strategies/              # Trading strategies
│   ├── 📁 signals/                 # Signal generation
│   ├── 📁 output/                  # Output and visualization
│   ├── 📁 scheduler/               # Task scheduling
│   ├── 📁 interfaces/              # Abstract interfaces
│   ├── 📁 models/                  # Data models
│   └── 📁 utils/                   # Utility functions
├── 📁 tests/                       # Unit tests
├── 📁 docs/                        # Documentation
└── 📁 dist/                        # Built binaries
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python run_tests.py

# Run specific test modules
python -m unittest tests.test_indicators
python -m unittest tests.test_strategy
python -m unittest tests.test_config_manager
```

## 🔧 Development

### Adding New Indicators

1. Create a new indicator class implementing `IndicatorInterface`
2. Register it in the `AnalysisEngine`
3. Add configuration parameters
4. Write unit tests

See [Developer Guide](docs/DEVELOPER_GUIDE.md) for detailed instructions.

### Adding New Strategies

1. Implement the `StrategyInterface`
2. Register in `SignalGenerator`
3. Configure parameters
4. Test thoroughly

## 📊 Data Management

### Comprehensive Historical Data
The bot automatically downloads **maximum available historical data** for each symbol:

| Symbol | Data Span | Records | Start Date |
|--------|-----------|---------|------------|
| AAPL   | 44.8 years | 11,281  | 1980-12-12 |
| GOOGL  | 21.1 years | 5,303   | 2004-08-19 |
| MSFT   | 39.5 years | 9,955   | 1986-03-13 |
| TSLA   | 15.2 years | 3,828   | 2010-06-29 |
| NVDA   | 26.6 years | 6,704   | 1999-01-22 |

### Smart Data Updates
- **First Run**: Downloads complete historical data (up to 44+ years)
- **Subsequent Runs**: Incremental updates with only new data
- **Database Storage**: SQLite for efficient data management
- **Data Verification**: Built-in data integrity checks

### Data Verification
```bash
# Verify what data is available
python verify_data.py

# Check current data status
python src/main.py --check-data
```

## 📈 Performance

- **Memory Usage**: < 2GB RAM
- **Processing Speed**: ~1-2 seconds per symbol
- **Binary Size**: ~56MB (includes all dependencies)
- **Supported Symbols**: Unlimited (Yahoo Finance coverage)
- **Historical Data**: Up to 44+ years per symbol
- **Data Storage**: Efficient SQLite database

## 🛠️ Dependencies

### Core Dependencies
- `yfinance>=0.2.18` - Yahoo Finance data
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0` - Numerical computing
- `ta>=0.10.2` - Technical analysis
- `matplotlib>=3.7.0` - Charting
- `PyYAML>=6.0` - Configuration
- `APScheduler>=3.10.0` - Task scheduling

### Development Dependencies
- `PyInstaller` - Binary building
- `unittest` - Testing framework

## 🚨 Risk Disclaimer

**This software is for educational and research purposes only. It is not financial advice.**

- Past performance does not guarantee future results
- Trading involves substantial risk of loss
- Always do your own research before making investment decisions
- Consider consulting with a qualified financial advisor
- The authors are not responsible for any financial losses

## 📋 Roadmap

### Completed ✅
- [x] Core technical analysis indicators
- [x] Swing trading strategy implementation
- [x] Yahoo Finance data integration
- [x] SQLite database storage
- [x] Configuration management
- [x] Automated scheduling
- [x] Cross-platform binary building
- [x] Comprehensive test suite
- [x] Chart generation
- [x] Extensible architecture

### Future Enhancements 🔮
- [ ] Additional technical indicators (MACD, Stochastic, etc.)
- [ ] Machine learning signal enhancement
- [ ] Multiple data source support (Alpha Vantage, IEX)
- [ ] Web dashboard interface
- [ ] Email/SMS notifications
- [ ] Backtesting framework
- [ ] Portfolio management features
- [ ] Real-time streaming data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read [Developer Guide](docs/DEVELOPER_GUIDE.md) for development guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Yahoo Finance for providing free market data
- The Python community for excellent libraries
- Technical analysis community for trading strategies
- Open source contributors

## 📞 Support

- 📖 Documentation: [Developer Guide](docs/DEVELOPER_GUIDE.md)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/stock-trading-bot/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/stock-trading-bot/discussions)

---

**Made with ❤️ for the trading community**