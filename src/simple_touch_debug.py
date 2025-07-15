#!/usr/bin/env python3
"""
Simple Touch Debug Test
Debug touch coordinates without time dependencies

Author: Companion Intelligence
Date: July 14, 2025
"""

from maix import camera, display, image, touchscreen, app

def simple_touch_test():
    """Simple touch coordinate test"""
    print("🖱️ Simple Touch Debug Test")
    print("Touch anywhere on screen to see coordinates")
    
    # Initialize hardware
    cam = camera.Camera(640, 480)
    disp = display.Display()
    touch = touchscreen.TouchScreen()
    
    # AI button bounds
    ai_button_x = 485
    ai_button_y = 5
    ai_button_width = 50
    ai_button_height = 50
    
    frame_count = 0
    touch_count = 0
    
    while not app.need_exit():
        # Get camera frame
        img = cam.read()
        
        # Handle touch events
        touch_data = touch.read()
        if touch_data[0]:  # Touch detected
            raw_x, raw_y = touch_data[1], touch_data[2]
            touch_count += 1
            
            # Check if touch is in AI button area
            in_ai_button = (ai_button_x <= raw_x <= ai_button_x + ai_button_width and 
                           ai_button_y <= raw_y <= ai_button_y + ai_button_height)
            
            print(f"Touch #{touch_count}: ({raw_x}, {raw_y}) - AI Button: {'HIT' if in_ai_button else 'MISS'}")
        
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
        display_img.draw_string(ai_button_x + 15, ai_button_y + 20, "AI", 
                               image.Color.from_rgb(255, 255, 255))
        
        # Draw button coordinates
        display_img.draw_string(490, 70, f"Button Area:", image.Color.from_rgb(200, 200, 200))
        display_img.draw_string(490, 85, f"X: {ai_button_x}-{ai_button_x + ai_button_width}", 
                               image.Color.from_rgb(200, 200, 200))
        display_img.draw_string(490, 100, f"Y: {ai_button_y}-{ai_button_y + ai_button_height}", 
                               image.Color.from_rgb(200, 200, 200))
        
        # Draw touch info
        display_img.draw_string(490, 130, f"Touches: {touch_count}", image.Color.from_rgb(150, 150, 150))
        
        # Draw crosshairs at current touch if active
        if touch_data[0]:
            tx, ty = touch_data[1], touch_data[2]
            # Draw crosshairs
            display_img.draw_line(tx - 10, ty, tx + 10, ty, image.Color.from_rgb(255, 0, 0), 2)
            display_img.draw_line(tx, ty - 10, tx, ty + 10, image.Color.from_rgb(255, 0, 0), 2)
            
            # Draw touch coordinates
            display_img.draw_string(10, 40, f"Touch: {tx},{ty}", image.Color.from_rgb(255, 0, 0))
            
            # Draw hit/miss status
            in_button = (ai_button_x <= tx <= ai_button_x + ai_button_width and 
                        ai_button_y <= ty <= ai_button_y + ai_button_height)
            status_text = "HIT AI BUTTON!" if in_button else "Outside button"
            status_color = (0, 255, 0) if in_button else (255, 255, 255)
            display_img.draw_string(10, 55, status_text, image.Color.from_rgb(*status_color))
        
        # Draw frame info
        display_img.draw_string(10, 10, f"Frame: {frame_count}", image.Color.from_rgb(255, 255, 255))
        display_img.draw_string(10, 25, "Touch anywhere to debug", image.Color.from_rgb(255, 255, 0))
        
        # Instructions
        display_img.draw_string(490, 160, "Touch the AI", image.Color.from_rgb(200, 200, 200))
        display_img.draw_string(490, 175, "button above", image.Color.from_rgb(200, 200, 200))
        display_img.draw_string(490, 190, "to test touch", image.Color.from_rgb(200, 200, 200))
        display_img.draw_string(490, 205, "detection", image.Color.from_rgb(200, 200, 200))
        
        # Exit instruction
        display_img.draw_string(490, 250, "Touch bottom", image.Color.from_rgb(150, 150, 150))
        display_img.draw_string(490, 265, "right corner", image.Color.from_rgb(150, 150, 150))
        display_img.draw_string(490, 280, "to exit", image.Color.from_rgb(150, 150, 150))
        
        # Exit area
        exit_area_x, exit_area_y = 590, 430
        exit_area_w, exit_area_h = 50, 50
        display_img.draw_rect(exit_area_x, exit_area_y, exit_area_w, exit_area_h,
                             image.Color.from_rgb(150, 0, 0), 2)
        display_img.draw_string(exit_area_x + 10, exit_area_y + 20, "EXIT", 
                               image.Color.from_rgb(150, 0, 0))
        
        # Check for exit touch
        if touch_data[0]:
            tx, ty = touch_data[1], touch_data[2]
            if (exit_area_x <= tx <= exit_area_x + exit_area_w and 
                exit_area_y <= ty <= exit_area_y + exit_area_h):
                print("Exit area touched - stopping test")
                break
        
        # Show display
        disp.show(display_img)
        
        frame_count += 1
        
        # Auto-exit after many frames
        if frame_count > 3000:  # About 1-2 minutes
            print("Auto-exit after timeout")
            break
    
    cam.close()
    print("✅ Simple touch debug test completed!")
    print(f"Total touches detected: {touch_count}")

if __name__ == "__main__":
    simple_touch_test()
