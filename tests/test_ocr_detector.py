"""
Tests for OcrDetector's pure quad-to-bbox conversion, detection mapping and
off-device fallback

maix.nn is only importable on real MaixCAM hardware, so off device
OcrDetector must initialize without raising, report itself unloaded, and
have process() return None forever - never touching a real PP_OCR model or
camera frame.

Run with:  python3 -m unittest tests/test_ocr_detector.py -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from ai.ocr_detector import OcrDetector, points_to_bbox, _to_ocr_detection  # noqa: E402


class FakeOcrBox:
    """Stand-in for maix.nn.OCR_Box - only needs to_list()."""

    def __init__(self, points):
        self._points = list(points)

    def to_list(self):
        return self._points


class FakeOcrObject:
    """Stand-in for maix.nn.OCR_Object - only needs char_str()/score/box."""

    def __init__(self, text, score, box_points):
        self._text = text
        self.score = score
        self.box = FakeOcrBox(box_points)

    def char_str(self):
        return self._text


class TestPointsToBbox(unittest.TestCase):
    """The pure OCR_Box quad -> axis-aligned [x, y, w, h] bbox conversion"""

    def test_flat_8_number_list_axis_aligned_rectangle(self):
        # top-left(10,10) -> top-right(50,10) -> bottom-right(50,40) ->
        # bottom-left(10,40): an already axis-aligned rectangle.
        points = [10, 10, 50, 10, 50, 40, 10, 40]

        self.assertEqual(points_to_bbox(points), [10, 10, 40, 30])

    def test_list_of_4_pairs_axis_aligned_rectangle(self):
        points = [[10, 10], [50, 10], [50, 40], [10, 40]]

        self.assertEqual(points_to_bbox(points), [10, 10, 40, 30])

    def test_list_of_4_tuple_pairs(self):
        points = [(10, 10), (50, 10), (50, 40), (10, 40)]

        self.assertEqual(points_to_bbox(points), [10, 10, 40, 30])

    def test_flat_8_number_list_rotated_quadrilateral(self):
        # A diamond (45-degree rotated square) centered at (50, 50):
        # top(50,10) -> right(90,50) -> bottom(50,90) -> left(10,50).
        # None of its edges are axis-aligned, so a naive "first two points"
        # reading would be wrong; the correct answer is the enclosing
        # rectangle over all four corners.
        points = [50, 10, 90, 50, 50, 90, 10, 50]

        self.assertEqual(points_to_bbox(points), [10, 10, 80, 80])

    def test_list_of_4_pairs_rotated_quadrilateral(self):
        points = [[50, 10], [90, 50], [50, 90], [10, 50]]

        self.assertEqual(points_to_bbox(points), [10, 10, 80, 80])

    def test_rotated_quadrilateral_with_negative_and_uneven_coordinates(self):
        # An arbitrary skewed quad - corners in no particular sorted order -
        # still reduces to min/max over x's and y's.
        points = [[5, 30], [40, -10], [70, 25], [20, 60]]

        x_min, x_max = 5, 70
        y_min, y_max = -10, 60
        self.assertEqual(
            points_to_bbox(points),
            [x_min, y_min, x_max - x_min, y_max - y_min],
        )

    def test_empty_input_returns_none(self):
        self.assertIsNone(points_to_bbox([]))
        self.assertIsNone(points_to_bbox(None))


class TestToOcrDetection(unittest.TestCase):
    """The pure maix.nn.OCR_Object -> unified detection mapping"""

    def test_maps_a_fake_ocr_object(self):
        obj = FakeOcrObject("hello", 0.93, [10, 10, 50, 10, 50, 40, 10, 40])

        detection = _to_ocr_detection(obj)

        self.assertEqual(detection, {
            "label": "hello",
            "text": "hello",
            "confidence": 0.93,
            "bbox": [10, 10, 40, 30],
        })

    def test_truncates_long_text_in_label_but_keeps_full_text(self):
        long_text = "x" * 50
        obj = FakeOcrObject(long_text, 0.5, [0, 0, 10, 0, 10, 10, 0, 10])

        detection = _to_ocr_detection(obj)

        self.assertEqual(len(detection["label"]), 40)
        self.assertEqual(detection["label"], long_text[:40])
        self.assertEqual(detection["text"], long_text)

    def test_text_exactly_at_the_limit_is_not_truncated(self):
        exact_text = "y" * 40
        obj = FakeOcrObject(exact_text, 0.5, [0, 0, 10, 0, 10, 10, 0, 10])

        detection = _to_ocr_detection(obj)

        self.assertEqual(detection["label"], exact_text)
        self.assertEqual(detection["text"], exact_text)

    def test_uses_the_rotated_quad_correctly(self):
        obj = FakeOcrObject("diamond", 0.75, [50, 10, 90, 50, 50, 90, 10, 50])

        detection = _to_ocr_detection(obj)

        self.assertEqual(detection["bbox"], [10, 10, 80, 80])
        self.assertEqual(detection["confidence"], 0.75)


class TestOffDeviceFallback(unittest.TestCase):
    """No maix package is installed in this test environment"""

    def _model_config(self, **overrides):
        config = {
            "model_path": "/root/models/pp_ocr.mud",
            "confidence_threshold": 0.8,
            "processing_interval": 15,
            "priority": 4,
            "enabled": True,
        }
        config.update(overrides)
        return config

    def test_initializes_without_raising_without_the_maix_sdk(self):
        detector = OcrDetector(self._model_config())
        self.assertFalse(detector.loaded)

    def test_process_returns_none_without_the_maix_sdk(self):
        detector = OcrDetector(self._model_config())
        self.assertIsNone(detector.process(img=None))

    def test_missing_model_path_is_non_fatal(self):
        detector = OcrDetector(self._model_config(model_path=None))
        self.assertFalse(detector.loaded)
        self.assertIsNone(detector.process(img=None))

    def test_empty_model_config_is_non_fatal(self):
        detector = OcrDetector({})
        self.assertFalse(detector.loaded)
        self.assertIsNone(detector.process(img=None))

    def test_cleanup_is_a_harmless_no_op(self):
        detector = OcrDetector(self._model_config())
        detector.cleanup()  # must not raise


if __name__ == '__main__':
    unittest.main()
