"""
Tests for the AI model registry and its config migration

The device runtime is MaixPy's CPython and imports `maix`, which is not
installable off-device — so only modules that stay clear of it can be tested
here. utils/models.py is deliberately one of those.

Run with:  python3 -m unittest discover tests

Author: Companion Intelligence
Date: August 26, 2026
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from utils.models import (  # noqa: E402
    ALL_MODELS,
    CONFIG_KEY_TO_MODEL,
    DEFAULT_ENABLED_MODELS,
    default_model_states,
    migrate_model_states,
    read_model_states,
)


class TestRegistry(unittest.TestCase):
    """The catalog itself"""

    def test_default_enabled_models_are_all_real_models(self):
        for name in DEFAULT_ENABLED_MODELS:
            self.assertIn(name, ALL_MODELS)

    def test_config_keys_map_onto_real_models(self):
        for config_key, display_name in CONFIG_KEY_TO_MODEL.items():
            self.assertIn(display_name, ALL_MODELS, config_key)

    def test_default_states_cover_every_model(self):
        states = default_model_states()
        self.assertEqual(sorted(states), sorted(ALL_MODELS))
        self.assertTrue(states["Object Classification"])
        self.assertFalse(states["OCR (Optical Character Recognition)"])


class TestReadModelStates(unittest.TestCase):
    """model_states is the one stored record; everything else is a view"""

    def test_stored_states_win_over_defaults(self):
        states = read_model_states({"model_states": {"Object Classification": False}})
        self.assertFalse(states["Object Classification"])

    def test_omitted_models_fall_back_to_defaults(self):
        states = read_model_states({"model_states": {"Object Classification": False}})
        self.assertTrue(states["Audio Recording"])
        self.assertEqual(sorted(states), sorted(ALL_MODELS))

    def test_missing_record_reads_as_defaults(self):
        self.assertEqual(read_model_states({}), default_model_states())

    def test_junk_record_reads_as_defaults(self):
        self.assertEqual(read_model_states({"model_states": "nonsense"}), default_model_states())


class TestMigrateModelStates(unittest.TestCase):
    """Older files carried the same fact in up to three places"""

    def test_ai_models_enabled_is_folded_in_and_dropped(self):
        config = {
            "ai_models": {
                "ocr": {"enabled": True, "confidence_threshold": 0.8},
                "face_detection": {"enabled": False, "confidence_threshold": 0.4},
            }
        }

        self.assertTrue(migrate_model_states(config))

        # The user's settings survive...
        states = read_model_states(config)
        self.assertTrue(states["OCR (Optical Character Recognition)"])
        self.assertFalse(states["Face Recognition"])

        # ...and the duplicate copy is gone, tuning untouched
        self.assertNotIn("enabled", config["ai_models"]["ocr"])
        self.assertNotIn("enabled", config["ai_models"]["face_detection"])
        self.assertEqual(config["ai_models"]["ocr"]["confidence_threshold"], 0.8)

    def test_model_states_wins_when_the_two_records_disagree(self):
        config = {
            "model_states": {"OCR (Optical Character Recognition)": True},
            "ai_models": {"ocr": {"enabled": False}},
        }

        self.assertTrue(migrate_model_states(config))
        self.assertTrue(read_model_states(config)["OCR (Optical Character Recognition)"])

    def test_selected_models_seeds_states_when_they_are_absent(self):
        config = {"selected_models": ["Audio Playback"]}

        self.assertTrue(migrate_model_states(config))

        states = read_model_states(config)
        self.assertTrue(states["Audio Playback"])
        self.assertFalse(states["Object Classification"])
        self.assertNotIn("selected_models", config)

    def test_selected_models_is_dropped_but_never_overrides_states(self):
        config = {
            "model_states": {name: False for name in ALL_MODELS},
            "selected_models": ["Object Classification"],
        }

        self.assertTrue(migrate_model_states(config))
        self.assertNotIn("selected_models", config)
        self.assertFalse(read_model_states(config)["Object Classification"])

    def test_already_migrated_file_is_left_alone(self):
        config = {"model_states": {"Object Classification": False}, "ai_models": {"ocr": {}}}
        before = {"model_states": {"Object Classification": False}, "ai_models": {"ocr": {}}}

        self.assertFalse(migrate_model_states(config))
        self.assertEqual(config, before)

    def test_file_with_no_model_record_gains_nothing(self):
        config = {"network": {"api_key": ""}}

        self.assertFalse(migrate_model_states(config))
        self.assertNotIn("model_states", config)


if __name__ == '__main__':
    unittest.main()
