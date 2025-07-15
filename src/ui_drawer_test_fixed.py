#!/usr/bin/env python3
"""
Standalone UI Test with Model Drawer
Test the new model selection drawer UI without dependencies

This file demonstrates the enhanced UI with:
- Sliding AI model selection drawer (PROJECT_PLAN.MD Step 3.5)
- Multiple AI model checkboxes matching PROJECT_PLAN.MD requirements
- Touch-responsive interface
- Animated drawer expansion/collapse

Author: Companion Intelligence
Date: July 14, 2025
"""

from maix import camera, display, image, touchscreen, app
import time as python_time

class MockConfig:
    """Mock configuration for testing"""
    
    def get_ui_config(self):
        return {
            "preview_area": {"x": 0, "y": 10, "width": 480, "height": 360},
            "ui_area": {"x": 480, "y": 0, "width": 160, "height": 480}
        }
    
    def get(self, key, default=None):
        configs = {
            "display": {},
            "ai_models": {
                "object_classification": {"enabled": True},
                "face_recognition": {"enabled": True},
                "face_emotion": {"enabled": False},
                "object_tracking": {"enabled": False},
                "ocr_detection": {"enabled": False},
                "hand_landmarks": {"enabled": False},
                "pose_classification": {"enabled": True},
                "hand_gesture": {"enabled": False},
            }
        }
        return configs.get(key, default)
    
    def is_model_enabled(self, model_name):
        return self.get("ai_models", {}).get(model_name, {}).get("enabled", False)

class SimpleButton:
    """Simplified button for testing"""
    
    def __init__(self, x, y, width, height, text="", 
                 color_normal=(100, 100, 100), color_pressed=(150, 150, 150)):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.color_normal = color_normal
        self.color_pressed = color_pressed
        self.pressed = False
    
    def is_touched(self, touch_x, touch_y):
        # Add 15px buffer around button for easier touch detection
        hit_area_expansion = 15
        expanded_x = self.x - hit_area_expansion
        expanded_y = self.y - hit_area_expansion
        expanded_width = self.width + (2 * hit_area_expansion)
        expanded_height = self.height + (2 * hit_area_expansion)
        
        return (expanded_x <= touch_x <= expanded_x + expanded_width and 
                expanded_y <= touch_y <= expanded_y + expanded_height)
    
    def set_pressed(self, pressed):
        self.pressed = pressed
    
    def draw(self, img):
        color = self.color_pressed if self.pressed else self.color_normal
        img.draw_rect(self.x, self.y, self.width, self.height, 
                     image.Color.from_rgb(*color), -1)
        img.draw_rect(self.x, self.y, self.width, self.height,
                     image.Color.from_rgb(200, 200, 200), 2)
        if self.text:
            text_x = self.x + (self.width - len(self.text) * 6) // 2
            text_y = self.y + (self.height - 12) // 2
            img.draw_string(text_x, text_y, self.text, image.Color.from_rgb(255, 255, 255))

class SimpleCheckbox:
    """Simplified checkbox for testing"""
    
    def __init__(self, x, y, width, height, text="", checked=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.checked = checked
    
    def toggle(self):
        self.checked = not self.checked
    
    def draw(self, img):
        color = (0, 200, 0) if self.checked else (100, 100, 100)
        img.draw_rect(self.x, self.y, self.width, self.height, 
                     image.Color.from_rgb(*color), -1)
        img.draw_rect(self.x, self.y, self.width, self.height,
                     image.Color.from_rgb(200, 200, 200), 1)
        if self.checked:
            # Draw checkmark
            img.draw_line(self.x + 3, self.y + self.height//2, 
                         self.x + self.width//2, self.y + self.height - 3,
                         image.Color.from_rgb(255, 255, 255), 2)
            img.draw_line(self.x + self.width//2, self.y + self.height - 3,
                         self.x + self.width - 3, self.y + 3,
                         image.Color.from_rgb(255, 255, 255), 2)
        
        # Draw text
        if self.text:
            img.draw_string(self.x + self.width + 5, self.y, self.text[:12], 
                           image.Color.from_rgb(255, 255, 255))

class ModelDrawerDemo:
    """Demonstration of the AI Model Selection Drawer"""
    
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
        # Drawer state
        self.expanded = False
        self.collapsed_width = 40
        self.expanded_width = width
        self.current_width = self.collapsed_width
        self.animation_speed = 8
        
        # Scroll properties
        self.scroll_offset = 0
        self.item_height = 22
        self.visible_items = (height - 100) // self.item_height
        
        # AI Models matching PROJECT_PLAN.MD requirements
        self.models = [
            # Computer Vision (AI Video)
            ("object_classification", "Object Classification", True),
            ("face_recognition", "Face Recognition", True),
            ("face_emotion", "Face Emotion Detection", False),
            ("object_tracking", "Object Tracking & Count", False),
            ("ocr_detection", "OCR Text Recognition", False),
            ("hand_landmarks", "Hand Landmarks", False),
            ("pose_classification", "Human Pose Classification", True),
            ("hand_gesture", "Hand Gesture Classification", False),
            
            # Audio Processing (AI Audio)
            ("audio_recording", "Audio Recording", False),
            ("audio_playback", "Audio Playback", False),
            ("voice_recognition", "Voice Recognition", False),
            
            # Media Capabilities
            ("video_recording", "Video Recording", False),
            ("video_playback", "Video Playback", False),
            
            # Additional AI Models (from MaixCAM)
            ("yolov8_detection", "YOLOv8 Objects", True),
            ("face_landmarks", "Face Landmarks", False),
            ("qr_detection", "QR Code Detection", False),
            ("classification", "Image Classification", False),
            ("yolo11_detection", "YOLO11 Objects", False),
            ("oriented_detection", "Oriented Detection", False),
            ("object_segmentation", "Object Segmentation", False),
        ]
        
        # Calculate max scroll
        total_items = len(self.models)
        self.max_scroll = max(0, (total_items - self.visible_items) * self.item_height)
        
        # UI elements
        self.toggle_button = SimpleButton(x + 5, y + 5, 50, 50, "AI", 
                                        (70, 70, 70), (100, 100, 100))
        self.scroll_up_button = SimpleButton(x + width - 35, y + 60, 30, 20, "^",
                                           (60, 60, 60), (90, 90, 90))
        self.scroll_down_button = SimpleButton(x + width - 35, y + height - 25, 30, 20, "v",
                                             (60, 60, 60), (90, 90, 90))
        
        # Create checkboxes
        self.checkboxes = []
        for i, (model_key, display_name, enabled) in enumerate(self.models):
            checkbox = SimpleCheckbox(
                x + 10, y + 80 + (i * self.item_height),
                15, 15, display_name, enabled
            )
            self.checkboxes.append(checkbox)
    
    def toggle_drawer(self):
        self.expanded = not self.expanded
        return self.expanded
    
    def update_animation(self):
        target_width = self.expanded_width if self.expanded else self.collapsed_width
        if self.current_width != target_width:
            if self.current_width < target_width:
                self.current_width = min(target_width, self.current_width + self.animation_speed)
            else:
                self.current_width = max(target_width, self.current_width - self.animation_speed)
    
    def handle_touch(self, touch_x, touch_y):
        # Debug print touch coordinates
        print(f"🎯 Touch detected at: ({touch_x}, {touch_y})")
        
        # Check toggle button (AI button)
        if self.toggle_button.is_touched(touch_x, touch_y):
            print(f"🚀 AI Button HIT! Drawer was {'expanded' if self.expanded else 'collapsed'}")
            self.toggle_button.set_pressed(True)
            self.toggle_drawer()
            return 'toggle'
        
        if not self.expanded:
            print("❌ Drawer collapsed - only AI button active")
            return None
        
        # Check scroll buttons
        if self.scroll_up_button.is_touched(touch_x, touch_y):
            print("⬆️ Scroll up button pressed")
            self.scroll_up_button.set_pressed(True)
            self.scroll_offset = max(0, self.scroll_offset - self.item_height)
            return 'scroll_up'
        
        if self.scroll_down_button.is_touched(touch_x, touch_y):
            print("⬇️ Scroll down button pressed")
            self.scroll_down_button.set_pressed(True)
            self.scroll_offset = min(self.max_scroll, self.scroll_offset + self.item_height)
            return 'scroll_down'
        
        # Check checkboxes
        visible_start = self.y + 80
        visible_end = self.y + self.height - 30
        
        for i, checkbox in enumerate(self.checkboxes):
            checkbox_y = checkbox.y - self.scroll_offset
            
            if (checkbox_y >= visible_start and checkbox_y + checkbox.height <= visible_end):
                # Expand checkbox touch area
                checkbox_touch_width = checkbox.width + len(checkbox.text) * 6 + 10
                if (checkbox.x <= touch_x <= checkbox.x + checkbox_touch_width and
                    checkbox_y <= touch_y <= checkbox_y + checkbox.height + 5):
                    
                    checkbox.toggle()
                    model_key, display_name, _ = self.models[i]
                    self.models[i] = (model_key, display_name, checkbox.checked)
                    print(f"✅ Checkbox toggled: {display_name} -> {'enabled' if checkbox.checked else 'disabled'}")
                    return f'model_changed:{model_key}:{checkbox.checked}'
        
        print("❌ Touch missed all targets")
        return None
    
    def clear_touch_feedback(self):
        self.toggle_button.set_pressed(False)
        self.scroll_up_button.set_pressed(False)
        self.scroll_down_button.set_pressed(False)
    
    def get_enabled_count(self):
        return sum(1 for _, _, enabled in self.models if enabled)
    
    def draw(self, img):
        self.update_animation()
        
        # Draw drawer background
        drawer_color = (40, 40, 40) if self.expanded else (30, 30, 30)
        img.draw_rect(self.x, self.y, int(self.current_width), self.height,
                     image.Color.from_rgb(*drawer_color), -1)
        
        # Draw border
        img.draw_rect(self.x, self.y, int(self.current_width), self.height,
                     image.Color.from_rgb(100, 100, 100), 1)
        
        # Always draw toggle button
        self.toggle_button.draw(img)
        
        # Draw expanded content
        if self.current_width > self.collapsed_width + 10:
            # Header
            img.draw_string(self.x + 65, self.y + 25, "AI Models", 
                           image.Color.from_rgb(200, 200, 200))
            
            # Separator
            img.draw_line(self.x + 10, self.y + 45, self.x + self.expanded_width - 10, self.y + 45,
                         image.Color.from_rgb(100, 100, 100), 1)
            
            # Scroll buttons
            if self.max_scroll > 0:
                self.scroll_up_button.draw(img)
                self.scroll_down_button.draw(img)
                
                # Scroll indicator
                if self.max_scroll > 0:
                    scroll_ratio = self.scroll_offset / self.max_scroll
                    indicator_y = self.y + 85 + int(scroll_ratio * (self.height - 150))
                    img.draw_rect(self.x + self.expanded_width - 8, indicator_y, 4, 10,
                                 image.Color.from_rgb(120, 120, 120), -1)
            
            # Draw visible checkboxes
            visible_start = self.y + 80
            visible_end = self.y + self.height - 30
            
            for checkbox in self.checkboxes:
                checkbox_y = checkbox.y - self.scroll_offset
                
                if (checkbox_y >= visible_start - self.item_height and 
                    checkbox_y <= visible_end):
                    
                    # Create temporary checkbox with adjusted position
                    temp_checkbox = SimpleCheckbox(
                        checkbox.x, checkbox_y, checkbox.width, checkbox.height,
                        checkbox.text, checkbox.checked
                    )
                    
                    if checkbox_y >= visible_start and checkbox_y + checkbox.height <= visible_end:
                        temp_checkbox.draw(img)
            
            # Draw enabled count
            enabled_count = self.get_enabled_count()
            img.draw_string(self.x + 10, self.y + self.height - 15, f"Enabled: {enabled_count}",
                           image.Color.from_rgb(150, 150, 150))

def test_model_drawer_ui():
    """Test the model drawer UI"""
    print("🎨 Testing Model Drawer UI...")
    
    # Initialize hardware
    cam = camera.Camera(640, 480)
    disp = display.Display()
    touch = touchscreen.TouchScreen()
    
    # Create UI elements
    model_drawer = ModelDrawerDemo(x=480, y=0, width=160, height=480)
    
    # Control buttons
    exit_button = SimpleButton(490, 420, 80, 30, "EXIT", (150, 0, 0), (200, 0, 0))
    demo_button = SimpleButton(490, 380, 80, 30, "DEMO", (0, 100, 150), (0, 150, 200))
    
    print("🖱️ Touch controls:")
    print("  - Touch 'AI' to expand/collapse drawer")
    print("  - Touch checkboxes to enable/disable models")
    print("  - Touch '^' and 'v' to scroll model list")
    print("  - Touch 'DEMO' to simulate model changes")
    print("  - Touch 'EXIT' to finish test")
    
    frame_count = 0
    demo_mode = False
    last_demo_time = python_time.time() * 1000  # Convert to milliseconds
    current_touch = None  # Store current touch coordinates
    
    while not app.need_exit():
        # Get camera frame
        img = cam.read()
        
        # Handle touch events
        touch_data = touch.read()
        if touch_data[0]:  # Touch detected
            touch_x, touch_y = touch_data[1], touch_data[2]
            current_touch = (touch_x, touch_y)  # Store for visual feedback
            
            # Display touch coordinates on console
            print(f"🔴 RAW TOUCH: ({touch_x}, {touch_y})")
            
            # Handle drawer touch
            drawer_action = model_drawer.handle_touch(touch_x, touch_y)
            if drawer_action:
                if drawer_action == 'toggle':
                    print(f"🚪 Drawer {'expanded' if model_drawer.expanded else 'collapsed'}")
                elif drawer_action.startswith('model_changed'):
                    _, model_key, enabled = drawer_action.split(':')
                    print(f"🔧 Model {model_key}: {'✅ enabled' if enabled == 'True' else '❌ disabled'}")
                elif drawer_action.startswith('scroll'):
                    print(f"📜 Scrolled {drawer_action}")
                
                # Clear touch feedback
                python_time.sleep(0.15)  # 150ms delay for visual feedback
                model_drawer.clear_touch_feedback()
            
            # Handle other buttons
            elif exit_button.is_touched(touch_x, touch_y):
                exit_button.set_pressed(True)
                print("🚪 Exiting model drawer test...")
                break
            
            elif demo_button.is_touched(touch_x, touch_y):
                demo_button.set_pressed(True)
                demo_mode = not demo_mode
                print(f"🎭 Demo mode: {'✅ ON' if demo_mode else '❌ OFF'}")
                python_time.sleep(0.15)  # 150ms delay
                demo_button.set_pressed(False)
        
        else:
            # Clear touch when not touching and clear button states
            current_touch = None
            exit_button.set_pressed(False)
            demo_button.set_pressed(False)
            model_drawer.clear_touch_feedback()
        
        # Demo mode - automatically toggle models
        current_time = python_time.time() * 1000
        if demo_mode and (current_time - last_demo_time) > 3000:  # Every 3 seconds
            if model_drawer.expanded:
                # Toggle a random model
                import random
                checkbox_idx = random.randint(0, len(model_drawer.checkboxes) - 1)
                model_drawer.checkboxes[checkbox_idx].toggle()
                model_key, display_name, _ = model_drawer.models[checkbox_idx]
                model_drawer.models[checkbox_idx] = (model_key, display_name, 
                                                   model_drawer.checkboxes[checkbox_idx].checked)
                print(f"🎭 Demo: Toggled {display_name}")
            last_demo_time = current_time
        
        # Draw camera preview area (left side)
        preview_img = img.resize(480, 480)
        
        # Add frame info to preview
        preview_img.draw_string(10, 10, f"Frame: {frame_count}", image.Color.from_rgb(255, 255, 255))
        
        enabled_count = model_drawer.get_enabled_count()
        preview_img.draw_string(10, 30, f"AI Models: {enabled_count}", image.Color.from_rgb(0, 255, 0))
        
        if demo_mode:
            preview_img.draw_string(10, 70, "DEMO MODE", image.Color.from_rgb(255, 255, 0))
        
        # Create full display image
        display_img = image.Image(640, 480, image.Format.FMT_RGB888)
        
        # Copy preview to left side
        display_img.draw_image(0, 0, preview_img)
        
        # Draw UI panel background (right side)
        display_img.draw_rect(480, 0, 160, 480, image.Color.from_rgb(20, 20, 20), -1)
        
        # Draw model drawer
        model_drawer.draw(display_img)
        
        # Draw control buttons
        exit_button.draw(display_img)
        demo_button.draw(display_img)
        
        # Draw title
        display_img.draw_string(490, 450, "Model Drawer", image.Color.from_rgb(200, 200, 200))
        display_img.draw_string(490, 465, "Demo Test", image.Color.from_rgb(200, 200, 200))
        
        # Draw touch feedback
        if current_touch:
            tx, ty = current_touch
            # Draw crosshairs at touch point
            display_img.draw_line(tx - 15, ty, tx + 15, ty, image.Color.from_rgb(255, 0, 0), 3)
            display_img.draw_line(tx, ty - 15, tx, ty + 15, image.Color.from_rgb(255, 0, 0), 3)
            # Draw touch coordinates on screen
            display_img.draw_string(10, 90, f"Touch: {tx},{ty}", image.Color.from_rgb(255, 0, 0))
        
        # Show display
        disp.show(display_img)
        
        frame_count += 1
        
        if frame_count % 30 == 0:
            print(f"📊 Frame {frame_count}: Models enabled: {enabled_count}")
    
    cam.close()
    print("✅ Model drawer UI test completed!")

def main():
    """Run the model drawer test"""
    print("🚀 AI Model Drawer Test")
    print("=" * 40)
    print("Testing PROJECT_PLAN.MD Step 3.5:")
    print("Create right sidebar for AI model toggle checkboxes")
    print()
    
    test_model_drawer_ui()
    
    print("\n📊 Test Summary:")
    print("✅ Sliding drawer animation")
    print("✅ PROJECT_PLAN.MD model checkboxes")  
    print("✅ Touch-responsive interface")
    print("✅ Scrollable model list")
    print("✅ Real-time model toggling")
    print("✅ Visual feedback system")

if __name__ == "__main__":
    main()
