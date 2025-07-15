#!/usr/bin/env python3
"""
Touch Test for AI Button Location
Quick test to identify exact AI button coordinates

Author: Companion Intelligence
Date: July 14, 2025
"""

from maix import camera, display, image, touchscreen, app

def test_ai_button_location():
    """Test exact AI button touch coordinates"""
    print("🎯 AI Button Location Test")
    print("Touch the AI button to see if coordinates match")
    
    # Initialize hardware
    cam = camera.Camera(640, 480)
    disp = display.Display()
    touch = touchscreen.TouchScreen()
    
    # Based on screenshot, AI button appears to be in top-right
    # Let's define multiple possible areas to test
    button_areas = [
        {"name": "Area 1 (485-535, 5-55)", "x": 485, "y": 5, "w": 50, "h": 50},
        {"name": "Area 2 (570-620, 5-55)", "x": 570, "y": 5, "w": 50, "h": 50},
        {"name": "Area 3 (590-640, 5-55)", "x": 590, "y": 5, "w": 50, "h": 50},
    ]
    
    frame_count = 0
    touch_count = 0
    
    while not app.need_exit():
        # Get camera frame
        img = cam.read()
        
        # Handle touch events
        touch_data = touch.read()
        if touch_data[0]:  # Touch detected
            touch_x, touch_y = touch_data[1], touch_data[2]
            touch_count += 1
            
            print(f"🎯 Touch #{touch_count}: ({touch_x}, {touch_y})")
            
            # Check each button area
            for area in button_areas:
                if (area["x"] <= touch_x <= area["x"] + area["w"] and 
                    area["y"] <= touch_y <= area["y"] + area["h"]):
                    print(f"🚀 HIT! {area['name']}")
                else:
                    print(f"❌ MISS {area['name']}")
        
        # Draw camera preview (left side)
        preview_img = img.resize(480, 480)
        display_img = image.Image(640, 480, image.Format.FMT_RGB888)
        display_img.draw_image(0, 0, preview_img)
        
        # Draw UI panel background (right side)
        display_img.draw_rect(480, 0, 160, 480, image.Color.from_rgb(20, 20, 20), -1)
        
        # Draw all test button areas
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        for i, area in enumerate(button_areas):
            color = colors[i % len(colors)]
            display_img.draw_rect(area["x"], area["y"], area["w"], area["h"],
                                 image.Color.from_rgb(*color), 2)
            display_img.draw_string(area["x"], area["y"] + area["h"] + 5, 
                                   f"Area {i+1}", image.Color.from_rgb(*color))
        
        # Draw current touch if active
        if touch_data[0]:
            tx, ty = touch_data[1], touch_data[2]
            # Draw crosshairs
            display_img.draw_line(tx - 15, ty, tx + 15, ty, image.Color.from_rgb(255, 255, 0), 3)
            display_img.draw_line(tx, ty - 15, tx, ty + 15, image.Color.from_rgb(255, 255, 0), 3)
            
            # Draw touch coordinates
            display_img.draw_string(10, 10, f"Touch: ({tx}, {ty})", image.Color.from_rgb(255, 255, 0))
        
        # Instructions
        display_img.draw_string(10, 30, "Touch AI button areas", image.Color.from_rgb(255, 255, 255))
        display_img.draw_string(10, 45, "to test coordinates", image.Color.from_rgb(255, 255, 255))
        
        # Exit instruction
        display_img.draw_string(10, 450, "Touch bottom-left to exit", image.Color.from_rgb(150, 150, 150))
        
        # Exit area (bottom-left)
        if touch_data[0]:
            tx, ty = touch_data[1], touch_data[2]
            if tx < 100 and ty > 400:
                print("Exit area touched - stopping test")
                break
        
        # Show display
        disp.show(display_img)
        
        frame_count += 1
        
        # Auto-exit after timeout
        if frame_count > 2000:
            print("Auto-exit after timeout")
            break
    
    cam.close()
    print("✅ AI button location test completed!")
    print(f"Total touches detected: {touch_count}")

if __name__ == "__main__":
    test_ai_button_location()
