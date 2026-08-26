"""
Tests for Config's view over the single stored model-enabled record

utils/config.py stays clear of the `maix` SDK, so it can be exercised off
device against a temporary file.

Run with:  python3 -m unittest discover tests

Author: Companion Intelligence
Date: August 26, 2026
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from utils.config import Config  # noqa: E402


class ConfigTestCase(unittest.TestCase):
    """Common temporary-config-file plumbing"""

    def setUp(self):
        self.config_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.config_dir, 'companion_config.json')

    def tearDown(self):
        shutil.rmtree(self.config_dir, ignore_errors=True)

    def write(self, document):
        with open(self.config_path, 'w') as f:
            json.dump(document, f)

    def read(self):
        with open(self.config_path, 'r') as f:
            return json.load(f)


class TestSingleStoredCopy(ConfigTestCase):
    """ai_models holds tuning; model_states holds what runs"""

    def test_defaults_store_no_enabled_flag(self):
        config = Config(config_path=self.config_path)

        for model_name, model_config in config.config["ai_models"].items():
            self.assertNotIn("enabled", model_config, model_name)

        for model_config in self.read()["ai_models"].values():
            self.assertNotIn("enabled", model_config)

    def test_is_model_enabled_reads_model_states(self):
        self.write({"model_states": {"OCR (Optical Character Recognition)": True,
                                     "Object Classification": False}})
        config = Config(config_path=self.config_path)

        self.assertTrue(config.is_model_enabled("ocr"))
        self.assertFalse(config.is_model_enabled("object_detection"))
        self.assertIn("ocr", config.get_enabled_models())
        self.assertNotIn("object_detection", config.get_enabled_models())

    def test_toggle_model_writes_only_model_states(self):
        config = Config(config_path=self.config_path)
        config.toggle_model("ocr", True)

        stored = self.read()
        self.assertTrue(stored["model_states"]["OCR (Optical Character Recognition)"])
        self.assertNotIn("enabled", stored["ai_models"]["ocr"])

        self.assertTrue(Config(config_path=self.config_path).is_model_enabled("ocr"))

    def test_model_config_view_carries_enabled_without_storing_it(self):
        self.write({"model_states": {"OCR (Optical Character Recognition)": True}})
        config = Config(config_path=self.config_path)

        view = config.get_ai_model_config("ocr")
        self.assertTrue(view["enabled"])
        self.assertEqual(view["model_path"], "/root/models/pp_ocr.mud")

        # The view is a copy - writing to it must not create a second record
        view["enabled"] = False
        self.assertTrue(config.is_model_enabled("ocr"))
        self.assertNotIn("enabled", config.config["ai_models"]["ocr"])

        self.assertTrue(config.get_ai_models_config()["ocr"]["enabled"])

    def test_unknown_model_config_is_still_empty(self):
        config = Config(config_path=self.config_path)
        self.assertEqual(config.get_ai_model_config("no_such_model"), {})


class TestLoadMigration(ConfigTestCase):
    """A device configured by an older build keeps its settings"""

    def test_legacy_enabled_flags_are_folded_forward(self):
        self.write({"ai_models": {"ocr": {"enabled": True},
                                  "face_detection": {"enabled": False}}})

        config = Config(config_path=self.config_path)
        self.assertTrue(config.is_model_enabled("ocr"))
        self.assertFalse(config.is_model_enabled("face_detection"))

        config.save_config()
        stored = self.read()
        self.assertTrue(stored["model_states"]["OCR (Optical Character Recognition)"])
        self.assertNotIn("enabled", stored["ai_models"]["ocr"])

    def test_model_states_wins_over_the_legacy_flag(self):
        self.write({"model_states": {"OCR (Optical Character Recognition)": True},
                    "ai_models": {"ocr": {"enabled": False}}})

        self.assertTrue(Config(config_path=self.config_path).is_model_enabled("ocr"))

    def test_setup_screen_keys_round_trip_through_a_save(self):
        self.write({"timestamp": 1.0,
                    "model_states": {"Video Playback": False},
                    "network": {"endpoint_url": "https://real.example/upload"}})

        config = Config(config_path=self.config_path)
        config.save_config()

        stored = self.read()
        self.assertEqual(stored["timestamp"], 1.0)
        self.assertFalse(stored["model_states"]["Video Playback"])
        self.assertEqual(stored["network"]["endpoint_url"], "https://real.example/upload")


if __name__ == '__main__':
    unittest.main()
