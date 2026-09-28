# Deployment

## Hardware requirements

- A Sipeed MaixCAM or MaixCAM-Pro running MaixPy v4 (MaixCDK-based)
  firmware - see `README.md` for the minimum-version notes and firmware
  update links. Base MaixCAM has only 256MiB RAM with a small shared
  camera/NPU/model memory pool (`docs/research-notes.md`); enable only the
  models you actually need.
- An SD card for `/sd/companion_config.json`, session logs, and the
  `uploaded/` archive.
- All seven `.mud` model files referenced in `docs/configuration.md` for
  whichever models you enable, pushed to their configured `model_path`s.
  A missing file disables just that model (logged, non-fatal) - it does
  not stop the app from starting with everything else enabled.
- Wi-Fi, configured via the vendor Settings app (QR or manual) before
  first launching this app - see `docs/scan-to-provision.md`.

## Deployment checklist

1. Flash/update MaixPy firmware (MaixVision IDE or the official image).
2. Push `.mud` model files for every model you plan to enable.
3. Connect Wi-Fi via the vendor Settings app.
4. Copy this app's `src/` to the device and run it once - this creates
   `/sd/companion_config.json` with defaults, and the setup screen appears.
5. In the setup screen, enable only the models you need; tap **START**.
6. If syncing to CI-Server: set `network.endpoint_url`, `network.api_key`,
   `network.upload_enabled: true` in the config file (`docs/configuration.md`),
   then restart the app.
7. Verify: start a capture session, confirm session JSON files appear
   under `storage.base_path`, and (if syncing) confirm
   `NetworkUploader.get_upload_stats()`'s `successful_uploads` increases
   after ending a session.

## Monitoring / health checks

No dedicated health-check endpoint exists on-device (it's headless and has
no server of its own) - health is read from the running app's own state:

- `AIModelManager.get_model_status()` - which models actually loaded
  (`True`) vs. silently disabled (`False`, e.g. missing model file).
- `DataLogger.get_session_stats()` / `DataLogger.list_sessions()` - active
  session state and the full session history (`docs/architecture.md`'s
  storage index, PROJECT_PLAN.MD 13.9).
- `NetworkUploader.get_upload_stats()` - queue size, success/failure
  counts, last error, whether the upload thread is running.
- CI-Server's own `GET /v1/ingest/status` (see `docs/ci-server-api.md`)
  reports what actually landed server-side, independent of what this
  device believes it sent.

## Backup and recovery

- The config file and session logs both live on the SD card - back up
  `/sd/companion_config.json` and `storage.base_path` (default `/sd/logs`)
  together; the config alone doesn't recreate historical sessions.
- Already-uploaded sessions are archived (gzip-compressed by default)
  under `<base_path>/uploaded/` rather than deleted, so a device can be
  re-flashed without losing that history as long as the SD card itself
  survives.
- CI-Server is the durable copy of anything successfully synced - a lost
  or corrupted SD card only loses sessions that were never uploaded (check
  `network.upload_enabled` was on, and `NetworkUploader.get_upload_stats()`
  before the loss if you need to know what that was).

## Maintenance

- Keep MaixPy firmware current via the MaixVision IDE or the
  [MaixPy releases page](https://github.com/sipeed/MaixPy/releases) -
  this app targets the current v4/MaixCDK API surface (`README.md`).
- `pip install -r requirements.txt` on-device to pick up `requests`/`pytest`
  version updates; `maix` itself is not a pip package (see `requirements.txt`).
- Re-run `python3 -m unittest discover tests` after any code change -
  every non-hardware module in this repo is designed to stay testable
  without a real device (`docs/architecture.md`).
