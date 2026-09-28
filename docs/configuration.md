# Configuration reference

The whole app shares one file, `/sd/companion_config.json`
(`utils/paths.CONFIG_PATH`), created with these defaults on first run and
merged with your changes on every load (`utils/config.Config`). A key not
listed here and not already in the schema below is preserved on save but
otherwise ignored by the app.

The one exception is `model_states` (`{"<display name>": true|false, ...}`),
written by the setup screen - it lives at the top level of the file, not
inside `ai_models`, and is the single source of truth for which models run
(`utils/models.py`'s `ALL_MODELS` lists every valid display name).

## `app`

| Key | Default | Notes |
|---|---|---|
| `name` | `"Companion Capture"` | |
| `version` | `"1.0.0"` | Stamped into every session's metadata |
| `debug` | `false` | Not currently read anywhere |
| `log_level` | `"INFO"` | Not currently read anywhere |

## `camera`

`width`/`height`/`fps`/`format`/`auto_exposure`/`brightness`/`contrast` -
declared but not yet wired into `main.py`'s hardcoded
`camera.Camera(width=640, height=480, fps=30)` call.

## `ai_models.<key>`

One entry per detector, each with `model_path` (where applicable),
`confidence_threshold`, `processing_interval` (run this model every N
frames - see `docs/architecture.md`) and `priority` (recorded, not
currently used to order execution).

| `<key>` | Backs display name(s) | Default `model_path` |
|---|---|---|
| `object_detection` | Object Classification | `/root/models/yolov8n.mud` |
| `face_detection` | Face Recognition | `/root/models/retinaface.mud` |
| `face_emotion` | Face Emotion Detection | `/root/models/face_emotion.mud` |
| `ocr` | OCR (Optical Character Recognition) | `/root/models/pp_ocr.mud` |
| `hand_landmarks` | Hand Landmarks Detection | `/root/models/hand_landmarks.mud` |
| `hand_gesture` | Hand Gesture Classification | `/root/models/hand_gesture.mud`\* |
| `pose_detection` | Human Pose Classification | `/root/models/yolov8n_pose.mud` |
| `object_tracking` | Object Tracking and Counting | *(no model - pure algorithm)* |
| `audio_recognition` | Audio Recording, Real-time Voice Recognition | *(voice recognition needs one, see below)* |

\* No dedicated gesture-classifier model is confirmed to exist for
MaixCAM; `HandDetector` falls back to a geometric heuristic over hand
landmarks when this path doesn't load. See `src/ai/hand_detector.py`.

`object_tracking` additionally has `max_track_age_frames` (default `30`) -
how many calls a track survives with no matching detection before it's
retired.

Real-time Voice Recognition needs both a trained keyword-spotting model
and a keyword table, neither of which this schema carries yet - see
`src/ai/audio_processor.py`'s module docstring; until both are supplied
via constructor kwargs it stays a documented no-op.

## `storage`

| Key | Default | Notes |
|---|---|---|
| `base_path` | `"/sd/logs"` | Session files + `index.json` + `uploaded/` |
| `max_log_size_mb` | `100` | Logged only, not yet enforced (no rotation) |
| `rotation_interval_hours` | `24` | Not currently read anywhere |
| `compression_enabled` | `true` | Gzip already-uploaded session files when archiving |
| `cleanup_old_files` | `true` | Keep only the 10 most recent session files |
| `max_storage_usage_percent` | `80` | Not currently enforced |

## `network`

| Key | Default | Notes |
|---|---|---|
| `wifi_enabled` | `true` | Not currently read anywhere (Wi-Fi is always probed) |
| `upload_enabled` | `false` | Master on/off for CI-Server sync |
| `upload_interval_seconds` | `300` | Background upload-worker poll interval |
| `retry_attempts` | `3` | Per-file upload retry count |
| `retry_delay_seconds` | `30` | Base delay, doubled-ish per retry |
| `batch_size` | `50` | Max files pulled off the queue per cycle |
| `endpoint_url` | `""` | Your CI-Server's base URL - **required** to sync |
| `api_key` | `""` | CI-Server API key, `capture` write scope |
| `device_id` | `""` | Fallback id, auto-filled off real hardware - don't set by hand |
| `timeout_seconds` | `30` | Per-HTTP-request timeout |

See `docs/ci-server-api.md` for the wire format.

## `ui`

`theme`/`show_fps`/`show_memory`/`show_ai_overlay`/`touch_feedback`/
`status_update_interval_ms` - read by `src/ui/main_ui.py`'s `MainUI`,
which (see `docs/architecture.md`) isn't currently wired into `main.py`'s
own simpler overlay.

## `performance`

| Key | Default | Notes |
|---|---|---|
| `memory_warning_threshold_mb` | `10` | Not currently enforced |
| `memory_critical_threshold_mb` | `5` | Not currently enforced |
| `max_frame_skip` | `5` | Not currently enforced |
| `thermal_throttling_enabled` | `true` | Gates `CompanionCaptureApp._is_thermal_throttled()` |
| `thermal_threshold_celsius` | `75` | AI inference is skipped for a frame at/above this CPU temp |
