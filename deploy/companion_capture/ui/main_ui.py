"""
Main UI Management System
Handles the primary user interface for the Companion Capture App

Author: Companion Intelligence
Date: July 13, 2025
"""

import time
from maix import image, display
from utils.logger import get_logger
from .ui_elements import Button, Checkbox, StatusBar

logger = get_logger('UI')

class MainUI:
    """Main UI class that manages the entire user interface"""
    
    def __init__(self, display, touchscreen, config):
        """Initialize the main UI"""
        self.display = display
        self.touchscreen = touchscreen
        self.config = config
        
        # Get UI configuration
        self.ui_config = config.get_ui_config()
        self.display_config = config.get("display", {})
        
        # Screen dimensions
        self.screen_width = self.display.width()
        self.screen_height = self.display.height()
        
        # UI areas
        self.preview_area = self.display_config.get("preview_area", {
            "x": 0, "y": 0, "width": 440, "height": 320
        })
        self.ui_area = self.display_config.get("ui_area", {
            "x": 440, "y": 0, "width": 112, "height": 368
        })
        
        # Current frame and AI results
        self.current_frame = None
        self.ai_results = []
        self.status_data = {}
        
        # UI elements
        self.buttons = {}
        self.checkboxes = {}
        self.status_bar = None
        
        # Touch state
        self.last_touch_time = 0
        self.touch_feedback_duration = 100  # ms
        
        # Initialize UI elements
        self._initialize_ui_elements()
        
        logger.info("Main UI initialized")
    
    def _initialize_ui_elements(self):
        """Initialize all UI elements"""
        
        # Control buttons
        self.buttons['start_stop'] = Button(
            x=self.ui_area['x'] + 10,
            y=50,
            width=92,
            height=40,
            text="START",
            color_normal=(0, 150, 0),
            color_pressed=(0, 200, 0)
        )
        
        self.buttons['exit'] = Button(
            x=self.ui_area['x'] + 10,
            y=self.screen_height - 50,
            width=92,
            height=30,
            text="EXIT",
            color_normal=(150, 0, 0),
            color_pressed=(200, 0, 0)
        )
        
        # AI model checkboxes
        model_names = [
            "object_detection",
            "face_detection", 
            "face_emotion",
            "ocr",
            "hand_landmarks",
            "pose_detection",
            "audio_recognition"
        ]
        
        y_start = 120
        for i, model_name in enumerate(model_names):
            self.checkboxes[model_name] = Checkbox(
                x=self.ui_area['x'] + 10,
                y=y_start + (i * 25),
                width=15,
                height=15,
                text=model_name.replace('_', ' ').title()[:8],
                checked=self.config.is_model_enabled(model_name)
            )
        
        # Status bar
        self.status_bar = StatusBar(
            x=0,
            y=self.preview_area['height'],
            width=self.preview_area['width'],
            height=self.screen_height - self.preview_area['height']
        )
        
        logger.info("UI elements initialized")
    
    def handle_events(self):
        """Handle touch events and return UI events"""
        events = []
        
        # Get touch data
        touch_data = self.touchscreen.read()
        
        if touch_data[0]:  # Touch detected
            x, y = touch_data[1], touch_data[2]
            self.last_touch_time = time.ticks_ms()
            
            # Check button presses
            for button_name, button in self.buttons.items():
                if button.is_touched(x, y):
                    button.set_pressed(True)
                    
                    if button_name == 'start_stop':
                        if button.text == "START":
                            button.text = "STOP"
                            button.color_normal = (150, 0, 0)
                            button.color_pressed = (200, 0, 0)
                            events.append({'type': 'start_capture'})
                        else:
                            button.text = "START"
                            button.color_normal = (0, 150, 0)
                            button.color_pressed = (0, 200, 0)
                            events.append({'type': 'stop_capture'})
                    
                    elif button_name == 'exit':
                        events.append({'type': 'exit_app'})
            
            # Check checkbox toggles
            for model_name, checkbox in self.checkboxes.items():
                if checkbox.is_touched(x, y):
                    checkbox.toggle()
                    events.append({
                        'type': 'toggle_model',
                        'model': model_name,
                        'enabled': checkbox.checked
                    })
        
        else:
            # Release button press states
            for button in self.buttons.values():
                button.set_pressed(False)
        
        return events
    
    def update_frame(self, frame, ai_results=None):
        """Update the current frame and AI results"""
        self.current_frame = frame
        if ai_results:
            self.ai_results = ai_results
    
    def update_status(self, status_data):
        """Update status information"""
        self.status_data = status_data
    
    def _draw_camera_preview(self):
        """Draw the camera preview area"""
        if self.current_frame is None:
            # Draw placeholder
            img = image.Image(
                self.preview_area['width'], 
                self.preview_area['height'], 
                image.Format.FMT_RGB888
            )
            img.draw_rect(0, 0, img.width(), img.height(), (50, 50, 50), -1)
            img.draw_string(
                img.width()//2 - 50, 
                img.height()//2, 
                "No Camera", 
                (255, 255, 255)
            )
        else:
            # Resize frame to fit preview area
            img = self.current_frame.resize(
                self.preview_area['width'], 
                self.preview_area['height']
            )
            
            # Draw AI detection overlays
            if self.ui_config.get('show_ai_overlay', True):
                self._draw_ai_overlays(img)
        
        # Display the frame
        self.display.show(img, x=self.preview_area['x'], y=self.preview_area['y'])
    
    def _draw_ai_overlays(self, img):
        """Draw AI detection overlays on the preview image"""
        for result in self.ai_results:
            result_type = result.get('type', '')
            
            if result_type == 'object_detection':
                # Draw bounding boxes for objects
                for obj in result.get('objects', []):
                    x, y, w, h = obj['bbox']
                    confidence = obj['confidence']
                    label = obj['label']
                    
                    # Scale coordinates to preview size
                    scale_x = self.preview_area['width'] / self.current_frame.width()
                    scale_y = self.preview_area['height'] / self.current_frame.height()
                    
                    x = int(x * scale_x)
                    y = int(y * scale_y)
                    w = int(w * scale_x)
                    h = int(h * scale_y)
                    
                    # Draw bounding box
                    img.draw_rect(x, y, w, h, (0, 255, 0), 2)
                    
                    # Draw label
                    label_text = f"{label} {confidence:.2f}"
                    img.draw_string(x, y-20, label_text, (0, 255, 0))
            
            elif result_type == 'face_detection':
                # Draw face bounding boxes
                for face in result.get('faces', []):
                    x, y, w, h = face['bbox']
                    
                    # Scale and draw
                    scale_x = self.preview_area['width'] / self.current_frame.width()
                    scale_y = self.preview_area['height'] / self.current_frame.height()
                    
                    x = int(x * scale_x)
                    y = int(y * scale_y)
                    w = int(w * scale_x)
                    h = int(h * scale_y)
                    
                    img.draw_rect(x, y, w, h, (255, 0, 0), 2)
                    
                    # Draw emotion if available
                    if 'emotion' in face:
                        emotion_text = f"{face['emotion']} {face.get('emotion_confidence', 0):.2f}"
                        img.draw_string(x, y-20, emotion_text, (255, 0, 0))
    
    def _draw_ui_panel(self):
        """Draw the right UI panel with controls"""
        # Create UI panel image
        panel_img = image.Image(
            self.ui_area['width'], 
            self.ui_area['height'], 
            image.Format.FMT_RGB888
        )
        
        # Fill background
        panel_img.draw_rect(0, 0, panel_img.width(), panel_img.height(), (30, 30, 30), -1)
        
        # Draw title
        panel_img.draw_string(10, 10, "Controls", (255, 255, 255))
        
        # Draw buttons
        for button in self.buttons.values():
            button.draw(panel_img, self.ui_area['x'], self.ui_area['y'])
        
        # Draw checkboxes
        for checkbox in self.checkboxes.values():
            checkbox.draw(panel_img, self.ui_area['x'], self.ui_area['y'])
        
        # Display UI panel
        self.display.show(panel_img, x=self.ui_area['x'], y=self.ui_area['y'])
    
    def _draw_status_bar(self):
        """Draw the status bar"""
        if self.status_bar:
            self.status_bar.update(self.status_data)
            status_img = self.status_bar.render()
            self.display.show(status_img, x=self.status_bar.x, y=self.status_bar.y)
    
    def draw(self):
        """Draw the complete UI"""
        try:
            # Draw camera preview
            self._draw_camera_preview()
            
            # Draw UI panel
            self._draw_ui_panel()
            
            # Draw status bar
            self._draw_status_bar()
            
        except Exception as e:
            logger.error(f"UI drawing error: {e}")
            # Draw error message
            error_img = image.Image(self.screen_width, self.screen_height, image.Format.FMT_RGB888)
            error_img.draw_rect(0, 0, self.screen_width, self.screen_height, (50, 0, 0), -1)
            error_img.draw_string(
                self.screen_width//2 - 50, 
                self.screen_height//2, 
                "UI Error", 
                (255, 255, 255)
            )
            self.display.show(error_img)
