# User Guide

## First run

1. Power on the MaixCAM. The **Companion Capture Setup** screen appears
   first — a scrollable list of AI models grouped as Computer Vision,
   Audio Processing and Media, each with a checkbox.
2. Tap a model's checkbox to toggle it. **ALL ON** / **ALL OFF** select
   every model at once. Your selection is saved to
   `/sd/companion_config.json` the moment you tap **START**.
3. Tap **START** to save your selection and launch the main capture app,
   or **CANCEL** to exit without changing anything.

Only toggle the models you actually want: MaixCAM's camera, NPU and model
weights share one small memory pool, and every enabled model is loaded
into it at startup (see `docs/research-notes.md` for why). A device with
two or three models on will run faster and use less memory than one with
all thirteen enabled.

## Using the main app

- **Top-left corner (touch):** start/stop a capture session. While
  capturing, every enabled model runs on the live camera feed and any
  detection is logged as a JSON event.
- **Top-right corner (touch):** exit the app.
- The status bar shows frame rate, active model count, capture state, and
  (while a session is active) how many events have been logged this
  session and in total.

Each capture session writes one JSON file under `/sd/logs/` (the
`storage.base_path` config value) with a session ID, start/end time, and
every detection event logged during that session. See
`docs/configuration.md` for the exact record shape and
`docs/ci-server-api.md` for how it's forwarded to CI-Server.

## Syncing to CI-Server

By default the device only logs locally. To also sync to your
[CI-Server](https://github.com/companionintelligence/CI-Server) instance,
set in the config file (see `docs/configuration.md`):

- `network.endpoint_url` — your CI-Server's base URL
- `network.api_key` — a CI-Server API key with `capture` write scope
- `network.upload_enabled` — `true`

Once a capture session ends, its file is queued for upload; the app
retries with backoff and skips uploading entirely while Wi-Fi is
disconnected, so nothing is lost while offline.

## Troubleshooting

See `docs/troubleshooting.md` for common issues (a model that never
produces events, Wi-Fi/CI-Server connectivity, storage filling up).
