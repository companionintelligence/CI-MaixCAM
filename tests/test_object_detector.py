"""
Tests for ObjectDetector's pure detection mapping and off-device fallback

maix.nn is only importable on real MaixCAM hardware, so off device
ObjectDetector must initialize without raising, report itself unloaded, and
have process() return None forever - never touching a real YOLOv8 model or
camera frame.

Run with:  python3 -m unittest tests/test_object_detector.py -v
"""

import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from ai.object_detector import ObjectDetector, _to_detection  # noqa: E402


class TestToDetection(unittest.TestCase):
    """The pure maix.nn.YOLOv8 result -> unified detection mapping"""

    def test_maps_a_fake_detection_object(self):
        obj = SimpleNamespace(class_id=0, score=0.87, x=10, y=20, w=30, h=40)
        labels = ["person", "car"]

        detection = _to_detection(obj, labels)

        self.assertEqual(detection, {
            "label": "person",
            "confidence": 0.87,
            "bbox": [10, 20, 30, 40],
        })

    def test_indexes_the_label_by_class_id(self):
        obj = SimpleNamespace(class_id=1, score=0.42, x=1, y=2, w=3, h=4)
        labels = ["person", "car", "dog"]

        detection = _to_detection(obj, labels)

        self.assertEqual(detection["label"], "car")
        self.assertEqual(detection["confidence"], 0.42)
        self.assertEqual(detection["bbox"], [1, 2, 3, 4])

    def test_works_with_a_plain_class_too(self):
        class FakeObject:
            def __init__(self, class_id, score, x, y, w, h):
                self.class_id = class_id
                self.score = score
                self.x = x
                self.y = y
                self.w = w
                self.h = h

        obj = FakeObject(class_id=0, score=0.99, x=5, y=6, w=7, h=8)
        labels = ["cat"]

        detection = _to_detection(obj, labels)

        self.assertEqual(detection, {
            "label": "cat",
            "confidence": 0.99,
            "bbox": [5, 6, 7, 8],
        })


class TestOffDeviceFallback(unittest.TestCase):
    """No maix package is installed in this test environment"""

    def _model_config(self, **overrides):
        config = {
            "model_path": "/root/models/yolov8n.mud",
            "confidence_threshold": 0.5,
            "processing_interval": 3,
            "priority": 1,
            "enabled": True,
        }
        config.update(overrides)
        return config

    def test_initializes_without_raising_without_the_maix_sdk(self):
        detector = ObjectDetector(self._model_config())
        self.assertFalse(detector.loaded)

    def test_process_returns_none_without_the_maix_sdk(self):
        detector = ObjectDetector(self._model_config())
        self.assertIsNone(detector.process(img=None))

    def test_missing_model_path_is_non_fatal(self):
        detector = ObjectDetector(self._model_config(model_path=None))
        self.assertFalse(detector.loaded)
        self.assertIsNone(detector.process(img=None))

    def test_empty_model_config_is_non_fatal(self):
        detector = ObjectDetector({})
        self.assertFalse(detector.loaded)
        self.assertIsNone(detector.process(img=None))

    def test_cleanup_is_a_harmless_no_op(self):
        detector = ObjectDetector(self._model_config())
        detector.cleanup()  # must not raise


if __name__ == '__main__':
    unittest.main()
