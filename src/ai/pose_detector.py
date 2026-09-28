"""
Pose Detector
Wraps maix.nn.YOLOv8 (pointed at a *_pose.mud model) for body keypoint
detection, plus a pure geometric posture classifier over its keypoints.

Backed by maix.nn (MaixPy v4 / MaixCDK), which is only importable on real
hardware. Off-device - desktop dev, unit tests - the maix import is deferred
to inside a try/except in __init__, so this module always imports cleanly;
the model then simply never loads and process() reports nothing, the same
off-device tolerance utils/device.py, network/network_manager.py and
ai/object_detector.py apply to their own maix.* usage.

API notes (confirmed against wiki.sipeed.com/maixpy, 2026-09-28):
- There is no separate "YOLOv8Pose" class. The same maix.nn.YOLOv8 class used
  for plain object detection also serves the pose variant when constructed
  with a "*_pose.mud" model file - see
  https://wiki.sipeed.com/maixpy/doc/en/vision/body_key_points.html, which
  lists `nn.YOLOv8(model="/root/models/yolov8n_pose.mud", dual_buff=True)` as
  the direct alternative to its lead `nn.YOLO11(...)` example.
- `detector.detect(img, conf_th=..., iou_th=..., keypoint_th=...)` - the
  `keypoint_th` kwarg is documented as "only for yolov8-pose model" (see
  https://wiki.sipeed.com/maixpy/api/maix/nn.html). Returned Object items
  carry `x, y, w, h, class_id, score, points`.
- `points` is a flat list alternating x, y per keypoint (length 34 for the
  17-keypoint COCO layout below), not a list of 17 (x, y) pairs - a value of
  -1 marks an occluded/invalid point. This matches
  advanced_life_logger.py's own `detector.detect(img, conf_th=0.5,
  iou_th=0.45, keypoint_th=0.5)` / `detector.draw_pose(img, pose.points, ...)`
  usage; that file's `"keypoints": len(pose.points)` line would report 34,
  not 17, for this reason.

Author: Companion Intelligence
"""

import time as _time

from utils.logger import get_logger

logger = get_logger('PoseDetector')

# COCO-17 keypoint order, confirmed verbatim from
# https://wiki.sipeed.com/maixpy/doc/en/vision/body_key_points.html :
# 0 nose, 1 left eye, 2 right eye, 3 left ear, 4 right ear,
# 5 left shoulder, 6 right shoulder, 7 left elbow, 8 right elbow,
# 9 left wrist, 10 right wrist, 11 left hip, 12 right hip,
# 13 left knee, 14 right knee, 15 left ankle, 16 right ankle.
NOSE = 0
LEFT_EYE, RIGHT_EYE = 1, 2
LEFT_EAR, RIGHT_EAR = 3, 4
LEFT_SHOULDER, RIGHT_SHOULDER = 5, 6
LEFT_ELBOW, RIGHT_ELBOW = 7, 8
LEFT_WRIST, RIGHT_WRIST = 9, 10
LEFT_HIP, RIGHT_HIP = 11, 12
LEFT_KNEE, RIGHT_KNEE = 13, 14
LEFT_ANKLE, RIGHT_ANKLE = 15, 16


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


def _to_keypoints(points):
    """Normalize a maix.nn.YOLOv8 pose result's points into [[x, y], ...].

    Pure - no maix dependency - so it is trivially unit-testable with a
    plain fake points value. Handles both shapes seen across maix.nn
    wrappers: an already-paired [(x, y), ...] / [[x, y], ...] sequence, or a
    flat [x0, y0, x1, y1, ...] sequence of numbers (the documented shape of
    YOLOv8-pose's `Object.points`). Returns [] for falsy input. A dangling
    odd trailing value in a flat sequence is dropped rather than raising.
    """
    if not points:
        return []

    first = points[0]
    if isinstance(first, (list, tuple)) and len(first) >= 2:
        return [[p[0], p[1]] for p in points]

    return [[points[i], points[i + 1]] for i in range(0, len(points) - 1, 2)]


def _valid_point(keypoints, index):
    """The (x, y) at `index`, or None if absent/out of range/invalid.

    A point is treated as absent - rather than raising or being taken at
    face value - when the list is too short, the entry isn't a coordinate
    pair, or either coordinate is <= 0. MaixPy marks an occluded/invalid
    keypoint with a negative value, and (0, 0) is the common "never
    detected" placeholder, so both are folded into "absent" here alongside
    a genuinely missing entry.
    """
    if index >= len(keypoints):
        return None

    point = keypoints[index]
    if not isinstance(point, (list, tuple)) or len(point) < 2:
        return None

    x, y = point[0], point[1]
    if x is None or y is None:
        return None
    try:
        if x <= 0 or y <= 0:
            return None
        return (float(x), float(y))
    except TypeError:
        # Non-numeric coordinate (e.g. malformed/garbage input) - treat the
        # same as a missing point rather than raising.
        return None


def _average_point(*points):
    """Midpoint of whichever of `points` are not None, or None if all are."""
    valid = [p for p in points if p is not None]
    if not valid:
        return None
    return (
        sum(p[0] for p in valid) / len(valid),
        sum(p[1] for p in valid) / len(valid),
    )


def classify_posture(keypoints):
    """Classify a body posture from COCO-17 keypoints using simple geometry.

    `keypoints` is a list of (x, y) pairs (or [x, y] lists) in the COCO-17
    order documented at the top of this module - the same shape
    `_to_keypoints()` produces. A keypoint that is missing from the list,
    not a coordinate pair, or has a non-positive coordinate (MaixPy's
    "invalid"/"never detected" marker) is treated as absent rather than
    used as-is or raised on. Left/right pairs (shoulders, hips, knees,
    ankles) are averaged when only one side is valid.

    Returns one of "standing" / "sitting" / "lying" / "unknown". "unknown"
    covers both "not enough valid keypoints to reason about" and any
    otherwise ambiguous geometry.

    Heuristic:
    - Lying: the body's horizontal span (shoulder/hip midpoint to
      ankle/knee/hip midpoint) exceeds its vertical span - i.e. the body
      reads as wide and short rather than tall, as when someone is
      stretched out roughly level with the camera.
    - Otherwise, with hip, knee and ankle all present: compare the
      hip->knee vertical drop against the knee->ankle vertical drop.
      Standing keeps hip->knee->ankle roughly in a straight vertical line,
      so the two drops are comparable. Sitting collapses the hip->knee
      drop relative to knee->ankle (thighs go roughly horizontal while
      shins stay roughly vertical), so a hip->knee drop much smaller than
      knee->ankle indicates sitting.
    - Without hip+knee+ankle all present, standing vs. sitting cannot be
      told apart, so the result is "unknown".
    """
    shoulder = _average_point(
        _valid_point(keypoints, LEFT_SHOULDER),
        _valid_point(keypoints, RIGHT_SHOULDER),
    )
    hip = _average_point(
        _valid_point(keypoints, LEFT_HIP),
        _valid_point(keypoints, RIGHT_HIP),
    )
    knee = _average_point(
        _valid_point(keypoints, LEFT_KNEE),
        _valid_point(keypoints, RIGHT_KNEE),
    )
    ankle = _average_point(
        _valid_point(keypoints, LEFT_ANKLE),
        _valid_point(keypoints, RIGHT_ANKLE),
    )

    top = shoulder if shoulder is not None else hip
    bottom = ankle if ankle is not None else (knee if knee is not None else hip)

    if top is None or bottom is None or top is bottom:
        return "unknown"

    vertical_span = abs(bottom[1] - top[1])
    horizontal_span = abs(bottom[0] - top[0])

    if horizontal_span > vertical_span:
        return "lying"

    if hip is None or knee is None or ankle is None:
        return "unknown"

    hip_to_knee = abs(knee[1] - hip[1])
    knee_to_ankle = abs(ankle[1] - knee[1])

    if hip_to_knee < knee_to_ankle * 0.5:
        return "sitting"

    return "standing"


def _to_pose_detection(obj):
    """Map one maix.nn.YOLOv8 (pose) result object to the unified detection
    dict.

    Pure function - no maix dependency - so it is trivially unit-testable
    with a plain fake object (e.g. a SimpleNamespace with score/x/y/w/h/
    points attributes), without any hardware or a real maix.nn.YOLOv8
    instance.
    """
    keypoints = _to_keypoints(obj.points)
    return {
        "label": "person",
        "confidence": obj.score,
        "bbox": [obj.x, obj.y, obj.w, obj.h],
        "keypoints": keypoints,
        "posture": classify_posture(keypoints),
    }


class PoseDetector:
    """Wraps maix.nn.YOLOv8 (loaded with a *_pose.mud model) to produce
    unified pose_detection events, each detection carrying a classified
    posture alongside raw keypoints.
    """

    def __init__(self, model_config, **kwargs):
        self.model_config = dict(model_config) if model_config else {}
        self.model_path = self.model_config.get("model_path")
        self.confidence_threshold = self.model_config.get("confidence_threshold", 0.5)
        self.iou_threshold = kwargs.get("iou_threshold", 0.45)
        self.keypoint_threshold = kwargs.get("keypoint_threshold", 0.5)

        self.detector = None
        self.loaded = False

        self._load_model()

    def _load_model(self):
        """Load the underlying YOLOv8-pose model. Any failure is non-fatal:
        self.loaded stays False and process() will simply report nothing
        for the lifetime of this instance - a missing/bad .mud file must
        never crash the app.
        """
        if not self.model_path:
            logger.error("PoseDetector: no model_path configured, staying disabled")
            return

        try:
            from maix import nn
            self.detector = nn.YOLOv8(model=self.model_path, dual_buff=True)
            self.loaded = True
            logger.info(f"PoseDetector: loaded {self.model_path}")
        except Exception as e:
            logger.error(f"PoseDetector: failed to load model '{self.model_path}': {e}")
            self.detector = None
            self.loaded = False

    def process(self, img):
        """Run pose detection on one frame.

        Returns None when the model isn't loaded, detect() raised, or
        nothing was detected. Otherwise returns a unified detection event:
        {"timestamp", "type": "pose_detection", "model": "YOLOv8-pose",
         "processing_time_ms", "detections": [...]}, each detection carrying
         label/confidence/bbox/keypoints/posture.
        """
        if not self.loaded or self.detector is None:
            return None

        start_ms = _now_ms()
        try:
            objs = self.detector.detect(
                img,
                conf_th=self.confidence_threshold,
                iou_th=self.iou_threshold,
                keypoint_th=self.keypoint_threshold,
            )
        except Exception as e:
            logger.error(f"PoseDetector: detect() failed: {e}")
            return None

        if not objs:
            return None

        detections = [_to_pose_detection(obj) for obj in objs]
        if not detections:
            return None

        return {
            "timestamp": _now_ms(),
            "type": "pose_detection",
            "model": "YOLOv8-pose",
            "processing_time_ms": _now_ms() - start_ms,
            "detections": detections,
        }

    def cleanup(self):
        """No-op, present for symmetry with DataLogger/NetworkUploader."""
        pass
