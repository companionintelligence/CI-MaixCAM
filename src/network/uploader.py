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

import requests

from utils.logger import get_logger
from utils.time_utils import get_iso_timestamp
from utils.device import get_stable_device_id
from network.network_manager import NetworkManager

logger = get_logger('NetworkUploader')

# Identifies this app to CI-Server's ingest plane, distinguishing MaixCAM
# events from other capture clients (e.g. "ci-applet" for the desktop app).
SOURCE_SYSTEM = "ci-maixcam"

# CI-Server's /v1 ingest routes are reverse-proxied with an /api prefix on
# some deployments and without it on others (the same ambiguity documented
# against CI-Capture, the platform's other capture-surface client). Try the
# bare path first, then the /api-prefixed one.
EVENTS_PATHS = ("/v1/events", "/api/v1/events")
FINISH_PATHS = ("/v1/ingest/finish", "/api/v1/ingest/finish")


def build_capture_event(event, device_id, source_system=SOURCE_SYSTEM):
    """Turn one of DataLogger's logged events into a CI-Server CaptureEvent

    Matches the wire envelope CI-Server's `/v1/events` lane expects: a
    provenance triple it dedupes on for idempotent re-POST, an open-text
    `kind`, and the original detection payload passed through untouched.
    """
    occurred_at = event.get("timestamp") or get_iso_timestamp()
    payload = dict(event.get("data", {}))
    payload["device_id"] = device_id

    capture_event = {
        "source_type": "capture",
        "source_system": source_system,
        "source_id": f"{source_system}:{device_id}:{event.get('event_id') or occurred_at}",
        "kind": event.get("type", "unknown"),
        "occurred_at": occurred_at,
        "observed_at": occurred_at,
        "payload": payload,
    }

    # Optional string fields: omit entirely rather than send `null` when
    # absent. CI-Server's schema accepts a missing key but rejects an
    # explicit null - the same gotcha CI-Capture had to fix on its own
    # vizier lane.
    model = event.get("model")
    if model:
        capture_event["title"] = model

    confidence_scores = event.get("confidence_scores") or []
    if confidence_scores:
        capture_event["confidence_score"] = max(confidence_scores)

    return capture_event


class NetworkUploader:
    """Uploads locally logged AI events to CI-Server's /v1 ingest plane"""

    def __init__(self, config):
        """Initialize network uploader"""
        self.config = config
        self.network_config = config.get_network_config()

        # Upload configuration
        self.enabled = self.network_config.get("upload_enabled", False)
        self.endpoint_url = self.network_config.get("endpoint_url", "").rstrip("/")
        self.api_key = self.network_config.get("api_key", "")
        self.upload_interval = self.network_config.get("upload_interval_seconds", 300)
        self.batch_size = self.network_config.get("batch_size", 50)
        self.retry_attempts = self.network_config.get("retry_attempts", 3)
        self.retry_delay = self.network_config.get("retry_delay_seconds", 30)
        self.timeout = self.network_config.get("timeout_seconds", 30)

        self.network_manager = NetworkManager()

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
                # Check for files to upload, but only when Wi-Fi is actually
                # associated - otherwise every attempt just burns its retry
                # budget against a dead link.
                if self.network_manager.is_connected():
                    self._process_upload_queue()
                else:
                    logger.debug("Wi-Fi not connected, skipping this upload cycle")

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
        """Upload every event in one session file to CI-Server, with retries"""
        for attempt in range(self.retry_attempts):
            try:
                with open(file_path, 'r') as f:
                    session_data = json.load(f)

                events = session_data.get("events", [])
                if not events:
                    logger.debug(f"No events to upload in {file_path}")
                    return True

                device_id = get_stable_device_id(self.config)
                capture_events = [build_capture_event(e, device_id) for e in events]

                if self._post_events(capture_events):
                    logger.info(f"Successfully uploaded {len(capture_events)} events: {file_path}")
                    self._call_ingest_finish()
                    return True

            except Exception as e:
                logger.error(f"Upload attempt {attempt + 1} failed for {file_path}: {e}")
                self.upload_stats["last_error"] = str(e)

            # Wait before retry
            if attempt < self.retry_attempts - 1:
                time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff

        logger.error(f"All upload attempts failed for: {file_path}")
        return False

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    def _post_with_fallback(self, paths, json_body):
        """POST to the first of `paths` that resolves; try the next only on a 404

        Mirrors CI-Capture's own bare-path-then-/api-prefixed probing, since
        whether a deployment's ingress strips /api before it reaches
        CI-Server varies. A connection-level failure or a non-404 error
        response is reported immediately rather than masked by a retry
        against the same unreachable host.
        """
        error = None
        for i, path in enumerate(paths):
            url = f"{self.endpoint_url}{path}"
            try:
                response = requests.post(
                    url, json=json_body, headers=self._headers(), timeout=self.timeout
                )
            except requests.exceptions.RequestException as e:
                error = e
                break

            if response.status_code == 404 and i < len(paths) - 1:
                continue

            if response.ok:
                return True

            error = f"HTTP {response.status_code}: {response.text[:200]}"
            break

        logger.error(f"POST to {self.endpoint_url} {paths} failed: {error}")
        return False

    def _post_events(self, capture_events):
        """POST a batch of CaptureEvents as CI-Server's {"events": [...]} envelope"""
        if not self.endpoint_url:
            logger.error("No endpoint URL configured")
            return False
        return self._post_with_fallback(EVENTS_PATHS, {"events": capture_events})

    def _call_ingest_finish(self):
        """Best-effort nudge for CI-Server's enrichment/search-index sweep

        Not fatal when it fails: CI-Server runs the same sweep on its own
        ~60s later regardless (its coalesce backstop), so a dropped nudge
        here only costs latency, not data.
        """
        try:
            self._post_with_fallback(FINISH_PATHS, {})
        except Exception as e:
            logger.debug(f"ingest/finish nudge failed (self-heals server-side): {e}")
    
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
        self.endpoint_url = url.rstrip("/")
        self.api_key = api_key

        # Update config
        self.config.set("network.endpoint_url", self.endpoint_url)
        self.config.set("network.api_key", api_key)
        self.config.save_config()

        logger.info(f"Upload endpoint set to: {self.endpoint_url}")
    
    def cleanup(self):
        """Clean up uploader resources"""
        logger.info("Cleaning up Network Uploader...")
        self.stop()
        logger.info("Network Uploader cleanup completed")
