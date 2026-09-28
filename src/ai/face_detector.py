"""
Face Detector
Wraps maix.nn.Retinaface for face bounding boxes + landmarks, with an
optional emotion-classification hook layered on top.

Backed by maix.nn (MaixPy v4 / MaixCDK), which is only importable on real
hardware. Off-device - desktop dev, unit tests - the maix import is deferred
to inside a try/except in __init__, so this module always imports cleanly;
the model then simply never loads and process() reports nothing, the same
off-device tolerance utils/device.py, network/network_manager.py and
ai/object_detector.py apply to their own maix.* usage.

Emotion classification (see module docstring in the task research notes) is
NOT a dedicated maix.nn class - MaixPy's official example feeds a cropped,
grayscale face region into the generic nn.Classifier loaded with a
face_emotion.mud model. That example sources its crop from a
nn.YOLOv8(...yolov8n_face.mud) detector's landmark points via a separate
nn.FaceLandmarks.crop_image() helper, not from nn.Retinaface's own 5 points -
wiring Retinaface's points into that helper is not confirmed to work. So the
emotion hook here only fires when maix.image.Image itself exposes a
crop()/roi() method we can call with a plain bbox; if it does not, the hook
logs once and permanently no-ops (skips the "emotion"/"emotion_confidence"
keys) rather than guessing at an unconfirmed argument shape.

Author: Companion Intelligence
"""

import time as _time

from utils.logger import get_logger

logger = get_logger('FaceDetector')


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


def _to_landmarks(points):
    """Normalize a maix.nn.Retinaface face's points into [[x, y], ...].

    Pure - no maix dependency - so it is trivially unit-testable with a
    plain fake points value. Handles both shapes seen across maix.nn
    wrappers: an already-paired [(x, y), ...] / [[x, y], ...] sequence, or a
    flat [x0, y0, x1, y1, ...] sequence of numbers (the shape MaixPy's own
    img.draw_keypoints() consumes). Returns [] for falsy input.
    """
    if not points:
        return []

    first = points[0]
    if isinstance(first, (list, tuple)) and len(first) >= 2:
        return [[p[0], p[1]] for p in points]

    # Flat sequence of numbers: group pairwise, dropping a dangling odd
    # trailing value rather than raising on it.
    return [[points[i], points[i + 1]] for i in range(0, len(points) - 1, 2)]


def _to_face_detection(obj):
    """Map one maix.nn.Retinaface result object to the unified detection dict.

    Pure function - no maix dependency - so it is trivially unit-testable
    with a plain fake object (e.g. a SimpleNamespace with score/x/y/w/h/
    points attributes), without any hardware or a real maix.nn.Retinaface
    instance. Does not add emotion keys - those are layered on separately by
    FaceDetector.process(), since they need a live classifier and image crop.
    """
    return {
        "label": "face",
        "confidence": obj.score,
        "bbox": [obj.x, obj.y, obj.w, obj.h],
        "landmarks": _to_landmarks(obj.points),
    }


def _top_emotion(res, labels):
    """Pick the top predicted emotion from nn.Classifier.classify()'s output.

    Pure classification heuristic - no maix dependency. `res` is the plain
    list of (class_index, score) tuples classify() returns and `labels` is
    classifier.labels. The official face_emotion.md example reads res[0] as
    "the" prediction (implying res is sorted by descending score), so this
    simply takes the first entry rather than re-deriving max() itself, but
    does so tolerantly of list/tuple shape. Returns None for empty/falsy res.
    """
    if not res:
        return None

    idx, score = res[0][0], res[0][1]
    label = labels[idx] if labels and 0 <= idx < len(labels) else str(idx)
    return label, float(score)


class FaceDetector:
    """Wraps maix.nn.Retinaface (+ optional emotion classifier) to produce
    unified face_detection events.

    Constructor intentionally departs from the generic (model_config,
    **kwargs) shape other detectors use: it takes the "face_detection" and
    "face_emotion" Config.get_ai_model_config() dicts together, since one
    face_detection event carries both. emotion_config is None/absent when
    Face Emotion Detection is toggled off.
    """

    def __init__(self, face_config, emotion_config=None, **kwargs):
        self.face_config = dict(face_config) if face_config else {}
        self.emotion_config = dict(emotion_config) if emotion_config else None

        self.face_model_path = self.face_config.get("model_path")
        self.confidence_threshold = self.face_config.get("confidence_threshold", 0.4)
        self.iou_threshold = kwargs.get("iou_threshold", 0.45)

        self.detector = None
        self.loaded = False

        self.emotion_classifier = None
        self.emotion_labels = []
        self.emotion_loaded = False
        # Set once the emotion hook has logged that it can't confirm a safe
        # crop API on this build, so it stops retrying every frame.
        self._emotion_hook_disabled = False

        self._load_face_model()
        if self.emotion_config:
            self._load_emotion_model()

    def _load_face_model(self):
        """Load the underlying Retinaface model. Any failure is non-fatal:
        self.loaded stays False and process() will simply report nothing
        for the lifetime of this instance - a missing/bad .mud model file
        must never crash the app.
        """
        if not self.face_model_path:
            logger.error("FaceDetector: no model_path configured for face_detection, staying disabled")
            return

        try:
            from maix import nn
            self.detector = nn.Retinaface(model=self.face_model_path, dual_buff=True)
            self.loaded = True
            logger.info(f"FaceDetector: loaded {self.face_model_path}")
        except Exception as e:
            logger.error(f"FaceDetector: failed to load model '{self.face_model_path}': {e}")
            self.detector = None
            self.loaded = False

    def _load_emotion_model(self):
        """Load the optional emotion classifier. Non-fatal on failure: the
        face detector keeps working, it simply never adds emotion keys.
        """
        model_path = self.emotion_config.get("model_path")
        if not model_path:
            logger.error("FaceDetector: no model_path configured for face_emotion, emotion hook staying disabled")
            return

        try:
            from maix import nn
            self.emotion_classifier = nn.Classifier(model=model_path, dual_buff=False)
            self.emotion_labels = list(getattr(self.emotion_classifier, "labels", None) or [])
            self.emotion_loaded = True
            logger.info(f"FaceDetector: loaded emotion classifier {model_path} ({len(self.emotion_labels)} classes)")
        except Exception as e:
            logger.error(f"FaceDetector: failed to load emotion model '{model_path}': {e}")
            self.emotion_classifier = None
            self.emotion_loaded = False

    def _add_emotion(self, detection, obj, img):
        """Best-effort: crop the face out of `img` and classify its emotion,
        adding "emotion"/"emotion_confidence" to `detection` in place.

        The crop step is the part MaixPy's official example does not show a
        confirmed path for from Retinaface's own points, so this only
        proceeds when maix.image.Image itself exposes a crop()/roi() method
        we can call with a plain bbox. The first time it doesn't, this logs
        once and disables the hook for the rest of this instance's life
        instead of guessing at an unconfirmed argument shape. A later
        per-face crop/classify exception (e.g. an edge-of-frame bbox) only
        skips that one face's emotion keys, it does not disable the hook.
        """
        if self._emotion_hook_disabled:
            return

        crop_fn = getattr(img, "crop", None) or getattr(img, "roi", None)
        if crop_fn is None:
            logger.info(
                "FaceDetector: maix.image.Image exposes no crop()/roi() method; "
                "emotion classifier input pipeline is unconfirmed for this build, "
                "disabling the emotion hook (face_detection keeps working without it)"
            )
            self._emotion_hook_disabled = True
            return

        try:
            face_img = crop_fn(obj.x, obj.y, obj.w, obj.h)

            from maix import image as maix_image
            gray = face_img.to_format(maix_image.Format.FMT_GRAYSCALE)

            res = self.emotion_classifier.classify(gray, softmax=True)
            top = _top_emotion(res, self.emotion_labels)
            if top is None:
                return

            label, confidence = top
            detection["emotion"] = label
            detection["emotion_confidence"] = confidence
        except Exception as e:
            logger.error(f"FaceDetector: emotion classification failed for a face: {e}")

    def process(self, img):
        """Run face detection (+ optional emotion classification) on one frame.

        Returns None when the model isn't loaded, detect() raised, or
        nothing was detected. Otherwise returns a unified detection event:
        {"timestamp", "type": "face_detection",
         "model": "Retinaface" (+ "+emotion" when the emotion hook is live),
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
            logger.error(f"FaceDetector: detect() failed: {e}")
            return None

        if not objs:
            return None

        emotion_active = self.emotion_loaded and not self._emotion_hook_disabled

        detections = []
        for obj in objs:
            detection = _to_face_detection(obj)
            if emotion_active:
                self._add_emotion(detection, obj, img)
            detections.append(detection)

        if not detections:
            return None

        model_name = "Retinaface+emotion" if (self.emotion_loaded and not self._emotion_hook_disabled) else "Retinaface"

        return {
            "timestamp": _now_ms(),
            "type": "face_detection",
            "model": model_name,
            "processing_time_ms": _now_ms() - start_ms,
            "detections": detections,
        }

    def cleanup(self):
        """No-op, present for symmetry with DataLogger/NetworkUploader."""
        pass
