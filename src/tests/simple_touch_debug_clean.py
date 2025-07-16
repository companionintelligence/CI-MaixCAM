#!/usr/bin/env python3
"""
Simple Touch Debug Test
Basic touchscreen test based on MaixPy examples

Author: Companion Intelligence  
Date: July 14, 2025
"""

from maix import touchscreen, app, time, display, image

def simple_touch_debug():
    """Simple touch debug based on touchscreen_read.py example"""
    print("🖱️ Simple Touch Debug Test")
    print("Touch anywhere on screen to see coordinates")
    
    ts = touchscreen.TouchScreen()
    disp = display.Display()
    
    # Create a simple image for visual feedback
    img = image.Image(disp.width(), disp.height())
    
    # Draw basic UI
    img.draw_string(10, 10, "Touch Debug Test", image.Color.from_rgb(255, 255, 255))
    img.draw_string(10, 30, "Touch anywhere to see coordinates", image.Color.from_rgb(200, 200, 200))
    
    # Draw AI button area for reference
    ai_button_x = 485
    ai_button_y = 5  
    ai_button_width = 50
    ai_button_height = 50
    
    img.draw_rect(ai_button_x, ai_button_y, ai_button_width, ai_button_height,
                 image.Color.from_rgb(100, 100, 100), -1)
    img.draw_rect(ai_button_x, ai_button_y, ai_button_width, ai_button_height,
                 image.Color.from_rgb(255, 255, 255), 2)
    img.draw_string(ai_button_x + 15, ai_button_y + 20, "AI", image.Color.from_rgb(255, 255, 255))
    
    pressed_already = False
    last_x = 0
    last_y = 0
    last_pressed = False
    
    frame_count = 0
    
    while not app.need_exit():
        x, y, pressed = ts.read()
        
        # Print touch changes
        if x != last_x or y != last_y or pressed != last_pressed:
            print(f"🎯 Touch: x={x}, y={y}, pressed={pressed}")
            last_x = x
            last_y = y
            last_pressed = pressed
        
        if pressed:
            pressed_already = True
            # Draw touch point
            img.draw_circle(x, y, 5, image.Color.from_rgb(255, 0, 0), -1)
            
            # Check if in AI button area
            if (ai_button_x <= x <= ai_button_x + ai_button_width and
                ai_button_y <= y <= ai_button_y + ai_button_height):
                print(f"🚀 AI Button touched at ({x}, {y})!")
                img.draw_string(10, 50, f"AI Button HIT! ({x}, {y})", 
                               image.Color.from_rgb(0, 255, 0))
            else:
                img.draw_string(10, 50, f"Touch at: ({x}, {y})", 
                               image.Color.from_rgb(255, 255, 0))
        else:
            if pressed_already:
                print(f"✅ Touch released at ({x}, {y})")
                pressed_already = False
        
        # Show current touch coordinates on screen
        img.draw_string(10, 70, f"Current: ({x}, {y}, {pressed})", 
                       image.Color.from_rgb(255, 255, 255))
        
        # Periodic status
        frame_count += 1
        if frame_count % 60 == 0:  # Every 2 seconds at ~30 FPS
            print(f"📊 Frame {frame_count}, Touch status: ({x}, {y}, {pressed})")
        
        disp.show(img)
        time.sleep_ms(1)  # Small delay as in examples

if __name__ == "__main__":
    simple_touch_debug()
