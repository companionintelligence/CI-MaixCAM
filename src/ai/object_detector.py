"""
Object Detector
Wraps maix.nn.YOLOv8 for general object detection

Backed by maix.nn (MaixPy v4 / MaixCDK), which is only importable on real
hardware. Off-device - desktop dev, unit tests - the maix import is deferred
to inside a try/except in __init__, so this module always imports cleanly;
the model then simply never loads and process() reports nothing, the same
off-device tolerance utils/device.py and network/network_manager.py apply to
their own maix.* usage.

Author: Companion Intelligence
"""

import time as _time

from utils.logger import get_logger

logger = get_logger('ObjectDetector')


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


def _to_detection(obj, labels):
    """Map one maix.nn.YOLOv8 result object to the unified detection dict.

    Pure function - no maix dependency - so it is trivially unit-testable
    with a plain fake object (e.g. a SimpleNamespace with class_id/score/
    x/y/w/h attributes) and a fake labels list, without any hardware or
    a real maix.nn.YOLOv8 instance.
    """
    return {
        "label": labels[obj.class_id],
        "confidence": obj.score,
        "bbox": [obj.x, obj.y, obj.w, obj.h],
    }


class ObjectDetector:
    """Wraps maix.nn.YOLOv8 to produce unified object_detection events"""

    def __init__(self, model_config, **kwargs):
        self.model_config = dict(model_config) if model_config else {}
        self.model_path = self.model_config.get("model_path")
        self.confidence_threshold = self.model_config.get("confidence_threshold", 0.5)
        self.iou_threshold = kwargs.get("iou_threshold", 0.45)

        self.detector = None
        self.labels = []
        self.loaded = False

        self._load_model()

    def _load_model(self):
        """Load the underlying YOLOv8 model. Any failure is non-fatal:
        self.loaded stays False and process() will simply report nothing
        for the lifetime of this instance - a missing/bad .mud file must
        never crash the app.
        """
        if not self.model_path:
            logger.error("ObjectDetector: no model_path configured, staying disabled")
            return

        try:
            from maix import nn
            self.detector = nn.YOLOv8(model=self.model_path, dual_buff=True)
            self.labels = self.detector.labels
            self.loaded = True
            logger.info(f"ObjectDetector: loaded {self.model_path} ({len(self.labels)} classes)")
        except Exception as e:
            logger.error(f"ObjectDetector: failed to load model '{self.model_path}': {e}")
            self.detector = None
            self.loaded = False

    def process(self, img):
        """Run object detection on one frame.

        Returns None when the model isn't loaded, detection raised, or
        nothing was detected. Otherwise returns a unified detection event:
        {"timestamp", "type": "object_detection", "model": "YOLOv8",
         "processing_time_ms", "detections": [...]}.
        """
        if not self.loaded or self.detector is None:
            return None

        start_ms = _now_ms()
        try:
            objs = self.detector.detect(
                img,
                conf_th=self.confidence_threshold,
                iou_th=self.iou_threshold,
            )
        except Exception as e:
            logger.error(f"ObjectDetector: detect() failed: {e}")
            return None

        if not objs:
            return None

        detections = [_to_detection(obj, self.labels) for obj in objs]
        if not detections:
            return None

        return {
            "timestamp": _now_ms(),
            "type": "object_detection",
            "model": "YOLOv8",
            "processing_time_ms": _now_ms() - start_ms,
            "detections": detections,
        }

    def cleanup(self):
        """No-op, present for symmetry with DataLogger/NetworkUploader."""
        pass
