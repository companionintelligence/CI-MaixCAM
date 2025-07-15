#!/usr/bin/env python3
"""
Quick Development Test Script
Test the current state of the Companion Capture App development

This script tests individual components to verify the current implementation
status and helps identify what needs to be fixed next.

Author: Companion Intelligence
Date: July 14, 2025
"""

import sys
import time
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from maix import app, display, camera, touchscreen, time as maix_time
        print("✅ MaixPy core modules imported successfully")
    except ImportError as e:
        print(f"❌ MaixPy import failed: {e}")
        return False
    
    try:
        from maix import nn, image
        print("✅ MaixPy AI modules imported successfully")
    except ImportError as e:
        print(f"❌ MaixPy AI import failed: {e}")
        return False
    
    try:
        from utils.config import Config
        from utils.logger import setup_logging
        print("✅ Utility modules imported successfully")
    except ImportError as e:
        print(f"❌ Utility import failed: {e}")
        return False
    
    try:
        from ui.main_ui import MainUI
        from ai_engine.ai_engine import AIEngine
        from data_logger.logger import DataLogger
        from network.uploader import NetworkUploader
        print("✅ Application modules imported successfully")
    except ImportError as e:
        print(f"❌ Application module import failed: {e}")
        return False
    
    return True

def test_camera_basic():
    """Test basic camera functionality"""
    print("\n📷 Testing basic camera...")
    
    try:
        from maix import camera, display, app, time
        
        cam = camera.Camera(640, 480)
        disp = display.Display()
        
        print(f"✅ Camera initialized: {cam.width()}x{cam.height()}")
        print(f"✅ Display initialized: {disp.width()}x{disp.height()}")
        
        # Test a few frames
        for i in range(5):
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

def test_configuration():
    """Test configuration system"""
    print("\n⚙️ Testing configuration...")
    
    try:
        from utils.config import Config
        
        config = Config()
        
        # Test some basic config values
        ai_models = config.get("ai_models", {})
        camera_config = config.get("camera", {})
        
        print(f"✅ Configuration loaded: {len(ai_models)} AI models configured")
        print(f"   Camera config: {camera_config.get('width')}x{camera_config.get('height')}")
        
        # Test model enabling/disabling
        object_detection = ai_models.get("object_detection", {})
        print(f"   Object detection enabled: {object_detection.get('enabled', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_ai_engine():
    """Test AI engine initialization"""
    print("\n🤖 Testing AI engine...")
    
    try:
        from ai_engine.ai_engine import AIEngine
        from utils.config import Config
        
        config = Config()
        
        # Create AI engine
        ai_engine = AIEngine(config)
        
        active_models = ai_engine.get_active_models()
        print(f"✅ AI Engine initialized with {len(active_models)} active models")
        print(f"   Active models: {active_models}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI Engine test failed: {e}")
        return False

def test_logger():
    """Test logging system"""
    print("\n📝 Testing logging system...")
    
    try:
        from utils.logger import setup_logging, get_logger
        
        logger = setup_logging()
        test_logger = get_logger('TEST')
        
        test_logger.info("Test log message")
        test_logger.debug("Test debug message")
        
        print("✅ Logging system working")
        return True
        
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False

def check_model_files():
    """Check if AI model files exist"""
    print("\n📂 Checking AI model files...")
    
    model_paths = [
        "/root/models/yolov8n.mud",
        "/root/models/retinaface.mud", 
        "/root/models/pp_ocr.mud",
        "/root/models/yolov8n_pose.mud"
    ]
    
    found_models = 0
    for model_path in model_paths:
        if os.path.exists(model_path):
            print(f"✅ Found: {model_path}")
            found_models += 1
        else:
            print(f"❌ Missing: {model_path}")
    
    print(f"📊 Model status: {found_models}/{len(model_paths)} models found")
    return found_models > 0

def run_tests():
    """Run all tests"""
    print("🚀 Companion Capture App - Development Test Suite")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_configuration),
        ("Logging Test", test_logger),
        ("AI Engine Test", test_ai_engine),
        ("Model Files Check", check_model_files),
        ("Camera Test", test_camera_basic),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for next development phase.")
        print("\n🎯 Next Steps:")
        print("   1. Test on actual MaixCAM hardware")
        print("   2. Validate AI model loading")
        print("   3. Implement audio processing (Step 5)")
        print("   4. Complete object classification (Step 6)")
    else:
        print("⚠️ Some tests failed. Fix issues before proceeding.")
        print("\n🔧 Common fixes:")
        print("   - Check MaixPy installation")
        print("   - Verify model file paths")
        print("   - Test on MaixCAM device")
    
    return passed == total

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
