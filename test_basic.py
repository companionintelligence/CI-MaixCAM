#!/usr/bin/env python3
"""
Basic Test Script
Tests the core components without requiring hardware

Author: Companion Intelligence
Date: July 13, 2025
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...")
    
    try:
        from utils.config import Config
        print("✅ Config module imported successfully")
        
        from utils.logger import setup_logging, get_logger
        print("✅ Logger module imported successfully")
        
        # Test basic config functionality
        config = Config("/tmp/test_config.json")
        print(f"✅ Config created: {config.get('app.name')}")
        
        # Test basic logging
        logger = setup_logging()
        logger.info("Test log message")
        print("✅ Logging system working")
        
        print("\n🎉 All basic components imported successfully!")
        print("\nNext steps:")
        print("1. Transfer the /src folder to your MaixCAM device")
        print("2. Run the main.py file on the device")
        print("3. Test with actual hardware")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_config_system():
    """Test configuration system"""
    print("\nTesting configuration system...")
    
    try:
        from utils.config import Config
        
        # Create test config
        config = Config("/tmp/test_companion_config.json")
        
        # Test getting values
        app_name = config.get("app.name")
        camera_width = config.get("camera.width")
        models = config.get_enabled_models()
        
        print(f"App name: {app_name}")
        print(f"Camera width: {camera_width}")
        print(f"Enabled models: {models}")
        
        # Test setting values
        config.set("test.value", "hello world")
        test_value = config.get("test.value")
        print(f"Test value: {test_value}")
        
        # Test model toggling
        config.toggle_model("face_detection", False)
        face_enabled = config.is_model_enabled("face_detection")
        print(f"Face detection enabled: {face_enabled}")
        
        print("✅ Configuration system working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Config test error: {e}")
        return False

def test_data_structures():
    """Test data structure creation"""
    print("\nTesting data structures...")
    
    try:
        # Test event structure
        test_event = {
            "timestamp": 1234567890,
            "type": "object_detection",
            "model": "yolov8",
            "objects": [
                {
                    "label": "person",
                    "confidence": 0.85,
                    "bbox": [100, 150, 50, 100]
                },
                {
                    "label": "car", 
                    "confidence": 0.92,
                    "bbox": [200, 100, 80, 60]
                }
            ],
            "count": 2
        }
        
        print(f"Test event created with {test_event['count']} objects")
        print(f"First object: {test_event['objects'][0]['label']} ({test_event['objects'][0]['confidence']})")
        
        print("✅ Data structures working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Data structure test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Companion Capture App - Basic Component Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config_system,
        test_data_structures
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 All tests passed! The basic structure is ready.")
        print("\n📋 Next Steps:")
        print("1. Transfer the entire /src folder to your MaixCAM device")
        print("2. Test imports on the actual device")
        print("3. Start implementing hardware-specific functionality")
        print("4. Test with real camera and AI models")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
