"""
Tests for ObjectTracker's pure IoU math, greedy matching, and track lifecycle

ObjectTracker has zero maix dependency (it tracks whatever bounding boxes
it's handed, never touching a camera or a model), so every test here runs
as plain Python - no maix import, no off-device fallback branch to test,
no network or hardware calls.

Run with:  python3 -m unittest tests/test_object_tracker.py -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from ai.object_tracker import ObjectTracker, iou, greedy_match  # noqa: E402


class TestIoU(unittest.TestCase):
    """The pure IoU([x, y, w, h], [x, y, w, h]) -> float math"""

    def test_identical_boxes_have_iou_one(self):
        box = [0, 0, 10, 10]
        self.assertEqual(iou(box, box), 1.0)

    def test_non_overlapping_boxes_have_iou_zero(self):
        self.assertEqual(iou([0, 0, 10, 10], [20, 20, 10, 10]), 0.0)

    def test_partial_overlap_matches_the_known_value(self):
        # Intersection is the 5x10 strip x in [5, 10], y in [0, 10] -> area 50.
        # Union = 100 + 100 - 50 = 150 -> iou = 50/150 = 1/3.
        result = iou([0, 0, 10, 10], [5, 0, 10, 10])
        self.assertAlmostEqual(result, 1.0 / 3.0)

    def test_a_box_fully_contained_in_another(self):
        # B is entirely inside A: intersection == area(B) == 16.
        # Union = 100 + 16 - 16 = 100 -> iou = 16/100 = 0.16.
        result = iou([0, 0, 10, 10], [2, 2, 4, 4])
        self.assertAlmostEqual(result, 0.16)

    def test_a_zero_area_box_has_iou_zero(self):
        self.assertEqual(iou([0, 0, 0, 10], [0, 0, 10, 10]), 0.0)

    def test_touching_but_not_overlapping_boxes_have_iou_zero(self):
        # Share an edge (x=10) but no interior overlap.
        self.assertEqual(iou([0, 0, 10, 10], [10, 0, 10, 10]), 0.0)


class TestGreedyMatch(unittest.TestCase):
    """The pure track/detection assignment, independent of ObjectTracker"""

    def test_matches_the_single_overlapping_pair(self):
        assignments, matched = greedy_match(
            track_ids=[1],
            track_boxes=[[0, 0, 10, 10]],
            det_boxes=[[1, 1, 10, 10]],
            iou_threshold=0.3,
        )
        self.assertEqual(assignments, {0: 1})
        self.assertEqual(matched, {1})

    def test_below_threshold_pairs_are_not_matched(self):
        assignments, matched = greedy_match(
            track_ids=[1],
            track_boxes=[[0, 0, 10, 10]],
            det_boxes=[[8, 8, 10, 10]],  # small overlap, well under 0.3
            iou_threshold=0.3,
        )
        self.assertEqual(assignments, {})
        self.assertEqual(matched, set())

    def test_two_overlapping_pairs_are_matched_without_swapping(self):
        # track2 vs det_a is 0.333 (above the 0.3 threshold) but strictly
        # lower than the correct pairs (0.818 each), so a correct greedy
        # implementation must still pick the higher-scoring pairing.
        track_ids = [1, 2]
        track_boxes = [[0, 0, 10, 10], [6, 0, 10, 10]]
        det_boxes = [[1, 0, 10, 10], [7, 0, 10, 10]]  # det_a, det_b

        assignments, matched = greedy_match(track_ids, track_boxes, det_boxes, 0.3)

        self.assertEqual(assignments, {0: 1, 1: 2})
        self.assertEqual(matched, {1, 2})

    def test_falsy_boxes_never_match(self):
        assignments, matched = greedy_match(
            track_ids=[1],
            track_boxes=[None],
            det_boxes=[[0, 0, 10, 10]],
            iou_threshold=0.3,
        )
        self.assertEqual(assignments, {})
        self.assertEqual(matched, set())


class TestObjectTracker(unittest.TestCase):
    """update(detections, frame_index) end to end, no maix import needed"""

    def _tracker(self, **overrides):
        config = {"max_track_age_frames": 30, "confidence_threshold": 0.0}
        config.update(overrides)
        return ObjectTracker(config)

    def test_constructs_without_a_config_dict(self):
        tracker = ObjectTracker({})
        self.assertTrue(tracker.loaded)
        self.assertEqual(tracker.max_track_age_frames, 30)

    def test_a_new_box_enters_and_gets_a_track_id(self):
        tracker = self._tracker()
        result = tracker.update(
            [{"label": "person", "confidence": 0.9, "bbox": [100, 100, 50, 50]}],
            frame_index=0,
        )

        self.assertEqual(result["type"], "object_tracking")
        self.assertEqual(result["model"], "IoU-tracker")
        self.assertEqual(result["count"], 1)
        self.assertEqual(len(result["entered"]), 1)
        self.assertEqual(result["exited"], [])
        track_id = result["detections"][0]["track_id"]
        self.assertEqual(result["entered"], [track_id])
        self.assertIsInstance(track_id, int)

    def test_a_box_keeps_a_stable_id_across_small_movement(self):
        tracker = self._tracker()

        r0 = tracker.update(
            [{"label": "person", "confidence": 0.9, "bbox": [100, 100, 50, 50]}], 0
        )
        track_id = r0["detections"][0]["track_id"]

        r1 = tracker.update(
            [{"label": "person", "confidence": 0.9, "bbox": [102, 101, 50, 50]}], 1
        )
        r2 = tracker.update(
            [{"label": "person", "confidence": 0.9, "bbox": [105, 103, 50, 50]}], 2
        )

        self.assertEqual(r1["detections"][0]["track_id"], track_id)
        self.assertEqual(r2["detections"][0]["track_id"], track_id)
        # Only entered once, on the very first frame it appeared.
        self.assertEqual(r1["entered"], [])
        self.assertEqual(r2["entered"], [])
        self.assertEqual(r1["count"], 1)
        self.assertEqual(r2["count"], 1)

    def test_two_overlapping_boxes_are_matched_correctly_across_frames(self):
        tracker = self._tracker()

        r0 = tracker.update(
            [
                {"label": "person", "confidence": 0.9, "bbox": [0, 0, 10, 10]},
                {"label": "person", "confidence": 0.9, "bbox": [6, 0, 10, 10]},
            ],
            frame_index=0,
        )
        track_a = r0["detections"][0]["track_id"]
        track_b = r0["detections"][1]["track_id"]
        self.assertNotEqual(track_a, track_b)
        self.assertEqual(sorted(r0["entered"]), sorted([track_a, track_b]))

        # Next frame: boxes given in swapped order, each moved slightly
        # toward the other track's old position - a naive/order-dependent
        # matcher could swap ids here, a correct IoU-greedy one must not.
        r1 = tracker.update(
            [
                {"label": "person", "confidence": 0.9, "bbox": [7, 0, 10, 10]},  # near track_b
                {"label": "person", "confidence": 0.9, "bbox": [1, 0, 10, 10]},  # near track_a
            ],
            frame_index=1,
        )

        self.assertEqual(r1["detections"][0]["track_id"], track_b)
        self.assertEqual(r1["detections"][1]["track_id"], track_a)
        self.assertEqual(r1["entered"], [])
        self.assertEqual(r1["exited"], [])
        self.assertEqual(r1["count"], 2)

    def test_a_box_missing_for_more_than_max_track_age_frames_exits(self):
        tracker = self._tracker(max_track_age_frames=2)

        r0 = tracker.update(
            [{"label": "person", "confidence": 0.9, "bbox": [0, 0, 10, 10]}], 0
        )
        track_id = r0["detections"][0]["track_id"]

        r1 = tracker.update([], 1)  # missed = 1
        self.assertEqual(r1["exited"], [])
        self.assertEqual(r1["count"], 1)

        r2 = tracker.update([], 2)  # missed = 2, still <= max_track_age_frames
        self.assertEqual(r2["exited"], [])
        self.assertEqual(r2["count"], 1)

        r3 = tracker.update([], 3)  # missed = 3 > max_track_age_frames -> retired
        self.assertEqual(r3["exited"], [track_id])
        self.assertEqual(r3["count"], 0)

    def test_a_retired_track_id_is_not_reused(self):
        tracker = self._tracker(max_track_age_frames=1)

        r0 = tracker.update(
            [{"label": "person", "confidence": 0.9, "bbox": [0, 0, 10, 10]}], 0
        )
        first_id = r0["detections"][0]["track_id"]

        tracker.update([], 1)  # missed = 1, not yet retired
        r2 = tracker.update([], 2)  # missed = 2 > 1 -> retired
        self.assertEqual(r2["exited"], [first_id])

        r3 = tracker.update(
            [{"label": "person", "confidence": 0.9, "bbox": [0, 0, 10, 10]}], 3
        )
        new_id = r3["detections"][0]["track_id"]
        self.assertNotEqual(new_id, first_id)
        self.assertEqual(r3["entered"], [new_id])

    def test_detections_below_the_confidence_threshold_are_dropped(self):
        tracker = self._tracker(confidence_threshold=0.5)

        result = tracker.update(
            [
                {"label": "a", "confidence": 0.9, "bbox": [0, 0, 10, 10]},
                {"label": "b", "confidence": 0.3, "bbox": [50, 50, 10, 10]},
            ],
            frame_index=0,
        )

        self.assertEqual(len(result["detections"]), 1)
        self.assertEqual(result["detections"][0]["label"], "a")
        self.assertEqual(result["count"], 1)

    def test_returns_a_dict_even_with_no_detections_and_no_tracks(self):
        tracker = self._tracker()
        result = tracker.update([], frame_index=0)

        self.assertEqual(result["detections"], [])
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["entered"], [])
        self.assertEqual(result["exited"], [])
        self.assertIsInstance(result["timestamp"], int)
        self.assertIsInstance(result["processing_time_ms"], int)

    def test_cleanup_is_a_harmless_no_op(self):
        tracker = self._tracker()
        tracker.update(
            [{"label": "person", "confidence": 0.9, "bbox": [0, 0, 10, 10]}], 0
        )
        tracker.cleanup()  # must not raise


if __name__ == '__main__':
    unittest.main()
