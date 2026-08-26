#!/usr/bin/env python3
"""
Companion Capture App - Main Entry Point
Life-logging application for Sipeed MaixCAM

This is the main application that orchestrates all components:
- Setup Screen for AI Model Selection
- UI Management
- AI Processing Engine
- Data Logging
- Network Upload

Author: Companion Intelligence
Date: July 14, 2025
Version: 1.1.0
"""

import sys
import os
import json
import gc
from maix import app, display, camera, touchscreen, time as maix_time, image
from setup_screen import run_setup_screen
from data_logger.logger import DataLogger
from utils.config import Config
from utils.models import default_model_states, migrate_model_states, read_model_states
from utils.paths import CONFIG_PATH, migrate_legacy_config

# Simplified logging for now
def log_info(msg):
    print(f"[INFO] {msg}")

def log_error(msg):
    print(f"[ERROR] {msg}")

class AIModelManager:
    """Manages all AI models and their states based on setup configuration"""
    
    def __init__(self, config_path=CONFIG_PATH):
        self.config_path = config_path
        self.active_models = {}
        self.model_processors = {}
        
        # Load configuration from setup screen
        self.load_configuration()
        
        # Initialize model processors
        self._initialize_model_processors()
    
    def load_configuration(self):
        """Load AI model configuration from setup screen"""
        try:
            # Pull forward a legacy config file if this device predates the
            # canonical path
            migrate_legacy_config(self.config_path)
            
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                # Fold an older build's duplicate enabled-state records into
                # model_states before reading it
                migrate_model_states(config)
                
                # Set active models based on configuration. model_states is
                # the one stored record of this; anything it omits falls back
                # to the same default the setup screen offers.
                self.active_models = read_model_states(config)
                
                log_info(f"Loaded configuration with {len([m for m in self.active_models.values() if m])} active models")
            else:
                log_error(f"Configuration file not found: {self.config_path}")
                # Set default models
                self._set_default_models()
                
        except Exception as e:
            log_error(f"Failed to load configuration: {e}")
            self._set_default_models()
    
    def _set_default_models(self):
        """Set default active models if no configuration found"""
        # The same defaults the setup screen shows, from utils/models.py
        self.active_models = default_model_states()
    
    def _initialize_model_processors(self):
        """Initialize processors for each active model"""
        
        # Computer Vision Models
        if self.active_models.get("Object Classification", False):
            self.model_processors["Object Classification"] = self._create_object_classifier()
        
        if self.active_models.get("Face Recognition", False):
            self.model_processors["Face Recognition"] = self._create_face_recognizer()
        
        if self.active_models.get("Face Emotion Detection", False):
            self.model_processors["Face Emotion Detection"] = self._create_emotion_detector()
        
        if self.active_models.get("Object Tracking and Counting", False):
            self.model_processors["Object Tracking and Counting"] = self._create_object_tracker()
        
        if self.active_models.get("OCR (Optical Character Recognition)", False):
            self.model_processors["OCR (Optical Character Recognition)"] = self._create_ocr_processor()
        
        if self.active_models.get("Hand Landmarks Detection", False):
            self.model_processors["Hand Landmarks Detection"] = self._create_hand_detector()
        
        if self.active_models.get("Human Pose Classification", False):
            self.model_processors["Human Pose Classification"] = self._create_pose_classifier()
        
        if self.active_models.get("Hand Gesture Classification", False):
            self.model_processors["Hand Gesture Classification"] = self._create_gesture_classifier()
        
        # Audio Processing Models
        if self.active_models.get("Audio Recording", False):
            self.model_processors["Audio Recording"] = self._create_audio_recorder()
        
        if self.active_models.get("Audio Playback", False):
            self.model_processors["Audio Playback"] = self._create_audio_player()
        
        if self.active_models.get("Real-time Voice Recognition", False):
            self.model_processors["Real-time Voice Recognition"] = self._create_voice_recognizer()
        
        # Media Capabilities
        if self.active_models.get("Video Recording", False):
            self.model_processors["Video Recording"] = self._create_video_recorder()
        
        if self.active_models.get("Video Playback", False):
            self.model_processors["Video Playback"] = self._create_video_player()
        
        active_count = len(self.model_processors)
        log_info(f"Initialized {active_count} AI model processors")
    
    # Model processor creation methods (to be implemented with actual AI models)
    def _create_object_classifier(self):
        log_info("✅ Object Classification processor ready")
        return {"type": "object_classification", "initialized": True}
    
    def _create_face_recognizer(self):
        log_info("✅ Face Recognition processor ready")
        return {"type": "face_recognition", "initialized": True}
    
    def _create_emotion_detector(self):
        log_info("✅ Face Emotion Detection processor ready")
        return {"type": "emotion_detection", "initialized": True}
    
    def _create_object_tracker(self):
        log_info("✅ Object Tracking and Counting processor ready")
        return {"type": "object_tracking", "initialized": True}
    
    def _create_ocr_processor(self):
        log_info("✅ OCR processor ready")
        return {"type": "ocr", "initialized": True}
    
    def _create_hand_detector(self):
        log_info("✅ Hand Landmarks Detection processor ready")
        return {"type": "hand_detection", "initialized": True}
    
    def _create_pose_classifier(self):
        log_info("✅ Human Pose Classification processor ready")
        return {"type": "pose_classification", "initialized": True}
    
    def _create_gesture_classifier(self):
        log_info("✅ Hand Gesture Classification processor ready")
        return {"type": "gesture_classification", "initialized": True}
    
    def _create_audio_recorder(self):
        log_info("✅ Audio Recording processor ready")
        return {"type": "audio_recording", "initialized": True}
    
    def _create_audio_player(self):
        log_info("✅ Audio Playback processor ready")
        return {"type": "audio_playback", "initialized": True}
    
    def _create_voice_recognizer(self):
        log_info("✅ Real-time Voice Recognition processor ready")
        return {"type": "voice_recognition", "initialized": True}
    
    def _create_video_recorder(self):
        log_info("✅ Video Recording processor ready")
        return {"type": "video_recording", "initialized": True}
    
    def _create_video_player(self):
        log_info("✅ Video Playback processor ready")
        return {"type": "video_playback", "initialized": True}
    
    def process_frame(self, img):
        """Process camera frame through all active AI models"""
        events = []
        
        # Process through each active model
        for model_name, processor in self.model_processors.items():
            try:
                if processor.get("initialized", False):
                    # Mock processing for now - replace with actual AI processing
                    event = self._mock_process(model_name, processor, img)
                    if event:
                        events.append(event)
            except Exception as e:
                log_error(f"Error processing {model_name}: {e}")
        
        return events
    
    def _mock_process(self, model_name, processor, img):
        """Mock AI processing - replace with actual model inference"""
        # For now, return mock detection every 60 frames for demo
        if hasattr(self, '_frame_count'):
            self._frame_count += 1
        else:
            self._frame_count = 0
        
        if self._frame_count % 60 == 0:  # Every 2 seconds at 30fps
            # Create event in format expected by existing DataLogger
            event = {
                "timestamp": maix_time.ticks_ms(),
                "type": self._get_event_type(processor["type"]),
                "model": model_name,
                "processing_time_ms": 15,  # Mock processing time
                "confidence": 0.85
            }
            
            # Add type-specific data structure
            if processor["type"] == "object_classification":
                event.update({
                    "objects": [
                        {
                            "class": "person",
                            "confidence": 0.85,
                            "bbox": [100, 100, 50, 100]
                        }
                    ]
                })
            elif processor["type"] == "face_recognition":
                event.update({
                    "faces": [
                        {
                            "confidence": 0.90,
                            "bbox": [150, 80, 60, 80],
                            "landmarks": [[160, 100], [180, 100], [170, 120]]
                        }
                    ]
                })
            elif processor["type"] == "audio_recording":
                event.update({
                    "audio_data": {
                        "duration_ms": 1000,
                        "sample_rate": 16000,
                        "channels": 1
                    }
                })
            elif processor["type"] == "video_recording":
                event.update({
                    "video_data": {
                        "frame_count": 30,
                        "duration_ms": 1000,
                        "resolution": "640x480"
                    }
                })
            else:
                event.update({
                    "details": f"Mock detection from {model_name}",
                    "raw_data": {"mock": True}
                })
            
            return event
        return None
    
    def _get_event_type(self, processor_type):
        """Map processor type to event type for DataLogger"""
        type_mapping = {
            "object_classification": "object_detection",
            "face_recognition": "face_detection", 
            "emotion_detection": "emotion_detection",
            "object_tracking": "object_tracking",
            "ocr": "ocr_detection",
            "hand_detection": "hand_landmarks",
            "pose_classification": "pose_detection",
            "gesture_classification": "gesture_detection",
            "audio_recording": "audio_event",
            "audio_playback": "audio_event",
            "voice_recognition": "voice_recognition",
            "video_recording": "video_event",
            "video_playback": "video_event"
        }
        return type_mapping.get(processor_type, "unknown_event")
    
    def get_active_models(self):
        """Get list of currently active model names"""
        return [name for name, active in self.active_models.items() if active]
    
    def get_model_count(self):
        """Get count of active models"""
        return len([active for active in self.active_models.values() if active])
class CompanionCaptureApp:
    """Main application class that coordinates all subsystems"""
    
    def __init__(self):
        """Initialize the application"""
        log_info("Starting Companion Capture App...")
        
        # Application state machine
        self.state = "INITIALIZING"
        self.states = ["INITIALIZING", "IDLE", "CAPTURING", "ERROR"]
        
        # Core configuration
        self.config = Config()
        
        # Initialize hardware components
        self.camera = None
        self.display = None
        self.touchscreen = None
        
        # Initialize AI model manager and data logger
        self.ai_manager = None
        self.data_logger = None
        
        # Performance monitoring
        self.frame_count = 0
        self.last_fps_time = maix_time.ticks_ms()
        self.fps = 0
        
        # UI state
        self.capturing = False
        
        # Initialize all components
        self._initialize_hardware()
        self._initialize_ai_manager()
        self._initialize_data_logger()
        
        log_info("Companion Capture App initialized successfully")
        self.state = "IDLE"
    
    def _initialize_hardware(self):
        """Initialize camera, display, and touchscreen"""
        try:
            # Initialize camera
            log_info("Initializing camera...")
            self.camera = camera.Camera(
                width=640, 
                height=480, 
                fps=30
            )
            log_info("Camera initialized successfully")
            
            # Initialize display
            log_info("Initializing display...")
            self.display = display.Display()
            log_info(f"Display initialized: {self.display.width()}x{self.display.height()}")
            
            # Initialize touchscreen
            log_info("Initializing touchscreen...")
            self.touchscreen = touchscreen.TouchScreen()
            log_info("Touchscreen initialized successfully")
            
        except Exception as e:
            log_error(f"Hardware initialization failed: {e}")
            self.state = "ERROR"
            raise
    
    def _initialize_ai_manager(self):
        """Initialize AI model manager with setup configuration"""
        try:
            log_info("Initializing AI Model Manager...")
            self.ai_manager = AIModelManager()
            log_info(f"AI Manager initialized with {self.ai_manager.get_model_count()} active models")
            
        except Exception as e:
            log_error(f"AI Manager initialization failed: {e}")
            self.state = "ERROR"
            raise
    
    def _initialize_data_logger(self):
        """Initialize data logger for AI events"""
        try:
            log_info("Initializing Data Logger...")
            self.data_logger = DataLogger(self.config)
            log_info("Data Logger initialized successfully")
            
        except Exception as e:
            log_error(f"Data Logger initialization failed: {e}")
            self.state = "ERROR"
            raise
    
    def _update_fps(self):
        """Update FPS counter"""
        self.frame_count += 1
        current_time = maix_time.ticks_ms()
        
        if maix_time.ticks_diff(current_time, self.last_fps_time) >= 1000:  # Update every second
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def _handle_touch_events(self):
        """Handle touch events for basic UI control"""
        x, y, pressed = self.touchscreen.read()
        
        if pressed:
            # Simple touch controls
            # Top-left corner: Toggle capture mode
            if x < 100 and y < 100:
                if not self.capturing:
                    # Start capturing
                    self.capturing = True
                    self.state = "CAPTURING"
                    self.data_logger.start_session()
                    log_info("🚀 Capture mode: STARTED")
                else:
                    # Stop capturing
                    self.capturing = False
                    self.state = "IDLE"
                    self.data_logger.end_session()
                    log_info("🛑 Capture mode: STOPPED")
                return True
            
            # Top-right corner: Exit app
            elif x > 540 and y < 100:
                log_info("Exit requested by touch")
                return False
        
        return True
    
    def _draw_ui(self, img):
        """Draw simple UI overlay on camera image"""
        
        # Status bar background
        img.draw_rect(0, 0, 640, 30, image.Color.from_rgb(0, 0, 0), -1)
        
        # Frame counter and FPS
        status_text = f"Frame: {self.frame_count} | FPS: {self.fps}"
        img.draw_string(10, 8, status_text, image.Color.from_rgb(255, 255, 255))
        
        # Active models count
        model_count = self.ai_manager.get_model_count()
        models_text = f"AI Models: {model_count}"
        img.draw_string(300, 8, models_text, image.Color.from_rgb(0, 255, 0))
        
        # Capture state
        state_color = (255, 0, 0) if self.capturing else (100, 100, 100)
        state_text = f"State: {self.state}"
        img.draw_string(500, 8, state_text, image.Color.from_rgb(*state_color))
        
        # Touch controls info
        img.draw_rect(0, 450, 640, 30, image.Color.from_rgb(40, 40, 40), -1)
        controls_text = "Touch: Top-Left=Capture | Top-Right=Exit"
        img.draw_string(10, 458, controls_text, image.Color.from_rgb(200, 200, 200))
        
        # Show active models list (scrolling if needed)
        active_models = self.ai_manager.get_active_models()
        session_stats = self.data_logger.get_session_stats()
        
        if active_models:
            # Show first 3 models in bottom area
            y_pos = 350
            for i, model in enumerate(active_models[:3]):
                if i < 3:
                    short_name = model[:20] + "..." if len(model) > 20 else model
                    img.draw_string(10, y_pos + i * 15, f"• {short_name}", 
                                   image.Color.from_rgb(0, 200, 0))
            
            if len(active_models) > 3:
                img.draw_string(10, y_pos + 45, f"+ {len(active_models) - 3} more...", 
                               image.Color.from_rgb(150, 150, 150))
        
        # Show logging status using existing DataLogger methods
        if session_stats["session_active"]:
            events_count = session_stats["events_logged"]
            img.draw_string(400, 380, f"📊 Events: {events_count}", 
                           image.Color.from_rgb(255, 255, 0))
        
        total_events = session_stats["total_events_logged"]
        storage_mb = session_stats["storage_used"] / (1024 * 1024) if session_stats["storage_used"] > 0 else 0
        img.draw_string(400, 400, f"📁 Total: {total_events} ({storage_mb:.1f}MB)", 
                       image.Color.from_rgb(150, 150, 150))
    
    def run(self):
        """Main application loop"""
        log_info("Starting main application loop")
        
        try:
            while not app.need_exit():
                # Update FPS counter
                self._update_fps()
                
                # Handle touch events (returns False if exit requested)
                if not self._handle_touch_events():
                    break
                
                # Capture camera frame
                img = self.camera.read()
                
                # Process AI if capturing
                if self.state == "CAPTURING":
                    try:
                        ai_events = self.ai_manager.process_frame(img)
                        
                        # Log AI events to file
                        if ai_events:
                            self.data_logger.log_events(ai_events)
                            for event in ai_events:
                                log_info(f"🤖 AI Event: {event['model']} - {event['details']}")
                                
                    except Exception as e:
                        log_error(f"AI processing error: {e}")
                
                # Draw UI overlay
                self._draw_ui(img)
                
                # Display frame
                self.display.show(img)
                
                # Memory management
                if self.frame_count % 100 == 0:
                    gc.collect()
                
                # Small delay (~30 FPS)
                maix_time.sleep_ms(33)
                
        except KeyboardInterrupt:
            log_info("Application interrupted by user")
        except Exception as e:
            log_error(f"Application error: {e}")
            self.state = "ERROR"
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Clean up resources before exit"""
        log_info("Cleaning up application resources...")
        
        try:
            # End data logging session if active using existing DataLogger
            if self.data_logger and self.capturing:
                self.data_logger.end_session()
                log_info("Data logging session ended")
            
            # Close camera
            if self.camera:
                self.camera.close()
                log_info("Camera closed")
            
            # Final garbage collection
            gc.collect()
            
        except Exception as e:
            log_error(f"Cleanup error: {e}")
        
        log_info("Application cleanup completed")

def main():
    """Main entry point with setup screen integration"""
    try:
        log_info("🎨 Starting Companion Capture with Setup Screen...")
        
        # Run setup screen first
        if run_setup_screen():
            log_info("✅ Setup completed, starting main application...")
            
            # Start main capture application
            app = CompanionCaptureApp()
            app.run()
        else:
            log_info("❌ Setup cancelled, exiting...")
            
    except Exception as e:
        log_error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
