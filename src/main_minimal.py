#!/usr/bin/env python3
"""
Minimal Test Version - Companion Capture App
Simple version to test basic functionality without complex features

Author: Companion Intelligence
Date: July 14, 2025
"""

import sys
import time
import gc

def test_basic_imports():
    """Test basic MaixPy imports"""
    print("Testing basic imports...")
    
    try:
        from maix import app, display, camera, time as maix_time
        print("✅ MaixPy core modules imported")
        return True
    except ImportError as e:
        print(f"❌ MaixPy import failed: {e}")
        return False

def test_camera_simple():
    """Test simple camera functionality"""
    print("Testing camera...")
    
    try:
        from maix import camera, display, app, time, image
        
        # Initialize camera and display
        cam = camera.Camera(640, 480)
        disp = display.Display()
        
        print(f"✅ Camera: {cam.width()}x{cam.height()}")
        print(f"✅ Display: {disp.width()}x{disp.height()}")
        
        # Simple loop
        frame_count = 0
        while not app.need_exit() and frame_count < 100:
            time.fps_start()
            
            # Get frame
            img = cam.read()
            
            # Draw simple info
            img.draw_string(10, 10, f"Frame: {frame_count}", color=image.COLOR_WHITE)
            img.draw_string(10, 30, "Basic Test", color=image.COLOR_GREEN)
            
            # Show frame
            disp.show(img)
            
            # Calculate FPS
            fps = time.fps()
            
            if frame_count % 10 == 0:
                print(f"Frame {frame_count}: FPS: {fps:.1f}")
            
            frame_count += 1
        
        cam.close()
        print("✅ Camera test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_only():
    """Test configuration loading only"""
    print("Testing configuration...")
    
    try:
        from utils.config import Config
        
        config = Config()
        ai_models = config.get("ai_models", {})
        
        print(f"✅ Configuration loaded: {len(ai_models)} AI models configured")
        
        for model_name, model_config in ai_models.items():
            enabled = model_config.get("enabled", False)
            print(f"   {model_name}: {'enabled' if enabled else 'disabled'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Minimal Companion Capture App Test")
    print("=" * 45)
    
    # Test imports first
    if not test_basic_imports():
        print("❌ Basic imports failed - cannot continue")
        return
    
    print()
    
    # Test configuration
    if not test_config_only():
        print("❌ Configuration failed")
        return
    
    print()
    
    # Test camera
    if not test_camera_simple():
        print("❌ Camera test failed")
        return
    
    print("\n✅ All tests completed successfully!")
    print("🎉 Ready to proceed with full app development")

if __name__ == "__main__":
    main()
