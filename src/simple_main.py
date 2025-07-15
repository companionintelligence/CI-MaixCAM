#!/usr/bin/env python3
"""
Simple MaixCAM Life Logger
Standalone version that doesn't require external modules

This is a simplified version of the Companion Capture App that can run
directly on MaixCAM without requiring the full project structure.

Author: Companion Intelligence
Date: July 14, 2025
"""

from maix import app, display, camera, touchscreen, nn, image, time
import gc

class SimpleLifeLogger:
    """Simple life logger for MaixCAM"""
    
    def __init__(self):
        """Initialize the simple life logger"""
        print("🚀 Initializing Simple Life Logger...")
        
        # State
        self.capturing = False
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.ticks_ms()
        
        # Initialize hardware
        self._init_hardware()
        
        # Try to initialize AI models
        self._init_ai_models()
        
        print("✅ Simple Life Logger initialized")
    
    def _init_hardware(self):
        """Initialize camera, display, and touchscreen"""
        print("📱 Initializing hardware...")
        
        # Camera
        self.camera = camera.Camera(640, 480)
        print(f"✅ Camera: {self.camera.width()}x{self.camera.height()}")
        
        # Display
        self.display = display.Display()
        print(f"✅ Display: {self.display.width()}x{self.display.height()}")
        
        # Touchscreen
        self.touchscreen = touchscreen.TouchScreen()
        print("✅ Touchscreen initialized")
    
    def _init_ai_models(self):
        """Try to initialize AI models"""
        print("🤖 Initializing AI models...")
        
        self.models = {}
        
        # Try object detection
        try:
            detector = nn.YOLOv8(model="/root/models/yolov8n.mud", dual_buff=True)
            self.models["object"] = detector
            print(f"✅ Object detection loaded: {len(detector.labels)} classes")
        except Exception as e:
            print(f"⚠️ Object detection failed: {e}")
        
        # Try face detection
        try:
            face_detector = nn.Retinaface(model="/root/models/retinaface.mud", dual_buff=True)
            self.models["face"] = face_detector
            print("✅ Face detection loaded")
        except Exception as e:
            print(f"⚠️ Face detection failed: {e}")
        
        print(f"📊 Loaded {len(self.models)} AI models")
    
    def _update_fps(self):
        """Update FPS counter"""
        self.frame_count += 1
        current_time = time.ticks_ms()
        
        if time.ticks_diff(current_time, self.last_fps_time) >= 1000:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def _handle_touch(self):
        """Handle touch input"""
        touch_data = self.touchscreen.read()
        
        if touch_data[0]:  # Touch detected
            x, y = touch_data[1], touch_data[2]
            
            # Simple touch zones
            # Top half = toggle capture
            # Bottom half = exit
            if y < self.display.height() // 2:
                self.capturing = not self.capturing
                print(f"📹 Capture {'started' if self.capturing else 'stopped'}")
            else:
                print("👋 Exit requested")
                return False
        
        return True
    
    def _process_ai(self, img):
        """Process AI models on the image"""
        events = []
        
        if not self.capturing:
            return events
        
        # Process object detection
        if "object" in self.models:
            try:
                detector = self.models["object"]
                objs = detector.detect(img, conf_th=0.5, iou_th=0.45)
                
                if objs:
                    # Draw detections
                    for obj in objs:
                        img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
                        label = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
                        img.draw_string(obj.x, obj.y, label, color=image.COLOR_RED)
                    
                    # Create event
                    event = {
                        "timestamp": time.ticks_ms(),
                        "type": "object_detection",
                        "count": len(objs),
                        "objects": [detector.labels[obj.class_id] for obj in objs]
                    }
                    events.append(event)
                    print(f"🔍 Detected {len(objs)} objects: {[detector.labels[obj.class_id] for obj in objs]}")
            
            except Exception as e:
                print(f"❌ Object detection error: {e}")
        
        # Process face detection  
        if "face" in self.models:
            try:
                face_detector = self.models["face"]
                faces = face_detector.detect(img, conf_th=0.4, iou_th=0.45)
                
                if faces:
                    # Draw face detections
                    for face in faces:
                        img.draw_rect(face.x, face.y, face.w, face.h, color=image.COLOR_GREEN)
                        # Draw landmarks
                        radius = max(2, face.w // 20)
                        img.draw_keypoints(face.points, image.COLOR_GREEN, size=radius)
                    
                    # Create event
                    event = {
                        "timestamp": time.ticks_ms(),
                        "type": "face_detection", 
                        "count": len(faces)
                    }
                    events.append(event)
                    print(f"👤 Detected {len(faces)} faces")
            
            except Exception as e:
                print(f"❌ Face detection error: {e}")
        
        return events
    
    def _draw_ui(self, img):
        """Draw simple UI elements"""
        # Status bar at top
        status_color = image.COLOR_GREEN if self.capturing else image.COLOR_WHITE
        status_text = "CAPTURING" if self.capturing else "IDLE"
        img.draw_string(10, 10, f"Status: {status_text}", color=status_color)
        
        # FPS and frame count
        img.draw_string(10, 30, f"FPS: {self.fps:.1f}", color=image.COLOR_WHITE)
        img.draw_string(10, 50, f"Frame: {self.frame_count}", color=image.COLOR_WHITE)
        
        # Memory usage
        memory_mb = gc.mem_free() // 1024 // 1024
        img.draw_string(10, 70, f"Memory: {memory_mb}MB", color=image.COLOR_WHITE)
        
        # Models loaded
        img.draw_string(10, 90, f"Models: {len(self.models)}", color=image.COLOR_WHITE)
        
        # Instructions at bottom
        img.draw_string(10, img.height() - 60, "Touch top: Start/Stop", color=image.COLOR_YELLOW)
        img.draw_string(10, img.height() - 40, "Touch bottom: Exit", color=image.COLOR_YELLOW)
        
        # Capture indicator
        if self.capturing:
            # Red circle in top right
            img.draw_circle(img.width() - 30, 30, 15, color=image.COLOR_RED, thickness=-1)
    
    def run(self):
        """Main application loop"""
        print("🏃 Starting main loop...")
        print("📱 Touch top half to start/stop capture")
        print("📱 Touch bottom half to exit")
        
        total_events = 0
        
        try:
            while not app.need_exit():
                # Update FPS
                self._update_fps()
                
                # Handle touch input
                if not self._handle_touch():
                    break
                
                # Capture frame
                img = self.camera.read()
                
                # Process AI
                events = self._process_ai(img)
                total_events += len(events)
                
                # Draw UI
                self._draw_ui(img)
                
                # Show display
                self.display.show(img)
                
                # Memory management
                if self.frame_count % 100 == 0:
                    gc.collect()
                
                # Small delay
                time.sleep_ms(33)  # ~30 FPS
        
        except KeyboardInterrupt:
            print("\n⏹️ Interrupted by user")
        
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
        
        finally:
            print(f"📊 Session complete: {total_events} total events")
            self._cleanup()
    
    def _cleanup(self):
        """Clean up resources"""
        print("🧹 Cleaning up...")
        
        try:
            if hasattr(self, 'camera'):
                self.camera.close()
                print("✅ Camera closed")
        except Exception as e:
            print(f"⚠️ Camera cleanup error: {e}")
        
        gc.collect()
        print("✅ Cleanup completed")

def main():
    """Main entry point"""
    try:
        logger = SimpleLifeLogger()
        logger.run()
    except Exception as e:
        print(f"💥 Fatal error: {e}")

if __name__ == "__main__":
    main()
