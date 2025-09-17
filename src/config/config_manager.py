"""
Configuration Manager

Handles loading, validation, and management of application configuration.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from ..models.exceptions import ConfigurationError


class ConfigManager:
    """Manages application configuration from YAML files."""
    
    DEFAULT_CONFIG = {
        'data_sources': {
            'yahoo_finance': {
                'enabled': True,
                'rate_limit': 5
            }
        },
        'watchlist': ['AAPL', 'GOOGL', 'MSFT'],
        'indicators': {
            'rsi': {
                'period': 14
            },
            'bollinger_bands': {
                'period': 20,
                'std_dev': 2
            },
            'ema': {
                'period': 20
            }
        },
        'strategy': {
            'swing_trading': {
                'rsi_oversold': 30,
                'rsi_overbought': 70
            }
        },
        'scheduling': {
            'update_interval': 300,
            'market_hours_only': True
        },
        'output': {
            'csv_file': 'signals.csv',
            'database': 'trading_data.db',
            'charts_enabled': False,
            'output_dir': 'output'
        },
        'logging': {
            'level': 'INFO',
            'file': 'trading_bot.log',
            'max_size_mb': 10,
            'backup_count': 5
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path or 'config.yaml')
        self.config = {}
        self.logger = logging.getLogger(__name__)
        
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or create default.
        
        Returns:
            Configuration dictionary
            
        Raises:
            ConfigurationError: If configuration loading fails
        """
        try:
            if not self.config_path.exists():
                self.logger.info(f"Configuration file not found at {self.config_path}, creating default")
                self._create_default_config()
            
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            # Merge with defaults to ensure all keys exist
            self.config = self._merge_with_defaults(self.config)
            
            # Validate configuration
            self._validate_config()
            
            self.logger.info(f"Configuration loaded from {self.config_path}")
            return self.config
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def _create_default_config(self):
        """Create default configuration file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                yaml.dump(self.DEFAULT_CONFIG, f, default_flow_style=False, indent=2)
                
            self.logger.info(f"Default configuration created at {self.config_path}")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to create default configuration: {e}")
    
    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge loaded config with defaults.
        
        Args:
            config: Loaded configuration
            
        Returns:
            Merged configuration
        """
        def merge_dict(default: Dict, custom: Dict) -> Dict:
            result = default.copy()
            for key, value in custom.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dict(result[key], value)
                else:
                    result[key] = value
            return result
        
        return merge_dict(self.DEFAULT_CONFIG, config)
    
    def _validate_config(self):
        """
        Validate configuration values.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        errors = []
        
        # Validate watchlist
        if not isinstance(self.config.get('watchlist'), list):
            errors.append("watchlist must be a list")
        elif not self.config['watchlist']:
            errors.append("watchlist cannot be empty")
        
        # Validate indicators
        indicators = self.config.get('indicators', {})
        
        if 'rsi' in indicators:
            period = indicators['rsi'].get('period', 14)
            if not isinstance(period, int) or period < 2:
                errors.append("RSI period must be an integer >= 2")
        
        if 'bollinger_bands' in indicators:
            bb = indicators['bollinger_bands']
            period = bb.get('period', 20)
            std_dev = bb.get('std_dev', 2)
            if not isinstance(period, int) or period < 2:
                errors.append("Bollinger Bands period must be an integer >= 2")
            if not isinstance(std_dev, (int, float)) or std_dev <= 0:
                errors.append("Bollinger Bands std_dev must be a positive number")
        
        if 'ema' in indicators:
            period = indicators['ema'].get('period', 20)
            if not isinstance(period, int) or period < 1:
                errors.append("EMA period must be an integer >= 1")
        
        # Validate strategy
        strategy = self.config.get('strategy', {}).get('swing_trading', {})
        oversold = strategy.get('rsi_oversold', 30)
        overbought = strategy.get('rsi_overbought', 70)
        
        if not isinstance(oversold, (int, float)) or not 0 <= oversold <= 100:
            errors.append("RSI oversold threshold must be between 0 and 100")
        if not isinstance(overbought, (int, float)) or not 0 <= overbought <= 100:
            errors.append("RSI overbought threshold must be between 0 and 100")
        if oversold >= overbought:
            errors.append("RSI oversold threshold must be less than overbought threshold")
        
        # Validate scheduling
        scheduling = self.config.get('scheduling', {})
        interval = scheduling.get('update_interval', 300)
        if not isinstance(interval, int) or interval < 60:
            errors.append("Update interval must be an integer >= 60 seconds")
        
        if errors:
            raise ConfigurationError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def reload_config(self):
        """Reload configuration from file."""
        self.load_config()
        self.logger.info("Configuration reloaded")
    
    def get_watchlist(self) -> list:
        """Get watchlist symbols."""
        return self.config.get('watchlist', [])
    
    def get_indicator_config(self, indicator_name: str) -> Dict[str, Any]:
        """Get configuration for specific indicator."""
        return self.config.get('indicators', {}).get(indicator_name, {})
    
    def get_strategy_config(self, strategy_name: str) -> Dict[str, Any]:
        """Get configuration for specific strategy."""
        return self.config.get('strategy', {}).get(strategy_name, {})