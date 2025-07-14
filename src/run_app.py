#!/usr/bin/env python3
"""
Run Companion Intelligence Life Logger
Quick launcher for the main application
"""

print("🚀 Starting Companion Intelligence Life Logger...")
print("📱 Loading main application...")

try:
    # Import and run the main application
    from main import main
    main()
except KeyboardInterrupt:
    print("\n⏹️ Application stopped by user")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
