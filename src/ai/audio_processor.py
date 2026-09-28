"""
Audio Processor
Step 5: Audio Recording, Audio Playback, Real-time Voice Recognition

Backs three independently-toggleable setup-screen models (see
utils/models.py's AUDIO_MODELS / model_states) from one class, because they
all share the single "audio_recognition" entry in utils/config.py's
ai_models schema (the setup screen still tracks their enabled state
separately, in model_states, under their own display names):

  * "Audio Recording" - continuous mic-activity monitoring. A caller arms it
    with start_recording()/stop_recording(); while armed, process(img=None)
    reads one short chunk from maix.audio.Recorder each call and reports a
    unified "audio_event" only when its level crosses `activity_threshold`,
    else None. This is the "process(img) reporting call" the rest of this
    AI module family exposes.

  * "Audio Playback" - play(file_path) plays a wav file through
    maix.audio.Player. This is a one-shot action a caller invokes on
    demand (e.g. a UI button), not a per-frame detector: there is no
    per-frame "detection" to report, and Player.play() blocks for the
    file's duration with the SDK's default block=True, which would stall
    the capture loop if driven from inside process(). So it deliberately
    sits outside the process(img) -> unified-event contract.

  * "Real-time Voice Recognition" - wraps maix.nn.Speech's real-time
    keyword-spotting entry point, confirmed present in the live MaixPy v4
    API reference: Speech.kws(kw_tbl, kw_gate, callback). That confirmed
    signature is genuinely wrapped below (nn.Speech(...).init(DEVICE_MIC)
    + .kws(...) + a per-call .run(1)) rather than guessed at - but it needs
    BOTH a trained acoustic .mud model AND an explicit keyword table/gate,
    neither of which utils/config.py's ai_models.audio_recognition schema
    carries and neither of which ships with this repo. Until a caller
    supplies both via kwargs (voice_model_path/model_path, keywords,
    kw_gate), this stays a documented no-op: it logs one warning and
    process() keeps returning None for this behavior - it never raises and
    never fabricates a model that doesn't exist on disk.

Gotcha carried over from research: maix.audio.Recorder and
maix.nn.Speech(..., DEVICE_MIC) both want the microphone, and no wiki
example wires them together, so process() below treats them as mutually
exclusive - an armed recording takes priority over the voice-recognition
poll on any given call (see process()).

Backed by maix.audio / maix.nn (MaixPy v4 / MaixCDK), which are only
importable on real hardware. Off-device - desktop dev, unit tests - every
maix.* import is local to a method body and wrapped in try/except, the same
off-device tolerance utils/device.py, network/network_manager.py and
ai/object_detector.py already apply to their own maix.* usage: this module
always imports cleanly, the underlying hardware/model then simply never
loads, and process()/play() report nothing rather than raise.

Author: Companion Intelligence
"""

import struct
import time as _time

from utils.logger import get_logger

logger = get_logger('AudioProcessor')


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


# ---------------------------------------------------------------------------
# Pure, hardware-free helpers - no maix dependency, plain Python in and out,
# so each is trivially unit-testable without a device.
# ---------------------------------------------------------------------------

def mean_abs_amplitude(samples):
    """Mean absolute amplitude of a raw PCM sample list.

    `samples` is any sequence of signed integers (e.g. one 16-bit PCM
    sample per element). An empty/falsy input is silence -> 0.0.
    """
    if not samples:
        return 0.0
    return sum(abs(sample) for sample in samples) / len(samples)


def normalize_level(raw_level, full_scale=32768.0):
    """Normalize a raw amplitude to a 0.0-1.0 level, clamped both ends.

    `full_scale` is the maximum magnitude of the PCM format in use (32768
    for signed 16-bit, matching maix.audio's default FMT_S16_LE). A
    non-positive `full_scale` is treated as "no signal" -> 0.0, rather than
    raising a ZeroDivisionError.
    """
    if full_scale <= 0:
        return 0.0

    level = raw_level / full_scale
    if level < 0.0:
        return 0.0
    if level > 1.0:
        return 1.0
    return level


def compute_audio_level(samples, full_scale=32768.0):
    """Mean-abs amplitude of `samples`, normalized to a 0.0-1.0 level.

    This is the single audio-level threshold helper AudioProcessor.process()
    gates its "Audio Recording" activity events on: the "Audio Recording"
    behavior's mic chunk is decoded to a plain int sample list (see
    decode_pcm_s16le) and passed straight in here, no hardware needed.
    """
    return normalize_level(mean_abs_amplitude(samples), full_scale=full_scale)


def decode_pcm_s16le(data):
    """Decode little-endian signed-16-bit PCM bytes into a list of ints.

    Matches maix.audio's default Format.FMT_S16_LE. A trailing odd byte (a
    chunk cut mid-sample) is dropped rather than raising. Falsy/empty input
    decodes to []. Pure stdlib (`struct`) - no maix dependency.
    """
    if not data:
        return []

    sample_count = len(data) // 2
    if sample_count == 0:
        return []

    return list(struct.unpack('<%dh' % sample_count, data[:sample_count * 2]))


def pick_best_keyword(scores, kw_table, kw_gate=None):
    """Pick the highest-scoring keyword from one kws() callback invocation.

    `scores` is the raw per-keyword score list maix.nn.Speech.kws()'s
    callback receives, aligned index-for-index with `kw_table` (the keyword
    strings passed into kws()) and, optionally, `kw_gate` (the per-keyword
    thresholds also passed into kws(); a flat 0.5 gate is used for any
    keyword missing one, or when `kw_gate` is omitted entirely).

    Returns (label, confidence) for the top-scoring keyword that clears its
    gate, confidence clamped to [0.0, 1.0], or None when `scores`/`kw_table`
    is empty, the best index doesn't line up with `kw_table`, or nothing
    clears its gate. A classification heuristic with zero maix dependency,
    so it is unit-testable with plain Python lists.
    """
    if not scores or not kw_table:
        return None

    best_index = max(range(len(scores)), key=lambda i: scores[i])
    if best_index >= len(kw_table):
        return None

    gate = 0.5
    if kw_gate and best_index < len(kw_gate):
        gate = kw_gate[best_index]

    confidence = scores[best_index]
    if confidence < gate:
        return None

    if confidence < 0.0:
        confidence = 0.0
    elif confidence > 1.0:
        confidence = 1.0

    return kw_table[best_index], confidence


def build_audio_activity_event(level, raw_level, duration_ms, timestamp,
                                processing_time_ms, model_name="Audio Recording"):
    """Pure construction of the unified 'audio_event' detection payload for
    one mic-activity threshold crossing."""
    return {
        "timestamp": timestamp,
        "type": "audio_event",
        "model": model_name,
        "processing_time_ms": processing_time_ms,
        "detections": [
            {
                "label": "audio_activity",
                "confidence": level,
                "bbox": None,
                "level": raw_level,
                "duration_ms": duration_ms,
            }
        ],
    }


def build_voice_recognition_event(label, confidence, timestamp, processing_time_ms,
                                   model_name="Real-time Voice Recognition"):
    """Pure construction of the unified 'voice_recognition' detection
    payload for one recognized keyword/utterance."""
    return {
        "timestamp": timestamp,
        "type": "voice_recognition",
        "model": model_name,
        "processing_time_ms": processing_time_ms,
        "detections": [
            {
                "label": label,
                "confidence": confidence,
                "bbox": None,
            }
        ],
    }


class AudioProcessor:
    """Audio Recording / Audio Playback / Real-time Voice Recognition.

    Config key: "audio_recognition" (utils/config.py's
    ai_models.audio_recognition; utils/models.py's CONFIG_KEY_TO_MODEL maps
    it 1:1 to the "Real-time Voice Recognition" model_states toggle only -
    "Audio Recording" and "Audio Playback" have no dedicated config entry
    and are driven purely by which methods a caller invokes). See the
    module docstring for the three behaviors and why voice recognition
    stays inert without extra kwargs.
    """

    def __init__(self, model_config, **kwargs):
        self.model_config = dict(model_config) if model_config else {}

        # "Real-time Voice Recognition"'s own enabled flag - the only one of
        # the three behaviors this config key actually maps to.
        self.voice_enabled = bool(self.model_config.get("enabled", False))

        # Recording / activity-detection tunables. Not part of the
        # audio_recognition schema (which only carries processing_interval/
        # priority), so accepted as overrides via kwargs; confidence_threshold
        # is honored too in case a future schema revision adds one.
        self.sample_rate = kwargs.get("sample_rate", 16000)
        self.channel = kwargs.get("channel", 1)
        self.chunk_ms = kwargs.get("chunk_ms", 50)
        self.activity_threshold = kwargs.get(
            "activity_threshold", self.model_config.get("confidence_threshold", 0.03)
        )

        # Real-time voice recognition needs both a model and a keyword
        # table - see class/module docstring.
        self.voice_model_path = kwargs.get("voice_model_path") or self.model_config.get("model_path")
        self.kw_table = kwargs.get("keywords") or kwargs.get("kw_table")
        self.kw_gate = kwargs.get("kw_gate")

        self.loaded = False        # audio.Recorder ready (Audio Recording)
        self.voice_loaded = False  # nn.Speech + kws() armed (Voice Recognition)
        self.recording = False

        self._recorder = None
        self._speech = None
        self._last_kws_scores = None
        self._voice_warning_logged = False

        self._load_recorder()

    def _load_recorder(self):
        """Construct the maix.audio.Recorder used for mic-activity
        monitoring. Any failure (no maix SDK, no mic hardware) is
        non-fatal: self.loaded stays False and process()/start_recording()
        simply report nothing for the lifetime of this instance.
        """
        try:
            from maix import audio as maix_audio
            self._recorder = maix_audio.Recorder(
                sample_rate=self.sample_rate,
                channel=self.channel,
                block=False,
            )
            self.loaded = True
            logger.info("AudioProcessor: audio.Recorder ready")
        except Exception as e:
            logger.error(f"AudioProcessor: failed to init audio.Recorder: {e}")
            self._recorder = None
            self.loaded = False

    # -- Audio Recording ----------------------------------------------------

    def start_recording(self):
        """Arm mic-activity monitoring for process(). Returns False (and
        stays unarmed) if the recorder never loaded."""
        if not self.loaded:
            logger.error("AudioProcessor: cannot start recording, audio.Recorder unavailable")
            return False
        self.recording = True
        logger.info("AudioProcessor: recording armed")
        return True

    def stop_recording(self):
        """Disarm mic-activity monitoring. Always safe to call."""
        self.recording = False
        if self._recorder is not None:
            try:
                self._recorder.finish()
            except Exception as e:
                logger.error(f"AudioProcessor: recorder.finish() failed: {e}")
        return True

    def _process_recording(self):
        if not self.loaded or self._recorder is None:
            return None

        start_ms = _now_ms()
        try:
            raw = self._recorder.record(self.chunk_ms)
        except Exception as e:
            logger.error(f"AudioProcessor: recorder.record() failed: {e}")
            return None

        samples = decode_pcm_s16le(raw)
        raw_level = mean_abs_amplitude(samples)
        level = normalize_level(raw_level)

        if level < self.activity_threshold:
            return None

        return build_audio_activity_event(
            level=level,
            raw_level=raw_level,
            duration_ms=self.chunk_ms,
            timestamp=start_ms,
            processing_time_ms=_now_ms() - start_ms,
        )

    # -- Audio Playback -------------------------------------------------
    #
    # Not a per-frame detector - see module docstring.

    def play(self, file_path):
        """Play a wav file through maix.audio.Player.

        Returns True on success, False on any failure (including no maix
        SDK) - never raises.
        """
        try:
            from maix import audio as maix_audio
            player = maix_audio.Player(
                path=file_path,
                sample_rate=self.sample_rate,
                channel=self.channel,
            )
            err = player.play()
            return not bool(err)
        except Exception as e:
            logger.error(f"AudioProcessor: play('{file_path}') failed: {e}")
            return False

    # -- Real-time Voice Recognition -------------------------------------

    def _ensure_speech_loaded(self):
        """Lazily construct nn.Speech and arm kws(). Non-fatal: any failure
        (missing SDK, missing .mud model, missing keyword table) is caught,
        logged once, and leaves voice_loaded False - process() then keeps
        returning None for this behavior, it never raises.
        """
        if self.voice_loaded and self._speech is not None:
            return True

        if not self.voice_model_path or not self.kw_table:
            if not self._voice_warning_logged:
                logger.warning(
                    "AudioProcessor: Real-time Voice Recognition is a documented "
                    "no-op here - maix.nn.Speech.kws() needs a trained acoustic "
                    ".mud model (pass voice_model_path=... or a model_path in "
                    "model_config) and a keyword table (pass keywords=[...]), "
                    "neither of which ships with this repo's config/model files. "
                    "See ai/audio_processor.py's module docstring."
                )
                self._voice_warning_logged = True
            return False

        try:
            from maix import nn as maix_nn

            self._speech = maix_nn.Speech(self.voice_model_path)
            self._speech.init(maix_nn.SpeechDevice.DEVICE_MIC)

            kw_gate = self.kw_gate or [0.5] * len(self.kw_table)

            def _on_kws(scores, length):
                self._last_kws_scores = list(scores)

            self._speech.kws(list(self.kw_table), list(kw_gate), _on_kws)
            self.voice_loaded = True
            logger.info("AudioProcessor: nn.Speech kws() armed")
            return True
        except Exception as e:
            logger.error(f"AudioProcessor: nn.Speech/kws init failed: {e}")
            self._speech = None
            self.voice_loaded = False
            return False

    def _process_voice(self):
        start_ms = _now_ms()

        if not self._ensure_speech_loaded():
            return None

        try:
            frames_left = self._speech.run(1)
        except Exception as e:
            logger.error(f"AudioProcessor: speech.run() failed: {e}")
            self.voice_loaded = False
            return None

        if frames_left < 1:
            # Stream ended (e.g. a WAV/PCM source, not a live mic) - the
            # next call will re-arm kws() from scratch.
            self.voice_loaded = False

        scores, self._last_kws_scores = self._last_kws_scores, None
        picked = pick_best_keyword(scores, self.kw_table, self.kw_gate)
        if picked is None:
            return None

        label, confidence = picked
        return build_voice_recognition_event(
            label=label,
            confidence=confidence,
            timestamp=start_ms,
            processing_time_ms=_now_ms() - start_ms,
        )

    # -- unified process(img) entry point --------------------------------

    def process(self, img=None):
        """Per-call reporting entry point (this module family's unified
        detection-event contract).

        A just-armed recording (start_recording() called) takes priority
        over the voice-recognition poll on any given call - see the module
        docstring on why audio.Recorder and nn.Speech(DEVICE_MIC) are
        treated as mutually exclusive. Returns None when nothing is
        armed/enabled, when nothing crossed its threshold/gate, or on any
        failure - never raises.
        """
        if self.recording:
            return self._process_recording()

        if self.voice_enabled:
            return self._process_voice()

        return None

    def cleanup(self):
        """Release the recorder/speech handles. No-op-safe, for symmetry
        with DataLogger/NetworkUploader."""
        self.recording = False
        if self._recorder is not None:
            try:
                self._recorder.finish()
            except Exception:
                pass
            self._recorder = None
        self._speech = None
        self.voice_loaded = False
