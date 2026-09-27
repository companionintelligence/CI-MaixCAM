"""
Network Manager
Wi-Fi connectivity status for gating uploads

Backed by maix.network.wifi (MaixPy v4 / MaixCDK), which is only importable
on real hardware. Off-device it reports "connected" unconditionally, so
desktop development and unit tests exercise the upload path on whatever
network the host already has, instead of being blocked by a missing SDK.

Author: Companion Intelligence
"""

from utils.logger import get_logger

logger = get_logger('NetworkManager')


class NetworkManager:
    """Reports Wi-Fi connectivity so callers can skip work while offline"""

    def __init__(self, iface='wlan0'):
        self._wifi = None
        try:
            from maix.network.wifi import Wifi
            self._wifi = Wifi(iface)
        except Exception as e:
            logger.info(f"maix Wi-Fi API unavailable, assuming host networking ({e})")

    def is_connected(self) -> bool:
        """True when Wi-Fi is associated with an AP (or off-device, always)"""
        if self._wifi is None:
            return True

        try:
            return bool(self._wifi.is_connected())
        except Exception as e:
            logger.error(f"Wi-Fi status check failed: {e}")
            return False

    def get_ip(self):
        """Current IP address, or None when unknown/disconnected"""
        if self._wifi is None:
            return None

        try:
            return self._wifi.get_ip() or None
        except Exception as e:
            logger.error(f"Failed to read Wi-Fi IP: {e}")
            return None
