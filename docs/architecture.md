# Architecture

## Module map

```
src/
  main.py                 CompanionCaptureApp - the on-device entry point:
                           camera/display/touch loop, AIModelManager,
                           DataLogger, NetworkUploader lifecycle
  setup_screen.py          Model-selection screen shown before main.py's app
  ai/                      One class per AI capability, each independently
                           importable off-device (see "The ai/ package" below)
    object_detector.py     ObjectDetector      - maix.nn.YOLOv8
    face_detector.py       FaceDetector        - maix.nn.Retinaface (+emotion)
    object_tracker.py      ObjectTracker       - pure Python, no maix at all
    ocr_detector.py        OcrDetector         - maix.nn.PP_OCR
    hand_detector.py       HandDetector        - hand landmarks (+gesture)
    pose_detector.py       PoseDetector        - maix.nn.YOLOv8 (pose) + a
                                                  pure posture-classification
                                                  heuristic
    audio_processor.py     AudioProcessor      - maix.audio + maix.nn.Speech
  data_logger/logger.py    DataLogger - session JSON files + the storage index
  network/
    uploader.py             NetworkUploader - CI-Server /v1 ingest client
    network_manager.py       NetworkManager - Wi-Fi connectivity gate
  utils/
    config.py                Config - the one companion_config.json schema
    models.py                 The model catalog (ALL_MODELS) and config-key
                               <-> display-name mapping
    device.py                  Device identity (maix.sys) + CPU temperature
    paths.py, time_utils.py, logger.py   Small cross-cutting helpers
  ui/                       A separate, more polished UI (MainUI, ModelDrawer)
                             not currently wired into main.py's own simpler
                             _draw_ui() - see "Two UI implementations" below
```

## Data flow

```
camera.read() -> AIModelManager.process_frame(img)
                     |
                     v
         one real detector .process(img) call per
         enabled model, each returning either None
         or a unified event dict (see below)
                     |
                     v
              DataLogger.log_events(events)
                     |
                     v
        one JSON file per session under storage.base_path
                     |
     (on session end) v
        NetworkUploader.queue_file_for_upload(path)
                     |
                     v
   background thread: read the file's events, POST each as
   a CI-Server CaptureEvent to /v1/events, then /v1/ingest/finish
```

## The unified detection event schema

Every `ai/*.py` class's `process(img)` method returns either `None`
(nothing to report this call) or:

```json
{
  "timestamp": 123456789,
  "type": "object_detection",
  "model": "YOLOv8",
  "processing_time_ms": 42,
  "detections": [
    {"label": "person", "confidence": 0.91, "bbox": [x, y, w, h], "...": "type-specific extras"}
  ]
}
```

`DataLogger._extract_confidence_scores()` and `ui/main_ui.py`'s overlay
drawing both read `detections` generically — adding a new detector type
needs no changes to either. Type-specific extras seen today: `landmarks`
(face/hand), `emotion`/`emotion_confidence` (face), `gesture` (hand),
`posture` (pose), `text` (OCR), `track_id`/`count`/`entered`/`exited`
(object tracking).

## The `ai/` package: designed to be testable without hardware

`maix` (MaixPy v4 / MaixCDK) is only importable on real MaixCAM hardware.
Every module under `src/ai/`, `src/network/`, and `src/utils/device.py`
follows the same rule so the whole app stays importable - and its
non-hardware logic stays testable - on a plain desktop Python:

- Every `from maix import ...` / `import maix` is inside a method body
  (usually the model-loading step), wrapped in `try/except`. A missing SDK
  or missing model file leaves `self.loaded = False`; `process()` then
  just returns `None` forever, never raising.
- Any pure computation (bbox math, IoU tracking, posture/gesture
  classification heuristics, PCM level decoding) is a plain
  module-level function with zero `maix` dependency, so `tests/test_*.py`
  can exercise it directly with fake data.

`src/ai/object_tracker.py` takes this furthest: it has **no** `maix`
import anywhere, because tracking is pure algorithm (IoU matching) over
whatever detections `ObjectDetector` hands it.

## AIModelManager: one instance per model, not per toggle

Two setup-screen toggles can share one underlying pipeline:

- **Face Recognition** and **Face Emotion Detection** share one
  `FaceDetector` (emotion is a second stage over the same face detection).
- **Hand Landmarks Detection** and **Hand Gesture Classification** share
  one `HandDetector`, same reasoning.
- **Audio Recording** and **Real-time Voice Recognition** share one
  `AudioProcessor`, which itself only ever does one or the other per call.
- **Object Tracking and Counting** reuses **Object Classification**'s own
  `ObjectDetector` instance and that frame's own detections, rather than
  running YOLOv8 a second time.

`AIModelManager.process_frame()` memoizes each detector's result per frame
(keyed by instance identity) so a shared instance is still only invoked
once per frame no matter how many scheduled slots or the tracker want its
output. Each slot also only actually runs every `processing_interval`
frames (`ai_models.<key>.processing_interval` in the config), so a light
model can run every frame while a heavy one runs every N frames.

## Two UI implementations

`src/ui/main_ui.py`'s `MainUI` (with `ModelDrawer`, a proper preview/sidebar
layout, and generic detection-overlay drawing) is **not** currently used by
`main.py`, which draws its own much simpler text-only overlay directly.
`MainUI` predates this pass and was left as-is except for generalizing its
overlay drawing to the unified schema above - wiring it into `main.py`'s
main loop is a separate, larger change this pass did not make.
