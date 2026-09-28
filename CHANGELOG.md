# Changelog

## 1.2.0 - 2026-09-28

Implements PROJECT_PLAN.MD steps 5-19: real on-device AI detectors,
CI-Server sync, and the remaining storage/performance/documentation work.

### Added

- `src/ai/` - real detector implementations replacing the mock event
  generator: `ObjectDetector` (YOLOv8), `FaceDetector` (Retinaface +
  emotion), `ObjectTracker` (pure-Python IoU tracking), `OcrDetector`
  (PP-OCR), `HandDetector` (landmarks + gesture), `PoseDetector` (YOLOv8
  pose + a posture-classification heuristic), `AudioProcessor` (recording,
  playback, keyword-spotting voice recognition).
- A unified detection-event schema (`{timestamp, type, model,
  processing_time_ms, detections: [...]}`) shared by every detector,
  `DataLogger`, and the UI overlay - see `docs/architecture.md`.
- Real CI-Server sync: `NetworkUploader` POSTs to CI-Server's `/v1/events`
  ingest plane instead of a mock transport (see `docs/ci-server-api.md`).
- `NetworkManager` (Wi-Fi status via `maix.network.wifi`) and
  `utils/device.py` (device identity via `maix.sys`, CPU temperature).
- Per-model frame-skipping (`ai_models.<key>.processing_interval`, read
  from config but previously unused) and thermal throttling
  (`performance.thermal_threshold_celsius`).
- Session storage index (`DataLogger.list_sessions()`) and gzip
  compression of archived, already-uploaded session files.
- `docs/`: user guide, architecture, troubleshooting, configuration
  reference, CI-Server API reference, deployment checklist, and research
  notes on other MaixCAM/MaixPy projects.
- `requirements.txt` (previously referenced by `CLAUDE.md`/`AGENTS.md`
  but missing).

### Changed

- `network.endpoint_url` now defaults to `""` instead of the placeholder
  `https://api.example.com/upload`.
- Event timestamps are UTC-aware now that they're sent off-device.

### Known limitations

- Not validated against real MaixCAM hardware, a live CI-Server, or actual
  `.mud` model files - only what's testable off-device
  (`python3 -m unittest discover tests`) has been verified.
- No self-service device enrolment/registration endpoint exists on the
  CI-Server side as far as could be confirmed; `network.api_key` is
  configured manually (see `docs/scan-to-provision.md` for a QR-based
  design that would remove that step).
