"""
Scheduler

Manages automated execution cycles and manual triggers.
"""

import logging
import time
from datetime import datetime, time as dt_time
from typing import Callable, Dict, Any
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from src.models.exceptions import TradingBotError


class TradingScheduler:
    """Manages scheduled execution of trading bot operations."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize scheduler.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.scheduler = BlockingScheduler()
        self.update_callback = None
        self.is_running = False
        
        # Get scheduling configuration
        scheduling_config = self.config.get('scheduling', {})
        self.update_interval = scheduling_config.get('update_interval', 300)  # 5 minutes default
        self.market_hours_only = scheduling_config.get('market_hours_only', True)
        
        self.logger.info(f"Scheduler initialized with {self.update_interval}s interval")
    
    def set_update_callback(self, callback: Callable):
        """
        Set the callback function for scheduled updates.
        
        Args:
            callback: Function to call on scheduled updates
        """
        self.update_callback = callback
        self.logger.info("Update callback set")
    
    def start_scheduled_mode(self):
        """Start scheduled execution mode."""
        try:
            if not self.update_callback:
                raise TradingBotError("No update callback set")
            
            # Add scheduled job
            if self.market_hours_only:
                # Schedule for market hours (9:30 AM - 4:00 PM EST, Monday-Friday)
                self.scheduler.add_job(
                    func=self._scheduled_update,
                    trigger=CronTrigger(
                        day_of_week='mon-fri',
                        hour='9-16',
                        minute='*/5',  # Every 5 minutes
                        timezone='US/Eastern'
                    ),
                    id='market_hours_update',
                    max_instances=1
                )
                self.logger.info("Scheduled for market hours only (9:30 AM - 4:00 PM EST, Mon-Fri)")
            else:
                # Schedule for continuous operation
                self.scheduler.add_job(
                    func=self._scheduled_update,
                    trigger=IntervalTrigger(seconds=self.update_interval),
                    id='continuous_update',
                    max_instances=1
                )
                self.logger.info(f"Scheduled for continuous operation every {self.update_interval} seconds")
            
            self.is_running = True
            self.logger.info("Starting scheduled mode...")
            self.scheduler.start()
            
        except KeyboardInterrupt:
            self.logger.info("Scheduler interrupted by user")
            self.stop()
        except Exception as e:
            self.logger.error(f"Scheduler failed to start: {e}")
            raise TradingBotError(f"Scheduler startup failed: {e}")
    
    def _scheduled_update(self):
        """Execute scheduled update."""
        try:
            start_time = datetime.now()
            self.logger.info("Starting scheduled update...")
            
            # Call the update callback
            if self.update_callback:
                result = self.update_callback()
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                self.logger.info(f"Scheduled update completed in {duration:.2f} seconds")
                
                # Log results if available
                if isinstance(result, dict):
                    processed_count = result.get('processed_symbols', 0)
                    signals_generated = result.get('signals_generated', 0)
                    self.logger.info(f"Processed {processed_count} symbols, generated {signals_generated} signals")
            
        except Exception as e:
            self.logger.error(f"Scheduled update failed: {e}")
            # Continue with next scheduled update instead of stopping
    
    def run_manual_update(self):
        """Run manual update immediately."""
        try:
            if not self.update_callback:
                raise TradingBotError("No update callback set")
            
            self.logger.info("Starting manual update...")
            start_time = datetime.now()
            
            result = self.update_callback()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.info(f"Manual update completed in {duration:.2f} seconds")
            
            if isinstance(result, dict):
                processed_count = result.get('processed_symbols', 0)
                signals_generated = result.get('signals_generated', 0)
                self.logger.info(f"Processed {processed_count} symbols, generated {signals_generated} signals")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Manual update failed: {e}")
            raise TradingBotError(f"Manual update failed: {e}")
    
    def stop(self):
        """Stop the scheduler."""
        try:
            if self.is_running:
                self.scheduler.shutdown(wait=False)
                self.is_running = False
                self.logger.info("Scheduler stopped")
        except Exception as e:
            self.logger.error(f"Error stopping scheduler: {e}")
    
    def is_market_hours(self) -> bool:
        """
        Check if current time is within market hours.
        
        Returns:
            True if within market hours
        """
        try:
            now = datetime.now()
            
            # Check if it's a weekday (Monday = 0, Sunday = 6)
            if now.weekday() >= 5:  # Saturday or Sunday
                return False
            
            # Check if it's within market hours (9:30 AM - 4:00 PM EST)
            market_open = dt_time(9, 30)
            market_close = dt_time(16, 0)
            current_time = now.time()
            
            return market_open <= current_time <= market_close
            
        except Exception as e:
            self.logger.error(f"Error checking market hours: {e}")
            return True  # Default to True to allow operation
    
    def get_next_run_time(self) -> datetime:
        """
        Get the next scheduled run time.
        
        Returns:
            Next scheduled execution time
        """
        try:
            jobs = self.scheduler.get_jobs()
            if jobs:
                return jobs[0].next_run_time
            return None
        except Exception as e:
            self.logger.error(f"Error getting next run time: {e}")
            return None
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        Get scheduler status information.
        
        Returns:
            Dictionary with scheduler status
        """
        try:
            return {
                'is_running': self.is_running,
                'update_interval': self.update_interval,
                'market_hours_only': self.market_hours_only,
                'next_run_time': self.get_next_run_time(),
                'is_market_hours': self.is_market_hours(),
                'job_count': len(self.scheduler.get_jobs()) if self.is_running else 0
            }
        except Exception as e:
            self.logger.error(f"Error getting scheduler status: {e}")
            return {'error': str(e)}