#!/usr/bin/env python3
# Test script for MaixCAM device
# Run this to verify the installation

import sys
import os

# Add app directory to path
sys.path.insert(0, "/root/companion_capture")

def test_installation():
    print("🧪 Testing Companion Capture App installation...")
    
    try:
        # Test imports
        from utils.config import Config
        from utils.logger import setup_logging
        print("✅ Core modules imported successfully")
        
        # Test config creation
        config = Config("/tmp/test_config.json")
        print("✅ Configuration system working")
        
        # Test MaixPy imports (device-specific)
        try:
            from maix import camera, display, app
            print("✅ MaixPy modules imported successfully")
        except ImportError as e:
            print(f"⚠️  MaixPy import warning: {e}")
            print("   This is normal if running on non-MaixCAM device")
        
        print("\n🎉 Installation test completed successfully!")
        print("   Run 'python main.py' to start the application")
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_installation()
