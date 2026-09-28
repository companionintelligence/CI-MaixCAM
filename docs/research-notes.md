# Research notes — other MaixCAM/MaixPy projects

> Gathered 2026-09-28 while implementing PROJECT_PLAN.MD steps 5-11 (the
> real AI detectors) and step 15 (model scheduling), to check this repo's
> design against what the wider MaixCAM ecosystem actually does.

**Key takeaway:** nobody in the public ecosystem documents a clean
round-robin/time-sliced scheduler for running several heavy NPU models per
frame. The two patterns actually used in the wild are (1) a cheap gatekeeper
triggering an expensive model, and (2) simple sequential cascades (detect →
crop → classify) — which matches this repo's own planned Step 7 approach
(face detect → crop → emotion classify) but leaves Step 15.4's general
"NPU scheduler for time-slicing between models" with no off-the-shelf
reference to copy.

## (a) How others structure the main loop with multiple heavy models

- **Sipeed's own primitive is per-model pipelining, not cross-model
  scheduling.** The `dual_buff` mechanism (default `True` on `nn.YOLOv8`
  etc., used throughout `src/ai/*.py`) lets the CPU hand a frame to the NPU
  and immediately start pre-processing the *next* frame instead of
  blocking — it pipelines one model's own CPU/NPU stages against each
  other, with a one-frame result latency, but gives no mechanism for
  interleaving *different* models.
  ([Dual Buffer Mode](https://wiki.sipeed.com/maixpy/doc/en/vision/dual_buff.html))
- **No official example runs 2+ heavy models in one loop.** The MaixPy
  examples tree only ships single-capability scripts — no combined
  "run everything" reference implementation exists to copy.
  ([MaixPy examples](https://github.com/sipeed/MaixPy/tree/main/examples))
- **The one real multi-model pattern found in the wild is "cheap gate,
  expensive verify."** [`bobberdolle1/maixcam-wildtrap`](https://github.com/bobberdolle1/maixcam-wildtrap)
  (a MaixCAM wildlife camera trap — the closest public analog to this
  repo's life-logging goal) runs its heavy YOLOv8n model *only when a
  cheap motion-diff fires*, rather than running multiple NN models every
  frame; its benchmarked FPS drop (30fps motion-only → 20fps AI-every-frame)
  is exactly the "NPU is a single serialized execution unit, cost is
  additive across models" constraint `src/main.py`'s `AIModelManager` now
  designs around (per-model `processing_interval` frame-skipping, and
  Object Tracking reusing Object Classification's own detections instead
  of a second YOLOv8 pass).
- **Two-stage cascades, not round-robin, are the other real pattern** —
  e.g. face-detect-then-crop-then-classify, matching `src/ai/face_detector.py`
  and `src/ai/hand_detector.py`'s own one-pipeline-two-toggles design.

## (b) Memory / frame-rate pitfalls with 2+ concurrent models

- **RAM is tight and shared with hardware drivers.** Base MaixCAM has only
  256MiB total, and NN model weights load into a shared "CMM" (contiguous
  memory) region also used by the camera, NPU, display and video codec —
  not plain userspace heap. Keeping several model files resident at once
  risks exhausting CMM before inference-time contention even shows up.
  MaixCAM2 (1-4GB variants) has much more headroom; base MaixCAM does not.
  ([Memory Usage Guide](https://wiki.sipeed.com/maixpy/doc/en/pro/memory.html),
  [MaixCAM FAQ](https://wiki.sipeed.com/maixpy/doc/en/faq.html))
- This is exactly why `AIModelManager._initialize_model_processors()` only
  ever instantiates a detector for a model the setup screen actually
  toggled on, rather than constructing all thirteen up front.
- No forum/issue thread reports an NPU *scheduling* crash from running 2+
  models concurrently — the real-world failure mode is out-of-memory when
  model weights collectively exceed the CMM pool, and cumulative FPS loss,
  not a driver race condition.

## (c) JSON event schema choices in comparable projects

- [`flaviostutz/cam-event-detector`](https://github.com/flaviostutz/cam-event-detector)
  (camera → detect/track → JSON → HTTP POST — architecturally the closest
  analog to this repo's capture-loop-to-CI-Server design) uses a typed
  envelope with a UUID, ISO-8601 time, a `type` discriminator and
  type-specific payload — validating this repo's own unified
  `{timestamp, type, model, processing_time_ms, detections: [...]}` shape.
- Every other public MaixCAM project found uses ad hoc per-capability
  logging instead: `maixcam-wildtrap` writes a JSON sidecar file per
  detection plus a flat CSV; a MaixCAM+YOLOv8 face-counting project skips
  JSON entirely and appends plain-text lines. **No project found uses one
  unified, versioned schema spanning multiple model types** the way this
  repo's Step 12 does — a genuine gap in the public ecosystem, and a
  reason to keep this repo's schema rather than simplify it away.

## What this changed in the implementation

- `AIModelManager` schedules each detector at its own configured
  `processing_interval` (previously read from config but never applied)
  instead of running everything every frame.
- Object Tracking and Counting reuses Object Classification's own
  per-frame detections when both are enabled, rather than running YOLOv8
  twice on the same image.
- Face Recognition/Emotion and Hand Landmarks/Gesture each share one
  underlying pipeline instance across their two toggles, so enabling both
  never doubles NPU work.
