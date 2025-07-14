#!/usr/bin/env python3
"""
Fixed Life Logger
Version that handles touch coordinate mapping issues
"""

import time
from maix import camera, display, touchscreen, image, app

def map_touch_coordinates(touch_x, touch_y, display_width=640, display_height=480):
    """Map touch coordinates to display coordinates"""
    # Based on the test, touches seem to cluster around (245, 1)
    # This suggests the touch coordinates might need scaling or mapping
    
    # Try different mapping strategies
    mapped_x = touch_x
    mapped_y = touch_y
    
    # If Y is consistently low (like 1), it might be swapped or scaled
    if touch_y < 10:
        # Might be X/Y swapped or Y needs scaling
        mapped_y = int((touch_x / 640.0) * 480)  # Scale X to Y range
        mapped_x = max(0, min(639, touch_x))
    
    # Ensure coordinates are within bounds
    mapped_x = max(0, min(display_width - 1, mapped_x))
    mapped_y = max(0, min(display_height - 1, mapped_y))
    
    return mapped_x, mapped_y

def main():
    print("🚀 Fixed Life Logger Starting...")
    
    # Initialize hardware
    try:
        cam = camera.Camera(640, 480)
        disp = display.Display()
        touch = touchscreen.TouchScreen()
        print(f"✅ Hardware ready: {disp.width()}x{disp.height()}")
    except Exception as e:
        print(f"❌ Hardware failed: {e}")
        return
    
    # UI state
    recording = False
    frame_count = 0
    last_touch_time = 0
    touch_debug = True
    
    # UI layout for 640x480
    preview_width = 480
    preview_height = 360
    panel_x = 480
    panel_width = 160
    
    # Button definitions
    start_button = {
        "x": panel_x + 10, "y": 60,
        "width": 140, "height": 40,
        "text": "START"
    }
    
    print("📱 Starting UI loop...")
    
    try:
        while not app.need_exit():
            # Capture camera frame
            frame = cam.read()
            frame_count += 1
            
            # Create main display image
            main_img = image.Image(640, 480, image.Format.FMT_RGB888)
            main_img.draw_rect(0, 0, 640, 480, image.Color.from_rgb(20, 20, 20), -1)
            
            # Draw camera preview (left side)
            try:
                preview = frame.resize(preview_width, preview_height)
                main_img.draw_image(0, 10, preview)
            except Exception as e:
                # Fallback: draw placeholder
                main_img.draw_rect(0, 10, preview_width, preview_height, image.Color.from_rgb(50, 50, 50), -1)
                main_img.draw_string(200, 200, "CAMERA ERROR", image.Color.from_rgb(255, 255, 255))
            
            # Draw UI panel (right side)
            main_img.draw_rect(panel_x, 0, panel_width, 480, image.Color.from_rgb(40, 40, 40), -1)
            
            # Title
            main_img.draw_string(panel_x + 20, 20, "LIFE LOG", image.Color.from_rgb(255, 255, 255))
            
            # Start/Stop button
            button_color = image.Color.from_rgb(200, 100, 100) if recording else image.Color.from_rgb(100, 200, 100)
            main_img.draw_rect(start_button["x"], start_button["y"], 
                             start_button["width"], start_button["height"], 
                             button_color, -1)
            
            # Button border
            main_img.draw_rect(start_button["x"], start_button["y"], 
                             start_button["width"], start_button["height"], 
                             image.Color.from_rgb(255, 255, 255), 2)
            
            # Button text
            button_text = "STOP" if recording else "START"
            text_x = start_button["x"] + 40
            text_y = start_button["y"] + 15
            main_img.draw_string(text_x, text_y, button_text, image.Color.from_rgb(255, 255, 255))
            
            # Status info
            status_y = 120
            main_img.draw_string(panel_x + 10, status_y, f"Frame: {frame_count}", image.Color.from_rgb(200, 200, 200))
            main_img.draw_string(panel_x + 10, status_y + 20, f"State: {'REC' if recording else 'IDLE'}", image.Color.from_rgb(200, 200, 200))
            
            # FPS on camera
            fps_text = f"FPS: {frame_count % 30}"
            main_img.draw_string(10, 380, fps_text, image.Color.from_rgb(255, 255, 0))
            
            # Handle touch input
            touch_data = touch.read()
            if touch_data[0]:  # Touch detected
                raw_x, raw_y = touch_data[1], touch_data[2]
                touch_x, touch_y = map_touch_coordinates(raw_x, raw_y)
                current_time = time.time()
                
                # Debounce touch
                if current_time - last_touch_time > 0.5:
                    last_touch_time = current_time
                    
                    if touch_debug:
                        print(f"👆 Touch: raw({raw_x}, {raw_y}) -> mapped({touch_x}, {touch_y})")
                    
                    # Check if touch is on the START/STOP button
                    if (start_button["x"] <= touch_x <= start_button["x"] + start_button["width"] and 
                        start_button["y"] <= touch_y <= start_button["y"] + start_button["height"]):
                        recording = not recording
                        print(f"🔴 Recording: {recording}")
                        touch_debug = False  # Reduce debug spam after first successful touch
                    
                    # Draw touch indicator
                    main_img.draw_circle(touch_x, touch_y, 20, image.Color.from_rgb(255, 255, 0), 3)
                    main_img.draw_string(10, 450, f"Touch: ({touch_x},{touch_y})", image.Color.from_rgb(255, 255, 0))
            
            # Recording indicator
            if recording:
                # Red dot in corner
                main_img.draw_circle(620, 20, 8, image.Color.from_rgb(255, 0, 0), -1)
                
                # Simulate AI detection (blink effect)
                if frame_count % 60 < 30:  # 30 frames on, 30 frames off
                    main_img.draw_rect(50, 50, 120, 80, image.Color.from_rgb(0, 255, 0), 3)
                    main_img.draw_string(55, 35, "AI DETECT", image.Color.from_rgb(0, 255, 0))
            
            # Display the composite image
            disp.show(main_img)
            
            # Small delay for ~30 FPS
            time.sleep(0.033)
            
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    try:
        cam.close()
        print("✅ Cleanup complete")
    except:
        pass

if __name__ == "__main__":
    main()
