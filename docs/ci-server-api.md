# CI-Server API usage

This device is a **capture surface** on the Companion Intelligence
platform, in the same category as CI-Capture (the desktop tray app) - it
authenticates with a pre-shared API key and posts into CI-Server's `/v1`
bulk ingest plane, rather than running its own OIDC login flow (impractical
on a headless/touchscreen-only device).

## Authentication

`x-api-key: <network.api_key>` on every request. The key should be scoped
for `capture` write access on the CI-Server side. There is no self-service
device-registration/enrolment endpoint this app calls - the key is
provisioned out of band today (see `docs/scan-to-provision.md` for a
QR-based design that would remove that manual step, not yet built).

## Endpoints

Base URL is `network.endpoint_url` (no trailing slash, no path suffix).
Both routes are tried bare-path first, falling back to an `/api`-prefixed
path on a `404` - some CI-Server deployments front the `/v1` plane behind
an `/api` proxy prefix and some don't:

- `POST {endpoint_url}/v1/events` (fallback `/api/v1/events`)
  Body: `{"events": [<CaptureEvent>, ...]}` - every event from one ended
  capture session, batched into a single request.
- `POST {endpoint_url}/v1/ingest/finish` (fallback `/api/v1/ingest/finish`)
  Sent once per successful upload, best-effort (a failure here is not
  fatal - CI-Server runs the same enrichment/search-index sweep on its own
  ~60s later regardless).

## The CaptureEvent wire shape

One entry in the `events` array per detection event this device logged:

```json
{
  "source_type": "capture",
  "source_system": "ci-maixcam",
  "source_id": "ci-maixcam:<device_id>:<event_id>",
  "kind": "object_detection",
  "occurred_at": "2026-09-28T00:00:00+00:00",
  "observed_at": "2026-09-28T00:00:00+00:00",
  "title": "Object Classification",
  "payload": { "...": "the detector's own event, plus device_id" },
  "confidence_score": 0.91
}
```

Notes, each the result of a specific gotcha found while implementing this
(see `src/network/uploader.py::build_capture_event`):

- `title` and `confidence_score` are **omitted entirely** when there's
  nothing to put there, never sent as JSON `null` - CI-Server's schema
  accepts an absent key but rejects an explicit `null` (the same issue
  CI-Capture hit and fixed on its own vizier lane).
- `source_id` is built from this device's stable id (`maix.sys.device_key()`
  when available, else a generated id persisted in `network.device_id` -
  see `utils/device.py`) plus the event's own id, so a retried POST is
  idempotent on CI-Server's side rather than creating a duplicate.
- `payload` is the detector's own unified event
  (`docs/architecture.md`'s schema) with `device_id` merged in; CI-Server
  stores it opaquely (searchable by `kind`/`title`, not by anything inside
  `payload`).
- `confidence_score` is the single highest per-detection confidence in
  that event, when the event has at least one detection; omitted otherwise.

## What this device does *not* do

- No `GET` calls of any kind - this device only ever pushes data.
- No file/image uploads (`/files/upload`) - only JSON detection events,
  never camera frames or screenshots.
- No use of the more specific `/v1/observations` lane (built for exactly
  this kind of bbox+label+confidence sighting) - `/v1/events` was chosen to
  match the platform's other capture-surface client (CI-Capture) as
  closely as possible; switching lanes is a future option, not a
  correctness issue with the current one.
