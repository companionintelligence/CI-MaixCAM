"""
AI Model Selection Drawer
Expandable UI drawer for selecting which AI models to enable/disable

Based on PROJECT_PLAN.MD Step 3.5: Create right sidebar for AI model toggle checkboxes
Based on standalone test results showing 25+ AI models available on MaixCAM

Author: Companion Intelligence
Date: July 14, 2025
"""

from maix import image, time
from .ui_elements import Checkbox, Button

class ModelDrawer:
    """Sliding drawer for AI model selection with checkboxes"""
    
    def __init__(self, x, y, width, height, models_config):
        """Initialize the model drawer
        
        Args:
            x, y: Position of the drawer
            width, height: Drawer dimensions  
            models_config: Dictionary of available AI models and their status
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.models_config = models_config
        
        # Drawer state
        self.expanded = False
        self.collapsed_width = 40  # Width when collapsed
        self.expanded_width = width  # Full width when expanded
        self.current_width = self.collapsed_width
        
        # Animation properties
        self.animation_speed = 8  # pixels per frame
        self.target_width = self.collapsed_width
        
        # Scroll properties for model list
        self.scroll_offset = 0
        self.max_scroll = 0
        self.item_height = 25
        self.visible_items = (height - 60) // self.item_height  # Space for header and toggle button
        
        # UI elements
        self.toggle_button = None
        self.checkboxes = {}
        self.scroll_up_button = None
        self.scroll_down_button = None
        
        # Initialize drawer
        self._initialize_drawer()
    
    def _initialize_drawer(self):
        """Initialize drawer UI elements"""
        
        # Toggle button (always visible) - Enlarged for better touch detection
        self.toggle_button = Button(
            x=self.x + 5,
            y=self.y + 5,
            width=50,
            height=50,
            text="AI",
            color_normal=(70, 70, 70),
            color_pressed=(100, 100, 100)
        )
        
        # Create checkboxes for each AI model
        self._create_model_checkboxes()
        
        # Scroll buttons
        self.scroll_up_button = Button(
            x=self.x + self.expanded_width - 35,
            y=self.y + 40,
            width=30,
            height=20,
            text="^",
            color_normal=(60, 60, 60),
            color_pressed=(90, 90, 90)
        )
        
        self.scroll_down_button = Button(
            x=self.x + self.expanded_width - 35,
            y=self.y + self.height - 25,
            width=30,
            height=20,
            text="v",
            color_normal=(60, 60, 60),
            color_pressed=(90, 90, 90)
        )
    
    def _create_model_checkboxes(self):
        """Create checkboxes for each available AI model"""
        
        # AI Models available on MaixCAM (from standalone test results)
        available_models = [
            ("object_detection", "YOLOv8 Objects", "yolov8n.mud"),
            ("face_detection", "Face Detection", "retinaface.mud"),
            ("face_emotion", "Face Emotion", "face_emotion.mud"),
            ("face_recognition", "Face Recognition", "face_feature.mud"),
            ("ocr_detection", "Text OCR", "pp_ocr.mud"),
            ("hand_landmarks", "Hand Tracking", "hand_landmarks.mud"),
            ("pose_detection", "Human Pose", "yolov8n_pose.mud"),
            ("object_segmentation", "Object Segmentation", "yolov8n_seg.mud"),
            ("pose_landmarks", "Pose Landmarks", "yolo11n_pose.mud"),
            ("qr_detection", "QR Code Detection", "yolov8_qr_det_seg.mud"),
            ("object_tracking", "Object Tracking", "nanotrack.mud"),
            ("classification", "Image Classification", "mobilenetv2.mud"),
            ("yolo11_detection", "YOLO11 Objects", "yolo11n.mud"),
            ("yolo11_segmentation", "YOLO11 Segmentation", "yolo11n_seg.mud"),
            ("oriented_detection", "Oriented Detection", "yolo11n_obb.mud"),
            ("face_landmarks", "Face Landmarks", "face_landmarks.mud"),
            ("audio_wakeword", "Audio Wakeword", "am_3332_192_int8.mud"),
            ("audio_recognition", "Audio Recognition", "am_7332_192_int8.mud"),
            ("face_detector_alt", "Face Detector Alt", "face_detector.mud"),
            ("yolov5_detection", "YOLOv5 Objects", "yolov5s.mud"),
        ]
        
        self.checkboxes.clear()
        
        for i, (model_key, display_name, model_file) in enumerate(available_models):
            # Get initial state from config
            initial_state = self.models_config.get(model_key, {}).get('enabled', False)
            
            checkbox = Checkbox(
                x=self.x + 10,
                y=self.y + 70 + (i * self.item_height),
                width=15,
                height=15,
                text=display_name,
                checked=initial_state,
                color_unchecked=(80, 80, 80),
                color_checked=(0, 180, 0)
            )
            
            self.checkboxes[model_key] = {
                'checkbox': checkbox,
                'display_name': display_name,
                'model_file': model_file,
                'enabled': initial_state
            }
        
        # Calculate max scroll based on number of models
        total_items = len(available_models)
        if total_items > self.visible_items:
            self.max_scroll = (total_items - self.visible_items) * self.item_height
        else:
            self.max_scroll = 0
    
    def toggle_drawer(self):
        """Toggle drawer between expanded and collapsed states"""
        self.expanded = not self.expanded
        self.target_width = self.expanded_width if self.expanded else self.collapsed_width
    
    def update_animation(self):
        """Update drawer animation (call this each frame)"""
        if self.current_width != self.target_width:
            if self.current_width < self.target_width:
                self.current_width = min(self.target_width, 
                                       self.current_width + self.animation_speed)
            else:
                self.current_width = max(self.target_width,
                                       self.current_width - self.animation_speed)
    
    def handle_touch(self, touch_x, touch_y):
        """Handle touch events for the drawer
        
        Returns:
            str: Action taken ('toggle', 'scroll_up', 'scroll_down', 'model_changed', None)
        """
        
        # Check toggle button
        if self.toggle_button.is_touched(touch_x, touch_y):
            self.toggle_button.set_pressed(True)
            self.toggle_drawer()
            return 'toggle'
        
        # Only handle other touches if drawer is expanded
        if not self.expanded:
            return None
        
        # Check scroll buttons
        if self.scroll_up_button.is_touched(touch_x, touch_y):
            self.scroll_up_button.set_pressed(True)
            self.scroll_up()
            return 'scroll_up'
        
        if self.scroll_down_button.is_touched(touch_x, touch_y):
            self.scroll_down_button.set_pressed(True)
            self.scroll_down()
            return 'scroll_down'
        
        # Check model checkboxes
        for model_key, model_data in self.checkboxes.items():
            checkbox = model_data['checkbox']
            
            # Adjust checkbox position for scroll offset
            checkbox_y = checkbox.y - self.scroll_offset
            
            # Only check if checkbox is visible
            if (checkbox_y >= self.y + 60 and 
                checkbox_y + checkbox.height <= self.y + self.height - 30):
                
                # Create temporary checkbox with adjusted position for touch testing
                temp_x = checkbox.x
                temp_y = checkbox_y
                
                if (temp_x <= touch_x <= temp_x + checkbox.width + len(checkbox.text) * 6 and
                    temp_y <= touch_y <= temp_y + checkbox.height):
                    
                    checkbox.toggle()
                    model_data['enabled'] = checkbox.checked
                    return 'model_changed'
        
        return None
    
    def scroll_up(self):
        """Scroll the model list up"""
        if self.scroll_offset > 0:
            self.scroll_offset = max(0, self.scroll_offset - self.item_height)
    
    def scroll_down(self):
        """Scroll the model list down"""
        if self.scroll_offset < self.max_scroll:
            self.scroll_offset = min(self.max_scroll, self.scroll_offset + self.item_height)
    
    def get_enabled_models(self):
        """Get list of currently enabled models
        
        Returns:
            dict: Dictionary of enabled models with their configuration
        """
        enabled = {}
        for model_key, model_data in self.checkboxes.items():
            if model_data['enabled']:
                enabled[model_key] = {
                    'display_name': model_data['display_name'],
                    'model_file': model_data['model_file'],
                    'enabled': True
                }
        return enabled
    
    def set_model_enabled(self, model_key, enabled):
        """Enable or disable a specific model
        
        Args:
            model_key (str): The model identifier
            enabled (bool): Whether to enable the model
        """
        if model_key in self.checkboxes:
            self.checkboxes[model_key]['checkbox'].checked = enabled
            self.checkboxes[model_key]['enabled'] = enabled
    
    def clear_touch_feedback(self):
        """Clear all button pressed states"""
        self.toggle_button.set_pressed(False)
        if self.expanded:
            self.scroll_up_button.set_pressed(False)
            self.scroll_down_button.set_pressed(False)
    
    def draw(self, img):
        """Draw the drawer on the given image"""
        
        # Update animation
        self.update_animation()
        
        # Draw drawer background
        drawer_color = (40, 40, 40) if self.expanded else (30, 30, 30)
        img.draw_rect(self.x, self.y, int(self.current_width), self.height, 
                     image.Color.from_rgb(*drawer_color), -1)
        
        # Draw drawer border
        img.draw_rect(self.x, self.y, int(self.current_width), self.height,
                     image.Color.from_rgb(100, 100, 100), 1)
        
        # Always draw toggle button
        self.toggle_button.draw(img)
        
        # Only draw expanded content if drawer is expanding or expanded
        if self.current_width > self.collapsed_width + 10:
            self._draw_expanded_content(img)
    
    def _draw_expanded_content(self, img):
        """Draw the expanded drawer content"""
        
        # Draw header
        img.draw_string(self.x + 45, self.y + 15, "AI Models", 
                       image.Color.from_rgb(200, 200, 200))
        
        # Draw separator line
        img.draw_line(self.x + 10, self.y + 35, self.x + self.expanded_width - 10, self.y + 35,
                     image.Color.from_rgb(100, 100, 100), 1)
        
        # Draw scroll indicators if needed
        if self.max_scroll > 0:
            self.scroll_up_button.draw(img)
            self.scroll_down_button.draw(img)
            
            # Draw scroll position indicator
            if self.max_scroll > 0:
                scroll_ratio = self.scroll_offset / self.max_scroll
                indicator_y = self.y + 65 + int(scroll_ratio * (self.height - 130))
                img.draw_rect(self.x + self.expanded_width - 8, indicator_y, 4, 10,
                             image.Color.from_rgb(120, 120, 120), -1)
        
        # Draw visible model checkboxes
        visible_start = self.y + 70
        visible_end = self.y + self.height - 30
        
        for model_key, model_data in self.checkboxes.items():
            checkbox = model_data['checkbox']
            
            # Calculate checkbox position with scroll offset
            checkbox_y = checkbox.y - self.scroll_offset
            
            # Only draw if checkbox is visible
            if (checkbox_y >= visible_start - self.item_height and 
                checkbox_y <= visible_end):
                
                # Create temporary checkbox with adjusted position
                temp_checkbox = Checkbox(
                    x=checkbox.x,
                    y=checkbox_y,
                    width=checkbox.width,
                    height=checkbox.height,
                    text=checkbox.text,
                    checked=checkbox.checked,
                    color_unchecked=checkbox.color_unchecked,
                    color_checked=checkbox.color_checked
                )
                
                # Only draw if within visible area
                if checkbox_y >= visible_start and checkbox_y + checkbox.height <= visible_end:
                    temp_checkbox.draw(img)
        
        # Draw enabled models count
        enabled_count = sum(1 for data in self.checkboxes.values() if data['enabled'])
        count_text = f"Enabled: {enabled_count}"
        img.draw_string(self.x + 10, self.y + self.height - 15, count_text,
                       image.Color.from_rgb(150, 150, 150))
