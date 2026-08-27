"""
AI Model Registry
Single source of truth for the AI model catalog and its enabled state

Author: Companion Intelligence
Date: August 26, 2026
"""

# Model names exactly as the setup screen draws them, grouped by section.
#
# These strings are also the keys of the "model_states" record in the config
# file, so they are part of the on-disk format: renaming one resets that model
# to its default on every device that already holds configuration.
COMPUTER_VISION_MODELS = (
    "Object Classification",
    "Face Recognition",
    "Face Emotion Detection",
    "Object Tracking and Counting",
    "OCR (Optical Character Recognition)",
    "Hand Landmarks Detection",
    "Human Pose Classification",
    "Hand Gesture Classification",
)

AUDIO_MODELS = (
    "Audio Recording",
    "Audio Playback",
    "Real-time Voice Recognition",
)

MEDIA_MODELS = (
    "Video Recording",
    "Video Playback",
)

ALL_MODELS = COMPUTER_VISION_MODELS + AUDIO_MODELS + MEDIA_MODELS

# Models that run on a device with no configuration yet. This is both the
# setup screen's checkbox default and the app's fallback when the config file
# is missing, so the screen cannot promise one thing and the app do another.
DEFAULT_ENABLED_MODELS = (
    "Object Classification",
    "Face Recognition",
    "Face Emotion Detection",
    "Audio Recording",
    "Audio Playback",
    "Real-time Voice Recognition",
    "Video Recording",
    "Video Playback",
)

# utils/config.py addresses models by these short keys, under which it holds
# per-model tuning: model path, confidence threshold, processing interval,
# priority. Whether a model RUNS is deliberately not stored there — it is read
# through this map out of model_states, so exactly one copy of that fact
# exists on disk.
CONFIG_KEY_TO_MODEL = {
    "object_detection": "Object Classification",
    "face_detection": "Face Recognition",
    "face_emotion": "Face Emotion Detection",
    "ocr": "OCR (Optical Character Recognition)",
    "hand_landmarks": "Hand Landmarks Detection",
    "pose_detection": "Human Pose Classification",
    "audio_recognition": "Real-time Voice Recognition",
}


def default_model_states():
    """Enabled state of every model on a device with no configuration"""
    return {name: name in DEFAULT_ENABLED_MODELS for name in ALL_MODELS}


def read_model_states(config):
    """Read the enabled state of every model out of a config document

    Anything the document omits falls back to its default, so callers always
    get a complete map whatever shape the file on the device is in.
    """
    states = default_model_states()

    stored = config.get("model_states")
    if isinstance(stored, dict):
        for name, enabled in stored.items():
            states[name] = bool(enabled)

    return states


def migrate_model_states(config):
    """Fold older enabled-state records into model_states, in place

    Builds before August 26, 2026 stored the same fact in up to three places:
    "model_states" (written by the setup screen and the only one the app ever
    read), "selected_models" (written by the setup screen, derivable from
    model_states) and "ai_models.<key>.enabled" (written by utils/config.py,
    read by nothing). Nothing reconciled them, and while the two components
    wrote to different files the disagreement was invisible.

    model_states is now the only stored copy. The other two shapes are folded
    into it here so a device configured by an older build keeps its settings,
    then dropped so they cannot drift again. model_states wins any conflict:
    it is the record that was actually driving the device.

    Returns True when the document was changed — callers that persist the
    document write the cleaned-up shape back.

    Delete this function and its three call sites (utils/config.py,
    setup_screen.py, main.py) once no deployed MaixCAM predates the change.
    """
    if not isinstance(config, dict):
        return False

    changed = False

    states = config.get("model_states")
    if not isinstance(states, dict):
        states = {}

    # "selected_models" is the enabled half of the same record: a device that
    # somehow has it without model_states still knows what the user picked.
    selected = config.get("selected_models")
    if not states and isinstance(selected, list):
        states = {name: name in selected for name in ALL_MODELS}
        changed = True

    ai_models = config.get("ai_models")
    if isinstance(ai_models, dict):
        for config_key, model_config in ai_models.items():
            if not isinstance(model_config, dict) or "enabled" not in model_config:
                continue

            enabled = bool(model_config.pop("enabled"))
            changed = True

            display_name = CONFIG_KEY_TO_MODEL.get(config_key)
            if display_name is not None and display_name not in states:
                states[display_name] = enabled

    if "selected_models" in config:
        del config["selected_models"]
        changed = True

    if changed:
        config["model_states"] = states

    return changed
