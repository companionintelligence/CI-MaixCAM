"""
Network Uploader
Handles uploading of JSON logs to remote server via REST API

Author: Companion Intelligence
Date: July 13, 2025
"""

import os
import json
import time
import threading
from queue import Queue, Empty
from utils.logger import get_logger

logger = get_logger('NetworkUploader')

class NetworkUploader:
    """Network uploader for JSON logs"""
    
    def __init__(self, config):
        """Initialize network uploader"""
        self.config = config
        self.network_config = config.get_network_config()
        
        # Upload configuration
        self.enabled = self.network_config.get("upload_enabled", False)
        self.endpoint_url = self.network_config.get("endpoint_url", "")
        self.api_key = self.network_config.get("api_key", "")
        self.upload_interval = self.network_config.get("upload_interval_seconds", 300)
        self.batch_size = self.network_config.get("batch_size", 50)
        self.retry_attempts = self.network_config.get("retry_attempts", 3)
        self.retry_delay = self.network_config.get("retry_delay_seconds", 30)
        self.timeout = self.network_config.get("timeout_seconds", 30)
        
        # Upload queue and threading
        self.upload_queue = Queue()
        self.upload_thread = None
        self.running = False
        
        # Statistics
        self.upload_stats = {
            "total_uploads": 0,
            "successful_uploads": 0,
            "failed_uploads": 0,
            "last_upload_time": None,
            "last_error": None
        }
        
        # Start upload thread if enabled
        if self.enabled and self.endpoint_url:
            self.start()
        
        logger.info(f"Network Uploader initialized (enabled: {self.enabled})")
    
    def start(self):
        """Start the upload thread"""
        if self.running:
            logger.warning("Upload thread already running")
            return
        
        if not self.enabled:
            logger.info("Upload disabled, not starting thread")
            return
        
        self.running = True
        self.upload_thread = threading.Thread(target=self._upload_worker, daemon=True)
        self.upload_thread.start()
        
        logger.info("Upload thread started")
    
    def stop(self):
        """Stop the upload thread"""
        if not self.running:
            return
        
        self.running = False
        if self.upload_thread and self.upload_thread.is_alive():
            self.upload_thread.join(timeout=5)
        
        logger.info("Upload thread stopped")
    
    def queue_file_for_upload(self, file_path):
        """Queue a log file for upload"""
        if not self.enabled:
            return
        
        if not os.path.exists(file_path):
            logger.error(f"File not found for upload: {file_path}")
            return
        
        try:
            self.upload_queue.put(file_path, block=False)
            logger.debug(f"Queued file for upload: {file_path}")
        except Exception as e:
            logger.error(f"Failed to queue file: {e}")
    
    def _upload_worker(self):
        """Background worker thread for uploads"""
        logger.info("Upload worker thread started")
        
        while self.running:
            try:
                # Check for files to upload
                self._process_upload_queue()
                
                # Sleep for upload interval
                time.sleep(self.upload_interval)
                
            except Exception as e:
                logger.error(f"Upload worker error: {e}")
                time.sleep(10)  # Short delay before retrying
        
        logger.info("Upload worker thread stopped")
    
    def _process_upload_queue(self):
        """Process files in upload queue"""
        files_to_upload = []
        
        # Collect files from queue (up to batch size)
        while len(files_to_upload) < self.batch_size:
            try:
                file_path = self.upload_queue.get(block=False, timeout=1)
                if os.path.exists(file_path):
                    files_to_upload.append(file_path)
                else:
                    logger.warning(f"File no longer exists: {file_path}")
            except Empty:
                break
        
        # Upload files if any
        if files_to_upload:
            self._upload_files(files_to_upload)
    
    def _upload_files(self, file_paths):
        """Upload a batch of files"""
        logger.info(f"Uploading {len(file_paths)} files")
        
        for file_path in file_paths:
            success = self._upload_single_file(file_path)
            
            if success:
                self.upload_stats["successful_uploads"] += 1
                # Move to uploaded folder
                self._move_uploaded_file(file_path)
            else:
                self.upload_stats["failed_uploads"] += 1
                # Re-queue for retry (with backoff)
                # For now, just log the failure
                logger.error(f"Failed to upload file: {file_path}")
            
            self.upload_stats["total_uploads"] += 1
        
        self.upload_stats["last_upload_time"] = time.time()
    
    def _upload_single_file(self, file_path):
        """Upload a single file with retries"""
        for attempt in range(self.retry_attempts):
            try:
                # Read file data
                with open(file_path, 'r') as f:
                    file_data = json.load(f)
                
                # Prepare upload payload
                payload = {
                    "device_id": self._get_device_id(),
                    "upload_timestamp": time.time(),
                    "file_name": os.path.basename(file_path),
                    "data": file_data
                }
                
                # Mock HTTP request (would use actual HTTP library in real implementation)
                success = self._mock_http_post(payload)
                
                if success:
                    logger.info(f"Successfully uploaded: {file_path}")
                    return True
                
            except Exception as e:
                logger.error(f"Upload attempt {attempt + 1} failed for {file_path}: {e}")
                self.upload_stats["last_error"] = str(e)
            
            # Wait before retry
            if attempt < self.retry_attempts - 1:
                time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
        
        logger.error(f"All upload attempts failed for: {file_path}")
        return False
    
    def _mock_http_post(self, payload):
        """Mock HTTP POST request (replace with actual implementation)"""
        # In real implementation, would use libraries like urllib or requests
        # For now, simulate success/failure
        
        if not self.endpoint_url:
            logger.error("No endpoint URL configured")
            return False
        
        try:
            # Simulate network request
            logger.debug(f"Mock POST to {self.endpoint_url}")
            logger.debug(f"Payload size: {len(json.dumps(payload))} bytes")
            
            # Simulate success (90% success rate for testing)
            import random
            success = random.random() > 0.1
            
            if success:
                logger.debug("Mock upload successful")
            else:
                logger.debug("Mock upload failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Mock HTTP error: {e}")
            return False
    
    def _get_device_id(self):
        """Get unique device identifier"""
        # In real implementation, would get actual device ID
        return "maixcam_device_001"
    
    def _move_uploaded_file(self, file_path):
        """Move successfully uploaded file to uploaded folder"""
        try:
            uploaded_dir = os.path.join(os.path.dirname(file_path), "uploaded")
            os.makedirs(uploaded_dir, exist_ok=True)
            
            filename = os.path.basename(file_path)
            uploaded_path = os.path.join(uploaded_dir, filename)
            
            os.rename(file_path, uploaded_path)
            logger.debug(f"Moved uploaded file to: {uploaded_path}")
            
        except Exception as e:
            logger.error(f"Failed to move uploaded file: {e}")
    
    def get_upload_stats(self):
        """Get upload statistics"""
        stats = self.upload_stats.copy()
        stats["queue_size"] = self.upload_queue.qsize()
        stats["enabled"] = self.enabled
        stats["running"] = self.running
        return stats
    
    def enable_upload(self, enabled=True):
        """Enable or disable uploads"""
        self.enabled = enabled
        
        if enabled and not self.running:
            self.start()
        elif not enabled and self.running:
            self.stop()
        
        logger.info(f"Upload {'enabled' if enabled else 'disabled'}")
    
    def set_endpoint(self, url, api_key=""):
        """Set upload endpoint and API key"""
        self.endpoint_url = url
        self.api_key = api_key
        
        # Update config
        self.config.set("network.endpoint_url", url)
        self.config.set("network.api_key", api_key)
        self.config.save_config()
        
        logger.info(f"Upload endpoint set to: {url}")
    
    def cleanup(self):
        """Clean up uploader resources"""
        logger.info("Cleaning up Network Uploader...")
        self.stop()
        logger.info("Network Uploader cleanup completed")
