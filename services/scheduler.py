import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
import logging

class FloodScheduler:
    """Service for scheduling automated flood detection updates"""
    
    def __init__(self):
        """Initialize the flood scheduler"""
        self.is_running = False
        self.scheduler_thread = None
        self.update_interval_seconds = 3600  # Default: 1 hour (3600 seconds)
        self.callbacks = {}
        self.last_update = None
        self.start_time = None
        self.update_count = 0
        self.successful_updates = 0
        self.failed_updates = 0
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def start_monitoring(self, location: Dict[str, Any], 
                        update_callback: Callable = None,
                        interval_seconds: int = 3600) -> bool:
        """
        Start automated flood monitoring for a location
        
        Args:
            location: Location dictionary with lat, lon, name
            update_callback: Function to call when updates are available
            interval_seconds: Update interval in seconds
            
        Returns:
            Boolean indicating if monitoring started successfully
        """
        try:
            if self.is_running:
                self.logger.info("Stopping existing monitoring before starting new session")
                self.stop_monitoring()
            
            self.update_interval = interval_seconds
            self.current_location = location
            
            if update_callback:
                self.callbacks['update'] = update_callback
            
            # Start the monitoring thread
            self.is_running = True
            self.scheduler_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.scheduler_thread.start()
            
            self.logger.info(f"Started flood monitoring for {location.get('name', 'Unknown')} "
                           f"with {interval_seconds}s interval")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {str(e)}")
            return False
    
    def stop_monitoring(self) -> bool:
        """
        Stop automated flood monitoring
        
        Returns:
            Boolean indicating if monitoring stopped successfully
        """
        try:
            if not self.is_running:
                return True
            
            self.is_running = False
            
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5.0)
            
            self.logger.info("Flood monitoring stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping monitoring: {str(e)}")
            return False
    
    def _monitoring_loop(self):
        """Main monitoring loop that runs in a separate thread"""
        self.logger.info("Monitoring loop started")
        
        while self.is_running:
            try:
                # Check if it's time for an update
                current_time = datetime.now()
                
                if (self.last_update is None or 
                    (current_time - self.last_update).total_seconds() >= self.update_interval):
                    
                    self.logger.info("Triggering scheduled flood analysis update")
                    
                    # Call the update callback if available
                    if 'update' in self.callbacks:
                        try:
                            self.callbacks['update'](self.current_location)
                            self.last_update = current_time
                            self.logger.info("Scheduled update completed successfully")
                        except Exception as e:
                            self.logger.error(f"Update callback failed: {str(e)}")
                    else:
                        self.logger.warning("No update callback registered")
                        self.last_update = current_time
                
                # Sleep for a short interval before checking again
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(60)  # Continue after error
        
        self.logger.info("Monitoring loop ended")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current monitoring status
        
        Returns:
            Dictionary with current status information
        """
        try:
            status = {
                'is_monitoring': self.is_running,
                'update_interval_seconds': self.update_interval,
                'update_interval_minutes': self.update_interval // 60,
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'current_location': getattr(self, 'current_location', None),
                'thread_alive': self.scheduler_thread.is_alive() if self.scheduler_thread else False
            }
            
            # Calculate next update time
            if self.last_update and self.is_running:
                next_update = self.last_update + timedelta(seconds=self.update_interval)
                status['next_update'] = next_update.isoformat()
                status['time_until_next_update_minutes'] = max(0, 
                    (next_update - datetime.now()).total_seconds() // 60)
            else:
                status['next_update'] = None
                status['time_until_next_update_minutes'] = None
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting status: {str(e)}")
            return {
                'is_monitoring': False,
                'error': str(e)
            }
    
    def update_interval(self, new_interval_seconds: int) -> bool:
        """
        Update the monitoring interval
        
        Args:
            new_interval_seconds: New interval in seconds
            
        Returns:
            Boolean indicating if update was successful
        """
        try:
            if new_interval_seconds < 300:  # Minimum 5 minutes
                self.logger.warning("Minimum update interval is 5 minutes (300 seconds)")
                return False
            
            self.update_interval = new_interval_seconds
            self.logger.info(f"Update interval changed to {new_interval_seconds} seconds")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating interval: {str(e)}")
            return False
    
    def force_update(self) -> bool:
        """
        Force an immediate update (reset the timer)
        
        Returns:
            Boolean indicating if force update was triggered
        """
        try:
            if not self.is_running:
                self.logger.warning("Cannot force update - monitoring is not running")
                return False
            
            # Reset last update time to trigger immediate update
            self.last_update = None
            self.logger.info("Forced update triggered")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error forcing update: {str(e)}")
            return False
    
    def register_callback(self, callback_name: str, callback_function: Callable) -> bool:
        """
        Register a callback function for specific events
        
        Args:
            callback_name: Name of the callback (e.g., 'update', 'error', 'status')
            callback_function: Function to call
            
        Returns:
            Boolean indicating if registration was successful
        """
        try:
            self.callbacks[callback_name] = callback_function
            self.logger.info(f"Registered callback: {callback_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering callback: {str(e)}")
            return False
    
    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """
        Get monitoring statistics and performance metrics
        
        Returns:
            Dictionary with monitoring statistics
        """
        try:
            stats = {
                'monitoring_active': self.is_running,
                'start_time': getattr(self, 'start_time', None),
                'total_updates': getattr(self, 'update_count', 0),
                'successful_updates': getattr(self, 'successful_updates', 0),
                'failed_updates': getattr(self, 'failed_updates', 0),
                'average_update_interval_actual': self.update_interval,
                'last_update_timestamp': self.last_update.isoformat() if self.last_update else None
            }
            
            # Calculate uptime
            if hasattr(self, 'start_time') and self.start_time:
                uptime_seconds = (datetime.now() - self.start_time).total_seconds()
                stats['uptime_hours'] = uptime_seconds / 3600
                stats['uptime_formatted'] = f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m"
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting statistics: {str(e)}")
            return {'error': str(e)}
    
    def set_priority_mode(self, high_priority: bool = True) -> bool:
        """
        Enable or disable high-priority monitoring mode
        
        Args:
            high_priority: If True, reduces update interval for urgent monitoring
            
        Returns:
            Boolean indicating if priority mode was set
        """
        try:
            if high_priority:
                # High priority: update every 15 minutes
                new_interval = 900
                self.logger.info("Enabled high-priority monitoring mode (15-minute intervals)")
            else:
                # Normal priority: update every hour
                new_interval = 3600
                self.logger.info("Disabled high-priority monitoring mode (1-hour intervals)")
            
            return self.update_interval(new_interval)
            
        except Exception as e:
            self.logger.error(f"Error setting priority mode: {str(e)}")
            return False