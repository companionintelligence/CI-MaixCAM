"""
Tests for PoseDetector's pure posture classifier, keypoint/detection mapping,
and off-device fallback

maix.nn is only importable on real MaixCAM hardware, so off device
PoseDetector must initialize without raising, report itself unloaded, and
have process() return None forever - never touching a real YOLOv8-pose model
or camera frame. classify_posture() itself has zero maix dependency and must
degrade to "unknown" rather than raise on missing/zeroed/occluded keypoints.

Run with:  python3 -m unittest tests/test_pose_detector.py -v
"""

import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from ai.pose_detector import (  # noqa: E402
    PoseDetector,
    _to_keypoints,
    _to_pose_detection,
    classify_posture,
)


# COCO-17 index order, mirrored from ai/pose_detector.py, to build readable
# synthetic keypoint lists in these tests without magic numbers.
NOSE, LEFT_EYE, RIGHT_EYE, LEFT_EAR, RIGHT_EAR = 0, 1, 2, 3, 4
LEFT_SHOULDER, RIGHT_SHOULDER = 5, 6
LEFT_ELBOW, RIGHT_ELBOW = 7, 8
LEFT_WRIST, RIGHT_WRIST = 9, 10
LEFT_HIP, RIGHT_HIP = 11, 12
LEFT_KNEE, RIGHT_KNEE = 13, 14
LEFT_ANKLE, RIGHT_ANKLE = 15, 16


def _keypoints(**by_name):
    """Build a full 17-entry COCO keypoint list, (0, 0) (i.e. "absent")
    everywhere except the named joints given, e.g.
    _keypoints(left_shoulder=(90, 100), right_hip=(105, 180)).
    """
    names_to_index = {
        "nose": NOSE, "left_eye": LEFT_EYE, "right_eye": RIGHT_EYE,
        "left_ear": LEFT_EAR, "right_ear": RIGHT_EAR,
        "left_shoulder": LEFT_SHOULDER, "right_shoulder": RIGHT_SHOULDER,
        "left_elbow": LEFT_ELBOW, "right_elbow": RIGHT_ELBOW,
        "left_wrist": LEFT_WRIST, "right_wrist": RIGHT_WRIST,
        "left_hip": LEFT_HIP, "right_hip": RIGHT_HIP,
        "left_knee": LEFT_KNEE, "right_knee": RIGHT_KNEE,
        "left_ankle": LEFT_ANKLE, "right_ankle": RIGHT_ANKLE,
    }
    points = [(0, 0)] * 17
    for name, xy in by_name.items():
        points[names_to_index[name]] = xy
    return points


class TestToKeypoints(unittest.TestCase):
    """The pure points -> [[x, y], ...] normalization"""

    def test_normalizes_a_flat_sequence_of_numbers(self):
        points = [1, 2, 3, 4, 5, 6]
        self.assertEqual(_to_keypoints(points), [[1, 2], [3, 4], [5, 6]])

    def test_normalizes_a_sequence_already_paired_as_tuples(self):
        points = [(1, 2), (3, 4)]
        self.assertEqual(_to_keypoints(points), [[1, 2], [3, 4]])

    def test_empty_points_is_an_empty_list(self):
        self.assertEqual(_to_keypoints([]), [])
        self.assertEqual(_to_keypoints(None), [])

    def test_drops_a_dangling_odd_trailing_value_in_a_flat_sequence(self):
        points = [1, 2, 3, 4, 5]
        self.assertEqual(_to_keypoints(points), [[1, 2], [3, 4]])

    def test_a_full_coco17_flat_list_pairs_into_17_points(self):
        flat = list(range(0, 68, 2))  # 34 numbers -> 17 pairs
        keypoints = _to_keypoints(flat)
        self.assertEqual(len(keypoints), 17)
        self.assertEqual(keypoints[0], [0, 2])
        self.assertEqual(keypoints[16], [64, 66])


class TestClassifyPostureStanding(unittest.TestCase):
    """A person standing upright: shoulders -> hips -> knees -> ankles form
    a roughly straight vertical line, much taller than it is wide."""

    def test_a_clearly_standing_pose(self):
        keypoints = _keypoints(
            nose=(100, 50), left_eye=(95, 48), right_eye=(105, 48),
            left_ear=(90, 50), right_ear=(110, 50),
            left_shoulder=(90, 100), right_shoulder=(110, 100),
            left_elbow=(85, 130), right_elbow=(115, 130),
            left_wrist=(80, 160), right_wrist=(120, 160),
            left_hip=(95, 180), right_hip=(105, 180),
            left_knee=(95, 230), right_knee=(105, 230),
            left_ankle=(95, 280), right_ankle=(105, 280),
        )
        self.assertEqual(classify_posture(keypoints), "standing")

    def test_standing_still_works_with_one_side_of_each_joint_occluded(self):
        # Only the left-side lower-body joints are valid; the right side is
        # zeroed out (as an occluded/never-detected point would be) - the
        # per-joint average should just fall back to the one valid side.
        keypoints = _keypoints(
            left_shoulder=(90, 100), right_shoulder=(0, 0),
            left_hip=(95, 180), right_hip=(0, 0),
            left_knee=(95, 230), right_knee=(0, 0),
            left_ankle=(95, 280), right_ankle=(0, 0),
        )
        self.assertEqual(classify_posture(keypoints), "standing")


class TestClassifyPostureSitting(unittest.TestCase):
    """A person sitting: hips and knees at roughly the same height (thighs
    horizontal), while the shins from knee to ankle stay roughly vertical."""

    def test_a_clearly_sitting_pose(self):
        keypoints = _keypoints(
            left_shoulder=(90, 100), right_shoulder=(110, 100),
            left_hip=(90, 180), right_hip=(110, 180),
            left_knee=(90, 185), right_knee=(110, 185),
            left_ankle=(90, 280), right_ankle=(110, 280),
        )
        self.assertEqual(classify_posture(keypoints), "sitting")


class TestClassifyPostureLying(unittest.TestCase):
    """A person lying down: all keypoints cluster near the same height, so
    the pose reads as wide and short rather than tall."""

    def test_a_clearly_lying_pose(self):
        keypoints = _keypoints(
            left_shoulder=(100, 200), right_shoulder=(100, 210),
            left_hip=(150, 200), right_hip=(150, 210),
            left_knee=(200, 200), right_knee=(200, 210),
            left_ankle=(250, 200), right_ankle=(250, 210),
        )
        self.assertEqual(classify_posture(keypoints), "lying")

    def test_lying_is_detected_even_without_knee_keypoints(self):
        # Only shoulders and ankles are valid, but they are far apart
        # horizontally and level vertically - still clearly lying.
        keypoints = _keypoints(
            left_shoulder=(100, 200), right_shoulder=(100, 210),
            left_ankle=(260, 205), right_ankle=(260, 215),
        )
        self.assertEqual(classify_posture(keypoints), "lying")


class TestClassifyPostureDegradesToUnknown(unittest.TestCase):
    """Missing, zeroed, or otherwise unusable keypoints must degrade to
    "unknown" rather than raise."""

    def test_all_zeroed_keypoints_is_unknown(self):
        keypoints = _keypoints()  # everything defaults to (0, 0)
        self.assertEqual(classify_posture(keypoints), "unknown")

    def test_only_a_face_detected_is_unknown(self):
        keypoints = _keypoints(nose=(100, 50), left_eye=(95, 48), right_eye=(105, 48))
        self.assertEqual(classify_posture(keypoints), "unknown")

    def test_empty_keypoint_list_is_unknown(self):
        self.assertEqual(classify_posture([]), "unknown")

    def test_negative_occluded_marker_values_are_treated_as_absent(self):
        # MaixPy marks an occluded/invalid keypoint with a negative value;
        # with only such points present there is nothing to reason about.
        keypoints = _keypoints(left_hip=(-1, -1), right_hip=(-1, -1))
        self.assertEqual(classify_posture(keypoints), "unknown")

    def test_upper_body_only_with_no_hip_knee_or_ankle_is_unknown(self):
        keypoints = _keypoints(
            left_shoulder=(90, 100), right_shoulder=(110, 100),
            left_elbow=(85, 130), right_elbow=(115, 130),
        )
        self.assertEqual(classify_posture(keypoints), "unknown")

    def test_shoulders_and_hips_without_knees_or_ankles_is_unknown(self):
        # Enough to tell the body isn't lying down flat, but not enough to
        # tell standing from sitting apart.
        keypoints = _keypoints(
            left_shoulder=(90, 100), right_shoulder=(110, 100),
            left_hip=(95, 180), right_hip=(105, 180),
        )
        self.assertEqual(classify_posture(keypoints), "unknown")

    def test_a_short_keypoint_list_does_not_raise(self):
        self.assertEqual(classify_posture([(90, 100), (110, 100)]), "unknown")

    def test_malformed_entries_do_not_raise(self):
        keypoints = [None, (1,), "nope", (5, 5)] + [(0, 0)] * 13
        self.assertEqual(classify_posture(keypoints), "unknown")


class TestToPoseDetection(unittest.TestCase):
    """The pure maix.nn.YOLOv8(pose) result -> unified detection mapping"""

    def test_maps_a_fake_detection_object_with_flat_points(self):
        flat_points = []
        keypoints = _keypoints(
            left_shoulder=(90, 100), right_shoulder=(110, 100),
            left_hip=(95, 180), right_hip=(105, 180),
            left_knee=(95, 230), right_knee=(105, 230),
            left_ankle=(95, 280), right_ankle=(105, 280),
        )
        for x, y in keypoints:
            flat_points.extend([x, y])

        obj = SimpleNamespace(score=0.91, x=50, y=40, w=100, h=220, points=flat_points)

        detection = _to_pose_detection(obj)

        self.assertEqual(detection["label"], "person")
        self.assertEqual(detection["confidence"], 0.91)
        self.assertEqual(detection["bbox"], [50, 40, 100, 220])
        self.assertEqual(len(detection["keypoints"]), 17)
        self.assertEqual(detection["keypoints"][LEFT_SHOULDER], [90, 100])
        self.assertEqual(detection["posture"], "standing")

    def test_maps_a_detection_with_no_points_to_unknown_posture(self):
        obj = SimpleNamespace(score=0.6, x=1, y=2, w=3, h=4, points=[])

        detection = _to_pose_detection(obj)

        self.assertEqual(detection["keypoints"], [])
        self.assertEqual(detection["posture"], "unknown")

    def test_works_with_a_plain_class_too(self):
        class FakeObject:
            def __init__(self, score, x, y, w, h, points):
                self.score = score
                self.x = x
                self.y = y
                self.w = w
                self.h = h
                self.points = points

        obj = FakeObject(score=0.5, x=1, y=2, w=3, h=4, points=[10, 20, 30, 40])

        detection = _to_pose_detection(obj)

        self.assertEqual(detection["label"], "person")
        self.assertEqual(detection["keypoints"], [[10, 20], [30, 40]])


class TestOffDeviceFallback(unittest.TestCase):
    """No maix package is installed in this test environment"""

    def _model_config(self, **overrides):
        config = {
            "model_path": "/root/models/yolov8n_pose.mud",
            "confidence_threshold": 0.5,
            "processing_interval": 12,
            "priority": 6,
            "enabled": True,
        }
        config.update(overrides)
        return config

    def test_initializes_without_raising_without_the_maix_sdk(self):
        detector = PoseDetector(self._model_config())
        self.assertFalse(detector.loaded)

    def test_process_returns_none_without_the_maix_sdk(self):
        detector = PoseDetector(self._model_config())
        self.assertIsNone(detector.process(img=None))

    def test_missing_model_path_is_non_fatal(self):
        detector = PoseDetector(self._model_config(model_path=None))
        self.assertFalse(detector.loaded)
        self.assertIsNone(detector.process(img=None))

    def test_empty_model_config_is_non_fatal(self):
        detector = PoseDetector({})
        self.assertFalse(detector.loaded)
        self.assertIsNone(detector.process(img=None))

    def test_cleanup_is_a_harmless_no_op(self):
        detector = PoseDetector(self._model_config())
        detector.cleanup()  # must not raise


if __name__ == '__main__':
    unittest.main()
