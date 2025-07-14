#!/usr/bin/env python3
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
