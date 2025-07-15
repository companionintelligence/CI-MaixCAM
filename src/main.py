#!/usr/bin/env python3
"""
Companion Capture App - Main Entry Point
Life-logging application for Sipeed MaixCAM

This is the main application that orchestrates all components:
- UI Management
- AI Processing Engine
- Data Logging
- Network Upload

Author: Companion Intelligence
Date: July 13, 2025
Version: 1.0.0
"""

import sys
import time
import gc
from maix import app, display, camera, touchscreen, time as maix_time
from ui.main_ui import MainUI
from ai_engine.ai_engine import AIEngine
from data_logger.logger import DataLogger
from network.uploader import NetworkUploader
from utils.config import Config
from utils.logger import setup_logging

# Setup logging
logger = setup_logging()

class CompanionCaptureApp:
    """Main application class that coordinates all subsystems"""
    
    def __init__(self):
        """Initialize the application"""
        logger.info("Starting Companion Capture App...")
        
        # Application state machine
        self.state = "INITIALIZING"
        self.states = ["INITIALIZING", "IDLE", "CAPTURING", "ERROR"]
        
        # Core configuration
        self.config = Config()
        
        # Initialize hardware components
        self.camera = None
        self.display = None
        self.touchscreen = None
        
        # Initialize software components
        self.ui = None
        self.ai_engine = None
        self.data_logger = None
        self.network_uploader = None
        
        # Performance monitoring
        self.frame_count = 0
        self.last_fps_time = maix_time.ticks_ms()
        self.fps = 0
        
        # Initialize all components
        self._initialize_hardware()
        self._initialize_software()
        
        logger.info("Companion Capture App initialized successfully")
        self.state = "IDLE"
    
    def _initialize_hardware(self):
        """Initialize camera, display, and touchscreen"""
        try:
            # Initialize camera
            logger.info("Initializing camera...")
            self.camera = camera.Camera(
                width=640, 
                height=480, 
                fps=30
            )
            logger.info("Camera initialized successfully")
            
            # Initialize display
            logger.info("Initializing display...")
            self.display = display.Display()
            logger.info(f"Display initialized: {self.display.width()}x{self.display.height()}")
            
            # Initialize touchscreen
            logger.info("Initializing touchscreen...")
            self.touchscreen = touchscreen.TouchScreen()
            logger.info("Touchscreen initialized successfully")
            
        except Exception as e:
            logger.error(f"Hardware initialization failed: {e}")
            self.state = "ERROR"
            raise
    
    def _initialize_software(self):
        """Initialize UI, AI engine, data logger, and network uploader"""
        try:
            # Initialize UI
            logger.info("Initializing UI...")
            self.ui = MainUI(
                display=self.display,
                touchscreen=self.touchscreen,
                config=self.config
            )
            logger.info("UI initialized successfully")
            
            # Initialize AI Engine
            logger.info("Initializing AI Engine...")
            self.ai_engine = AIEngine(config=self.config)
            logger.info("AI Engine initialized successfully")
            
            # Initialize Data Logger
            logger.info("Initializing Data Logger...")
            self.data_logger = DataLogger(config=self.config)
            logger.info("Data Logger initialized successfully")
            
            # Initialize Network Uploader
            logger.info("Initializing Network Uploader...")
            self.network_uploader = NetworkUploader(config=self.config)
            logger.info("Network Uploader initialized successfully")
            
        except Exception as e:
            logger.error(f"Software initialization failed: {e}")
            self.state = "ERROR"
            raise
    
    def _update_fps(self):
        """Update FPS counter"""
        self.frame_count += 1
        current_time = maix_time.ticks_ms()
        
        if time.ticks_diff(current_time, self.last_fps_time) >= 1000:  # Update every second
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def _handle_ui_events(self):
        """Process UI events and state changes"""
        ui_events = self.ui.handle_events()
        
        for event in ui_events:
            if event['type'] == 'start_capture':
                logger.info("Starting capture mode")
                self.state = "CAPTURING"
                self.data_logger.start_session()
                
            elif event['type'] == 'stop_capture':
                logger.info("Stopping capture mode")
                self.state = "IDLE"
                self.data_logger.end_session()
                
            elif event['type'] == 'toggle_model':
                model_name = event['model']
                enabled = event['enabled']
                logger.info(f"Toggling model {model_name}: {enabled}")
                self.ai_engine.toggle_model(model_name, enabled)
                
            elif event['type'] == 'exit_app':
                logger.info("Exit requested by user")
                return False
        
        return True
    
    def _process_ai_frame(self, img):
        """Process current frame through AI engine if capturing"""
        if self.state != "CAPTURING":
            return []
        
        try:
            # Process frame through AI engine
            events = self.ai_engine.process_frame(img)
            
            # Log events if any detected
            if events:
                self.data_logger.log_events(events)
                logger.debug(f"Logged {len(events)} AI events")
            
            return events
            
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            return []
    
    def _memory_management(self):
        """Perform memory management"""
        # Force garbage collection every 100 frames
        if self.frame_count % 100 == 0:
            gc.collect()
            free_memory = gc.mem_free()
            logger.debug(f"Memory management: {free_memory} bytes free")
            
            # Check for memory warnings
            if free_memory < 10 * 1024 * 1024:  # Less than 10MB
                logger.warning(f"Low memory warning: {free_memory} bytes free")
    
    def run(self):
        """Main application loop"""
        logger.info("Starting main application loop")
        
        try:
            while not app.need_exit():
                # Update FPS counter
                self._update_fps()
                
                # Handle UI events (returns False if exit requested)
                if not self._handle_ui_events():
                    break
                
                # Capture camera frame
                img = self.camera.read()
                
                # Process AI if capturing
                ai_events = self._process_ai_frame(img)
                
                # Update UI with current frame and AI results
                self.ui.update_frame(img, ai_events)
                self.ui.update_status({
                    'state': self.state,
                    'fps': self.fps,
                    'memory_free': gc.mem_free(),
                    'ai_models_active': self.ai_engine.get_active_models(),
                    'storage_used': self.data_logger.get_storage_usage()
                })
                
                # Draw UI
                self.ui.draw()
                
                # Memory management
                self._memory_management()
                
                # Small delay to prevent overwhelming the system (~30 FPS)
                time.sleep_ms(33)
                
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Application error: {e}")
            self.state = "ERROR"
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Clean up resources before exit"""
        logger.info("Cleaning up application resources...")
        
        try:
            # Stop data logging session if active
            if self.data_logger and self.state == "CAPTURING":
                self.data_logger.end_session()
            
            # Close camera
            if self.camera:
                self.camera.close()
                logger.info("Camera closed")
            
            # Cleanup AI engine
            if self.ai_engine:
                self.ai_engine.cleanup()
                logger.info("AI Engine cleaned up")
            
            # Final garbage collection
            gc.collect()
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        
        logger.info("Application cleanup completed")

def main():
    """Main entry point"""
    try:
        app = CompanionCaptureApp()
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
