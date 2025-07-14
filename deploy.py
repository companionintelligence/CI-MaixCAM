#!/usr/bin/env python3
"""
Deployment Script for MaixCAM
Helps deploy the Companion Capture App to the MaixCAM device

Author: Companion Intelligence
Date: July 13, 2025
"""

import os
import sys
import subprocess
import shutil

def check_requirements():
    """Check if required tools are available"""
    print("🔍 Checking deployment requirements...")
    
    # Check if we're in the right directory
    if not os.path.exists("src/main.py"):
        print("❌ Error: Run this script from the MaixPy project root directory")
        return False
    
    print("✅ Project structure found")
    return True

def create_deployment_package():
    """Create a deployment package"""
    print("📦 Creating deployment package...")
    
    # Create deployment directory
    deploy_dir = "deploy"
    if os.path.exists(deploy_dir):
        shutil.rmtree(deploy_dir)
    os.makedirs(deploy_dir)
    
    # Copy source files
    shutil.copytree("src", os.path.join(deploy_dir, "companion_capture"))
    
    # Copy additional files
    files_to_copy = ["README.md", "PROJECT_PLAN.MD"]
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, deploy_dir)
    
    print(f"✅ Deployment package created in {deploy_dir}/")
    return deploy_dir

def generate_deployment_instructions():
    """Generate deployment instructions"""
    instructions = """
🚀 DEPLOYMENT INSTRUCTIONS FOR MAIXCAM
=======================================

1. CONNECT TO YOUR MAIXCAM DEVICE:
   
   Method A - USB Cable:
   - Connect MaixCAM via USB-C cable
   - Use MaixVision IDE file manager
   
   Method B - SSH (if WiFi configured):
   ssh root@<MAIXCAM_IP_ADDRESS>

2. TRANSFER FILES:
   
   Method A - Using MaixVision IDE:
   - Open MaixVision IDE
   - Connect to device
   - Use file manager to upload 'companion_capture' folder to /root/
   
   Method B - Using SCP:
   scp -r deploy/companion_capture/ root@<MAIXCAM_IP>:/root/
   
   Method C - Manual copy:
   - Copy files via USB storage mode
   - Place in /root/companion_capture/

3. SET PERMISSIONS (if needed):
   chmod +x /root/companion_capture/main.py

4. RUN THE APPLICATION:
   cd /root/companion_capture
   python main.py

5. CONFIGURATION:
   - Config file will be created at: /sd/config/app_config.json
   - Logs will be stored at: /sd/logs/
   - Modify settings as needed

6. TROUBLESHOOTING:
   - Check logs: tail -f /sd/system.log
   - Monitor memory: free -h
   - Check storage: df -h /sd

FIRST RUN CHECKLIST:
- [ ] Device boots correctly
- [ ] Camera preview appears
- [ ] Touch interface responds
- [ ] AI models load (check console output)
- [ ] Start/Stop button works
- [ ] Events are logged to /sd/logs/

For detailed documentation, see README.md
"""
    
    with open("deploy/DEPLOYMENT_INSTRUCTIONS.txt", "w") as f:
        f.write(instructions)
    
    print("✅ Deployment instructions created")

def create_startup_script():
    """Create a startup script for the device"""
    startup_script = """#!/usr/bin/env python3
# Companion Capture App Startup Script
# This script can be used for auto-start functionality

import sys
import os

# Add the app directory to Python path
app_dir = "/root/companion_capture"
sys.path.insert(0, app_dir)

# Change to app directory
os.chdir(app_dir)

# Import and run the app
try:
    from main import main
    main()
except Exception as e:
    print(f"Startup error: {e}")
    import traceback
    traceback.print_exc()
"""
    
    with open("deploy/start_companion_capture.py", "w") as f:
        f.write(startup_script)
    
    print("✅ Startup script created")

def create_test_script():
    """Create a test script for the device"""
    test_script = """#!/usr/bin/env python3
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
        
        print("\\n🎉 Installation test completed successfully!")
        print("   Run 'python main.py' to start the application")
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_installation()
"""
    
    with open("deploy/test_installation.py", "w") as f:
        f.write(test_script)
    
    print("✅ Test script created")

def main():
    """Main deployment script"""
    print("🚀 Companion Capture App - Deployment Script")
    print("=" * 50)
    
    if not check_requirements():
        sys.exit(1)
    
    # Create deployment package
    deploy_dir = create_deployment_package()
    
    # Generate additional files
    generate_deployment_instructions()
    create_startup_script()
    create_test_script()
    
    print(f"\\n✅ Deployment package ready in '{deploy_dir}/' directory")
    print("\\n📋 Next steps:")
    print("1. Read DEPLOYMENT_INSTRUCTIONS.txt")
    print("2. Transfer companion_capture/ folder to your MaixCAM")
    print("3. Run test_installation.py on the device")
    print("4. Start the app with start_companion_capture.py")
    
    print("\\n🎯 Ready to deploy to your MaixCAM device!")

if __name__ == "__main__":
    main()
