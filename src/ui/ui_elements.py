"""
UI Elements
Custom UI components for the Companion Capture App

Author: Companion Intelligence
Date: July 13, 2025
"""

from maix import image

class Button:
    """Custom button UI element"""
    
    def __init__(self, x, y, width, height, text="", 
                 color_normal=(100, 100, 100), color_pressed=(150, 150, 150),
                 text_color=(255, 255, 255)):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.color_normal = color_normal
        self.color_pressed = color_pressed
        self.text_color = text_color
        self.pressed = False
    
    def is_touched(self, touch_x, touch_y):
        """Check if touch coordinates are within button bounds"""
        return (self.x <= touch_x <= self.x + self.width and 
                self.y <= touch_y <= self.y + self.height)
    
    def set_pressed(self, pressed):
        """Set button pressed state"""
        self.pressed = pressed
    
    def draw(self, img, offset_x=0, offset_y=0):
        """Draw button on the given image"""
        # Adjust coordinates for offset
        draw_x = self.x - offset_x
        draw_y = self.y - offset_y
        
        # Choose color based on state
        color = self.color_pressed if self.pressed else self.color_normal
        
        # Draw button background
        img.draw_rect(draw_x, draw_y, self.width, self.height, color, -1)
        
        # Draw button border
        img.draw_rect(draw_x, draw_y, self.width, self.height, (200, 200, 200), 2)
        
        # Draw text centered
        if self.text:
            text_x = draw_x + (self.width - len(self.text) * 6) // 2
            text_y = draw_y + (self.height - 12) // 2
            img.draw_string(text_x, text_y, self.text, self.text_color)

class Checkbox:
    """Custom checkbox UI element"""
    
    def __init__(self, x, y, width, height, text="", checked=False,
                 color_unchecked=(100, 100, 100), color_checked=(0, 200, 0),
                 text_color=(255, 255, 255)):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.checked = checked
        self.color_unchecked = color_unchecked
        self.color_checked = color_checked
        self.text_color = text_color
    
    def is_touched(self, touch_x, touch_y):
        """Check if touch coordinates are within checkbox bounds (including text)"""
        text_width = len(self.text) * 6 if self.text else 0
        total_width = self.width + 5 + text_width
        return (self.x <= touch_x <= self.x + total_width and 
                self.y <= touch_y <= self.y + self.height)
    
    def toggle(self):
        """Toggle checkbox state"""
        self.checked = not self.checked
    
    def draw(self, img, offset_x=0, offset_y=0):
        """Draw checkbox on the given image"""
        # Adjust coordinates for offset
        draw_x = self.x - offset_x
        draw_y = self.y - offset_y
        
        # Choose color based on state
        color = self.color_checked if self.checked else self.color_unchecked
        
        # Draw checkbox box
        img.draw_rect(draw_x, draw_y, self.width, self.height, color, -1)
        
        # Draw checkbox border
        img.draw_rect(draw_x, draw_y, self.width, self.height, (200, 200, 200), 1)
        
        # Draw checkmark if checked
        if self.checked:
            # Simple checkmark (diagonal lines)
            center_x = draw_x + self.width // 2
            center_y = draw_y + self.height // 2
            img.draw_line(
                center_x - 3, center_y,
                center_x - 1, center_y + 2,
                (255, 255, 255), 2
            )
            img.draw_line(
                center_x - 1, center_y + 2,
                center_x + 3, center_y - 2,
                (255, 255, 255), 2
            )
        
        # Draw text
        if self.text:
            text_x = draw_x + self.width + 5
            text_y = draw_y + (self.height - 12) // 2
            img.draw_string(text_x, text_y, self.text, self.text_color)

class StatusBar:
    """Status bar UI element"""
    
    def __init__(self, x, y, width, height, 
                 background_color=(20, 20, 20), text_color=(255, 255, 255)):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.background_color = background_color
        self.text_color = text_color
        self.status_data = {}
    
    def update(self, status_data):
        """Update status data"""
        self.status_data = status_data
    
    def render(self):
        """Render status bar and return image"""
        # Create status bar image
        img = image.Image(self.width, self.height, image.Format.FMT_RGB888)
        
        # Fill background
        img.draw_rect(0, 0, self.width, self.height, self.background_color, -1)
        
        # Draw status information
        y_offset = 5
        line_height = 15
        
        # App state
        state = self.status_data.get('state', 'UNKNOWN')
        img.draw_string(5, y_offset, f"State: {state}", self.text_color)
        y_offset += line_height
        
        # FPS
        if self.status_data.get('fps') is not None:
            fps = self.status_data['fps']
            img.draw_string(5, y_offset, f"FPS: {fps}", self.text_color)
            y_offset += line_height
        
        # Memory
        if self.status_data.get('memory_free') is not None:
            memory_mb = self.status_data['memory_free'] // (1024 * 1024)
            img.draw_string(5, y_offset, f"Memory: {memory_mb}MB", self.text_color)
            y_offset += line_height
        
        # Active AI models
        active_models = self.status_data.get('ai_models_active', [])
        if active_models:
            models_text = f"AI: {len(active_models)} active"
            img.draw_string(5, y_offset, models_text, self.text_color)
            y_offset += line_height
        
        # Storage usage
        if self.status_data.get('storage_used') is not None:
            storage_mb = self.status_data['storage_used'] // (1024 * 1024)
            img.draw_string(5, y_offset, f"Storage: {storage_mb}MB", self.text_color)
        
        return img

class ProgressBar:
    """Progress bar UI element"""
    
    def __init__(self, x, y, width, height, min_value=0, max_value=100,
                 background_color=(50, 50, 50), progress_color=(0, 150, 0)):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = min_value
        self.background_color = background_color
        self.progress_color = progress_color
    
    def set_value(self, value):
        """Set progress bar value"""
        self.current_value = max(self.min_value, min(self.max_value, value))
    
    def draw(self, img, offset_x=0, offset_y=0):
        """Draw progress bar on the given image"""
        # Adjust coordinates for offset
        draw_x = self.x - offset_x
        draw_y = self.y - offset_y
        
        # Draw background
        img.draw_rect(draw_x, draw_y, self.width, self.height, self.background_color, -1)
        
        # Draw progress
        progress_ratio = (self.current_value - self.min_value) / (self.max_value - self.min_value)
        progress_width = int(self.width * progress_ratio)
        
        if progress_width > 0:
            img.draw_rect(draw_x, draw_y, progress_width, self.height, self.progress_color, -1)
        
        # Draw border
        img.draw_rect(draw_x, draw_y, self.width, self.height, (200, 200, 200), 1)

class TextLabel:
    """Simple text label UI element"""
    
    def __init__(self, x, y, text="", text_color=(255, 255, 255)):
        self.x = x
        self.y = y
        self.text = text
        self.text_color = text_color
    
    def set_text(self, text):
        """Set label text"""
        self.text = text
    
    def draw(self, img, offset_x=0, offset_y=0):
        """Draw text label on the given image"""
        draw_x = self.x - offset_x
        draw_y = self.y - offset_y
        
        if self.text:
            img.draw_string(draw_x, draw_y, self.text, self.text_color)
