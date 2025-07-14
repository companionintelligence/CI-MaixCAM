"""
Time Utilities for MaixPy
Cross-platform time functions that work with MaixPy's time API
"""

import time
import gc
import os

def get_time_ms():
    """Get current time in milliseconds"""
    return int(time.time() * 1000)

def get_time_diff_ms(start_time_ms, end_time_ms=None):
    """Get time difference in milliseconds"""
    if end_time_ms is None:
        end_time_ms = get_time_ms()
    return end_time_ms - start_time_ms

def sleep_ms(ms):
    """Sleep for specified milliseconds"""
    time.sleep(ms / 1000.0)

def get_iso_timestamp():
    """Get current time as ISO format string"""
    import datetime
    return datetime.datetime.now().isoformat()

def get_free_memory():
    """Get free memory in bytes (simplified estimate)"""
    try:
        # Try to read /proc/meminfo if available (Linux systems)
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemAvailable:'):
                    return int(line.split()[1]) * 1024  # Convert KB to bytes
        # Fallback: return a reasonable estimate
        return 100 * 1024 * 1024  # 100MB estimate
    except:
        # Last fallback: return a reasonable estimate
        return 100 * 1024 * 1024  # 100MB estimate
