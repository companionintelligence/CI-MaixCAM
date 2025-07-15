#!/usr/bin/env python3
"""
AI Button Test with Touch Transformer
Test AI button with fixed touch coordinates

Author: Companion Intelligence
Date: July 14, 2025
"""

from maix import camera, display, image, touchscreen, app
from touch_transformer import TouchTransformer

def test_ai_button_with_transformer():
    """Test AI button with coordinate transformation"""
    print("🎯 AI Button Test with Touch Transformer")
    print("Testing fixed touch coordinates for AI button")
    
    # Initialize hardware
    cam = camera.Camera(640, 480)
    disp = display.Display()
    touch = touchscreen.TouchScreen()
    
    # Initialize touch transformer
    transformer = TouchTransformer()
    
    # AI button coordinates (top-right)
    ai_button_x = 485
    ai_button_y = 5
    ai_button_width = 50
    ai_button_height = 50
    
    frame_count = 0
    touch_count = 0
    button_hits = 0
    
    print(f"\n🎯 AI Button Area: ({ai_button_x}, {ai_button_y}) to ({ai_button_x + ai_button_width}, {ai_button_y + ai_button_height})")
    print("Touch the top-right area to test the AI button!")
    
    while not app.need_exit():
        # Get camera frame
        img = cam.read()
        
        # Handle touch events
        touch_data = touch.read()
        if touch_data[0]:  # Touch detected
            raw_x, raw_y = touch_data[1], touch_data[2]
            
            # Transform coordinates
            transformed_x, transformed_y = transformer.transform_with_fallback(
                raw_x, raw_y, fallback_y=ai_button_y + ai_button_height//2
            )
            
            touch_count += 1
            
            # Check if transformed touch hits AI button
            in_ai_button = (ai_button_x <= transformed_x <= ai_button_x + ai_button_width and 
                           ai_button_y <= transformed_y <= ai_button_y + ai_button_height)
            
            if in_ai_button:
                button_hits += 1
                print(f"🚀 AI BUTTON HIT #{button_hits}!")
                print(f"   Raw: ({raw_x}, {raw_y}) → Transformed: ({transformed_x}, {transformed_y})")
            else:
                print(f"❌ Miss #{touch_count}: Raw({raw_x}, {raw_y}) → Transformed({transformed_x}, {transformed_y})")
        
        # Draw camera preview
        preview_img = img.resize(480, 480)
        
        # Create full display image
        display_img = image.Image(640, 480, image.Format.FMT_RGB888)
        display_img.draw_image(0, 0, preview_img)
        
        # Draw UI panel background (right side)
        display_img.draw_rect(480, 0, 160, 480, image.Color.from_rgb(20, 20, 20), -1)
        
        # Draw AI button with clear bounds
        button_color = (0, 255, 0) if touch_data[0] else (100, 100, 100)
        display_img.draw_rect(ai_button_x, ai_button_y, ai_button_width, ai_button_height,
                             image.Color.from_rgb(*button_color), -1)
        display_img.draw_rect(ai_button_x, ai_button_y, ai_button_width, ai_button_height,
                             image.Color.from_rgb(255, 255, 255), 2)
        
        # Draw AI text
        display_img.draw_string(ai_button_x + 15, ai_button_y + 20, "AI", 
                               image.Color.from_rgb(255, 255, 255))
        
        # Draw statistics
        display_img.draw_string(490, 70, f"Touches: {touch_count}", image.Color.from_rgb(200, 200, 200))
        display_img.draw_string(490, 85, f"Hits: {button_hits}", image.Color.from_rgb(0, 255, 0))
        
        # Draw current touch if active
        if touch_data[0]:
            raw_x, raw_y = touch_data[1], touch_data[2]
            transformed_x, transformed_y = transformer.transform_with_fallback(
                raw_x, raw_y, fallback_y=ai_button_y + ai_button_height//2
            )
            
            # Draw transformed touch point
            display_img.draw_circle(transformed_x, transformed_y, 15, image.Color.from_rgb(255, 255, 0), 3)
            display_img.draw_circle(transformed_x, transformed_y, 5, image.Color.from_rgb(255, 0, 0), -1)
            
            # Draw coordinate info
            display_img.draw_string(10, 10, f"Raw: ({raw_x}, {raw_y})", image.Color.from_rgb(255, 255, 255))
            display_img.draw_string(10, 25, f"Fixed: ({transformed_x}, {transformed_y})", image.Color.from_rgb(255, 255, 0))
            
            # Draw hit/miss status
            in_button = (ai_button_x <= transformed_x <= ai_button_x + ai_button_width and 
                        ai_button_y <= transformed_y <= ai_button_y + ai_button_height)
            status_text = "🚀 AI BUTTON HIT!" if in_button else "Outside button"
            status_color = (0, 255, 0) if in_button else (255, 255, 255)
            display_img.draw_string(10, 40, status_text, image.Color.from_rgb(*status_color))
        
        # Instructions
        display_img.draw_string(490, 120, "Touch top-right", image.Color.from_rgb(200, 200, 200))
        display_img.draw_string(490, 135, "for AI button", image.Color.from_rgb(200, 200, 200))
        
        # Transformer info
        display_img.draw_string(490, 160, "Touch Transform:", image.Color.from_rgb(150, 150, 150))
        display_img.draw_string(490, 175, "X: 34-463 → 0-640", image.Color.from_rgb(150, 150, 150))
        display_img.draw_string(490, 190, "Y: Broken → Fixed", image.Color.from_rgb(150, 150, 150))
        
        # Exit instruction
        display_img.draw_string(490, 250, "Touch bottom", image.Color.from_rgb(150, 150, 150))
        display_img.draw_string(490, 265, "for exit", image.Color.from_rgb(150, 150, 150))
        
        # Exit area check (bottom area)
        if touch_data[0]:
            raw_x, raw_y = touch_data[1], touch_data[2]
            if raw_x > 400:  # Right side of screen in raw coordinates
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
    
    print(f"\n📊 Test Results:")
    print(f"   Total touches: {touch_count}")
    print(f"   AI button hits: {button_hits}")
    if touch_count > 0:
        hit_rate = (button_hits / touch_count) * 100
        print(f"   Hit rate: {hit_rate:.1f}%")
    
    print("✅ AI button test with transformer completed!")

if __name__ == "__main__":
    test_ai_button_with_transformer()
