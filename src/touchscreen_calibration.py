#!/usr/bin/env python3
"""
Touchscreen Calibration Test
Map touch coordinates to find the correct calibration

Author: Companion Intelligence
Date: July 14, 2025
"""

from maix import camera, display, image, touchscreen, app

def touchscreen_calibration_test():
    """Test touchscreen calibration and coordinate mapping"""
    print("🎯 Touchscreen Calibration Test")
    print("Touch the corners and center to map coordinates")
    
    # Initialize hardware
    cam = camera.Camera(640, 480)
    disp = display.Display()
    touch = touchscreen.TouchScreen()
    
    # Calibration points to test
    calibration_points = [
        {"name": "TOP-LEFT", "x": 0, "y": 0, "color": (255, 0, 0)},
        {"name": "TOP-RIGHT", "x": 590, "y": 0, "color": (0, 255, 0)},
        {"name": "BOTTOM-LEFT", "x": 0, "y": 430, "color": (0, 0, 255)},
        {"name": "BOTTOM-RIGHT", "x": 590, "y": 430, "color": (255, 255, 0)},
        {"name": "CENTER", "x": 320, "y": 240, "color": (255, 0, 255)},
    ]
    
    frame_count = 0
    touch_history = []
    max_history = 10
    
    while not app.need_exit():
        # Get camera frame
        img = cam.read()
        
        # Handle touch events
        touch_data = touch.read()
        if touch_data[0]:  # Touch detected
            touch_x, touch_y = touch_data[1], touch_data[2]
            
            # Add to history
            if not touch_history or (touch_x, touch_y) != touch_history[-1]:
                touch_history.append((touch_x, touch_y))
                print(f"🎯 Touch: ({touch_x}, {touch_y})")
                
                # Keep only recent touches
                if len(touch_history) > max_history:
                    touch_history.pop(0)
        
        # Create display image
        display_img = image.Image(640, 480, image.Format.FMT_RGB888)
        
        # Draw camera preview (scaled down)
        preview_img = img.resize(320, 240)
        display_img.draw_image(160, 120, preview_img)
        
        # Draw calibration target points
        for point in calibration_points:
            # Draw target circle
            display_img.draw_circle(point["x"] + 25, point["y"] + 25, 25, 
                                   image.Color.from_rgb(*point["color"]), 3)
            
            # Draw center dot
            display_img.draw_circle(point["x"] + 25, point["y"] + 25, 5, 
                                   image.Color.from_rgb(*point["color"]), -1)
            
            # Draw label
            display_img.draw_string(point["x"], point["y"] + 55, point["name"][:8], 
                                   image.Color.from_rgb(*point["color"]))
        
        # Draw touch history
        for i, (tx, ty) in enumerate(touch_history):
            alpha = 255 - (len(touch_history) - i - 1) * 25
            alpha = max(50, alpha)
            
            # Draw touch point
            display_img.draw_circle(tx, ty, 8, image.Color.from_rgb(255, 255, 255), 2)
            display_img.draw_circle(tx, ty, 3, image.Color.from_rgb(255, 0, 0), -1)
            
            # Draw coordinates
            display_img.draw_string(tx + 15, ty - 10, f"({tx},{ty})", 
                                   image.Color.from_rgb(255, 255, 255))
        
        # Draw current touch if active
        if touch_data[0]:
            tx, ty = touch_data[1], touch_data[2]
            # Large crosshairs
            display_img.draw_line(tx - 30, ty, tx + 30, ty, image.Color.from_rgb(255, 255, 0), 4)
            display_img.draw_line(tx, ty - 30, tx, ty + 30, image.Color.from_rgb(255, 255, 0), 4)
            
            # Current coordinates (large text)
            display_img.draw_string(10, 10, f"CURRENT: ({tx}, {ty})", 
                                   image.Color.from_rgb(255, 255, 0))
        
        # Instructions
        display_img.draw_string(10, 30, "Touch each colored circle", image.Color.from_rgb(255, 255, 255))
        display_img.draw_string(10, 45, "to map coordinates", image.Color.from_rgb(255, 255, 255))
        
        # Draw screen bounds
        display_img.draw_rect(0, 0, 640, 480, image.Color.from_rgb(100, 100, 100), 2)
        
        # Draw grid lines for reference
        for x in range(0, 640, 80):
            display_img.draw_line(x, 0, x, 480, image.Color.from_rgb(50, 50, 50), 1)
        for y in range(0, 480, 60):
            display_img.draw_line(0, y, 640, y, image.Color.from_rgb(50, 50, 50), 1)
        
        # Exit instruction
        display_img.draw_string(10, 450, "Touch center circle 3 times to exit", 
                               image.Color.from_rgb(150, 150, 150))
        
        # Check for exit condition (touching center multiple times)
        if len(touch_history) >= 3:
            center_touches = 0
            for tx, ty in touch_history[-3:]:
                if abs(tx - 345) < 30 and abs(ty - 265) < 30:  # Near center
                    center_touches += 1
            
            if center_touches >= 3:
                print("Center touched 3 times - exiting")
                break
        
        # Show display
        disp.show(display_img)
        
        frame_count += 1
        
        # Auto-exit after timeout
        if frame_count > 3000:
            print("Auto-exit after timeout")
            break
    
    cam.close()
    
    print("\n📊 Calibration Results:")
    print("Touch History (last 10 touches):")
    for i, (tx, ty) in enumerate(touch_history):
        print(f"  Touch {i+1}: ({tx}, {ty})")
    
    if touch_history:
        print(f"\nTouch Range:")
        print(f"  X: {min(tx for tx, ty in touch_history)} to {max(tx for tx, ty in touch_history)}")
        print(f"  Y: {min(ty for tx, ty in touch_history)} to {max(ty for tx, ty in touch_history)}")
    
    print("✅ Touchscreen calibration test completed!")

if __name__ == "__main__":
    touchscreen_calibration_test()
