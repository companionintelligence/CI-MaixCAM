"""
Tests for NetworkManager's off-device fallback

maix.network.wifi is only importable on real MaixCAM hardware, so off
device NetworkManager must report "connected" rather than block every
caller on a Wi-Fi stack that isn't there.

Run with:  python3 -m unittest discover tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from network.network_manager import NetworkManager  # noqa: E402


class TestOffDeviceFallback(unittest.TestCase):

    def test_reports_connected_without_the_maix_sdk(self):
        manager = NetworkManager()
        self.assertTrue(manager.is_connected())

    def test_reports_no_ip_without_the_maix_sdk(self):
        manager = NetworkManager()
        self.assertIsNone(manager.get_ip())


if __name__ == '__main__':
    unittest.main()
