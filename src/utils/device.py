"""
Device Identity
Stable identifiers for the physical MaixCAM this app is running on

Backed by maix.sys (MaixPy v4 / MaixCDK), which is only importable on real
hardware. Off-device - desktop dev, unit tests - every function here falls
back to a config-persisted id or a plain "unknown" rather than raising, the
same off-device tolerance utils/paths.py and utils/time_utils.py already
apply to filesystem and memory access.

Author: Companion Intelligence
"""

import uuid


def get_device_key():
    """Stable 32-hex-char hardware id from maix.sys.device_key(), or None off-device"""
    try:
        from maix import sys as maix_sys
        return maix_sys.device_key()
    except Exception:
        return None


def get_device_name():
    """Human-readable device name, e.g. "MaixCAM" / "MaixCAM-Pro"."""
    try:
        from maix import sys as maix_sys
        return maix_sys.device_name()
    except Exception:
        return "unknown"


def get_maixpy_version():
    """Installed MaixPy firmware version, e.g. "4.12.5", or "unknown" off-device"""
    try:
        from maix import sys as maix_sys
        version = maix_sys.maixpy_version()
        return version or "unknown"
    except Exception:
        return "unknown"


def get_cpu_temp_celsius():
    """CPU temperature in Celsius, or None when unavailable

    Reads the standard Linux sysfs thermal zone (reported in millidegrees
    C), the same off-device-tolerant style utils/time_utils.py's
    get_free_memory() already applies to /proc/meminfo - no maix
    dependency, so this reads identically on MaixCAM's own Linux userspace
    and fails safe (None) everywhere else, including off-device.
    """
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            millidegrees = int(f.read().strip())
        return millidegrees / 1000.0
    except Exception:
        return None


def get_stable_device_id(config):
    """A device id that survives restarts, even off real MaixCAM hardware

    Prefers the real hardware key. Falls back to an id persisted in the app
    config the first time this runs without one - e.g. during desktop
    development, or on a board this SDK doesn't recognise - so repeated runs
    (and therefore CI-Server's idempotency key, which is built from this
    value) stay stable instead of minting a fresh identity every time.
    """
    device_key = get_device_key()
    if device_key:
        return device_key

    stored = config.get("network.device_id")
    if stored:
        return stored

    generated = uuid.uuid4().hex
    config.set("network.device_id", generated)
    config.save_config()
    return generated
