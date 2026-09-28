# Companion Capture App Development Plan

## Sipeed MaixCAM Device Using MaixPy

### Project Overview

Develop a comprehensive life-logging application for the Sipeed MaixCAM device using the MaixPy framework. The application will detect and record objects, people, places, things, and events through continuous AI-powered analysis.

### Core Objectives

- **Target Recording**: People, places, things, and events
- **Output Format**: All results in JSON format only
- **Storage**: Local JSON storage with REST API sync via WiFi
- **Use Case**: Life logging for house and backyard monitoring

### Reference Documentation

- [MaixPy Basic App Development](https://wiki.sipeed.com/maixpy/doc/en/basic/app.html)
- [MaixPy Documentation](https://wiki.sipeed.com/maixpy/doc/en/index.html)

### AI Features to Implement

#### Computer Vision (AI Video)

- Object Classification
- Face Recognition
- Face Emotion Detection
- Object Tracking and Counting
- OCR (Optical Character Recognition)
- Hand Landmarks Detection
- Human Pose Classification
- Hand Gesture Classification

#### Audio Processing (AI Audio)

- Audio Recording
- Audio Playback
- Real-time Voice Recognition

#### Media Capabilities

- Video Recording
- Video Playback

### Technical Requirements

- **Data Format**: JSON with timestamps, sensor details, and confidence scores
- **Storage Strategy**: Local storage with REST API synchronization
- **User Interface**: Preview display with start/stop controls and model toggle checkboxes
- **Connectivity**: WiFi-enabled for remote data upload

### Development Framework

All features will be implemented using the MaixPy framework and its comprehensive AI toolkit as documented in the official documentation.
 

# PROJECT PLAN STEPS:

## Detailed Implementation Roadmap

| Step | Task | Description | Status |
|------|------|-------------|--------|
| 1 | Initial Setup | Setup Sipeed MaxiCam hardware and install MaixPy firmware. Verify device functionality. | ✅ |
| 2 | Development Environment | Install and configure MaixPy IDE. Ensure serial and Wi-Fi connectivity. | ✅ |
| 3 | UI Design | Design simple user interface with preview, start, stop, log, and detection model toggle checkboxes. | ✅ |
| 4 | Camera Integration | Develop and test camera preview and video recording functionalities. | ✅ |
| 5 | Audio Integration | Integrate audio recording and playback functionalities; verify real-time voice recognition. | ✅ |
| 6 | Object Classification | Implement object classification model; output JSON with timestamp, confidence scores, and sensor details. | ✅ |
| 7 | Face Recognition & Emotion | Implement facial recognition and emotion detection models; ensure accurate JSON outputs. | ✅ |
| 8 | Object Tracking & Counting | Implement object tracking and counting functionality; validate JSON accuracy. | ✅ |
| 9 | OCR Implementation | Develop OCR for text recognition; verify accuracy and JSON formatting. | ✅ |
| 10 | Hand & Gesture Recognition | Integrate hand landmarks and hand gesture classifier; test thoroughly for reliable JSON outputs. | ✅ |
| 11 | Human Pose Classifier | Integrate human pose detection and classification; ensure robust JSON logging. | ✅ |
| 12 | JSON Output Format | Standardize JSON format to include timestamps, sensor details, model type, detection confidence, and detected entity details. | ✅ |
| 13 | Local Storage Management | Set up reliable local storage system to log JSON results continuously with clear storage management policies. | ✅ |
| 14 | REST API Integration | Develop REST client to post JSON logs securely and reliably to external server via Wi-Fi. | ✅ |
| 15 | Detection Model Toggles | Implement toggle functionality in UI to enable/disable each detection model dynamically. | ✅ |
| 16 | Testing & Debugging | Conduct unit tests and integrated testing of all features and components; fix bugs and optimize performance. | ☐ |
| 17 | Performance Optimization | Optimize AI model performance, Wi-Fi data transfer efficiency, and battery usage for continuous logging. | ☐ |
| 18 | Documentation & Deployment | Write clear documentation for usage, troubleshooting, and further development; prepare for final deployment. | ✅ |
| 19 | Final Deployment & Monitoring | Deploy final Companion Capture App to the MaxiCam, monitor initial operation, and make necessary adjustments. | ☐ |

> **Note (2026-09-28):** ✅ here means implemented in code and, where the
> logic doesn't need real hardware, covered by `python3 -m unittest
> discover tests`. None of it has run on a real MaixCAM, real `.mud`
> models, a real microphone, or a real CI-Server - sub-steps that
> specifically call for that kind of validation stay unchecked within each
> section below even where the top-level row is ✅, the same way Step 4
> already did.

---
 
### Step 3: UI Design
**Sub-steps:**
- [x] 3.2 Implement custom `Checkbox` class using MaixUI primitives
- [x] 3.3 Implement custom `Button` class with touch event handling
- [x] 3.4 Design camera preview area (top 80% of screen)
- [x] 3.5 Create right sidebar for AI model toggle checkboxes
- [x] 3.6 Design bottom action bar with start/stop button and status indicators
- [x] 3.7 Implement touch event routing system
- [x] 3.8 Add visual feedback for button presses and checkbox states
- [x] 3.9 Create application state machine (INITIALIZING, IDLE, CAPTURING, ERROR)
- [x] 3.10 Test UI responsiveness and layout on actual device

### Step 4: Camera Integration
**Sub-steps:**
- [ ] 4.1 Initialize `maix.camera.Camera` object with optimal resolution
- [ ] 4.2 Implement live camera preview in main UI loop
- [ ] 4.3 Add frame rate monitoring and display
- [ ] 4.4 Test different camera formats (RGB888, YUV420, etc.)
- [ ] 4.5 Implement camera settings adjustment (brightness, contrast)
- [ ] 4.6 Add image capture functionality for single frames
- [ ] 4.7 Implement video recording using `maix.video.Encoder`
- [ ] 4.8 Test video file output and playback compatibility
- [ ] 4.9 Handle camera initialization errors gracefully
- [ ] 4.10 Optimize camera performance for continuous operation

### Step 5: Audio Integration

`src/ai/audio_processor.py`'s `AudioProcessor`. Real-time Voice Recognition
needs a trained keyword-spotting model + keyword table this repo doesn't
ship (see `docs/configuration.md`); until supplied it's a documented no-op
rather than a guessed-at API.

**Sub-steps:**
- [x] 5.1 Initialize `maix.audio` recording capability
- [ ] 5.2 Test basic audio recording and playback (needs real hardware/mic)
- [x] 5.3 Implement continuous audio buffer management
- [x] 5.4 Initialize `maix.nn.Speech` for voice recognition
- [ ] 5.5 Configure keyword spotting models (no model/keyword table shipped yet)
- [x] 5.6 Implement audio callback system for real-time processing
- [ ] 5.7 Create separate thread for audio processing (`AudioProcessor.process()` runs on the main capture loop's thread today, like every other detector - not split out)
- [ ] 5.8 Test audio quality and recognition accuracy (needs real hardware/mic)
- [x] 5.9 Implement audio event queuing system (`DataLogger`'s existing session log)
- [ ] 5.10 Add audio level indicators to UI (`main.py`'s own overlay doesn't show this yet; the level is in every emitted event)

### Step 6: Object Classification

`src/ai/object_detector.py`'s `ObjectDetector`; scheduled by `main.py`'s
`AIModelManager` (named that rather than `AIEngine` - see `docs/architecture.md`).

**Sub-steps:**
- [x] 6.1 Load YOLOv8 object detection model (`/root/models/yolov8n.mud`)
- [x] 6.2 Create `AIEngine` class with model management (`AIModelManager`)
- [x] 6.3 Implement `process_frame()` method for object detection
- [x] 6.4 Parse detection results (bounding boxes, labels, confidence)
- [x] 6.5 Create JSON event format for object detections
- [ ] 6.6 Test detection accuracy with various objects (needs real hardware/camera)
- [x] 6.7 Implement confidence threshold filtering
- [x] 6.8 Add visual bounding box overlay on camera preview (`ui/main_ui.py`)
- [ ] 6.9 Test performance impact on frame rate (needs real hardware)
- [x] 6.10 Validate JSON output format and structure (`tests/test_object_detector.py`)

### Step 7: Face Recognition & Emotion

`src/ai/face_detector.py`'s `FaceDetector` wraps Retinaface
(`/root/models/retinaface.mud`, not the `yolov8n_face.mud` this sub-step
originally named - Retinaface is what `advanced_life_logger.py`'s
prototype and this repo's own `ai_models.face_detection` config already
used) plus an emotion classifier as a second stage over each detected face.

**Sub-steps:**
- [x] 7.1 Load face detection model (Retinaface, not YOLOv8-face - see above)
- [x] 7.2 Load emotion classification model (`/root/models/face_emotion.mud`)
- [x] 7.3 Implement face detection pipeline
- [x] 7.4 Create face cropping and preprocessing for emotion analysis
- [x] 7.5 Implement two-stage pipeline (detect faces → classify emotions)
- [x] 7.6 Create JSON schema for face and emotion events
- [ ] 7.7 Test accuracy with multiple faces and expressions (needs real hardware)
- [ ] 7.8 Add face recognition database functionality (this is face *detection*, not identifying *who* - a real, unbuilt feature, not just untested)
- [ ] 7.9 Implement face tracking between frames (a per-face identity tracker, distinct from Step 8's general object tracker - not built)
- [ ] 7.10 Optimize performance for real-time emotion detection (needs real hardware to profile)

### Step 8: Object Tracking & Counting

`src/ai/object_tracker.py`'s `ObjectTracker` - pure-Python greedy IoU
matching over `ObjectDetector`'s own per-frame output, no `maix` dependency
or model file at all, so this one is fully unit-tested
(`tests/test_object_tracker.py`) rather than only off-device-fallback-tested.

**Sub-steps:**
- [x] 8.1 Implement object tracking using detection results
- [x] 8.2 Create unique ID assignment for tracked objects
- [x] 8.3 Implement object persistence across frames (`max_track_age_frames`)
- [x] 8.4 Add object counting functionality (`count` in every tracking event)
- [ ] 8.5 Create entry/exit zone detection (tracks entering/exiting *tracking itself* are reported as `entered`/`exited`; a configurable spatial zone boundary is not implemented)
- [ ] 8.6 Implement tracking history and trajectory logging (only the current frame's state is kept, no path history)
- [x] 8.7 Add JSON events for object tracking milestones
- [x] 8.8 Test tracking accuracy with moving objects (synthetic multi-frame unit tests)
- [ ] 8.9 Handle object occlusion and re-identification (simple greedy IoU matching does not re-identify a track after a full occlusion - it gets a new id)
- [ ] 8.10 Optimize tracking performance and memory usage (needs real hardware to profile)

### Step 9: OCR Implementation

`src/ai/ocr_detector.py`'s `OcrDetector`, wrapping `maix.nn.PP_OCR`.

**Sub-steps:**
- [x] 9.1 Load PP-OCR model (`/root/models/pp_ocr.mud`)
- [x] 9.2 Implement text detection pipeline
- [x] 9.3 Add text recognition functionality
- [x] 9.4 Create text bounding box visualization (`ui/main_ui.py`'s generic overlay; `points_to_bbox()` turns PP-OCR's rotated quadrilateral into an axis-aligned box)
- [x] 9.5 Implement text confidence filtering (`confidence_threshold`)
- [x] 9.6 Create JSON schema for OCR events
- [ ] 9.7 Test OCR accuracy with various text types and sizes (needs real hardware/camera)
- [x] 9.8 Handle multiple text regions in single frame (one detection per recognized region, already covered by `tests/test_ocr_detector.py`)
- [ ] 9.9 Add text orientation detection and correction (relies on PP-OCR's own handling; no extra correction added here)
- [x] 9.10 Optimize OCR processing frequency for performance (`processing_interval`, its own dedicated - and by far the longest - default cadence)

### Step 10: Hand & Gesture Recognition

`src/ai/hand_detector.py`'s `HandDetector` wraps `maix.nn.HandLandmarks`;
no dedicated MaixPy gesture-classifier model could be confirmed to exist,
so gesture classification is a geometric heuristic (extended-finger
counting) over the landmark points, documented and unit-tested as such
rather than guessed at as a fake model API.

**Sub-steps:**
- [x] 10.1 Load hand landmarks model (`/root/models/hand_landmarks.mud`)
- [x] 10.2 Implement hand detection and keypoint extraction
- [x] 10.3 Create hand gesture classification pipeline (geometric heuristic, not a dedicated model - see above)
- [ ] 10.4 Add visual hand keypoint overlay (bbox+label overlay exists in `ui/main_ui.py`; per-point keypoint skeleton drawing does not)
- [x] 10.5 Implement gesture recognition from keypoint patterns
- [x] 10.6 Create JSON schema for hand and gesture events
- [ ] 10.7 Test accuracy with various hand positions and gestures (needs real hardware/camera; heuristic is unit-tested against synthetic coordinates only)
- [x] 10.8 Handle multiple hands in single frame
- [ ] 10.9 Add gesture history and pattern recognition (current classification is per-frame/instantaneous, no temporal pattern tracking)
- [ ] 10.10 Optimize hand processing for real-time performance (needs real hardware to profile)

### Step 11: Human Pose Classifier

`src/ai/pose_detector.py`'s `PoseDetector` wraps the pose variant of
`maix.nn.YOLOv8`; posture classification (standing/sitting/lying) is a
geometric heuristic over the COCO 17-keypoint output, unit-tested against
synthetic keypoint sets for all three postures plus degraded/missing input.

**Sub-steps:**
- [x] 11.1 Load human pose model (`/root/models/yolov8n_pose.mud`)
- [x] 11.2 Implement 17-keypoint human pose detection
- [ ] 11.3 Create pose visualization with skeleton overlay (bbox+label overlay exists; per-keypoint skeleton line drawing does not)
- [x] 11.4 Implement pose classification (standing, sitting, lying, etc.)
- [ ] 11.5 Add pose tracking across frames (per-person identity across frames, distinct from Step 8's object tracker - not built)
- [x] 11.6 Create JSON schema for pose events
- [ ] 11.7 Test accuracy with various poses and body positions (needs real hardware/camera; heuristic is unit-tested against synthetic keypoints only)
- [x] 11.8 Handle multiple people in single frame
- [ ] 11.9 Implement pose-based activity recognition (current classification is a static per-frame posture label, not activity recognition over a pose sequence)
- [ ] 11.10 Optimize pose processing performance (needs real hardware to profile)

### Step 12: JSON Output Format

The unified `{timestamp, type, model, processing_time_ms, detections: [...]}`
event shape every `src/ai/*.py` detector emits - see `docs/architecture.md`.

**Sub-steps:**
- [x] 12.1 Define comprehensive JSON schema with versioning (documented in `docs/architecture.md`; no explicit numeric schema-version field is stamped into each event)
- [x] 12.2 Create event envelope with metadata (timestamp, event_id, etc.) (`DataLogger._process_event`'s `event_id`/`timestamp`/`session_id`/`metadata`)
- [x] 12.3 Implement type-specific payload structures (the `detections[]` extras: `landmarks`, `emotion`, `gesture`, `posture`, `text`, `track_id`, ...)
- [x] 12.4 Add UUID generation for unique event IDs (pre-existing in `DataLogger`)
- [x] 12.5 Implement ISO 8601 timestamp formatting (now UTC-aware - see `CHANGELOG.md`)
- [ ] 12.6 Create JSON validation functions (no explicit schema-validator function exists; correctness is enforced by convention + the `tests/test_*.py` suite, not a runtime validator)
- [x] 12.7 Add confidence score normalization (`DataLogger._extract_confidence_scores` now reads every event type generically, not just three of them)
- [x] 12.8 Implement sensor metadata inclusion (device info, model versions) (`DataLogger._get_device_info()` now reports real `maix.sys` device id/name/firmware version instead of hardcoded `"unknown"`)
- [ ] 12.9 Test JSON serialization performance (needs real hardware to profile)
- [x] 12.10 Create JSON schema documentation (`docs/architecture.md`)

### Step 13: Local Storage Management
**Sub-steps:**
- [x] 13.1 Create `DataLogger` class for file management
- [x] 13.2 Implement SD card storage structure (`/sd/logs/`)
- [x] 13.3 Add log file rotation based on capture sessions (one file per session; size-based rotation *within* a session is not implemented - see the code comment at `_check_storage_limits`)
- [x] 13.4 Implement atomic file writing for data integrity (temp file + `os.rename`)
- [x] 13.5 Create storage space monitoring and cleanup (keeps the 10 most recent session files)
- [x] 13.6 Add file naming convention with timestamps
- [x] 13.7 Implement log file compression for storage efficiency (gzip on archive, after a successful CI-Server upload - see `NetworkUploader._move_uploaded_file`)
- [x] 13.8 Add error handling for storage failures
- [x] 13.9 Create log file indexing for quick access (`DataLogger.list_sessions()` / `index.json`)
- [ ] 13.10 Test storage reliability under continuous operation (needs real hardware/long-running test)

### Step 14: REST API Integration

> Related design note: [`docs/scan-to-provision.md`](docs/scan-to-provision.md) —
> the device can already decode QR codes and the vendor Settings app already
> provisions Wi-Fi that way. 14.1 and 14.4 are the two blockers standing
> between that and scan-to-provision for our own endpoint and enrolment.

**Sub-steps:**
- [x] 14.1 Create `NetworkManager` class for Wi-Fi handling
- [x] 14.2 Implement `NetworkUploader` class with threading
- [x] 14.3 Add REST endpoint configuration (URL, authentication)
- [x] 14.4 Implement HTTP POST requests using `requests` library
- [x] 14.5 Add JSON payload formatting for API calls
- [x] 14.6 Implement retry logic with exponential backoff
- [x] 14.7 Add upload progress tracking and status reporting
- [x] 14.8 Handle network errors and disconnections gracefully
- [x] 14.9 Implement upload queue management
- [ ] 14.10 Test API integration with mock server

### Step 15: Detection Model Toggles

See `docs/research-notes.md` for why 15.4 is a per-model frame-skip +
shared-instance design rather than literal round-robin: no MaixCAM/MaixPy
project, official or community, was found doing true concurrent NPU
time-slicing - the NPU executes one model at a time, so the real lever is
running each model *less often*, not interleaving them more cleverly.

**Sub-steps:**
- [x] 15.1 Create AI model configuration dictionary (`utils/config.py`'s `ai_models`)
- [x] 15.2 Link UI checkboxes to model enable/disable flags (`model_states`, pre-existing)
- [x] 15.3 Implement dynamic model loading/unloading (`AIModelManager` now only instantiates a toggled-on model's detector at all)
- [x] 15.4 Add NPU scheduler for time-slicing between models (per-model `processing_interval` frame-skipping + tracking reusing detection's own output, rather than true concurrent time-slicing - see note above)
- [x] 15.5 Create model priority and frequency settings (`processing_interval` is live; `priority` is recorded but not yet used to order execution - see `docs/configuration.md`)
- [x] 15.6 Implement memory management for model switching (only enabled models are ever loaded; `cleanup()` releases them on shutdown - switching models *while running* isn't supported, since the setup screen only configures models before the main app starts)
- [x] 15.7 Add visual indicators for active models in UI (`main.py`'s own overlay already listed active models; `ui/main_ui.py`'s `ModelDrawer` predates this pass)
- [ ] 15.8 Test performance impact of different model combinations (needs real hardware)
- [x] 15.9 Implement model configuration persistence (`Config.save_config()`, pre-existing)
- [x] 15.10 Add model status reporting and error handling (`AIModelManager.get_model_status()`; every detector fails non-fatally and reports `loaded=False` instead of crashing)

### Step 16: Testing & Debugging

211 tests (`python3 -m unittest discover tests`), covering every module
that doesn't strictly need real hardware. `main.py` itself is still
untested (it imports `maix` at module level, like `setup_screen.py`,
and always has).

**Sub-steps:**
- [x] 16.1 Create unit tests for each AI model pipeline (`tests/test_{object_detector,face_detector,object_tracker,ocr_detector,hand_detector,pose_detector,audio_processor}.py`)
- [ ] 16.2 Implement integration tests for full workflow (no test exercises `main.py`'s `AIModelManager`/`CompanionCaptureApp` end-to-end - it isn't importable off-device)
- [ ] 16.3 Add memory leak detection and monitoring (needs real hardware/long-running test)
- [ ] 16.4 Create performance benchmarking suite (needs real hardware)
- [x] 16.5 Test error handling and recovery scenarios (missing model files, network failures, malformed config, off-device fallbacks - all unit-tested)
- [x] 16.6 Implement logging system for debugging (`utils/logger.py`, pre-existing, used throughout)
- [ ] 16.7 Add UI responsiveness testing (needs real hardware/touchscreen)
- [x] 16.8 Test storage and network failure scenarios (`tests/test_uploader.py`, `tests/test_data_logger.py`)
- [ ] 16.9 Perform stress testing with continuous operation (needs real hardware)
- [x] 16.10 Document and fix all identified bugs (the detector-module verify pass found and fixed two real bugs in `audio_processor.py` - see `CHANGELOG.md`)

### Step 17: Performance Optimization
**Sub-steps:**
- [ ] 17.1 Profile CPU and NPU usage patterns (needs real hardware)
- [x] 17.2 Optimize AI model processing intervals (`ai_models.<key>.processing_interval` was read from config but never applied before this pass - `AIModelManager` now honors it)
- [x] 17.3 Implement intelligent frame skipping (per-model interval gating, plus Object Tracking reusing Object Classification's own detections instead of a second YOLOv8 pass)
- [ ] 17.4 Add dual buffering for all AI models (`ObjectDetector`, `FaceDetector`'s main Retinaface stage, and `PoseDetector` use `dual_buff=True`; `maix.nn.PP_OCR`'s actual constructor takes no such parameter, so "for all" isn't achievable as written - see `src/ai/ocr_detector.py`)
- [x] 17.5 Optimize memory allocation and garbage collection (periodic `gc.collect()`, pre-existing)
- [x] 17.6 Implement power management strategies (thermal throttling skips AI inference, the heaviest per-frame cost, when overheating)
- [x] 17.7 Optimize network upload batching (`NetworkUploader` already batched a whole session's events into one POST; `batch_size`/queueing pre-existing)
- [ ] 17.8 Add adaptive quality settings based on performance (no dynamic resolution/quality adjustment exists)
- [x] 17.9 Implement thermal throttling protection (`CompanionCaptureApp._is_thermal_throttled()`, `utils/device.get_cpu_temp_celsius()`)
- [ ] 17.10 Benchmark and validate all optimizations (needs real hardware)

### Step 18: Documentation & Deployment
**Sub-steps:**
- [x] 18.1 Create user manual with setup instructions (`docs/user-guide.md`)
- [x] 18.2 Write developer documentation for code architecture (`docs/architecture.md`)
- [x] 18.3 Create troubleshooting guide for common issues (`docs/troubleshooting.md`)
- [x] 18.4 Document API specification for REST endpoints (`docs/ci-server-api.md`)
- [x] 18.5 Create configuration file documentation (`docs/configuration.md`)
- [x] 18.6 Write deployment scripts and procedures (a checklist, not automation scripts - there's little here to script beyond what the MaixVision IDE / vendor Settings app already do; see `docs/deployment.md`)
- [x] 18.7 Create backup and recovery procedures (`docs/deployment.md`)
- [x] 18.8 Document hardware requirements and compatibility (`docs/deployment.md`, `README.md`)
- [x] 18.9 Create training materials for end users (`docs/user-guide.md`)
- [x] 18.10 Prepare release notes and version documentation (`CHANGELOG.md`; `main.py`/`Config`'s `app.version` bumped to 1.2.0)

### Step 19: Final Deployment & Monitoring

This step is mostly what it says - deploying to a real device - which
this pass could not do (no MaixCAM hardware available). Only the
documentation/tooling that can be prepared in advance is checked off.

**Sub-steps:**
- [ ] 19.1 Prepare production firmware image (that's Sipeed's MaixPy firmware, not something this repo builds)
- [x] 19.2 Create deployment checklist and validation procedures (`docs/deployment.md`)
- [ ] 19.3 Deploy to test environment for final validation (no device available)
- [x] 19.4 Implement monitoring and health check systems (`AIModelManager.get_model_status()`, `NetworkUploader.get_upload_stats()`, `DataLogger.get_session_stats()`/`list_sessions()` - all local, read by whatever operator tooling connects to the device; see `docs/deployment.md`)
- [ ] 19.5 Create remote diagnostic capabilities (the status methods above are local Python calls, not reachable over the network - this device runs no server of its own)
- [ ] 19.6 Deploy to production environment (no device available)
- [ ] 19.7 Monitor initial operation for 24-48 hours (no device available)
- [ ] 19.8 Collect performance metrics and user feedback (no device available)
- [ ] 19.9 Address any critical issues found in deployment (nothing deployed yet)
- [x] 19.10 Create maintenance schedule and update procedures (`docs/deployment.md`)
 