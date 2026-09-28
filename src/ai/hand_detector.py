"""
Hand Detector
Wraps maix.nn.HandLandmarks for 21-point hand keypoints + bbox, with an
optional geometric gesture-classification hook layered on top.

Backed by maix.nn (MaixPy v4 / MaixCDK), which is only importable on real
hardware. Off-device - desktop dev, unit tests - the maix import is deferred
to inside a try/except in __init__, so this module always imports cleanly;
the model then simply never loads and process() reports nothing, the same
off-device tolerance utils/device.py, network/network_manager.py and
ai/object_detector.py apply to their own maix.* usage. maix.nn.HandLandmarks
itself additionally requires MaixPy/MaixCDK firmware >= 4.9.3.

Gesture classification (see the task research notes) is NOT backed by a
dedicated maix.nn class - a full case-insensitive grep of the entire maix.nn
API reference for "Gesture" turns up zero matches; HandLandmarks is the only
hand-related nn class. What Sipeed documents/ships instead is a separate,
uncompiled Python-level project (MaixPy/projects/app_hand_gesture_classifier)
built around a small custom LinearSVC (linear SVM) trained on a landmark ->
geometric-feature-vector pipeline, not an importable maix.nn.* class. Rather
than vendor/reimplement that project's model file and preprocessing exactly,
gesture classification here is done with the pure classify_gesture()
heuristic below, over HandLandmarks' own 21 keypoints - fingertip-to-palm
distance vs. that finger's own base-knuckle-to-palm distance, per finger.
This needs no model file, so it "loads" successfully as soon as a
gesture_config is supplied - see HandDetector's docstring.

Author: Companion Intelligence
"""

import math
import time as _time

from utils.logger import get_logger

logger = get_logger('HandDetector')

# maix.nn.HandLandmarks packs one flat `obj.points` array per detected hand:
# 8 bbox-corner values (box_topleft_x, box_topleft_y, box_topright_x,
# box_topright_y, box_bottomright_x, box_bottomright_y, box_bottomleft_x,
# box_bottomleft_y), followed by 21 (x, y, z) keypoint triples, followed
# optionally by a further 42-value bbox-relative (x, y) block when
# detect(landmarks_rel=True) was used (not requested here, so not read).
_BBOX_CORNER_VALUES = 8
_NUM_KEYPOINTS = 21
_KEYPOINT_VALUES = _NUM_KEYPOINTS * 3

# Assumed 21-point keypoint order (ported from MediaPipe's hand-landmark
# topology per MaixPy's docs; not spelled out index-by-index in the fetched
# text itself, so treated as a reasonable but not textually confirmed
# inference): 0 = wrist, 1-4 = thumb (CMC, MCP, IP, TIP), 5-8 = index (MCP,
# PIP, DIP, TIP), 9-12 = middle, 13-16 = ring, 17-20 = pinky, each finger's
# four points running base-to-tip.
_WRIST = 0
# (base/MCP-ish joint index, fingertip index) per finger, used by the
# extended-vs-curled heuristic below. Thumb has no true MCP at index 2 in
# the strict anatomical sense (that is its own MCP joint), but it plays the
# same "base of the finger" role for this heuristic.
_FINGER_JOINTS = {
    "thumb": (2, 4),
    "index": (5, 8),
    "middle": (9, 12),
    "ring": (13, 16),
    "pinky": (17, 20),
}
# The four MCP-ish joints used, together with the wrist, to approximate the
# palm center.
_PALM_REFERENCE_POINTS = (_WRIST, 5, 9, 13, 17)

# A finger counts as "extended" when its tip sits at least this much farther
# from the palm center than its own base joint does. >1.0 gives a margin so
# a nearly-straight-but-not-fully-open finger doesn't flip on noise; it is a
# heuristic constant, not a value from any spec.
_EXTENDED_MARGIN = 1.2


def _now_ms():
    """Current time in integer milliseconds.

    Uses maix.time.ticks_ms() when the maix SDK is available (on-device),
    otherwise falls back to the wall clock. The maix import is lazy and
    wrapped in try/except so this stays safe to call off-device.
    """
    try:
        from maix import time as maix_time
        return maix_time.ticks_ms()
    except Exception:
        return int(_time.time() * 1000)


def _extract_landmarks(points):
    """Pull the 21 (x, y) hand keypoints out of a maix.nn.HandLandmarks
    result's flat `points` array, dropping the z (depth) component and the
    leading 8 bbox-corner values.

    Pure - no maix dependency - so it is trivially unit-testable with a
    plain flat list of numbers. Returns [] when `points` is falsy or too
    short to hold a full 21-point block (fewer than 8 + 21*3 = 71 values) -
    NOTE the official hand_landmarks.md example itself has a copy/paste bug
    computing this offset ("21**" instead of "21*3", apparently mangled by
    markdown bold-parsing); this module always uses the correct 21 * 3 = 63.
    """
    if not points or len(points) < _BBOX_CORNER_VALUES + _KEYPOINT_VALUES:
        return []

    keypoints = points[_BBOX_CORNER_VALUES:_BBOX_CORNER_VALUES + _KEYPOINT_VALUES]
    return [[keypoints[i], keypoints[i + 1]] for i in range(0, len(keypoints), 3)]


def _bbox_from_landmarks(landmarks):
    """Derive an axis-aligned [x, y, w, h] bbox from the extents of a list
    of [x, y] landmark points, for use when no direct bbox field is
    available on the detection object.

    Pure - no maix dependency. Returns None for an empty landmarks list.
    """
    if not landmarks:
        return None

    xs = [p[0] for p in landmarks]
    ys = [p[1] for p in landmarks]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    return [min_x, min_y, max_x - min_x, max_y - min_y]


def _to_hand_detection(obj):
    """Map one maix.nn.HandLandmarks result object to the unified detection
    dict (without the "gesture" key - that is layered on separately by
    HandDetector.process(), since it needs to know whether the gesture hook
    is active).

    Pure function - no maix dependency - so it is trivially unit-testable
    with a plain fake object (e.g. a SimpleNamespace with score/points and
    optionally x/y/w/h attributes), without any hardware or a real
    maix.nn.HandLandmarks instance. Prefers the object's own x/y/w/h bbox
    (confirmed present on maix.nn.HandLandmarks results per the API
    reference) and falls back to deriving a bbox from the landmark extents
    when those attributes are absent.
    """
    landmarks = _extract_landmarks(getattr(obj, "points", None))

    if all(hasattr(obj, attr) for attr in ("x", "y", "w", "h")):
        bbox = [obj.x, obj.y, obj.w, obj.h]
    else:
        bbox = _bbox_from_landmarks(landmarks)

    return {
        "label": "hand",
        "confidence": obj.score,
        "bbox": bbox,
        "landmarks": landmarks,
    }


def _dist(a, b):
    """Euclidean distance between two [x, y] points. Pure, zero maix dependency."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _palm_center(landmarks):
    """Approximate palm center: the average of the wrist and the four MCP
    (finger-base) points. Pure, zero maix dependency.
    """
    xs = [landmarks[i][0] for i in _PALM_REFERENCE_POINTS]
    ys = [landmarks[i][1] for i in _PALM_REFERENCE_POINTS]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def _is_finger_extended(landmarks, base_idx, tip_idx, palm_center):
    """One finger's extended-vs-curled call: extended when its tip sits
    meaningfully farther from the palm center than its own base joint does.
    Pure, zero maix dependency.
    """
    tip_dist = _dist(landmarks[tip_idx], palm_center)
    base_dist = _dist(landmarks[base_idx], palm_center)
    return tip_dist > base_dist * _EXTENDED_MARGIN


def classify_gesture(landmarks):
    """Classify a hand shape from its 21 (x, y) landmark points into one of
    "open_hand" / "fist" / "pointing" / "unknown".

    Pure geometric heuristic, zero maix dependency, so it is fully
    unit-testable with synthetic coordinate lists: for each finger, compares
    its fingertip-to-palm-center distance against its own base-knuckle-to-
    palm-center distance to decide extended vs. curled (see
    _is_finger_extended), then maps the pattern of extended fingers:
    - all five curled -> "fist"
    - four or more extended -> "open_hand"
    - exactly one extended, and it's the index finger -> "pointing"
    - anything else (e.g. two/three fingers extended, or a lone non-index
      finger extended) -> "unknown"

    No dedicated maix.nn gesture-classifier API is confirmed to exist (see
    the module docstring), so this is the shipped gesture-classification
    path for HandDetector rather than a stand-in for one.

    Assumes the MediaPipe-style 21-point ordering documented at the top of
    this module (0=wrist, 1-4=thumb, 5-8=index, 9-12=middle, 13-16=ring,
    17-20=pinky) - a reasonable inference from "ported from MediaPipe" per
    the research notes, not a textually confirmed index mapping. Returns
    "unknown" for None/too-short input rather than raising.
    """
    if not landmarks or len(landmarks) < _NUM_KEYPOINTS:
        return "unknown"

    palm_center = _palm_center(landmarks)
    extended = {
        finger: _is_finger_extended(landmarks, base_idx, tip_idx, palm_center)
        for finger, (base_idx, tip_idx) in _FINGER_JOINTS.items()
    }
    extended_count = sum(1 for is_extended in extended.values() if is_extended)

    if extended_count == 0:
        return "fist"
    if extended_count >= 4:
        return "open_hand"
    if extended_count == 1 and extended["index"]:
        return "pointing"
    return "unknown"


class HandDetector:
    """Wraps maix.nn.HandLandmarks (+ optional gesture classification) to
    produce unified hand_landmarks events.

    Constructor intentionally departs from the generic (model_config,
    **kwargs) shape other detectors use, the same way FaceDetector's does:
    it takes the "hand_landmarks" and "hand_gesture"
    Config.get_ai_model_config() dicts together, since one hand_landmarks
    event carries both. gesture_config is None/absent when Hand Gesture
    Classification is toggled off.

    Unlike FaceDetector's emotion hook, the gesture hook here is a pure
    Python heuristic (classify_gesture(), see above) with no model file to
    load - no dedicated maix.nn gesture-classifier class is confirmed to
    exist - so it becomes active as soon as gesture_config is supplied,
    independent of whether the underlying hand_landmarks model itself
    loaded (though process() still reports nothing at all when the
    landmarks model didn't load, since there are no landmarks to classify).
    """

    def __init__(self, landmarks_config, gesture_config=None, **kwargs):
        self.landmarks_config = dict(landmarks_config) if landmarks_config else {}
        self.gesture_config = dict(gesture_config) if gesture_config else None

        self.model_path = self.landmarks_config.get("model_path")
        self.confidence_threshold = self.landmarks_config.get("confidence_threshold", 0.7)
        self.iou_threshold = kwargs.get("iou_threshold", 0.45)
        self.conf_th2 = kwargs.get("conf_th2", 0.8)

        self.detector = None
        self.loaded = False

        # The gesture heuristic is pure Python with no model to load, so it
        # is considered "loaded" as soon as a gesture_config was supplied.
        self.gesture_loaded = self.gesture_config is not None

        self._load_model()

    def _load_model(self):
        """Load the underlying HandLandmarks model. Any failure is
        non-fatal: self.loaded stays False and process() will simply report
        nothing for the lifetime of this instance - a missing/bad .mud
        model file must never crash the app.
        """
        if not self.model_path:
            logger.error("HandDetector: no model_path configured for hand_landmarks, staying disabled")
            return

        try:
            from maix import nn
            self.detector = nn.HandLandmarks(model=self.model_path)
            self.loaded = True
            logger.info(f"HandDetector: loaded {self.model_path}")
        except Exception as e:
            logger.error(f"HandDetector: failed to load model '{self.model_path}': {e}")
            self.detector = None
            self.loaded = False

    def process(self, img):
        """Run hand landmark detection (+ optional gesture classification)
        on one frame.

        Returns None when the model isn't loaded, detect() raised, or
        nothing was detected. Otherwise returns a unified detection event:
        {"timestamp", "type": "hand_landmarks",
         "model": "HandLandmarks" (+ "+gesture_heuristic" when the gesture
         hook is active), "processing_time_ms", "detections": [...]}, with
         each detection carrying a "gesture" key too when the hook is active.
        """
        if not self.loaded or self.detector is None:
            return None

        start_ms = _now_ms()
        try:
            objs = self.detector.detect(
                img,
                conf_th=self.confidence_threshold,
                iou_th=self.iou_threshold,
                conf_th2=self.conf_th2,
            )
        except Exception as e:
            logger.error(f"HandDetector: detect() failed: {e}")
            return None

        if not objs:
            return None

        detections = []
        for obj in objs:
            detection = _to_hand_detection(obj)
            if self.gesture_loaded:
                detection["gesture"] = classify_gesture(detection["landmarks"])
            detections.append(detection)

        if not detections:
            return None

        model_name = "HandLandmarks+gesture_heuristic" if self.gesture_loaded else "HandLandmarks"

        return {
            "timestamp": _now_ms(),
            "type": "hand_landmarks",
            "model": model_name,
            "processing_time_ms": _now_ms() - start_ms,
            "detections": detections,
        }

    def cleanup(self):
        """No-op, present for symmetry with DataLogger/NetworkUploader."""
        pass
