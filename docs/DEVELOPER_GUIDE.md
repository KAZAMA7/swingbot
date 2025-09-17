# Developer Guide

## Architecture Overview

The Stock Trading Bot follows a modular, plugin-based architecture that allows for easy extension and customization.

### Core Components

```
src/
├── main.py                 # Application entry point
├── config/                 # Configuration management
├── data/                   # Data fetching and storage
├── analysis/               # Technical analysis indicators
├── strategies/             # Trading strategies
├── signals/                # Signal generation and management
├── output/                 # Output and visualization
├── scheduler/              # Task scheduling
├── interfaces/             # Abstract interfaces
├── models/                 # Data models and exceptions
└── utils/                  # Utility functions
```

## Adding New Indicators

To add a new technical indicator:

1. **Create the indicator class** in `src/analysis/`:

```python
from ..interfaces.indicator import IndicatorInterface
from ..models.exceptions import IndicatorError

class MyIndicator(IndicatorInterface):
    def calculate(self, data: pd.DataFrame, params: Dict) -> pd.Series:
        # Your calculation logic here
        pass
    
    def get_required_periods(self, params: Dict) -> int:
        return params.get('period', 14)
    
    def validate_params(self, params: Dict) -> bool:
        # Validate parameters
        return True
    
    def get_default_params(self) -> Dict:
        return {'period': 14}
```

2. **Register the indicator** in `AnalysisEngine`:

```python
# In src/analysis/analysis_engine.py
from .my_indicator import MyIndicator

class AnalysisEngine:
    def __init__(self, config: Dict[str, Any] = None):
        self.calculators = {
            'rsi': RSICalculator(),
            'bollinger_bands': BollingerBandsCalculator(),
            'ema': EMACalculator(),
            'my_indicator': MyIndicator(),  # Add your indicator
        }
```

3. **Add configuration** in `config.yaml`:

```yaml
indicators:
  my_indicator:
    period: 14
    # other parameters
```

## Adding New Trading Strategies

To create a new trading strategy:

1. **Implement the strategy interface**:

```python
from ..interfaces.strategy import StrategyInterface
from ..models.data_models import Signal, SignalType

class MyStrategy(StrategyInterface):
    def generate_signal(self, data: pd.DataFrame, indicators: Dict) -> Signal:
        # Your signal generation logic
        return Signal(
            symbol=symbol,
            timestamp=datetime.now(),
            signal_type=SignalType.BUY,  # or SELL, NO_SIGNAL
            confidence=0.8,
            indicators=indicator_values,
            strategy_name='my_strategy'
        )
    
    def get_required_indicators(self) -> List[str]:
        return ['rsi', 'my_indicator']
    
    def validate_conditions(self, conditions: Dict) -> bool:
        return True
    
    def get_strategy_params(self) -> Dict:
        return {'threshold': 0.5}
```

2. **Register the strategy**:

```python
# In src/signals/signal_generator.py
from ..strategies.my_strategy import MyStrategy

class SignalGenerator:
    def __init__(self, config: Dict[str, Any] = None, db_manager=None):
        self.strategies = {
            'swing_trading': SwingTradingStrategy(),
            'my_strategy': MyStrategy(),  # Add your strategy
        }
```

## Adding New Data Sources

To add a new data source:

1. **Implement the data fetcher interface**:

```python
from ..interfaces.data_fetcher import DataFetcherInterface

class MyDataFetcher(DataFetcherInterface):
    def fetch_current_data(self, symbols: List[str]) -> Dict[str, 'OHLCV']:
        # Fetch current data from your source
        pass
    
    def fetch_historical_data(self, symbol: str, period: str) -> pd.DataFrame:
        # Fetch historical data
        pass
    
    def validate_symbol(self, symbol: str) -> bool:
        # Validate symbol
        return True
    
    def get_supported_exchanges(self) -> List[str]:
        return ['NYSE', 'NASDAQ']
```

2. **Configure the data source**:

```yaml
data_sources:
  my_source:
    enabled: true
    api_key: "your_api_key"
    rate_limit: 10
```

## Testing Guidelines

### Unit Tests

Create unit tests for all new components:

```python
import unittest
from src.analysis.my_indicator import MyIndicator

class TestMyIndicator(unittest.TestCase):
    def setUp(self):
        self.indicator = MyIndicator()
        # Set up test data
    
    def test_calculation(self):
        # Test the calculation logic
        pass
    
    def test_parameter_validation(self):
        # Test parameter validation
        pass
```

### Integration Tests

Test component interactions:

```python
def test_strategy_with_new_indicator(self):
    # Test that your strategy works with indicators
    pass
```

### Running Tests

```bash
python run_tests.py
```

## Configuration Management

### Adding New Configuration Options

1. **Update default configuration** in `ConfigManager.DEFAULT_CONFIG`
2. **Add validation** in `ConfigManager._validate_config()`
3. **Document the option** in configuration files

### Configuration Schema

```yaml
# Main configuration structure
data_sources:
  source_name:
    enabled: boolean
    # source-specific options

watchlist:
  - "SYMBOL1"
  - "SYMBOL2"

indicators:
  indicator_name:
    parameter: value

strategy:
  strategy_name:
    parameter: value

scheduling:
  update_interval: seconds
  market_hours_only: boolean

output:
  csv_file: filename
  database: filename
  charts_enabled: boolean
```

## Error Handling

### Custom Exceptions

Use appropriate custom exceptions:

```python
from ..models.exceptions import IndicatorError, StrategyError, DataFetchError

# In your code
if invalid_condition:
    raise IndicatorError("Specific error message")
```

### Logging

Use structured logging:

```python
import logging

class MyComponent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def my_method(self):
        self.logger.info("Operation started")
        try:
            # Your code
            self.logger.debug("Debug information")
        except Exception as e:
            self.logger.error(f"Operation failed: {e}")
            raise
```

## Performance Considerations

### Memory Management

- Use generators for large datasets
- Clean up old data regularly
- Implement data retention policies

### Computation Efficiency

- Cache expensive calculations
- Use vectorized operations with pandas/numpy
- Implement lazy loading where appropriate

### Database Optimization

- Use appropriate indexes
- Batch database operations
- Implement connection pooling

## Deployment

### Building Binaries

```bash
python build_binary.py
```

### Cross-Platform Considerations

- Use `pathlib` for file paths
- Handle platform-specific dependencies
- Test on target platforms

## Contributing

1. **Follow the architecture patterns**
2. **Write comprehensive tests**
3. **Document your changes**
4. **Follow coding standards**
5. **Update configuration schemas**

## API Reference

### Core Interfaces

- `DataFetcherInterface`: For data sources
- `IndicatorInterface`: For technical indicators
- `StrategyInterface`: For trading strategies

### Data Models

- `OHLCV`: Price data structure
- `Signal`: Trading signal structure
- `IndicatorValue`: Indicator result structure

### Exceptions

- `TradingBotError`: Base exception
- `DataFetchError`: Data fetching issues
- `IndicatorError`: Indicator calculation issues
- `StrategyError`: Strategy execution issues
- `ConfigurationError`: Configuration issues
- `DatabaseError`: Database operation issues