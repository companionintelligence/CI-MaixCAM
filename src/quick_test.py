#!/usr/bin/env python3
"""
Simple MaixCAM Test
Quick device connectivity test for MaixVision
"""

import time

def main():
    print("🚀 MaixCAM Quick Test Starting...")
    
    # Test 1: Basic imports
    try:
        from maix import camera, display, app, image
        print("✅ MaixPy imports successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return
    
    # Test 2: Camera
    try:
        cam = camera.Camera(640, 480)
        print("✅ Camera initialized")
        
        img = cam.read()
        print(f"✅ Frame captured: {img.width()}x{img.height()}")
        
        cam.close()
        print("✅ Camera closed")
    except Exception as e:
        print(f"❌ Camera failed: {e}")
    
    # Test 3: Display
    try:
        disp = display.Display()
        print(f"✅ Display ready: {disp.width()}x{disp.height()}")
        
        # Create test image
        test_img = image.Image(320, 240, image.Format.FMT_RGB888)
        test_img.draw_rect(0, 0, 320, 240, image.Color.from_rgb(0, 100, 200), -1)
        test_img.draw_string(50, 100, "DEVICE TEST OK", image.Color.from_rgb(255, 255, 255))
        
        disp.show(test_img)
        print("✅ Test image displayed")
        
        time.sleep(2)
    except Exception as e:
        print(f"❌ Display failed: {e}")
    
    # Test 4: Storage
    try:
        import os
        if os.path.exists("/sd"):
            print("✅ SD card accessible")
        else:
            print("⚠️ SD card not found")
    except Exception as e:
        print(f"❌ Storage check failed: {e}")
    
    print("🎉 Test complete! Check your MaixCAM screen.")

if __name__ == "__main__":
    main()
