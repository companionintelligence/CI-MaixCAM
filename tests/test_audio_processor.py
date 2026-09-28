"""
Tests for AudioProcessor's pure audio-level/keyword-selection math and
off-device fallback

maix.audio / maix.nn are only importable on real MaixCAM hardware, so off
device AudioProcessor must initialize without raising, report itself
unloaded, and have process()/play() return safely forever - never touching
a real microphone, speaker or Speech model.

Run with:  python3 -m unittest tests/test_audio_processor.py -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from ai.audio_processor import (  # noqa: E402
    AudioProcessor,
    build_audio_activity_event,
    build_voice_recognition_event,
    compute_audio_level,
    decode_pcm_s16le,
    mean_abs_amplitude,
    normalize_level,
    pick_best_keyword,
)


class TestMeanAbsAmplitude(unittest.TestCase):
    """The pure mean-abs-amplitude helper"""

    def test_empty_list_is_silence(self):
        self.assertEqual(mean_abs_amplitude([]), 0.0)

    def test_none_is_silence(self):
        self.assertEqual(mean_abs_amplitude(None), 0.0)

    def test_all_zero_samples_is_silence(self):
        self.assertEqual(mean_abs_amplitude([0, 0, 0]), 0.0)

    def test_averages_absolute_values(self):
        self.assertEqual(mean_abs_amplitude([-100, 100]), 100.0)
        self.assertEqual(mean_abs_amplitude([10, -20, 30]), 20.0)

    def test_single_sample(self):
        self.assertEqual(mean_abs_amplitude([-5000]), 5000.0)


class TestNormalizeLevel(unittest.TestCase):
    """The pure raw-amplitude -> 0.0-1.0 level helper"""

    def test_zero_is_zero(self):
        self.assertEqual(normalize_level(0), 0.0)

    def test_full_scale_is_one(self):
        self.assertEqual(normalize_level(32768.0), 1.0)

    def test_half_scale_is_half(self):
        self.assertEqual(normalize_level(16384.0), 0.5)

    def test_clamps_above_one(self):
        self.assertEqual(normalize_level(100000.0), 1.0)

    def test_clamps_below_zero(self):
        self.assertEqual(normalize_level(-50.0), 0.0)

    def test_non_positive_full_scale_is_zero_not_a_crash(self):
        self.assertEqual(normalize_level(100.0, full_scale=0), 0.0)
        self.assertEqual(normalize_level(100.0, full_scale=-10), 0.0)


class TestComputeAudioLevel(unittest.TestCase):
    """The combined mean-abs -> normalized-level helper process() gates on"""

    def test_silence_is_zero(self):
        self.assertEqual(compute_audio_level([0] * 10), 0.0)

    def test_empty_is_zero(self):
        self.assertEqual(compute_audio_level([]), 0.0)

    def test_half_scale_samples(self):
        self.assertEqual(compute_audio_level([16384] * 5), 0.5)

    def test_over_scale_samples_are_clamped(self):
        self.assertEqual(compute_audio_level([40000, -40000]), 1.0)

    def test_mixed_polarity_samples(self):
        # mean(|100|, |-300|) = 200, / 32768
        self.assertAlmostEqual(compute_audio_level([100, -300]), 200.0 / 32768.0)


class TestDecodePcmS16le(unittest.TestCase):
    """The pure little-endian signed-16-bit PCM byte decoder"""

    def test_empty_bytes_decodes_to_empty_list(self):
        self.assertEqual(decode_pcm_s16le(b''), [])

    def test_none_decodes_to_empty_list(self):
        self.assertEqual(decode_pcm_s16le(None), [])

    def test_decodes_zero(self):
        self.assertEqual(decode_pcm_s16le(b'\x00\x00'), [0])

    def test_decodes_max_positive(self):
        self.assertEqual(decode_pcm_s16le(b'\xff\x7f'), [32767])

    def test_decodes_max_negative(self):
        self.assertEqual(decode_pcm_s16le(b'\x00\x80'), [-32768])

    def test_decodes_multiple_samples_in_order(self):
        data = b'\x00\x00' + b'\xff\x7f' + b'\x00\x80'
        self.assertEqual(decode_pcm_s16le(data), [0, 32767, -32768])

    def test_drops_a_trailing_odd_byte_instead_of_raising(self):
        data = b'\x00\x00' + b'\x01'
        self.assertEqual(decode_pcm_s16le(data), [0])

    def test_single_trailing_byte_alone_decodes_to_empty_list(self):
        self.assertEqual(decode_pcm_s16le(b'\x01'), [])


class TestPickBestKeyword(unittest.TestCase):
    """The pure kws() score -> (label, confidence) classification heuristic"""

    def test_empty_scores_is_none(self):
        self.assertIsNone(pick_best_keyword([], ["hello"], [0.5]))

    def test_empty_kw_table_is_none(self):
        self.assertIsNone(pick_best_keyword([0.9], [], [0.5]))

    def test_picks_the_highest_scoring_keyword_that_clears_its_gate(self):
        result = pick_best_keyword([0.2, 0.9, 0.4], ["yes", "no", "stop"], [0.5, 0.5, 0.5])
        self.assertEqual(result, ("no", 0.9))

    def test_returns_none_when_best_score_does_not_clear_its_gate(self):
        result = pick_best_keyword([0.2, 0.3], ["yes", "no"], [0.5, 0.5])
        self.assertIsNone(result)

    def test_defaults_to_a_flat_half_gate_when_kw_gate_is_omitted(self):
        self.assertIsNone(pick_best_keyword([0.4], ["yes"], None))
        self.assertEqual(pick_best_keyword([0.6], ["yes"], None), ("yes", 0.6))

    def test_uses_the_flat_default_gate_for_a_keyword_missing_its_own(self):
        # kw_gate shorter than scores/kw_table -> missing entries default to 0.5
        result = pick_best_keyword([0.9], ["yes"], [])
        self.assertEqual(result, ("yes", 0.9))

    def test_clamps_confidence_above_one(self):
        result = pick_best_keyword([1.5], ["yes"], [0.5])
        self.assertEqual(result, ("yes", 1.0))

    def test_best_index_out_of_range_of_kw_table_is_none(self):
        # 3 scores but only 1 keyword: index 1 (the highest score) has no
        # matching label, so this must not raise or fabricate a label.
        self.assertIsNone(pick_best_keyword([0.1, 0.99, 0.2], ["only_one"], [0.5]))


class TestBuildAudioActivityEvent(unittest.TestCase):
    """The pure 'audio_event' unified-schema constructor"""

    def test_matches_the_unified_detection_event_schema(self):
        event = build_audio_activity_event(
            level=0.42, raw_level=13762.56, duration_ms=50,
            timestamp=1000, processing_time_ms=2,
        )
        self.assertEqual(event, {
            "timestamp": 1000,
            "type": "audio_event",
            "model": "Audio Recording",
            "processing_time_ms": 2,
            "detections": [
                {
                    "label": "audio_activity",
                    "confidence": 0.42,
                    "bbox": None,
                    "level": 13762.56,
                    "duration_ms": 50,
                }
            ],
        })


class TestBuildVoiceRecognitionEvent(unittest.TestCase):
    """The pure 'voice_recognition' unified-schema constructor"""

    def test_matches_the_unified_detection_event_schema(self):
        event = build_voice_recognition_event(
            label="stop", confidence=0.83, timestamp=2000, processing_time_ms=5,
        )
        self.assertEqual(event, {
            "timestamp": 2000,
            "type": "voice_recognition",
            "model": "Real-time Voice Recognition",
            "processing_time_ms": 5,
            "detections": [
                {
                    "label": "stop",
                    "confidence": 0.83,
                    "bbox": None,
                }
            ],
        })


class TestOffDeviceFallback(unittest.TestCase):
    """No maix package is installed in this test environment"""

    def _model_config(self, **overrides):
        config = {
            "processing_interval": 20,
            "priority": 7,
            "enabled": True,
        }
        config.update(overrides)
        return config

    def test_initializes_without_raising_without_the_maix_sdk(self):
        processor = AudioProcessor(self._model_config())
        self.assertFalse(processor.loaded)
        self.assertFalse(processor.voice_loaded)

    def test_empty_model_config_is_non_fatal(self):
        processor = AudioProcessor({})
        self.assertFalse(processor.loaded)
        self.assertIsNone(processor.process(img=None))

    def test_none_model_config_is_non_fatal(self):
        processor = AudioProcessor(None)
        self.assertFalse(processor.loaded)
        self.assertIsNone(processor.process(img=None))

    def test_start_recording_fails_closed_without_the_maix_sdk(self):
        processor = AudioProcessor(self._model_config())
        self.assertFalse(processor.start_recording())
        self.assertFalse(processor.recording)

    def test_stop_recording_is_always_safe(self):
        processor = AudioProcessor(self._model_config())
        processor.stop_recording()  # never started - must not raise
        self.assertFalse(processor.recording)

    def test_process_returns_none_when_nothing_is_armed_or_enabled(self):
        processor = AudioProcessor(self._model_config(enabled=False))
        self.assertIsNone(processor.process(img=None))

    def test_process_returns_none_for_voice_recognition_without_the_maix_sdk(self):
        processor = AudioProcessor(
            self._model_config(enabled=True),
            voice_model_path="/root/models/am_3332_192_int8.mud",
            keywords=["hello"],
        )
        self.assertIsNone(processor.process(img=None))
        self.assertFalse(processor.voice_loaded)

    def test_voice_recognition_without_a_model_or_keywords_logs_one_warning(self):
        processor = AudioProcessor(self._model_config(enabled=True))
        with self.assertLogs('CompanionCapture.AudioProcessor', level='WARNING') as logs:
            self.assertIsNone(processor.process(img=None))
            self.assertIsNone(processor.process(img=None))
        # Documented no-op is logged once, not spammed every call.
        warnings = [line for line in logs.output if 'WARNING' in line]
        self.assertEqual(len(warnings), 1)
        self.assertIn('documented no-op', warnings[0])

    def test_play_fails_closed_without_the_maix_sdk(self):
        processor = AudioProcessor(self._model_config())
        self.assertFalse(processor.play("/root/test.wav"))

    def test_cleanup_is_a_harmless_no_op(self):
        processor = AudioProcessor(self._model_config())
        processor.cleanup()  # must not raise
        self.assertFalse(processor.recording)

    def test_kwargs_override_the_defaults(self):
        processor = AudioProcessor(
            self._model_config(), sample_rate=48000, channel=2,
            chunk_ms=100, activity_threshold=0.1,
        )
        self.assertEqual(processor.sample_rate, 48000)
        self.assertEqual(processor.channel, 2)
        self.assertEqual(processor.chunk_ms, 100)
        self.assertEqual(processor.activity_threshold, 0.1)


if __name__ == '__main__':
    unittest.main()
