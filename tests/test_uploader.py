"""
Tests for the CI-Server upload transport

Covers the pure CaptureEvent mapping and the URL-fallback/retry logic with
requests.post mocked out - no real network call, no maix import, matching
the off-device-testable scope the rest of tests/ holds to.

Run with:  python3 -m unittest discover tests
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from utils.config import Config  # noqa: E402
from network.uploader import NetworkUploader, build_capture_event  # noqa: E402


class FakeResponse:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text
        self.ok = 200 <= status_code < 400


class TestBuildCaptureEvent(unittest.TestCase):
    """The pure event -> CI-Server CaptureEvent mapping"""

    def test_maps_the_common_fields(self):
        event = {
            "event_id": "evt-1",
            "timestamp": "2026-09-27T12:00:00+00:00",
            "type": "object_detection",
            "model": "Object Classification",
            "confidence_scores": [0.7, 0.91],
            "data": {"objects": [{"class": "person"}]},
        }

        capture_event = build_capture_event(event, device_id="abc123")

        self.assertEqual(capture_event["source_type"], "capture")
        self.assertEqual(capture_event["source_system"], "ci-maixcam")
        self.assertEqual(capture_event["source_id"], "ci-maixcam:abc123:evt-1")
        self.assertEqual(capture_event["kind"], "object_detection")
        self.assertEqual(capture_event["occurred_at"], "2026-09-27T12:00:00+00:00")
        self.assertEqual(capture_event["observed_at"], "2026-09-27T12:00:00+00:00")
        self.assertEqual(capture_event["title"], "Object Classification")
        self.assertEqual(capture_event["confidence_score"], 0.91)
        self.assertEqual(capture_event["payload"]["device_id"], "abc123")
        self.assertEqual(capture_event["payload"]["objects"], [{"class": "person"}])

    def test_omits_title_when_no_model(self):
        event = {"event_id": "evt-2", "timestamp": "2026-09-27T12:00:00+00:00", "type": "ocr_detection"}
        capture_event = build_capture_event(event, device_id="abc123")
        self.assertNotIn("title", capture_event)

    def test_omits_confidence_score_when_no_scores(self):
        event = {"event_id": "evt-3", "timestamp": "2026-09-27T12:00:00+00:00", "type": "audio_event"}
        capture_event = build_capture_event(event, device_id="abc123")
        self.assertNotIn("confidence_score", capture_event)

    def test_falls_back_to_occurred_at_when_event_id_is_missing(self):
        event = {"timestamp": "2026-09-27T12:00:00+00:00", "type": "object_detection"}
        capture_event = build_capture_event(event, device_id="abc123")
        self.assertEqual(capture_event["source_id"], "ci-maixcam:abc123:2026-09-27T12:00:00+00:00")


class UploaderTestCase(unittest.TestCase):
    """Common uploader-pointed-at-a-fake-server plumbing"""

    def setUp(self):
        self.config_dir = tempfile.mkdtemp()
        config_path = os.path.join(self.config_dir, 'companion_config.json')
        self.config = Config(config_path=config_path)
        self.config.set("network.endpoint_url", "https://ci-server.example")
        self.config.set("network.api_key", "test-api-key")
        self.config.set("network.retry_attempts", 1)
        self.config.set("network.retry_delay_seconds", 0)
        self.uploader = NetworkUploader(self.config)

    def tearDown(self):
        shutil.rmtree(self.config_dir, ignore_errors=True)


class TestPostWithFallback(UploaderTestCase):

    @patch("network.uploader.requests.post")
    def test_succeeds_on_the_bare_path(self, mock_post):
        mock_post.return_value = FakeResponse(200)

        self.assertTrue(self.uploader._post_with_fallback(("/v1/events", "/api/v1/events"), {}))
        mock_post.assert_called_once()
        self.assertEqual(mock_post.call_args.args[0], "https://ci-server.example/v1/events")
        self.assertEqual(mock_post.call_args.kwargs["headers"]["x-api-key"], "test-api-key")

    @patch("network.uploader.requests.post")
    def test_falls_back_to_the_api_prefixed_path_on_404(self, mock_post):
        mock_post.side_effect = [FakeResponse(404), FakeResponse(200)]

        self.assertTrue(self.uploader._post_with_fallback(("/v1/events", "/api/v1/events"), {}))
        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(mock_post.call_args.args[0], "https://ci-server.example/api/v1/events")

    @patch("network.uploader.requests.post")
    def test_fails_when_every_path_404s(self, mock_post):
        mock_post.side_effect = [FakeResponse(404), FakeResponse(404)]
        self.assertFalse(self.uploader._post_with_fallback(("/v1/events", "/api/v1/events"), {}))

    @patch("network.uploader.requests.post")
    def test_a_real_error_status_does_not_try_the_fallback_path(self, mock_post):
        mock_post.return_value = FakeResponse(401, "unauthorized")

        self.assertFalse(self.uploader._post_with_fallback(("/v1/events", "/api/v1/events"), {}))
        mock_post.assert_called_once()

    @patch("network.uploader.requests.post")
    def test_a_connection_error_does_not_try_the_fallback_path(self, mock_post):
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("no route to host")

        self.assertFalse(self.uploader._post_with_fallback(("/v1/events", "/api/v1/events"), {}))
        mock_post.assert_called_once()


class TestUploadSingleFile(UploaderTestCase):

    def _write_session(self, events):
        session_file = os.path.join(self.config_dir, "session_test.json")
        with open(session_file, "w") as f:
            json.dump({"session_id": "s1", "events": events}, f)
        return session_file

    @patch("network.uploader.requests.post")
    def test_uploads_events_then_nudges_finish(self, mock_post):
        session_file = self._write_session([
            {"event_id": "evt-1", "timestamp": "2026-09-27T12:00:00+00:00",
             "type": "object_detection", "model": "Object Classification", "data": {}},
        ])
        mock_post.return_value = FakeResponse(200)

        self.assertTrue(self.uploader._upload_single_file(session_file))

        called_urls = [call.args[0] for call in mock_post.call_args_list]
        self.assertIn("https://ci-server.example/v1/events", called_urls)
        self.assertIn("https://ci-server.example/v1/ingest/finish", called_urls)

    @patch("network.uploader.requests.post")
    def test_empty_session_is_a_no_op_success(self, mock_post):
        session_file = self._write_session([])
        self.assertTrue(self.uploader._upload_single_file(session_file))
        mock_post.assert_not_called()

    @patch("network.uploader.requests.post")
    def test_server_failure_is_reported_as_failure(self, mock_post):
        session_file = self._write_session([
            {"event_id": "evt-1", "timestamp": "2026-09-27T12:00:00+00:00",
             "type": "object_detection", "data": {}},
        ])
        mock_post.return_value = FakeResponse(500, "boom")

        self.assertFalse(self.uploader._upload_single_file(session_file))


if __name__ == '__main__':
    unittest.main()
