"""
Data Manager

Manages comprehensive data fetching, storage, and incremental updates.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd

from .yahoo_finance_fetcher import YahooFinanceFetcher
from .database import DatabaseManager
from ..models.data_models import OHLCV
from ..models.exceptions import DataFetchError, DatabaseError


class DataManager:
    """Manages comprehensive data operations with incremental updates."""
    
    def __init__(self, config: Dict[str, Any] = None, db_manager: DatabaseManager = None):
        """
        Initialize data manager.
        
        Args:
            config: Configuration dictionary
            db_manager: Database manager instance
        """
        self.config = config or {}
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize data fetcher
        rate_limit = self.config.get('data_sources', {}).get('yahoo_finance', {}).get('rate_limit', 5)
        self.data_fetcher = YahooFinanceFetcher(rate_limit)
        
        self.logger.info("Data manager initialized")
    
    def initialize_symbol_data(self, symbol: str, force_refresh: bool = False) -> pd.DataFrame:
        """
        Initialize comprehensive historical data for a symbol.
        
        On first run: Downloads maximum available historical data (up to 10+ years)
        On subsequent runs: Updates with latest data only
        
        Args:
            symbol: Stock symbol to initialize
            force_refresh: Force complete data refresh
            
        Returns:
            DataFrame with complete historical data
        """
        try:
            self.logger.info(f"Initializing data for {symbol}")
            
            # Check if we have existing data
            existing_data = self._get_existing_data(symbol)
            
            if existing_data.empty or force_refresh:
                # First time or forced refresh - get maximum historical data
                self.logger.info(f"Downloading complete historical data for {symbol}")
                return self._download_complete_history(symbol)
            else:
                # Incremental update - get only new data
                self.logger.info(f"Performing incremental update for {symbol}")
                return self._incremental_update(symbol, existing_data)
                
        except Exception as e:
            self.logger.error(f"Failed to initialize data for {symbol}: {e}")
            raise DataFetchError(f"Data initialization failed for {symbol}: {e}")
    
    def _download_complete_history(self, symbol: str, config: dict = None) -> pd.DataFrame:
        """
        Download complete historical data for a symbol with enhanced configuration support.
        
        Yahoo Finance provides:
        - Daily data: From inception with "max" period
        - Intraday data: Limited to recent periods
        
        Args:
            symbol: Stock symbol
            config: Configuration dictionary with data fetching parameters
            
        Returns:
            DataFrame with complete historical data
        """
        try:
            # Get configuration parameters
            if config and 'data_fetching' in config:
                data_config = config['data_fetching']
                periods_to_try = data_config.get('fallback_periods', ["max", "10y", "5y", "2y", "1y", "6mo"])
                min_threshold = data_config.get('min_data_threshold', 200)
            else:
                periods_to_try = ["max", "10y", "5y", "2y", "1y", "6mo"]
                min_threshold = 200
            
            period_used = None
            for period in periods_to_try:
                try:
                    self.logger.debug(f"Trying to fetch {period} data for {symbol}")
                    hist_data = self.data_fetcher.fetch_historical_data(symbol, period)
                    
                    if not hist_data.empty and len(hist_data) >= min_threshold:
                        period_used = period
                        
                        # Enhanced data summary
                        start_date = hist_data.index.min().strftime('%Y-%m-%d')
                        end_date = hist_data.index.max().strftime('%Y-%m-%d')
                        years_span = (hist_data.index.max() - hist_data.index.min()).days / 365.25
                        
                        self.logger.info(f"Successfully fetched {len(hist_data)} days of data for {symbol} "
                                       f"from {start_date} to {end_date} ({years_span:.1f} years) [Period: {period}]")
                        
                        # Warn if limited data
                        if years_span < 1.0:
                            self.logger.warning(f"Limited historical data for {symbol}: {years_span:.1f} years")
                        
                        # Convert to OHLCV objects and store
                        ohlcv_list = self._dataframe_to_ohlcv_list(symbol, hist_data)
                        
                        if self.db_manager:
                            self.db_manager.store_price_data(ohlcv_list)
                            self.logger.info(f"Stored {len(ohlcv_list)} records for {symbol}")
                        
                        return hist_data
                    else:
                        self.logger.debug(f"Insufficient data with {period} for {symbol}: {len(hist_data) if not hist_data.empty else 0} days")
                        
                except Exception as e:
                    self.logger.warning(f"Failed to fetch {period} data for {symbol}: {e}")
                    continue
            
            raise DataFetchError(f"Could not fetch sufficient historical data for {symbol} (need {min_threshold}+ days)")
            
        except Exception as e:
            raise DataFetchError(f"Complete history download failed for {symbol}: {e}")
    
    def _incremental_update(self, symbol: str, existing_data: pd.DataFrame) -> pd.DataFrame:
        """
        Perform incremental update for a symbol.
        
        Args:
            symbol: Stock symbol
            existing_data: Existing data from database
            
        Returns:
            DataFrame with updated data
        """
        try:
            # Get the latest date in existing data
            latest_date = existing_data.index.max()
            days_since_update = (datetime.now() - latest_date).days
            
            self.logger.debug(f"Latest data for {symbol}: {latest_date}, {days_since_update} days ago")
            
            if days_since_update <= 1:
                self.logger.info(f"Data for {symbol} is up to date")
                return existing_data
            
            # Fetch recent data to fill the gap
            # Add buffer to ensure we don't miss any data
            fetch_period = f"{min(days_since_update + 5, 30)}d"
            
            try:
                new_data = self.data_fetcher.fetch_historical_data(symbol, fetch_period)
                
                if new_data.empty:
                    self.logger.warning(f"No new data available for {symbol}")
                    return existing_data
                
                # Filter out data we already have
                new_data = new_data[new_data.index > latest_date]
                
                if new_data.empty:
                    self.logger.info(f"No new data to add for {symbol}")
                    return existing_data
                
                # Store new data
                new_ohlcv_list = self._dataframe_to_ohlcv_list(symbol, new_data)
                
                if self.db_manager:
                    self.db_manager.store_price_data(new_ohlcv_list)
                    self.logger.info(f"Added {len(new_ohlcv_list)} new records for {symbol}")
                
                # Combine existing and new data
                combined_data = pd.concat([existing_data, new_data])
                combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
                combined_data = combined_data.sort_index()
                
                self.logger.info(f"Updated {symbol}: {len(existing_data)} -> {len(combined_data)} records")
                return combined_data
                
            except Exception as e:
                self.logger.warning(f"Incremental update failed for {symbol}, using existing data: {e}")
                return existing_data
                
        except Exception as e:
            self.logger.error(f"Incremental update error for {symbol}: {e}")
            return existing_data
    
    def _get_existing_data(self, symbol: str) -> pd.DataFrame:
        """
        Get existing data for a symbol from database.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            DataFrame with existing data
        """
        try:
            if not self.db_manager:
                return pd.DataFrame()
            
            # Get data from database
            ohlcv_list = self.db_manager.get_price_data(symbol)
            
            if not ohlcv_list:
                return pd.DataFrame()
            
            # Convert to DataFrame
            data_dict = {
                'Open': [d.open for d in ohlcv_list],
                'High': [d.high for d in ohlcv_list],
                'Low': [d.low for d in ohlcv_list],
                'Close': [d.close for d in ohlcv_list],
                'Volume': [d.volume for d in ohlcv_list]
            }
            
            timestamps = [d.timestamp for d in ohlcv_list]
            df = pd.DataFrame(data_dict, index=timestamps)
            df.index.name = 'Date'
            
            # Sort by date (most recent last)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to get existing data for {symbol}: {e}")
            return pd.DataFrame()
    
    def _dataframe_to_ohlcv_list(self, symbol: str, df: pd.DataFrame) -> List[OHLCV]:
        """
        Convert DataFrame to list of OHLCV objects.
        
        Args:
            symbol: Stock symbol
            df: DataFrame with OHLCV data
            
        Returns:
            List of OHLCV objects
        """
        ohlcv_list = []
        
        for timestamp, row in df.iterrows():
            ohlcv = OHLCV(
                symbol=symbol,
                timestamp=timestamp.to_pydatetime() if hasattr(timestamp, 'to_pydatetime') else timestamp,
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume'])
            )
            ohlcv_list.append(ohlcv)
        
        return ohlcv_list
    
    def get_data_summary(self, symbol: str) -> Dict[str, Any]:
        """
        Get data summary for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with data summary
        """
        try:
            existing_data = self._get_existing_data(symbol)
            
            if existing_data.empty:
                return {
                    'symbol': symbol,
                    'status': 'no_data',
                    'records': 0,
                    'date_range': None,
                    'last_update': None
                }
            
            return {
                'symbol': symbol,
                'status': 'data_available',
                'records': len(existing_data),
                'date_range': {
                    'start': existing_data.index.min().strftime('%Y-%m-%d'),
                    'end': existing_data.index.max().strftime('%Y-%m-%d')
                },
                'last_update': existing_data.index.max().strftime('%Y-%m-%d'),
                'days_of_data': (existing_data.index.max() - existing_data.index.min()).days
            }
            
        except Exception as e:
            return {
                'symbol': symbol,
                'status': 'error',
                'error': str(e)
            }
    
    def bulk_initialize(self, symbols: List[str], force_refresh: bool = False) -> Dict[str, Any]:
        """
        Initialize data for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            force_refresh: Force complete data refresh
            
        Returns:
            Dictionary with initialization results
        """
        results = {
            'initialized': 0,
            'updated': 0,
            'errors': 0,
            'details': {}
        }
        
        for symbol in symbols:
            try:
                self.logger.info(f"Initializing {symbol} ({symbols.index(symbol) + 1}/{len(symbols)})")
                
                data = self.initialize_symbol_data(symbol, force_refresh)
                
                if not data.empty:
                    summary = self.get_data_summary(symbol)
                    results['details'][symbol] = summary
                    
                    if summary['status'] == 'data_available':
                        if summary['records'] > 100:  # Assume initialization if we have lots of data
                            results['initialized'] += 1
                        else:
                            results['updated'] += 1
                
            except Exception as e:
                self.logger.error(f"Failed to initialize {symbol}: {e}")
                results['errors'] += 1
                results['details'][symbol] = {'status': 'error', 'error': str(e)}
        
        self.logger.info(f"Bulk initialization completed: {results}")
        return results
    
    def check_data_availability(self, symbol: str) -> Dict[str, Any]:
        """
        Check what data is available for a symbol from Yahoo Finance.
        
        Args:
            symbol: Stock symbol to check
            
        Returns:
            Dictionary with availability information
        """
        try:
            # Test different periods to see what's available
            availability = {
                'symbol': symbol,
                'available_periods': {},
                'recommended_period': 'max',
                'max_records': 0
            }
            
            test_periods = ['5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max']
            
            for period in test_periods:
                try:
                    data = self.data_fetcher.fetch_historical_data(symbol, period)
                    if not data.empty:
                        availability['available_periods'][period] = {
                            'records': len(data),
                            'start_date': data.index.min().strftime('%Y-%m-%d'),
                            'end_date': data.index.max().strftime('%Y-%m-%d')
                        }
                        
                        if len(data) > availability['max_records']:
                            availability['max_records'] = len(data)
                            availability['recommended_period'] = period
                            
                except Exception as e:
                    availability['available_periods'][period] = {'error': str(e)}
            
            return availability
            
        except Exception as e:
            return {
                'symbol': symbol,
                'error': str(e),
                'available_periods': {}
            }