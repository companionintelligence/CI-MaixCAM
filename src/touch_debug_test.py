#!/usr/bin/env python3
"""
Touch Debug Test
Debug touch coordinates and button positioning

This helps identify why the AI button isn't responding to touches.

Author: Companion Intelligence
Date: July 14, 2025
"""

from maix import camera, display, image, touchscreen, app
import time as python_time

def test_touch_coordinates():
    """Test and debug touch coordinates"""
    print("🖱️ Touch Debug Test")
    print("Touch anywhere on screen to see coordinates")
    
    # Initialize hardware
    cam = camera.Camera(640, 480)
    disp = display.Display()
    touch = touchscreen.TouchScreen()
    
    # AI button bounds (same as in the drawer test)
    ai_button_x = 485  # 480 + 5
    ai_button_y = 5
    ai_button_width = 30
    ai_button_height = 30
    
    # Touch history
    touch_history = []
    max_history = 10
    
    frame_count = 0
    
    while not app.need_exit():
        # Get camera frame
        img = cam.read()
        
        # Handle touch events
        touch_data = touch.read()
        if touch_data[0]:  # Touch detected
            raw_x, raw_y = touch_data[1], touch_data[2]
            
            # Add to history
            touch_history.append((raw_x, raw_y))
            if len(touch_history) > max_history:
                touch_history.pop(0)
            
            # Check if touch is in AI button area
            in_ai_button = (ai_button_x <= raw_x <= ai_button_x + ai_button_width and 
                           ai_button_y <= raw_y <= ai_button_y + ai_button_height)
            
            print(f"Touch: ({raw_x}, {raw_y}) - AI Button: {'YES' if in_ai_button else 'NO'}")
        
        # Draw camera preview
        preview_img = img.resize(480, 480)
        
        # Create full display image
        display_img = image.Image(640, 480, image.Format.FMT_RGB888)
        display_img.draw_image(0, 0, preview_img)
        
        # Draw UI panel background (right side)
        display_img.draw_rect(480, 0, 160, 480, image.Color.from_rgb(20, 20, 20), -1)
        
        # Draw AI button with clear bounds
        display_img.draw_rect(ai_button_x, ai_button_y, ai_button_width, ai_button_height,
                             image.Color.from_rgb(100, 100, 100), -1)
        display_img.draw_rect(ai_button_x, ai_button_y, ai_button_width, ai_button_height,
                             image.Color.from_rgb(255, 255, 255), 2)
        
        # Draw AI text
        display_img.draw_string(ai_button_x + 8, ai_button_y + 10, "AI", 
                               image.Color.from_rgb(255, 255, 255))
        
        # Draw button coordinates
        display_img.draw_string(490, 50, f"Button:", image.Color.from_rgb(200, 200, 200))
        display_img.draw_string(490, 65, f"X:{ai_button_x}-{ai_button_x + ai_button_width}", 
                               image.Color.from_rgb(200, 200, 200))
        display_img.draw_string(490, 80, f"Y:{ai_button_y}-{ai_button_y + ai_button_height}", 
                               image.Color.from_rgb(200, 200, 200))
        
        # Draw touch history
        display_img.draw_string(490, 110, "Touch History:", image.Color.from_rgb(150, 150, 150))
        for i, (tx, ty) in enumerate(touch_history[-5:]):  # Show last 5 touches
            y_pos = 125 + (i * 15)
            in_button = (ai_button_x <= tx <= ai_button_x + ai_button_width and 
                        ai_button_y <= ty <= ai_button_y + ai_button_height)
            color = (0, 255, 0) if in_button else (255, 255, 255)
            display_img.draw_string(490, y_pos, f"{tx},{ty}", image.Color.from_rgb(*color))
        
        # Draw crosshairs at current touch if active
        if touch_data[0]:
            tx, ty = touch_data[1], touch_data[2]
            # Draw crosshairs
            display_img.draw_line(tx - 10, ty, tx + 10, ty, image.Color.from_rgb(255, 0, 0), 2)
            display_img.draw_line(tx, ty - 10, tx, ty + 10, image.Color.from_rgb(255, 0, 0), 2)
            
            # Draw touch point
            display_img.draw_circle(tx, ty, 5, image.Color.from_rgb(255, 0, 0), 2)
        
        # Draw frame info
        display_img.draw_string(10, 10, f"Frame: {frame_count}", image.Color.from_rgb(255, 255, 255))
        display_img.draw_string(10, 25, f"FPS: {time.fps():.1f}", image.Color.from_rgb(255, 255, 255))
        display_img.draw_string(10, 40, "Touch anywhere to debug", image.Color.from_rgb(255, 255, 0))
        
        # Instructions
        display_img.draw_string(490, 220, "Debug Info:", image.Color.from_rgb(200, 200, 200))
        display_img.draw_string(490, 235, "Green = Hit AI", image.Color.from_rgb(0, 255, 0))
        display_img.draw_string(490, 250, "White = Miss", image.Color.from_rgb(255, 255, 255))
        display_img.draw_string(490, 265, "Red crosshair", image.Color.from_rgb(255, 0, 0))
        display_img.draw_string(490, 280, "= current touch", image.Color.from_rgb(255, 0, 0))
        
        # Exit instructions
        display_img.draw_string(490, 320, "Touch here to", image.Color.from_rgb(150, 150, 150))
        display_img.draw_string(490, 335, "test AI button", image.Color.from_rgb(150, 150, 150))
        display_img.draw_string(490, 350, "coordinates", image.Color.from_rgb(150, 150, 150))
        
        # Show display
        disp.show(display_img)
        
        frame_count += 1
        
        # Auto-exit after showing coordinates for a while
        if frame_count > 1000:  # About 30 seconds at 30 FPS
            break
    
    cam.close()
    print("✅ Touch debug test completed!")
    print("Check the console output for touch coordinate analysis")

if __name__ == "__main__":
    test_touch_coordinates()
