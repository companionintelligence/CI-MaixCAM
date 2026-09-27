"""
Tests for device identity helpers

maix.sys is only importable on real MaixCAM hardware, so these tests only
exercise the off-device fallback paths - the same scope test_models.py and
test_config.py already hold to.

Run with:  python3 -m unittest discover tests
"""

import os
import sys
import tempfile
import shutil
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from utils.config import Config  # noqa: E402
from utils.device import (  # noqa: E402
    get_device_key,
    get_device_name,
    get_maixpy_version,
    get_stable_device_id,
)


class TestOffDeviceFallbacks(unittest.TestCase):
    """No maix.sys here, so every getter must degrade instead of raising"""

    def test_device_key_is_none_off_device(self):
        self.assertIsNone(get_device_key())

    def test_device_name_falls_back_to_unknown(self):
        self.assertEqual(get_device_name(), "unknown")

    def test_maixpy_version_falls_back_to_unknown(self):
        self.assertEqual(get_maixpy_version(), "unknown")


class TestStableDeviceId(unittest.TestCase):
    """Off-device, the id comes from (and persists in) the config file"""

    def setUp(self):
        self.config_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.config_dir, 'companion_config.json')
        self.config = Config(config_path=self.config_path)

    def tearDown(self):
        shutil.rmtree(self.config_dir, ignore_errors=True)

    def test_generates_and_persists_an_id(self):
        first = get_stable_device_id(self.config)
        self.assertTrue(first)

        reloaded = Config(config_path=self.config_path)
        second = get_stable_device_id(reloaded)
        self.assertEqual(first, second)

    def test_reuses_an_already_stored_id(self):
        self.config.set("network.device_id", "existing-id")
        self.config.save_config()

        self.assertEqual(get_stable_device_id(self.config), "existing-id")


if __name__ == '__main__':
    unittest.main()
