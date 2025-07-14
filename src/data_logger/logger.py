"""
Data Logger
Handles logging of AI detection events to JSON files

Author: Companion Intelligence
Date: July 13, 2025
"""

import os
import json
import time
import uuid
from datetime import datetime
from utils.logger import get_logger
from utils.time_utils import get_time_ms, get_free_memory
from utils.time_utils import get_time_ms, get_iso_timestamp

logger = get_logger('DataLogger')

class DataLogger:
    """Data logger for AI detection events"""
    
    def __init__(self, config):
        """Initialize data logger"""
        self.config = config
        self.storage_config = config.get_storage_config()
        
        # Storage paths
        self.base_path = self.storage_config.get("base_path", "/sd/logs")
        self.current_session_file = None
        self.current_session_id = None
        
        # Session state
        self.session_active = False
        self.events_logged = 0
        self.session_start_time = None
        
        # Performance tracking
        self.total_events_logged = 0
        self.total_storage_used = 0
        
        # Create base directory
        os.makedirs(self.base_path, exist_ok=True)
        
        logger.info("Data Logger initialized")
    
    def start_session(self):
        """Start a new logging session"""
        if self.session_active:
            logger.warning("Session already active, ending previous session")
            self.end_session()
        
        # Generate session ID and filename
        self.session_start_time = datetime.now()
        self.current_session_id = str(uuid.uuid4())
        
        timestamp = self.session_start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"session_{timestamp}_{self.current_session_id[:8]}.json"
        self.current_session_file = os.path.join(self.base_path, filename)
        
        # Create session metadata
        session_metadata = {
            "session_id": self.current_session_id,
            "start_time": self.session_start_time.isoformat(),
            "device_info": self._get_device_info(),
            "app_version": self.config.get("app.version", "1.0.0"),
            "events": []
        }
        
        # Write initial session file
        try:
            with open(self.current_session_file, 'w') as f:
                json.dump(session_metadata, f, indent=2)
            
            self.session_active = True
            self.events_logged = 0
            
            logger.info(f"Started logging session: {self.current_session_id}")
            logger.info(f"Session file: {self.current_session_file}")
            
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            self.session_active = False
    
    def end_session(self):
        """End current logging session"""
        if not self.session_active:
            logger.warning("No active session to end")
            return
        
        try:
            # Update session metadata
            session_end_time = datetime.now()
            duration = (session_end_time - self.session_start_time).total_seconds()
            
            # Read current session file
            with open(self.current_session_file, 'r') as f:
                session_data = json.load(f)
            
            # Update metadata
            session_data.update({
                "end_time": session_end_time.isoformat(),
                "duration_seconds": duration,
                "total_events": self.events_logged,
                "events_per_minute": (self.events_logged / (duration / 60)) if duration > 0 else 0
            })
            
            # Write updated session file
            with open(self.current_session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logger.info(f"Ended logging session: {self.current_session_id}")
            logger.info(f"Session duration: {duration:.1f} seconds")
            logger.info(f"Events logged: {self.events_logged}")
            
            # Cleanup
            self.session_active = False
            self.current_session_file = None
            self.current_session_id = None
            self.events_logged = 0
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
    
    def log_events(self, events):
        """Log a list of AI detection events"""
        if not self.session_active:
            logger.warning("No active session, cannot log events")
            return
        
        if not events:
            return
        
        try:
            # Read current session file
            with open(self.current_session_file, 'r') as f:
                session_data = json.load(f)
            
            # Process and add events
            for event in events:
                processed_event = self._process_event(event)
                session_data["events"].append(processed_event)
                self.events_logged += 1
                self.total_events_logged += 1
            
            # Write updated session file atomically
            temp_file = self.current_session_file + ".tmp"
            with open(temp_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            # Atomic rename
            os.rename(temp_file, self.current_session_file)
            
            logger.debug(f"Logged {len(events)} events")
            
            # Check storage limits
            self._check_storage_limits()
            
        except Exception as e:
            logger.error(f"Error logging events: {e}")
    
    def _process_event(self, event):
        """Process and standardize an event before logging"""
        # Generate unique event ID
        event_id = str(uuid.uuid4())
        
        # Standardize timestamp
        if "timestamp" in event:
            # Convert ticks_ms to ISO format
            timestamp_ms = event["timestamp"]
            # Note: This is a simplified conversion, real implementation would need proper time handling
            timestamp_iso = datetime.now().isoformat()
        else:
            timestamp_iso = datetime.now().isoformat()
        
        # Create standardized event structure
        processed_event = {
            "event_id": event_id,
            "timestamp": timestamp_iso,
            "timestamp_ms": event.get("timestamp", get_time_ms()),
            "session_id": self.current_session_id,
            "type": event.get("type", "unknown"),
            "model": event.get("model", "unknown"),
            "confidence_scores": self._extract_confidence_scores(event),
            "data": self._extract_event_data(event),
            "metadata": {
                "device_info": self._get_device_info(),
                "processing_time_ms": event.get("processing_time_ms"),
                "memory_usage": self._get_memory_usage()
            }
        }
        
        return processed_event
    
    def _extract_confidence_scores(self, event):
        """Extract confidence scores from event"""
        scores = []
        
        if event.get("type") == "object_detection":
            for obj in event.get("objects", []):
                scores.append(obj.get("confidence", 0))
        
        elif event.get("type") == "face_detection":
            for face in event.get("faces", []):
                scores.append(face.get("confidence", 0))
        
        elif event.get("type") == "pose_detection":
            for pose in event.get("poses", []):
                scores.append(pose.get("confidence", 0))
        
        return scores
    
    def _extract_event_data(self, event):
        """Extract relevant data from event"""
        # Remove metadata that's handled separately
        data = event.copy()
        data.pop("timestamp", None)
        data.pop("processing_time_ms", None)
        
        return data
    
    def _get_device_info(self):
        """Get device information"""
        return {
            "device_type": "MaixCAM",
            "firmware_version": "unknown",  # Would be populated from actual device
            "app_version": self.config.get("app.version", "1.0.0")
        }
    
    def _get_memory_usage(self):
        """Get current memory usage"""
        try:
            return {
                "free_bytes": get_free_memory(),
                "used_bytes": None  # Would need system-specific implementation
            }
        except:
            return None
    
    def _check_storage_limits(self):
        """Check and enforce storage limits"""
        try:
            # Check file size
            if os.path.exists(self.current_session_file):
                file_size = os.path.getsize(self.current_session_file)
                max_size = self.storage_config.get("max_log_size_mb", 100) * 1024 * 1024
                
                if file_size > max_size:
                    logger.warning(f"Session file size exceeded limit: {file_size} bytes")
                    # Could implement file rotation here
            
            # Check total storage usage
            self._cleanup_old_files()
            
        except Exception as e:
            logger.error(f"Error checking storage limits: {e}")
    
    def _cleanup_old_files(self):
        """Clean up old log files if needed"""
        if not self.storage_config.get("cleanup_old_files", True):
            return
        
        try:
            # Get all log files
            log_files = []
            for filename in os.listdir(self.base_path):
                if filename.startswith("session_") and filename.endswith(".json"):
                    filepath = os.path.join(self.base_path, filename)
                    file_stat = os.stat(filepath)
                    log_files.append((filepath, file_stat.st_mtime))
            
            # Sort by modification time (oldest first)
            log_files.sort(key=lambda x: x[1])
            
            # Calculate total storage usage
            total_size = sum(os.path.getsize(f[0]) for f in log_files)
            max_storage = self.storage_config.get("max_storage_usage_percent", 80)
            
            # Get available space (simplified check)
            # In real implementation, would check actual filesystem usage
            if len(log_files) > 10:  # Simple cleanup: keep only 10 most recent files
                files_to_delete = log_files[:-10]
                for filepath, _ in files_to_delete:
                    if filepath != self.current_session_file:  # Don't delete current session
                        os.remove(filepath)
                        logger.info(f"Deleted old log file: {filepath}")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_storage_usage(self):
        """Get current storage usage in bytes"""
        try:
            total_size = 0
            for filename in os.listdir(self.base_path):
                if filename.startswith("session_") and filename.endswith(".json"):
                    filepath = os.path.join(self.base_path, filename)
                    total_size += os.path.getsize(filepath)
            return total_size
        except:
            return 0
    
    def get_session_stats(self):
        """Get current session statistics"""
        return {
            "session_active": self.session_active,
            "session_id": self.current_session_id,
            "events_logged": self.events_logged,
            "total_events_logged": self.total_events_logged,
            "storage_used": self.get_storage_usage(),
            "session_file": self.current_session_file
        }
