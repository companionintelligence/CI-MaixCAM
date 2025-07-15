#!/usr/bin/env python3
"""
Device Test for MaixCAM - No Complex Imports
This file should work on MaixCAM without import issues

Author: Companion Intelligence  
Date: July 14, 2025
"""

import sys
import os

def test_basic_imports():
    """Test basic MaixPy imports"""
    print("🔍 Testing basic imports...")
    
    try:
        from maix import app, display, camera, time
        print("✅ MaixPy core modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ MaixPy import failed: {e}")
        return False

def test_basic_camera():
    """Test basic camera functionality"""
    print("\n📷 Testing basic camera...")
    
    try:
        from maix import camera, display, app, time
        
        cam = camera.Camera(640, 480)
        disp = display.Display()
        
        print(f"✅ Camera initialized: {cam.width()}x{cam.height()}")
        print(f"✅ Display initialized: {disp.width()}x{disp.height()}")
        
        # Test a few frames
        for i in range(3):
            img = cam.read()
            print(f"   Frame {i+1}: {img.width()}x{img.height()}")
            disp.show(img)
            time.sleep_ms(100)
        
        cam.close()
        print("✅ Basic camera test passed")
        return True
        
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False

def test_ai_imports():
    """Test AI module imports"""
    print("\n🤖 Testing AI imports...")
    
    try:
        from maix import nn, image
        print("✅ MaixPy AI modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ MaixPy AI import failed: {e}")
        return False

def check_files():
    """Check what files are available"""
    print("\n📂 Checking available files...")
    
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    if os.path.exists("/tmp/maixpy_run"):
        print("Files in /tmp/maixpy_run:")
        for item in os.listdir("/tmp/maixpy_run"):
            print(f"  {item}")

def run_device_test():
    """Run device tests without complex imports"""
    print("🚀 MaixCAM Device Test")
    print("=" * 30)
    
    tests = [
        ("Check Files", check_files),
        ("Basic Imports", test_basic_imports),
        ("AI Imports", test_ai_imports),
        ("Basic Camera", test_basic_camera),
    ]
    
    passed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n▶️ Running {test_name}...")
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    return passed >= 2

if __name__ == "__main__":
    try:
        run_device_test()
    except Exception as e:
        print(f"💥 Test crashed: {e}")
