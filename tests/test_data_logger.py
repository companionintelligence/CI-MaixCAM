"""
Tests for DataLogger

DataLogger has no maix dependency at all (only via utils/device.py's own
already-guarded functions), so its full session lifecycle is testable
off-device against a temporary storage directory.

Run with:  python3 -m unittest discover tests
"""

import os
import sys
import json
import shutil
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from utils.config import Config  # noqa: E402
from data_logger.logger import DataLogger  # noqa: E402


class DataLoggerTestCase(unittest.TestCase):
    """Common temp-storage-directory plumbing"""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        config_path = os.path.join(self.tmp_dir, 'companion_config.json')
        self.storage_dir = os.path.join(self.tmp_dir, 'logs')
        self.config = Config(config_path=config_path)
        self.config.set("storage.base_path", self.storage_dir)
        self.data_logger = DataLogger(self.config)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)


class TestSessionLifecycle(DataLoggerTestCase):

    def test_start_log_end_round_trips_through_the_session_file(self):
        self.data_logger.start_session()
        self.assertTrue(self.data_logger.session_active)
        session_file = self.data_logger.current_session_file
        self.assertTrue(os.path.exists(session_file))

        self.data_logger.log_events([
            {"event_id": "evt-1", "type": "object_detection", "model": "YOLOv8",
             "detections": [{"label": "person", "confidence": 0.9, "bbox": [1, 2, 3, 4]}]},
        ])
        self.assertEqual(self.data_logger.events_logged, 1)

        self.data_logger.end_session()
        self.assertFalse(self.data_logger.session_active)

        with open(session_file, 'r') as f:
            stored = json.load(f)
        self.assertEqual(stored["total_events"], 1)
        self.assertEqual(len(stored["events"]), 1)
        self.assertEqual(stored["events"][0]["confidence_scores"], [0.9])

    def test_ending_with_no_active_session_does_not_raise(self):
        self.data_logger.end_session()  # never started - must not raise


class TestExtractConfidenceScores(DataLoggerTestCase):
    """The unified "detections" list replaces three special-cased branches"""

    def test_reads_confidence_from_any_event_type(self):
        for event_type in ("object_detection", "face_detection", "pose_detection",
                           "ocr_detection", "hand_landmarks", "gesture_detection"):
            event = {"type": event_type, "detections": [{"confidence": 0.5}, {"confidence": 0.7}]}
            self.assertEqual(self.data_logger._extract_confidence_scores(event), [0.5, 0.7])

    def test_missing_detections_key_is_an_empty_list(self):
        self.assertEqual(self.data_logger._extract_confidence_scores({"type": "audio_event"}), [])

    def test_a_detection_missing_confidence_reads_as_zero(self):
        event = {"type": "object_detection", "detections": [{"label": "x"}]}
        self.assertEqual(self.data_logger._extract_confidence_scores(event), [0])


class TestSessionIndex(DataLoggerTestCase):
    """The quick-access index (PROJECT_PLAN.MD 13.9)"""

    def test_no_sessions_yet_is_an_empty_list(self):
        self.assertEqual(self.data_logger.list_sessions(), [])

    def test_a_completed_session_appears_in_the_index(self):
        self.data_logger.start_session()
        session_id = self.data_logger.current_session_id
        self.data_logger.log_events([{"event_id": "evt-1", "type": "object_detection", "data": {}}])
        self.data_logger.end_session()

        sessions = self.data_logger.list_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["session_id"], session_id)
        self.assertEqual(sessions[0]["total_events"], 1)
        self.assertIsNotNone(sessions[0]["end_time"])

    def test_two_sessions_both_appear_without_clobbering_each_other(self):
        self.data_logger.start_session()
        first_id = self.data_logger.current_session_id
        self.data_logger.end_session()

        self.data_logger.start_session()
        second_id = self.data_logger.current_session_id
        self.data_logger.end_session()

        ids = {s["session_id"] for s in self.data_logger.list_sessions()}
        self.assertEqual(ids, {first_id, second_id})


if __name__ == '__main__':
    unittest.main()
