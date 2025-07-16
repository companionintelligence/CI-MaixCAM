#!/usr/bin/env python3
"""
Integration Test for Companion Capture App
Test the complete flow from setup screen to main app with existing DataLogger

Author: Companion Intelligence
Date: July 14, 2025
"""

def test_integration():
    """Test the integration of all components"""
    
    print("🧪 Testing Companion Capture App Integration")
    print("=" * 50)
    
    # Test 1: Setup Screen Integration
    print("1. Testing Setup Screen Integration...")
    try:
        from setup_screen import run_setup_screen
        print("   ✅ Setup screen import successful")
    except Exception as e:
        print(f"   ❌ Setup screen import failed: {e}")
        return False
    
    # Test 2: DataLogger Integration  
    print("2. Testing DataLogger Integration...")
    try:
        from data_logger.logger import DataLogger
        from utils.config import Config
        
        config = Config()
        data_logger = DataLogger(config)
        print("   ✅ DataLogger import and initialization successful")
        
        # Test session stats
        stats = data_logger.get_session_stats()
        print(f"   ✅ Session stats: {stats['session_active']}")
        
    except Exception as e:
        print(f"   ❌ DataLogger integration failed: {e}")
        return False
    
    # Test 3: AI Model Manager
    print("3. Testing AI Model Manager...")
    try:
        # Mock the configuration file for testing
        import json
        import os
        
        test_config = {
            "timestamp": 1642121200,
            "selected_models": [
                "Object Classification",
                "Face Recognition", 
                "Audio Recording"
            ],
            "model_states": {
                "Object Classification": True,
                "Face Recognition": True,
                "Face Emotion Detection": False,
                "Object Tracking and Counting": False,
                "OCR (Optical Character Recognition)": False,
                "Hand Landmarks Detection": False,
                "Human Pose Classification": False,
                "Hand Gesture Classification": False,
                "Audio Recording": True,
                "Audio Playback": False,
                "Real-time Voice Recognition": False,
                "Video Recording": False,
                "Video Playback": False
            }
        }
        
        # Create test config file
        os.makedirs("/tmp", exist_ok=True)
        test_config_path = "/tmp/test_companion_config.json"
        with open(test_config_path, 'w') as f:
            json.dump(test_config, f)
        
        # Test AI Model Manager
        import sys
        sys.path.append('.')
        from main import AIModelManager
        
        ai_manager = AIModelManager(config_path=test_config_path)
        active_models = ai_manager.get_active_models()
        print(f"   ✅ AI Manager initialized with {len(active_models)} active models")
        print(f"   📝 Active models: {active_models}")
        
        # Cleanup
        os.remove(test_config_path)
        
    except Exception as e:
        print(f"   ❌ AI Model Manager test failed: {e}")
        return False
    
    # Test 4: Main App Import
    print("4. Testing Main App Import...")
    try:
        from main import CompanionCaptureApp, main
        print("   ✅ Main app import successful")
    except Exception as e:
        print(f"   ❌ Main app import failed: {e}")
        print(f"      Error details: {str(e)}")
        return False
    
    # Test 5: Configuration Compatibility
    print("5. Testing Configuration Compatibility...")
    try:
        config = Config()
        
        # Test storage config
        storage_config = config.get_storage_config()
        print(f"   ✅ Storage config: {storage_config['base_path']}")
        
        # Test AI models config  
        ai_config = config.get_ai_models_config()
        print(f"   ✅ AI models config loaded: {len(ai_config)} models")
        
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False
    
    print("\n🎉 All integration tests passed!")
    print("\n📋 Ready for deployment to MaixCAM:")
    print("   1. Copy all files to MaixCAM device")
    print("   2. Run: python3 main.py")
    print("   3. Setup screen will appear first")
    print("   4. Select AI models and click START")
    print("   5. Main app will launch with camera preview")
    print("   6. Touch controls: Top-left=Capture, Top-right=Exit")
    
    return True

if __name__ == "__main__":
    test_integration()
