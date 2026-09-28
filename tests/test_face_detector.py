"""
Tests for FaceDetector's pure landmark/bbox/emotion mapping and off-device
fallback

maix.nn is only importable on real MaixCAM hardware, so off device
FaceDetector must initialize without raising, report itself unloaded, and
have process() return None forever - never touching a real Retinaface model,
emotion classifier, or camera frame.

Run with:  python3 -m unittest tests/test_face_detector.py -v
"""

import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from ai.face_detector import (  # noqa: E402
    FaceDetector,
    _to_face_detection,
    _to_landmarks,
    _top_emotion,
)


class TestToLandmarks(unittest.TestCase):
    """The pure points -> [[x, y], ...] normalization"""

    def test_normalizes_a_flat_sequence_of_numbers(self):
        points = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.assertEqual(
            _to_landmarks(points),
            [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]],
        )

    def test_normalizes_a_sequence_already_paired_as_tuples(self):
        points = [(1, 2), (3, 4), (5, 6)]
        self.assertEqual(_to_landmarks(points), [[1, 2], [3, 4], [5, 6]])

    def test_normalizes_a_sequence_already_paired_as_lists(self):
        points = [[1, 2], [3, 4]]
        self.assertEqual(_to_landmarks(points), [[1, 2], [3, 4]])

    def test_empty_points_is_an_empty_list(self):
        self.assertEqual(_to_landmarks([]), [])
        self.assertEqual(_to_landmarks(None), [])

    def test_drops_a_dangling_odd_trailing_value_in_a_flat_sequence(self):
        points = [1, 2, 3, 4, 5]
        self.assertEqual(_to_landmarks(points), [[1, 2], [3, 4]])


class TestToFaceDetection(unittest.TestCase):
    """The pure maix.nn.Retinaface result -> unified detection mapping"""

    def test_maps_a_fake_detection_object_with_flat_points(self):
        obj = SimpleNamespace(
            score=0.93, x=10, y=20, w=30, h=40,
            points=[15, 25, 35, 25, 25, 35, 15, 45, 35, 45],
        )

        detection = _to_face_detection(obj)

        self.assertEqual(detection, {
            "label": "face",
            "confidence": 0.93,
            "bbox": [10, 20, 30, 40],
            "landmarks": [[15, 25], [35, 25], [25, 35], [15, 45], [35, 45]],
        })

    def test_maps_a_fake_detection_object_with_paired_points(self):
        obj = SimpleNamespace(
            score=0.5, x=1, y=2, w=3, h=4,
            points=[(6, 7), (8, 9)],
        )

        detection = _to_face_detection(obj)

        self.assertEqual(detection["label"], "face")
        self.assertEqual(detection["confidence"], 0.5)
        self.assertEqual(detection["bbox"], [1, 2, 3, 4])
        self.assertEqual(detection["landmarks"], [[6, 7], [8, 9]])

    def test_works_with_a_plain_class_too(self):
        class FakeObject:
            def __init__(self, score, x, y, w, h, points):
                self.score = score
                self.x = x
                self.y = y
                self.w = w
                self.h = h
                self.points = points

        obj = FakeObject(score=0.77, x=5, y=6, w=7, h=8, points=[])

        detection = _to_face_detection(obj)

        self.assertEqual(detection, {
            "label": "face",
            "confidence": 0.77,
            "bbox": [5, 6, 7, 8],
            "landmarks": [],
        })


class TestTopEmotion(unittest.TestCase):
    """The pure classify()-result -> top (label, confidence) heuristic"""

    def test_picks_the_first_result_as_the_top_prediction(self):
        res = [(3, 0.81), (0, 0.10), (5, 0.05)]
        labels = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]

        top = _top_emotion(res, labels)

        self.assertEqual(top, ("happy", 0.81))

    def test_falls_back_to_the_index_when_labels_do_not_cover_it(self):
        res = [(99, 0.4)]
        labels = ["angry", "happy"]

        top = _top_emotion(res, labels)

        self.assertEqual(top, ("99", 0.4))

    def test_empty_result_is_none(self):
        self.assertIsNone(_top_emotion([], ["angry", "happy"]))
        self.assertIsNone(_top_emotion(None, ["angry", "happy"]))

    def test_confidence_is_coerced_to_float(self):
        res = [(0, 1)]
        labels = ["angry"]

        top = _top_emotion(res, labels)

        self.assertEqual(top, ("angry", 1.0))
        self.assertIsInstance(top[1], float)


class TestOffDeviceFallback(unittest.TestCase):
    """No maix package is installed in this test environment"""

    def _face_config(self, **overrides):
        config = {
            "model_path": "/root/models/retinaface.mud",
            "confidence_threshold": 0.4,
            "processing_interval": 5,
            "priority": 2,
            "enabled": True,
        }
        config.update(overrides)
        return config

    def _emotion_config(self, **overrides):
        config = {
            "model_path": "/root/models/face_emotion.mud",
            "confidence_threshold": 0.6,
            "processing_interval": 10,
            "priority": 3,
            "enabled": True,
        }
        config.update(overrides)
        return config

    def test_initializes_without_raising_without_the_maix_sdk(self):
        detector = FaceDetector(self._face_config())
        self.assertFalse(detector.loaded)

    def test_initializes_with_emotion_config_without_raising(self):
        detector = FaceDetector(self._face_config(), self._emotion_config())
        self.assertFalse(detector.loaded)
        self.assertFalse(detector.emotion_loaded)

    def test_process_returns_none_without_the_maix_sdk(self):
        detector = FaceDetector(self._face_config())
        self.assertIsNone(detector.process(img=None))

    def test_process_returns_none_with_emotion_enabled_too(self):
        detector = FaceDetector(self._face_config(), self._emotion_config())
        self.assertIsNone(detector.process(img=None))

    def test_missing_model_path_is_non_fatal(self):
        detector = FaceDetector(self._face_config(model_path=None))
        self.assertFalse(detector.loaded)
        self.assertIsNone(detector.process(img=None))

    def test_missing_emotion_model_path_is_non_fatal(self):
        detector = FaceDetector(self._face_config(), self._emotion_config(model_path=None))
        self.assertFalse(detector.emotion_loaded)
        self.assertIsNone(detector.process(img=None))

    def test_empty_face_config_is_non_fatal(self):
        detector = FaceDetector({})
        self.assertFalse(detector.loaded)
        self.assertIsNone(detector.process(img=None))

    def test_emotion_config_absent_leaves_emotion_hook_off(self):
        detector = FaceDetector(self._face_config())
        self.assertIsNone(detector.emotion_config)
        self.assertFalse(detector.emotion_loaded)

    def test_cleanup_is_a_harmless_no_op(self):
        detector = FaceDetector(self._face_config(), self._emotion_config())
        detector.cleanup()  # must not raise


if __name__ == '__main__':
    unittest.main()
