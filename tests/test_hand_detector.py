"""
Tests for HandDetector's pure landmark/bbox/gesture mapping and off-device
fallback

maix.nn is only importable on real MaixCAM hardware, so off device
HandDetector must initialize without raising, report itself unloaded, and
have process() return None forever - never touching a real HandLandmarks
model or camera frame. classify_gesture() is a pure geometric heuristic with
zero maix dependency, so it is exercised directly with synthetic coordinate
lists (no model, no hardware).

Run with:  python3 -m unittest tests/test_hand_detector.py -v
"""

import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from ai.hand_detector import (  # noqa: E402
    HandDetector,
    _bbox_from_landmarks,
    _extract_landmarks,
    _to_hand_detection,
    classify_gesture,
)


class TestExtractLandmarks(unittest.TestCase):
    """The pure obj.points -> 21 [x, y] keypoints extraction"""

    def test_extracts_21_points_dropping_bbox_corners_and_z(self):
        bbox_corners = [0, 0, 10, 0, 10, 10, 0, 10]  # 8 values, ignored
        keypoints = []
        for i in range(21):
            keypoints.extend([i, i * 2, i * 3])  # x=i, y=i*2, z=i*3
        points = bbox_corners + keypoints

        landmarks = _extract_landmarks(points)

        self.assertEqual(len(landmarks), 21)
        self.assertEqual(landmarks[0], [0, 0])
        self.assertEqual(landmarks[5], [5, 10])
        self.assertEqual(landmarks[20], [20, 40])

    def test_ignores_a_trailing_landmarks_rel_block(self):
        bbox_corners = [0] * 8
        keypoints = []
        for i in range(21):
            keypoints.extend([i, i, i])
        rel_block = [999] * 42  # would corrupt results if not ignored
        points = bbox_corners + keypoints + rel_block

        landmarks = _extract_landmarks(points)

        self.assertEqual(len(landmarks), 21)
        self.assertEqual(landmarks[-1], [20, 20])

    def test_empty_or_none_points_is_an_empty_list(self):
        self.assertEqual(_extract_landmarks([]), [])
        self.assertEqual(_extract_landmarks(None), [])

    def test_too_short_points_is_an_empty_list(self):
        self.assertEqual(_extract_landmarks([1, 2, 3]), [])


class TestBboxFromLandmarks(unittest.TestCase):
    """The pure landmark-extents -> axis-aligned [x, y, w, h] fallback"""

    def test_derives_bbox_from_point_extents(self):
        landmarks = [[10, 20], [30, 5], [15, 40]]
        self.assertEqual(_bbox_from_landmarks(landmarks), [10, 5, 20, 35])

    def test_empty_landmarks_is_none(self):
        self.assertIsNone(_bbox_from_landmarks([]))


class TestToHandDetection(unittest.TestCase):
    """The pure maix.nn.HandLandmarks result -> unified detection mapping"""

    def _points_for(self, landmarks_2d):
        points = [0] * 8  # bbox corners, unused by this mapping
        for x, y in landmarks_2d:
            points.extend([x, y, 0])  # z unused
        return points

    def test_prefers_the_objects_own_xywh_bbox(self):
        landmarks_2d = [[i, i] for i in range(21)]
        obj = SimpleNamespace(
            score=0.88, x=1, y=2, w=3, h=4,
            points=self._points_for(landmarks_2d),
        )

        detection = _to_hand_detection(obj)

        self.assertEqual(detection["label"], "hand")
        self.assertEqual(detection["confidence"], 0.88)
        self.assertEqual(detection["bbox"], [1, 2, 3, 4])
        self.assertEqual(detection["landmarks"], landmarks_2d)

    def test_derives_bbox_from_landmarks_when_no_xywh_present(self):
        landmarks_2d = [[0, 0], [10, 0], [10, 10], [0, 10]] + [[5, 5]] * 17
        obj = SimpleNamespace(score=0.5, points=self._points_for(landmarks_2d))

        detection = _to_hand_detection(obj)

        self.assertEqual(detection["bbox"], [0, 0, 10, 10])
        self.assertEqual(detection["landmarks"], landmarks_2d)

    def test_works_with_a_plain_class_too(self):
        class FakeObject:
            def __init__(self, score, x, y, w, h, points):
                self.score = score
                self.x = x
                self.y = y
                self.w = w
                self.h = h
                self.points = points

        landmarks_2d = [[i, i] for i in range(21)]
        obj = FakeObject(score=0.7, x=5, y=6, w=7, h=8, points=self._points_for(landmarks_2d))

        detection = _to_hand_detection(obj)

        self.assertEqual(detection, {
            "label": "hand",
            "confidence": 0.7,
            "bbox": [5, 6, 7, 8],
            "landmarks": landmarks_2d,
        })


class TestClassifyGesture(unittest.TestCase):
    """The pure 21-point landmark -> gesture-name heuristic

    Synthetic landmark sets assume the MediaPipe-style ordering documented
    in hand_detector.py: 0=wrist, 1-4=thumb, 5-8=index, 9-12=middle,
    13-16=ring, 17-20=pinky, each finger's four points running base-to-tip.
    Each set fixes a wrist + per-finger base ("MCP") point and only varies
    the fingertip position: far from the palm center to mean "extended",
    close to it to mean "curled into the fist".
    """

    # Shared base/knuckle layout for every synthetic hand below - only the
    # fingertips (index 4, 8, 12, 16, 20) vary between test cases.
    _BASE_POINTS = {
        0: (100, 200),  # wrist
        1: (90, 190), 2: (80, 180), 3: (75, 178),    # thumb: CMC, MCP, IP
        5: (90, 150), 6: (90, 145), 7: (90, 143),     # index: MCP, PIP, DIP
        9: (100, 145), 10: (100, 140), 11: (100, 135),  # middle: MCP, PIP, DIP
        13: (110, 150), 14: (110, 145), 15: (110, 140),  # ring: MCP, PIP, DIP
        17: (120, 160), 18: (120, 155), 19: (120, 150),  # pinky: MCP, PIP, DIP
    }
    # Default (curled-into-the-palm) tip position per finger.
    _CURLED_TIPS = {4: (85, 175), 8: (98, 158), 12: (100, 155), 16: (108, 158), 20: (115, 162)}
    # Extended (pointing away from the palm) tip position per finger.
    _EXTENDED_TIPS = {4: (60, 150), 8: (90, 80), 12: (100, 70), 16: (110, 80), 20: (120, 100)}

    def _hand(self, extended_fingertips=()):
        """Build a 21-point synthetic hand; `extended_fingertips` names
        which of the 5 fingertip indices (4, 8, 12, 16, 20) are extended -
        every other fingertip stays curled.
        """
        points = dict(self._BASE_POINTS)
        for tip_idx, pos in self._CURLED_TIPS.items():
            points[tip_idx] = pos
        for tip_idx in extended_fingertips:
            points[tip_idx] = self._EXTENDED_TIPS[tip_idx]
        return [list(points[i]) for i in range(21)]

    def test_all_fingers_curled_is_a_fist(self):
        landmarks = self._hand(extended_fingertips=())
        self.assertEqual(classify_gesture(landmarks), "fist")

    def test_all_fingers_extended_is_an_open_hand(self):
        landmarks = self._hand(extended_fingertips=(4, 8, 12, 16, 20))
        self.assertEqual(classify_gesture(landmarks), "open_hand")

    def test_four_fingers_extended_thumb_curled_is_still_an_open_hand(self):
        landmarks = self._hand(extended_fingertips=(8, 12, 16, 20))
        self.assertEqual(classify_gesture(landmarks), "open_hand")

    def test_only_the_index_finger_extended_is_pointing(self):
        landmarks = self._hand(extended_fingertips=(8,))
        self.assertEqual(classify_gesture(landmarks), "pointing")

    def test_only_the_pinky_extended_is_not_pointing(self):
        landmarks = self._hand(extended_fingertips=(20,))
        self.assertEqual(classify_gesture(landmarks), "unknown")

    def test_two_fingers_extended_is_unknown(self):
        landmarks = self._hand(extended_fingertips=(8, 12))
        self.assertEqual(classify_gesture(landmarks), "unknown")

    def test_too_few_points_is_unknown(self):
        self.assertEqual(classify_gesture([[0, 0]] * 5), "unknown")

    def test_empty_or_none_is_unknown(self):
        self.assertEqual(classify_gesture([]), "unknown")
        self.assertEqual(classify_gesture(None), "unknown")


class TestOffDeviceFallback(unittest.TestCase):
    """No maix package is installed in this test environment"""

    def _landmarks_config(self, **overrides):
        config = {
            "model_path": "/root/models/hand_landmarks.mud",
            "confidence_threshold": 0.7,
            "processing_interval": 8,
            "priority": 5,
            "enabled": True,
        }
        config.update(overrides)
        return config

    def _gesture_config(self, **overrides):
        config = {
            "model_path": "/root/models/hand_gesture.mud",
            "confidence_threshold": 0.6,
            "processing_interval": 8,
            "priority": 5,
            "enabled": True,
        }
        config.update(overrides)
        return config

    def test_initializes_without_raising_without_the_maix_sdk(self):
        detector = HandDetector(self._landmarks_config())
        self.assertFalse(detector.loaded)

    def test_gesture_heuristic_is_active_without_the_maix_sdk_too(self):
        # classify_gesture() is pure Python with no model to load, so the
        # gesture hook is active purely because gesture_config was supplied
        # - independent of whether the maix SDK, or the landmarks model
        # itself, is available.
        detector = HandDetector(self._landmarks_config(), self._gesture_config())
        self.assertTrue(detector.gesture_loaded)

    def test_process_returns_none_without_the_maix_sdk(self):
        detector = HandDetector(self._landmarks_config())
        self.assertIsNone(detector.process(img=None))

    def test_process_returns_none_with_gesture_config_too(self):
        # The landmarks model itself still isn't loaded off-device, so
        # process() must report nothing regardless of the gesture hook.
        detector = HandDetector(self._landmarks_config(), self._gesture_config())
        self.assertIsNone(detector.process(img=None))

    def test_missing_model_path_is_non_fatal(self):
        detector = HandDetector(self._landmarks_config(model_path=None))
        self.assertFalse(detector.loaded)
        self.assertIsNone(detector.process(img=None))

    def test_empty_landmarks_config_is_non_fatal(self):
        detector = HandDetector({})
        self.assertFalse(detector.loaded)
        self.assertIsNone(detector.process(img=None))

    def test_gesture_config_absent_leaves_gesture_inactive(self):
        detector = HandDetector(self._landmarks_config())
        self.assertIsNone(detector.gesture_config)
        self.assertFalse(detector.gesture_loaded)

    def test_cleanup_is_a_harmless_no_op(self):
        detector = HandDetector(self._landmarks_config(), self._gesture_config())
        detector.cleanup()  # must not raise


if __name__ == '__main__':
    unittest.main()
