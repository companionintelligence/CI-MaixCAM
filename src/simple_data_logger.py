#!/usr/bin/env python3
"""
Simple Data Logger for AI Events
Logs AI detection events to JSON files

Author: Companion Intelligence
Date: July 14, 2025
"""

import json
import os
from maix import time as maix_time

class SimpleDataLogger:
    """Simple data logger for AI detection events"""
    
    def __init__(self, log_dir="/sd/companion_logs"):
        self.log_dir = log_dir
        self.current_session = None
        self.session_file = None
        self.events_logged = 0
        
        # Ensure log directory exists
        self._ensure_log_directory()
    
    def _ensure_log_directory(self):
        """Create log directory if it doesn't exist"""
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            print(f"📁 Log directory ready: {self.log_dir}")
        except Exception as e:
            print(f"❌ Failed to create log directory: {e}")
            # Fallback to current directory
            self.log_dir = "."
    
    def start_session(self):
        """Start a new logging session"""
        try:
            # Create session timestamp
            timestamp = maix_time.time()
            session_id = f"session_{int(timestamp)}"
            
            # Create session info
            self.current_session = {
                "session_id": session_id,
                "start_time": timestamp,
                "start_time_readable": self._format_timestamp(timestamp),
                "events": [],
                "active_models": [],
                "total_events": 0
            }
            
            # Create session file
            filename = f"{session_id}.json"
            self.session_file = os.path.join(self.log_dir, filename)
            
            # Save initial session file
            self._save_session()
            
            self.events_logged = 0
            print(f"📊 Started logging session: {session_id}")
            return session_id
            
        except Exception as e:
            print(f"❌ Failed to start session: {e}")
            return None
    
    def log_events(self, events):
        """Log AI detection events"""
        if not self.current_session:
            return
        
        try:
            for event in events:
                # Add event to session
                enhanced_event = {
                    **event,
                    "event_id": len(self.current_session["events"]) + 1,
                    "session_time": maix_time.time() - self.current_session["start_time"]
                }
                
                self.current_session["events"].append(enhanced_event)
                self.events_logged += 1
            
            # Update session totals
            self.current_session["total_events"] = len(self.current_session["events"])
            
            # Save session file (every 10 events to avoid excessive writes)
            if self.events_logged % 10 == 0:
                self._save_session()
            
            print(f"📝 Logged {len(events)} events (total: {self.current_session['total_events']})")
            
        except Exception as e:
            print(f"❌ Failed to log events: {e}")
    
    def end_session(self):
        """End current logging session"""
        if not self.current_session:
            return
        
        try:
            # Update session end time
            end_time = maix_time.time()
            self.current_session["end_time"] = end_time
            self.current_session["end_time_readable"] = self._format_timestamp(end_time)
            self.current_session["duration_seconds"] = end_time - self.current_session["start_time"]
            
            # Final save
            self._save_session()
            
            session_id = self.current_session["session_id"]
            total_events = self.current_session["total_events"]
            duration = self.current_session["duration_seconds"]
            
            print(f"🏁 Ended session {session_id}: {total_events} events in {duration:.1f}s")
            
            # Clear current session
            self.current_session = None
            self.session_file = None
            self.events_logged = 0
            
        except Exception as e:
            print(f"❌ Failed to end session: {e}")
    
    def _save_session(self):
        """Save current session to file"""
        if not self.current_session or not self.session_file:
            return
        
        try:
            with open(self.session_file, 'w') as f:
                json.dump(self.current_session, f, indent=2)
                
        except Exception as e:
            print(f"❌ Failed to save session: {e}")
    
    def _format_timestamp(self, timestamp):
        """Format timestamp for readability"""
        # Simple formatting since we don't have datetime module
        return f"timestamp_{int(timestamp)}"
    
    def get_storage_info(self):
        """Get storage information"""
        try:
            total_files = len([f for f in os.listdir(self.log_dir) if f.endswith('.json')])
            current_events = self.current_session["total_events"] if self.current_session else 0
            
            return {
                "log_directory": self.log_dir,
                "total_sessions": total_files,
                "current_session_events": current_events,
                "current_session_active": self.current_session is not None
            }
        except:
            return {
                "log_directory": self.log_dir,
                "total_sessions": 0,
                "current_session_events": 0,
                "current_session_active": False
            }
