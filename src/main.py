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
Version: 1.2.0
"""

import sys
import gc
from maix import app, display, camera, touchscreen, time as maix_time, image
from setup_screen import run_setup_screen
from data_logger.logger import DataLogger
from network.uploader import NetworkUploader
from utils.config import Config
from utils.device import get_cpu_temp_celsius
from ai.object_detector import ObjectDetector
from ai.face_detector import FaceDetector
from ai.object_tracker import ObjectTracker
from ai.ocr_detector import OcrDetector
from ai.hand_detector import HandDetector
from ai.pose_detector import PoseDetector
from ai.audio_processor import AudioProcessor

# Simplified logging for now
def log_info(msg):
    print(f"[INFO] {msg}")

def log_error(msg):
    print(f"[ERROR] {msg}")

class AIModelManager:
    """Owns real detector instances for every toggled-on model and schedules
    them per frame.

    Only a toggled-on model is ever instantiated: MaixCAM's camera, NPU and
    model weights share one small memory pool (see docs/research-notes.md),
    so a device with two models enabled never pays another eleven models'
    worth of that budget (PROJECT_PLAN.MD 15.3/15.6). Each processor also
    only actually runs every `processing_interval` frames (its own
    ai_models.<key> config value, previously read but never applied -
    PROJECT_PLAN.MD 17.2/17.3), and Object Tracking and Counting reuses
    Object Classification's own detections instead of running YOLOv8 a
    second time on the same frame when both are enabled - MaixCAM's NPU
    executes one model at a time, so a second concurrent model is pure
    added latency, not parallel work.
    """

    def __init__(self, config):
        self.config = config
        self.active_models = config.get_model_states()

        # display_name -> instance exposing .process(img) -> event|None
        self.model_processors = {}
        self._processing_intervals = {}

        # Every real detector instance created, for cleanup() and status
        # reporting. A shared instance (e.g. one FaceDetector backing both
        # "Face Recognition" and "Face Emotion Detection") appears once here
        # even though it may be reachable through model_processors too.
        self._instances = []

        # Object Tracking and Counting rides on a detector's own per-frame
        # detections rather than being scheduled through model_processors
        # itself - see _update_tracking().
        self.object_tracker = None
        self._tracking_detector = None

        self.frame_index = 0

        self._initialize_model_processors()

    def _register(self, display_name, processor, config_key):
        """Schedule `processor` under `display_name` at its own configured cadence"""
        self.model_processors[display_name] = processor
        interval = self.config.get_ai_model_config(config_key).get("processing_interval", 1)
        try:
            interval = int(interval)
        except (TypeError, ValueError):
            interval = 1
        self._processing_intervals[display_name] = max(1, interval)

    def _initialize_model_processors(self):
        """Instantiate a real detector only for each toggled-on model"""

        object_detector = None
        if self.active_models.get("Object Classification", False):
            object_detector = ObjectDetector(self.config.get_ai_model_config("object_detection"))
            self._instances.append(object_detector)
            self._register("Object Classification", object_detector, "object_detection")
            log_info("✅ Object Classification processor ready")

        # Face Recognition and Face Emotion Detection are ONE pipeline
        # (emotion is a second stage over face detection's own faces, see
        # ai/face_detector.py) - registered under a single slot either way
        # so it is never invoked twice in the same frame.
        face_enabled = self.active_models.get("Face Recognition", False)
        emotion_enabled = self.active_models.get("Face Emotion Detection", False)
        if face_enabled or emotion_enabled:
            face_config = self.config.get_ai_model_config("face_detection")
            emotion_config = self.config.get_ai_model_config("face_emotion") if emotion_enabled else None
            face_detector = FaceDetector(face_config, emotion_config)
            self._instances.append(face_detector)
            if face_enabled:
                self._register("Face Recognition", face_detector, "face_detection")
            else:
                self._register("Face Emotion Detection", face_detector, "face_emotion")
            log_info(f"✅ Face Recognition processor ready (emotion: {emotion_enabled})")

        if self.active_models.get("OCR (Optical Character Recognition)", False):
            ocr_detector = OcrDetector(self.config.get_ai_model_config("ocr"))
            self._instances.append(ocr_detector)
            self._register("OCR (Optical Character Recognition)", ocr_detector, "ocr")
            log_info("✅ OCR processor ready")

        # Same one-pipeline-two-toggles shape as face/emotion above.
        hand_enabled = self.active_models.get("Hand Landmarks Detection", False)
        gesture_enabled = self.active_models.get("Hand Gesture Classification", False)
        if hand_enabled or gesture_enabled:
            landmarks_config = self.config.get_ai_model_config("hand_landmarks")
            gesture_config = self.config.get_ai_model_config("hand_gesture") if gesture_enabled else None
            hand_detector = HandDetector(landmarks_config, gesture_config)
            self._instances.append(hand_detector)
            if hand_enabled:
                self._register("Hand Landmarks Detection", hand_detector, "hand_landmarks")
            else:
                self._register("Hand Gesture Classification", hand_detector, "hand_gesture")
            log_info(f"✅ Hand Landmarks Detection processor ready (gesture: {gesture_enabled})")

        if self.active_models.get("Human Pose Classification", False):
            pose_detector = PoseDetector(self.config.get_ai_model_config("pose_detection"))
            self._instances.append(pose_detector)
            self._register("Human Pose Classification", pose_detector, "pose_detection")
            log_info("✅ Human Pose Classification processor ready")

        # "Audio Recording" and "Real-time Voice Recognition" share one
        # config entry (ai_models.audio_recognition) and one AudioProcessor,
        # which itself treats them as mutually exclusive per call (an armed
        # recording takes priority - see ai/audio_processor.py), so a single
        # scheduled slot is correct even with both toggled on.
        recording_enabled = self.active_models.get("Audio Recording", False)
        voice_enabled = self.active_models.get("Real-time Voice Recognition", False)
        if recording_enabled or voice_enabled:
            audio_processor = AudioProcessor(self.config.get_ai_model_config("audio_recognition"))
            self._instances.append(audio_processor)
            if recording_enabled:
                audio_processor.start_recording()
                self._register("Audio Recording", audio_processor, "audio_recognition")
            else:
                self._register("Real-time Voice Recognition", audio_processor, "audio_recognition")
            log_info(f"✅ Audio processor ready (recording: {recording_enabled}, voice: {voice_enabled})")

        # Audio Playback, Video Recording and Video Playback are on-demand
        # actions a caller triggers directly, not per-frame detectors polled
        # from process_frame() - nothing to schedule here for them. Video
        # capture has no maix.video wrapper yet and is not one of
        # PROJECT_PLAN.MD's numbered steps 1-19.

        if self.active_models.get("Object Tracking and Counting", False):
            # Reuse Object Classification's own detector when it exists
            # (avoids a second YOLOv8 pass on the same frame); otherwise
            # stand up a dedicated one just for tracking.
            self._tracking_detector = object_detector or ObjectDetector(
                self.config.get_ai_model_config("object_detection")
            )
            if self._tracking_detector is not object_detector:
                self._instances.append(self._tracking_detector)
            self.object_tracker = ObjectTracker(self.config.get_ai_model_config("object_tracking"))
            self._processing_intervals["Object Tracking and Counting"] = max(
                1, int(self.config.get_ai_model_config("object_tracking").get("processing_interval", 1) or 1)
            )
            log_info("✅ Object Tracking and Counting processor ready")

        log_info(
            f"Initialized {len(self._instances)} AI model instance(s), "
            f"{len(self.model_processors)} scheduled detector slot(s)"
        )

    def _should_run_now(self, display_name):
        interval = self._processing_intervals.get(display_name, 1)
        return self.frame_index % interval == 0

    def process_frame(self, img):
        """Process one camera frame through every active, due-this-frame model"""
        events = []
        # Memoized per instance for this frame only, so a detector shared
        # between a scheduled slot and tracking never runs twice on one img.
        frame_cache = {}

        def run_once(detector):
            key = id(detector)
            if key not in frame_cache:
                frame_cache[key] = detector.process(img)
            return frame_cache[key]

        for model_name, processor in self.model_processors.items():
            if not self._should_run_now(model_name):
                continue
            try:
                event = run_once(processor)
                if event:
                    events.append(event)
            except Exception as e:
                log_error(f"Error processing {model_name}: {e}")

        if self.object_tracker is not None and self._should_run_now("Object Tracking and Counting"):
            try:
                detection_event = run_once(self._tracking_detector)
                detections = detection_event["detections"] if detection_event else []
                tracking_event = self.object_tracker.update(detections, self.frame_index)
                if tracking_event:
                    events.append(tracking_event)
            except Exception as e:
                log_error(f"Error processing Object Tracking and Counting: {e}")

        self.frame_index += 1
        return events

    def get_active_models(self):
        """Get list of currently active model names"""
        return [name for name, active in self.active_models.items() if active]

    def get_model_count(self):
        """Get count of active models"""
        return len([active for active in self.active_models.values() if active])

    def get_model_status(self):
        """Per-instance loaded/unloaded status, for diagnostics (PROJECT_PLAN 15.10)"""
        return {
            display_name: getattr(processor, "loaded", True)
            for display_name, processor in self.model_processors.items()
        }

    def cleanup(self):
        """Release every real detector instance this manager created"""
        for instance in self._instances:
            try:
                instance.cleanup()
            except Exception as e:
                log_error(f"Error cleaning up an AI model instance: {e}")

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
        
        # Initialize AI model manager, data logger and CI-Server uploader
        self.ai_manager = None
        self.data_logger = None
        self.network_uploader = None

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
        self._initialize_network_uploader()

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
            self.ai_manager = AIModelManager(self.config)
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

    def _initialize_network_uploader(self):
        """Initialize the CI-Server uploader for logged AI events"""
        try:
            log_info("Initializing Network Uploader...")
            self.network_uploader = NetworkUploader(self.config)
            log_info("Network Uploader initialized successfully")

        except Exception as e:
            # Sync to CI-Server is best-effort - local logging must keep
            # working even with no network configured, so this does not
            # escalate to self.state = "ERROR" the way the other
            # initializers do.
            log_error(f"Network Uploader initialization failed: {e}")
            self.network_uploader = None
    
    def _is_thermal_throttled(self):
        """True when the device is over its configured thermal threshold

        AI inference is the heaviest per-frame cost, so this gates that,
        not the capture/display loop itself (PROJECT_PLAN.MD 17.6/17.9).
        Fails open (never throttles) when the temperature can't be read at
        all, e.g. off-device - it never guesses.
        """
        perf_config = self.config.get_performance_config()
        if not perf_config.get("thermal_throttling_enabled", True):
            return False

        temp = get_cpu_temp_celsius()
        if temp is None:
            return False

        threshold = perf_config.get("thermal_threshold_celsius", 75)
        if temp >= threshold:
            log_error(f"Thermal throttling: CPU at {temp:.1f}C (threshold {threshold}C), skipping AI this frame")
            return True
        return False

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
                    session_file = self.data_logger.current_session_file
                    self.data_logger.end_session()
                    self._queue_session_for_upload(session_file)
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
                        ai_events = [] if self._is_thermal_throttled() else self.ai_manager.process_frame(img)
                        
                        # Log AI events to file
                        if ai_events:
                            self.data_logger.log_events(ai_events)
                            for event in ai_events:
                                count = len(event.get("detections", []))
                                log_info(f"🤖 AI Event: {event['model']} ({event['type']}) - {count} detection(s)")
                                
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
                session_file = self.data_logger.current_session_file
                self.data_logger.end_session()
                self._queue_session_for_upload(session_file)
                log_info("Data logging session ended")

            # Close camera
            if self.camera:
                self.camera.close()
                log_info("Camera closed")

            # Release AI model instances
            if self.ai_manager:
                self.ai_manager.cleanup()

            # Stop the upload thread (queued files are picked up next launch)
            if self.network_uploader:
                self.network_uploader.cleanup()

            # Final garbage collection
            gc.collect()

        except Exception as e:
            log_error(f"Cleanup error: {e}")

        log_info("Application cleanup completed")

    def _queue_session_for_upload(self, session_file):
        """Hand a just-ended session's log file to the CI-Server uploader"""
        if self.network_uploader and session_file:
            self.network_uploader.queue_file_for_upload(session_file)

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
