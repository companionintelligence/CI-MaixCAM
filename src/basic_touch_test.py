#!/usr/bin/env python3
"""
Basic Touch Test
Test based on MaixPy touchscreen_read.py example

Author: Companion Intelligence
Date: July 14, 2025
"""

from maix import touchscreen, app, time

def basic_touch_test():
    """Basic touch test following MaixPy example exactly"""
    print("🖱️ Basic Touch Test")
    print("Touch the screen to see coordinates")
    print("This follows the exact MaixPy touchscreen_read.py pattern")
    
    ts = touchscreen.TouchScreen()
    
    pressed_already = False
    last_x = 0
    last_y = 0
    last_pressed = False
    
    frame_count = 0
    
    while not app.need_exit():
        x, y, pressed = ts.read()
        
        if x != last_x or y != last_y or pressed != last_pressed:
            print(f"🎯 Touch: x={x}, y={y}, pressed={pressed}")
            last_x = x
            last_y = y
            last_pressed = pressed
        
        if pressed:
            pressed_already = True
        else:
            if pressed_already:
                print(f"✅ Clicked at: x={x}, y={y}")
                pressed_already = False
        
        # Periodic status to show we're running
        frame_count += 1
        if frame_count % 300 == 0:  # Every 10 seconds
            print(f"📊 Running... Frame {frame_count}")
        
        time.sleep_ms(1)  # sleep some time to free some CPU usage

if __name__ == "__main__":
    basic_touch_test()
