"""
Tests for Configuration Manager
"""

import unittest
import tempfile
import yaml
from pathlib import Path

from src.config.config_manager import ConfigManager
from src.models.exceptions import ConfigurationError


class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / 'test_config.yaml'
    
    def test_create_default_config(self):
        """Test default configuration creation."""
        manager = ConfigManager(str(self.config_path))
        config = manager.load_config()
        
        self.assertTrue(self.config_path.exists())
        self.assertIn('watchlist', config)
        self.assertIn('indicators', config)
        self.assertIn('strategy', config)
    
    def test_load_existing_config(self):
        """Test loading existing configuration."""
        test_config = {
            'watchlist': ['TSLA', 'NVDA'],
            'indicators': {
                'rsi': {'period': 21}
            }
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        manager = ConfigManager(str(self.config_path))
        config = manager.load_config()
        
        self.assertEqual(config['watchlist'], ['TSLA', 'NVDA'])
        self.assertEqual(config['indicators']['rsi']['period'], 21)
    
    def test_config_validation_invalid_rsi_period(self):
        """Test configuration validation with invalid RSI period."""
        test_config = {
            'indicators': {
                'rsi': {'period': 1}  # Invalid: too small
            }
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        manager = ConfigManager(str(self.config_path))
        
        with self.assertRaises(ConfigurationError):
            manager.load_config()
    
    def test_get_method(self):
        """Test configuration value retrieval."""
        manager = ConfigManager(str(self.config_path))
        config = manager.load_config()
        
        # Test dot notation
        rsi_period = manager.get('indicators.rsi.period')
        self.assertEqual(rsi_period, 14)
        
        # Test default value
        missing_value = manager.get('nonexistent.key', 'default')
        self.assertEqual(missing_value, 'default')


if __name__ == '__main__':
    unittest.main()