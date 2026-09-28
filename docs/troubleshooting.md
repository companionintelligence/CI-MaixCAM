# Troubleshooting

## A model never produces any events

1. Check the model's `.mud` file actually exists on the device at the
   path configured in `ai_models.<key>.model_path` (`docs/configuration.md`
   has the default paths). A missing file logs `"failed to load model"` /
   `"no model_path configured"` from that detector and the app keeps
   running with that model permanently disabled - it never crashes.
2. Check `AIModelManager.get_model_status()` (or the console log at
   startup: `"✅ <Model> processor ready"`) - if a model's line never
   appears, its toggle is off in `model_states` (re-open the setup screen).
3. A loaded-but-silent model may just not be finding anything: lower
   `ai_models.<key>.confidence_threshold` in the config, or increase
   `processing_interval` if it's competing with several other heavy models
   for the NPU (see `docs/research-notes.md` on why running everything
   every frame isn't realistic on this hardware).

## Wi-Fi / CI-Server sync isn't happening

1. `network.upload_enabled` must be `true` and `network.endpoint_url` must
   be a real CI-Server base URL (not empty - that's the shipped default
   until you configure it).
2. Sync is skipped entirely while Wi-Fi is disconnected
   (`NetworkManager.is_connected()`) - this is intentional, not a bug; it
   resumes automatically once connectivity returns.
3. Check `network.api_key` is a CI-Server API key with `capture` write
   scope. An auth failure logs `"POST to ... failed: HTTP 401/403"` and is
   retried with backoff, but will keep failing until the key is fixed.
4. `NetworkUploader.get_upload_stats()` reports `total_uploads`,
   `successful_uploads`, `failed_uploads`, `last_error` and the current
   queue size - the fastest way to tell "never tried" from "tried and
   failed" from "succeeded".

## Storage filling up

- `storage.max_storage_usage_percent` and the automatic 10-most-recent-file
  retention in `DataLogger._cleanup_old_files()` bound how much local
  storage capture sessions use.
- Already-uploaded sessions are archived under `<base_path>/uploaded/`,
  gzip-compressed by default (`storage.compression_enabled`) - safe to
  delete manually once you've confirmed they're in CI-Server, since
  nothing on-device reads that folder back.

## The device seems to be throttling itself

A log line like `"Thermal throttling: CPU at 82.3C (threshold 75C),
skipping AI this frame"` means `performance.thermal_threshold_celsius` was
exceeded - AI inference is skipped for that frame (the camera/display loop
keeps running) until the temperature drops. Raise the threshold, improve
airflow/mounting, or reduce how many heavy models are enabled at once.

## Nothing works at all off-device (during development)

`maix` is not a pip package - it ships with MaixCAM's own firmware and is
only importable there. `src/main.py` and `src/setup_screen.py` therefore
can't run on a desktop at all; everything under `src/ai/`, `src/network/`,
and `src/utils/` is designed to still be importable and unit-testable
without it (see `docs/architecture.md`). `python3 -m unittest discover
tests` should always pass on a plain desktop Python - if it doesn't,
that's a real regression, not an environment problem.
