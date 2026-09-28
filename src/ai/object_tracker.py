"""
Object Tracker
IoU-based greedy multi-object tracker over a detector's per-frame output

Pure Python - zero maix dependency. Unlike ai/object_detector.py and
ai/face_detector.py, this module wraps no maix.nn model at all: it just
associates bounding boxes across frames, so there is nothing here that can
fail to load off-device and nothing to guard with a lazy maix import. See
the task research notes: MaixPy does ship a first-party multi-object
tracker (maix.tracker.ByteTracker) that does something similar on real
hardware, but this module implements the plain IoU/greedy-matching
algorithm it was scoped to, independent of that API.

Author: Companion Intelligence
"""

import time as _time

from utils.logger import get_logger

logger = get_logger('ObjectTracker')

# Two boxes are considered the same tracked object when their IoU exceeds
# this. Below it, a detection is treated as a new object rather than a
# continuation of an existing track.
DEFAULT_MATCH_IOU_THRESHOLD = 0.3


def _now_ms():
    """Current time in integer milliseconds (plain wall clock).

    No maix.time.ticks_ms() fallback here on purpose - this module has zero
    maix dependency, so it never even attempts that import.
    """
    return int(_time.time() * 1000)


def iou(box_a, box_b):
    """Intersection-over-union of two [x, y, w, h] boxes (top-left + size).

    Pure function, no maix dependency. Returns 0.0 for degenerate boxes
    (zero/negative area) or boxes that don't overlap, and 1.0 for two
    identical boxes.
    """
    ax, ay, aw, ah = box_a
    bx, by, bw, bh = box_b

    area_a = max(0, aw) * max(0, ah)
    area_b = max(0, bw) * max(0, bh)
    if area_a <= 0 or area_b <= 0:
        return 0.0

    ax2, ay2 = ax + aw, ay + ah
    bx2, by2 = bx + bw, by + bh

    inter_x1 = max(ax, bx)
    inter_y1 = max(ay, by)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    if inter_area <= 0:
        return 0.0

    union_area = area_a + area_b - inter_area
    if union_area <= 0:
        return 0.0

    return inter_area / union_area


def greedy_match(track_ids, track_boxes, det_boxes, iou_threshold):
    """Greedily pair tracks to detections by descending IoU.

    Pure function - no maix dependency, no class state. `track_boxes` and
    `det_boxes` are parallel-indexed to `track_ids` and to the detection
    list respectively (box i belongs to track_ids[i] / detection index i).
    A box that is falsy (e.g. bbox missing) never matches anything.

    Returns (assignments, matched_track_ids) where `assignments` maps
    detection index -> track_id for every matched pair, and
    `matched_track_ids` is the set of track ids consumed by a match.
    """
    candidate_pairs = []
    for ti, track_id in enumerate(track_ids):
        track_box = track_boxes[ti]
        if not track_box:
            continue
        for di, det_box in enumerate(det_boxes):
            if not det_box:
                continue
            score = iou(track_box, det_box)
            if score > iou_threshold:
                candidate_pairs.append((score, track_id, di))

    # Highest IoU first; ties broken by insertion order (stable sort), which
    # is deterministic given the fixed track/detection ordering above.
    candidate_pairs.sort(key=lambda pair: pair[0], reverse=True)

    assignments = {}
    matched_track_ids = set()
    matched_det_indices = set()

    for score, track_id, di in candidate_pairs:
        if track_id in matched_track_ids or di in matched_det_indices:
            continue
        assignments[di] = track_id
        matched_track_ids.add(track_id)
        matched_det_indices.add(di)

    return assignments, matched_track_ids


class ObjectTracker:
    """Greedy IoU tracker that assigns stable track_ids to detections

    Takes the "detections" list from one ObjectDetector-shaped event and
    returns the same list back with a "track_id" on each entry, plus
    which track ids newly appeared ("entered") or were just retired
    ("exited") this call.
    """

    def __init__(self, model_config, **kwargs):
        self.model_config = dict(model_config) if model_config else {}
        self.max_track_age_frames = self.model_config.get("max_track_age_frames", 30)
        self.confidence_threshold = self.model_config.get("confidence_threshold", 0.0)
        self.match_iou_threshold = kwargs.get("match_iou_threshold", DEFAULT_MATCH_IOU_THRESHOLD)

        # No model to load - this tracker is pure algorithm over whatever
        # detections it's handed - so it is always "loaded".
        self.loaded = True

        # track_id -> {"bbox", "label", "confidence", "missed"}
        self._tracks = {}
        self._next_track_id = 1

    def update(self, detections, frame_index):
        """Advance the tracker by one frame's worth of detections.

        `detections` is the list of {"label", "confidence", "bbox": [x, y,
        w, h]} dicts from one ObjectDetector event; `frame_index` is an
        informational frame counter (not required to be contiguous).

        Always returns a dict shaped like the shared detection-event
        schema (never None): {"timestamp", "type": "object_tracking",
        "model": "IoU-tracker", "processing_time_ms", "detections" (each
        now carrying "track_id"), "count", "entered", "exited"}.
        """
        start_ms = _now_ms()

        detections = detections or []
        candidates = [
            det for det in detections
            if det.get("confidence", 1.0) >= self.confidence_threshold
        ]

        track_ids = list(self._tracks.keys())
        track_boxes = [self._tracks[tid]["bbox"] for tid in track_ids]
        det_boxes = [det.get("bbox") for det in candidates]

        assignments, matched_track_ids = greedy_match(
            track_ids, track_boxes, det_boxes, self.match_iou_threshold
        )

        entered = []
        output_detections = []

        for di, det in enumerate(candidates):
            track_id = assignments.get(di)
            if track_id is not None:
                track = self._tracks[track_id]
                track["bbox"] = det.get("bbox")
                track["label"] = det.get("label")
                track["confidence"] = det.get("confidence")
                track["missed"] = 0
            else:
                track_id = self._next_track_id
                self._next_track_id += 1
                self._tracks[track_id] = {
                    "bbox": det.get("bbox"),
                    "label": det.get("label"),
                    "confidence": det.get("confidence"),
                    "missed": 0,
                }
                entered.append(track_id)

            out_det = dict(det)
            out_det["track_id"] = track_id
            output_detections.append(out_det)

        # Age every previously-existing track that wasn't matched this call.
        for track_id in track_ids:
            if track_id not in matched_track_ids:
                self._tracks[track_id]["missed"] += 1

        exited = []
        for track_id in list(self._tracks.keys()):
            if self._tracks[track_id]["missed"] > self.max_track_age_frames:
                del self._tracks[track_id]
                exited.append(track_id)

        return {
            "timestamp": _now_ms(),
            "type": "object_tracking",
            "model": "IoU-tracker",
            "processing_time_ms": _now_ms() - start_ms,
            "detections": output_detections,
            "count": len(self._tracks),
            "entered": entered,
            "exited": exited,
        }

    def cleanup(self):
        """No-op, present for symmetry with DataLogger/NetworkUploader."""
        pass
