"""
OCR Detector
Wraps maix.nn.PP_OCR for scene-text recognition

Backed by maix.nn (MaixPy v4 / MaixCDK), which is only importable on real
hardware. Off-device - desktop dev, unit tests - the maix import is deferred
to inside a try/except in __init__, so this module always imports cleanly;
the model then simply never loads and process() reports nothing, the same
off-device tolerance utils/device.py, network/network_manager.py and
ai/object_detector.py apply to their own maix.* usage.

maix.nn.OCR_Box (obj.box) is a rotated quadrilateral - four (x, y) corner
points, point 1 at the top-left going clockwise - not an axis-aligned
[x, y, w, h] box like the other detectors' results. points_to_bbox() below is
the pure conversion from that quad (via obj.box.to_list()) to the unified
schema's axis-aligned bbox, and is the one piece of this module worth testing
thoroughly off-device.

Author: Companion Intelligence
"""

import time as _time

from utils.logger import get_logger

logger = get_logger('OcrDetector')

# Detection labels/text longer than this are truncated for the unified
# event's "label" field; the full string is always kept in "text".
_LABEL_MAX_LEN = 40


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


def points_to_bbox(points):
    """Convert a maix.nn.OCR_Box's 4-corner quadrilateral into an
    axis-aligned [x, y, w, h] bounding rect.

    `points` accepts either shape defensively:
      - a flat list/tuple of 8 numbers: [x1, y1, x2, y2, x3, y3, x4, y4]
        (exactly what OCR_Box.to_list() returns)
      - a list of 4 (x, y) pairs: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
        (or tuples)

    The result is the min/max enclosing rectangle over all four points, so a
    rotated (non-axis-aligned) quadrilateral is still covered correctly -
    unlike the raw quad, this is safe to feed anywhere an [x, y, w, h] box is
    expected. Pure function - no maix dependency - so it is trivially
    unit-testable without hardware or a real maix.nn.PP_OCR instance.

    Returns None for empty/falsy input.
    """
    if not points:
        return None

    first = points[0]
    if isinstance(first, (list, tuple)) and len(first) >= 2:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
    else:
        # Flat sequence of numbers: [x1, y1, x2, y2, ...]
        xs = [points[i] for i in range(0, len(points) - 1, 2)]
        ys = [points[i] for i in range(1, len(points), 2)]

    if not xs or not ys:
        return None

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    return [x_min, y_min, x_max - x_min, y_max - y_min]


def _to_ocr_detection(obj):
    """Map one maix.nn.OCR_Object result to the unified detection dict.

    Pure function - no maix dependency - so it is trivially unit-testable
    with a plain fake object (e.g. a SimpleNamespace-like stand-in exposing
    char_str(), score and box.to_list()), without any hardware or a real
    maix.nn.PP_OCR instance.
    """
    text = obj.char_str()
    label = text[:_LABEL_MAX_LEN] if len(text) > _LABEL_MAX_LEN else text

    return {
        "label": label,
        "text": text,
        "confidence": obj.score,
        "bbox": points_to_bbox(obj.box.to_list()),
    }


class OcrDetector:
    """Wraps maix.nn.PP_OCR to produce unified ocr_detection events"""

    def __init__(self, model_config, **kwargs):
        self.model_config = dict(model_config) if model_config else {}
        self.model_path = self.model_config.get("model_path")
        # detect()'s own default is 0.3 (text-region detection confidence);
        # a caller-configured confidence_threshold overrides it.
        self.confidence_threshold = self.model_config.get("confidence_threshold", 0.3)
        # box_thresh is not part of Config.get_ai_model_config()'s shape, so
        # it is only ever set via an explicit kwarg; default matches
        # detect()'s own default (0.6).
        self.box_thresh = kwargs.get("box_thresh", 0.6)

        self.detector = None
        self.loaded = False

        self._load_model()

    def _load_model(self):
        """Load the underlying PP_OCR model. Any failure is non-fatal:
        self.loaded stays False and process() will simply report nothing
        for the lifetime of this instance - a missing/bad .mud model file
        must never crash the app.
        """
        if not self.model_path:
            logger.error("OcrDetector: no model_path configured, staying disabled")
            return

        try:
            from maix import nn
            self.detector = nn.PP_OCR(model=self.model_path)
            self.loaded = True
            logger.info(f"OcrDetector: loaded {self.model_path}")
        except Exception as e:
            logger.error(f"OcrDetector: failed to load model '{self.model_path}': {e}")
            self.detector = None
            self.loaded = False

    def process(self, img):
        """Run OCR text detection/recognition on one frame.

        Returns None when the model isn't loaded, detect() raised, or
        nothing was recognized. Otherwise returns a unified detection event:
        {"timestamp", "type": "ocr_detection", "model": "PP-OCR",
         "processing_time_ms", "detections": [...]}, one entry per
         recognized text region.
        """
        if not self.loaded or self.detector is None:
            return None

        start_ms = _now_ms()
        try:
            objs = self.detector.detect(
                img,
                thresh=self.confidence_threshold,
                box_thresh=self.box_thresh,
            )
        except Exception as e:
            logger.error(f"OcrDetector: detect() failed: {e}")
            return None

        if not objs:
            return None

        detections = [_to_ocr_detection(obj) for obj in objs]
        if not detections:
            return None

        return {
            "timestamp": _now_ms(),
            "type": "ocr_detection",
            "model": "PP-OCR",
            "processing_time_ms": _now_ms() - start_ms,
            "detections": detections,
        }

    def cleanup(self):
        """No-op, present for symmetry with DataLogger/NetworkUploader."""
        pass
