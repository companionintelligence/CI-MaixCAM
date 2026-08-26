#!/usr/bin/env python3
"""
Setup Screen for Companion Capture App
Configure AI models before starting the main application

This screen allows users to select which AI models to enable:
- Computer Vision (8 models)
- Audio Processing (3 models) 
- Media Capabilities (2 models)

Author: Companion Intelligence
Date: July 14, 2025
"""

from maix import camera, display, image, touchscreen, app, time
import json
import os

from utils.models import (
    AUDIO_MODELS,
    COMPUTER_VISION_MODELS,
    MEDIA_MODELS,
    migrate_model_states,
    read_model_states,
)
from utils.paths import CONFIG_PATH, ensure_config_dir, migrate_legacy_config

class SimpleCheckbox:
    """Simple checkbox widget for model selection"""
    
    def __init__(self, x, y, width, height, text="", checked=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.checked = checked
        self.checkbox_size = 20
    
    def is_touched(self, touch_x, touch_y):
        # Expand touch area for easier selection
        margin = 5
        return (self.x - margin <= touch_x <= self.x + self.width + margin and
                self.y - margin <= touch_y <= self.y + self.height + margin)
    
    def toggle(self):
        self.checked = not self.checked
        print(f"✅ Toggled '{self.text}': {'ON' if self.checked else 'OFF'}")
    
    def draw(self, img):
        # Draw checkbox square
        checkbox_x = self.x
        checkbox_y = self.y + (self.height - self.checkbox_size) // 2
        
        # Background color based on state
        color = (0, 150, 0) if self.checked else (60, 60, 60)
        img.draw_rect(checkbox_x, checkbox_y, self.checkbox_size, self.checkbox_size,
                     image.Color.from_rgb(*color), -1)
        
        # Border
        border_color = (255, 255, 255) if self.checked else (120, 120, 120)
        img.draw_rect(checkbox_x, checkbox_y, self.checkbox_size, self.checkbox_size,
                     image.Color.from_rgb(*border_color), 2)
        
        # Checkmark if checked
        if self.checked:
            # Simple checkmark using lines
            check_x = checkbox_x + 4
            check_y = checkbox_y + 10
            img.draw_line(check_x, check_y, check_x + 4, check_y + 4,
                         image.Color.from_rgb(255, 255, 255), 2)
            img.draw_line(check_x + 4, check_y + 4, check_x + 12, check_y - 4,
                         image.Color.from_rgb(255, 255, 255), 2)
        
        # Text label
        text_x = checkbox_x + self.checkbox_size + 10
        text_y = checkbox_y + 4
        text_color = (255, 255, 255) if self.checked else (200, 200, 200)
        img.draw_string(text_x, text_y, self.text, image.Color.from_rgb(*text_color))

class SimpleButton:
    """Simple button widget"""
    
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
        return (self.x <= touch_x <= self.x + self.width and 
                self.y <= touch_y <= self.y + self.height)
    
    def set_pressed(self, pressed):
        self.pressed = pressed
    
    def draw(self, img):
        color = self.color_pressed if self.pressed else self.color_normal
        img.draw_rect(self.x, self.y, self.width, self.height, 
                     image.Color.from_rgb(*color), -1)
        img.draw_rect(self.x, self.y, self.width, self.height,
                     image.Color.from_rgb(200, 200, 200), 2)
        if self.text:
            text_x = self.x + (self.width - len(self.text) * 8) // 2
            text_y = self.y + (self.height - 12) // 2
            img.draw_string(text_x, text_y, self.text, image.Color.from_rgb(255, 255, 255))

class SetupScreen:
    """Setup screen for AI model configuration"""
    
    def __init__(self):
        self.display_width = 640
        self.display_height = 480
        
        # Configuration file path (canonical - see utils/paths.py). Set before
        # the checkboxes: they are seeded from what this file already holds.
        self.config_file = CONFIG_PATH
        
        # Model categories and checkboxes
        self.checkboxes = []
        self.buttons = []
        
        # Create checkboxes for all AI models
        self._create_model_checkboxes()
        self._create_control_buttons()
    
    def _create_model_checkboxes(self):
        """Create checkboxes for all AI models from PROJECT_PLAN.MD"""
        
        # Starting positions
        start_x = 40
        start_y = 60
        row_height = 30
        
        # Model names come from utils/models.py, and their state from the one
        # stored record - so the screen opens showing what the device is
        # configured to run, and pressing START cannot silently reset it.
        # Anything the file does not mention falls back to the shared default.
        model_states = read_model_states(self._load_existing_configuration())
        sections = (COMPUTER_VISION_MODELS, AUDIO_MODELS, MEDIA_MODELS)
        
        current_y = start_y
        
        for section_index, section in enumerate(sections):
            for model in section:
                checkbox = SimpleCheckbox(start_x, current_y, 300, 25, model,
                                         checked=model_states[model])
                self.checkboxes.append(checkbox)
                current_y += row_height
            
            # Add spacing between sections
            if section_index < len(sections) - 1:
                current_y += 15
    
    def _create_control_buttons(self):
        """Create control buttons"""
        
        button_width = 100
        button_height = 40
        button_y = self.display_height - 60
        
        # Start button
        start_btn = SimpleButton(self.display_width - 220, button_y, 
                               button_width, button_height, "START",
                               color_normal=(0, 120, 0), color_pressed=(0, 180, 0))
        self.buttons.append(('start', start_btn))
        
        # Cancel button  
        cancel_btn = SimpleButton(self.display_width - 110, button_y,
                                button_width, button_height, "CANCEL", 
                                color_normal=(120, 0, 0), color_pressed=(180, 0, 0))
        self.buttons.append(('cancel', cancel_btn))
        
        # Select All button
        select_all_btn = SimpleButton(40, button_y, button_width, button_height, "ALL ON",
                                    color_normal=(0, 0, 120), color_pressed=(0, 0, 180))
        self.buttons.append(('select_all', select_all_btn))
        
        # Clear All button
        clear_all_btn = SimpleButton(150, button_y, button_width, button_height, "ALL OFF",
                                   color_normal=(80, 80, 80), color_pressed=(120, 120, 120))
        self.buttons.append(('clear_all', clear_all_btn))
    
    def handle_touch(self, touch_x, touch_y):
        """Handle touch events"""
        
        # Check checkboxes
        for checkbox in self.checkboxes:
            if checkbox.is_touched(touch_x, touch_y):
                checkbox.toggle()
                return 'checkbox'
        
        # Check buttons
        for button_name, button in self.buttons:
            if button.is_touched(touch_x, touch_y):
                button.set_pressed(True)
                print(f"🔥 Button pressed: {button_name}")
                
                if button_name == 'start':
                    return 'start'
                elif button_name == 'cancel':
                    return 'cancel'
                elif button_name == 'select_all':
                    self._select_all_models(True)
                    return 'select_all'
                elif button_name == 'clear_all':
                    self._select_all_models(False)
                    return 'clear_all'
        
        return None
    
    def _select_all_models(self, enable):
        """Enable or disable all models"""
        for checkbox in self.checkboxes:
            checkbox.checked = enable
        print(f"🎛️ All models {'ENABLED' if enable else 'DISABLED'}")
    
    def get_selected_models(self):
        """Get list of selected models"""
        selected = []
        for checkbox in self.checkboxes:
            if checkbox.checked:
                selected.append(checkbox.text)
        return selected
    
    def _load_existing_configuration(self):
        """Read the current configuration file so a save preserves other keys"""
        
        # Pull forward a legacy config file if this device predates the
        # canonical path
        migrate_legacy_config(self.config_file)
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    existing = json.load(f)
                if isinstance(existing, dict):
                    # Fold an older build's duplicate enabled-state records
                    # into model_states; saving below persists the cleanup
                    migrate_model_states(existing)
                    return existing
        except Exception as e:
            print(f"⚠️ Could not read existing configuration: {e}")
        
        return {}
    
    def save_configuration(self):
        """Save selected models to configuration file"""
        
        # The whole app shares one config file, so read what is already there
        # and update only the keys this screen owns
        config = self._load_existing_configuration()
        
        config["timestamp"] = time.time()
        config["model_states"] = {}
        
        # Save individual model states. This is the only stored record of
        # which models run - the enabled list is derived from it on read, so
        # nothing else in the file can contradict it.
        for checkbox in self.checkboxes:
            config["model_states"][checkbox.text] = checkbox.checked
        
        try:
            # Ensure directory exists
            ensure_config_dir(self.config_file)
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"💾 Configuration saved to {self.config_file}")
            print(f"🎯 Selected models: {len(self.get_selected_models())}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")
            return False
    
    def draw(self, img):
        """Draw the setup screen"""
        
        # Clear background
        img.draw_rect(0, 0, self.display_width, self.display_height,
                     image.Color.from_rgb(20, 20, 30), -1)
        
        # Title
        title = "Companion Capture Setup"
        img.draw_string(40, 20, title, image.Color.from_rgb(255, 255, 255), scale=1.5)
        
        # Section headers
        img.draw_string(40, 45, "Select AI Models to Enable:", image.Color.from_rgb(200, 200, 200))
        
        # Draw all checkboxes
        for checkbox in self.checkboxes:
            checkbox.draw(img)
        
        # Draw all buttons
        for _, button in self.buttons:
            button.draw(img)
        
        # Status information
        selected_count = sum(1 for cb in self.checkboxes if cb.checked)
        status_text = f"Models Selected: {selected_count}/{len(self.checkboxes)}"
        img.draw_string(350, self.display_height - 30, status_text, 
                       image.Color.from_rgb(150, 150, 150))

def run_setup_screen():
    """Run the setup screen interface"""
    
    print("🎨 Starting Companion Capture Setup Screen...")
    
    # Initialize hardware
    disp = display.Display()
    touch = touchscreen.TouchScreen()
    
    # Create setup screen
    setup = SetupScreen()
    
    # Main loop
    last_touch_time = 0
    button_release_delay = 500  # ms
    
    while not app.need_exit():
        # Create image
        img = image.Image(disp.width(), disp.height())
        
        # Draw setup screen
        setup.draw(img)
        
        # Handle touch input
        x, y, pressed = touch.read()
        current_time = time.ticks_ms()
        
        if pressed:
            result = setup.handle_touch(x, y)
            
            if result == 'start':
                # Save configuration and start main app
                if setup.save_configuration():
                    selected = setup.get_selected_models()
                    print(f"🚀 Starting with {len(selected)} models:")
                    for model in selected:
                        print(f"   ✅ {model}")
                    
                    # Show confirmation before starting
                    img.draw_rect(100, 200, 440, 80, image.Color.from_rgb(0, 100, 0), -1)
                    img.draw_rect(100, 200, 440, 80, image.Color.from_rgb(255, 255, 255), 2)
                    img.draw_string(130, 225, "Configuration Saved!", image.Color.from_rgb(255, 255, 255))
                    img.draw_string(130, 245, "Starting Companion Capture...", image.Color.from_rgb(255, 255, 255))
                    disp.show(img)
                    time.sleep(2)
                    
                    return True
                    
            elif result == 'cancel':
                print("❌ Setup cancelled")
                return False
            
            last_touch_time = current_time
        
        # Release button states after delay
        if current_time - last_touch_time > button_release_delay:
            for _, button in setup.buttons:
                button.set_pressed(False)
        
        # Show image
        disp.show(img)
        time.sleep_ms(30)  # ~30 FPS
    
    return False

def main():
    """Main entry point"""
    
    try:
        if run_setup_screen():
            print("🎯 Setup completed successfully!")
            print("📱 Ready to start main application...")
            # Here you would start your main capture application
        else:
            print("🚪 Setup cancelled by user")
            
    except KeyboardInterrupt:
        print("\n🛑 Setup interrupted by user")
    except Exception as e:
        print(f"❌ Setup error: {e}")

if __name__ == "__main__":
    main()
