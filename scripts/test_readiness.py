"""State transitions stay distinct from actual inference verification."""
import unittest
from unittest.mock import Mock, patch

import manage


class ReadinessChecks(unittest.TestCase):
    def setUp(self):
        self.build_patch = patch.object(manage, "verify_build")
        self.build_patch.start()

    def tearDown(self):
        self.build_patch.stop()

    def check_state(self, health, expected, code, model_status=200):
        cfg = {"server": {"host": "127.0.0.1", "port": "18081", "api_key": "synthetic-test-key"},
               "proxy": {"default_model": "claude-opus-5-5", "require_opus55": True, "agent_thread": True, "agent_session_v2": True}}
        with patch.object(manage, "CONFIG", Mock(is_file=lambda: True)), patch.object(manage, "EXE", Mock(is_file=lambda: True)), \
             patch.object(manage, "config", return_value=cfg), patch.object(manage, "owned_process", return_value={"pid": 1, "transport": "agent-session-v2"}), \
             patch.object(manage, "request", side_effect=[(200, health), (model_status, b'{}')]):
            value, actual = manage.readiness()
        self.assertEqual(value["state"], expected)
        self.assertEqual(actual, code)
        self.assertFalse(value["notion_inference_verified"])
        self.assertNotIn("api_key", value)
        self.assertNotIn("account_details", value)

    def test_imported_but_unusable_account_still_requires_user(self):
        self.check_state(b'{"available":0,"accounts":2,"email":"synthetic@example.invalid"}', "awaiting_account", 3)

    def test_available_account_is_only_ready_for_acceptance(self):
        self.check_state(b'{"available":1}', "ready_for_acceptance", 0)

    def test_bad_gateway_auth_does_not_become_ready(self):
        self.check_state(b'{"available":1}', "gateway_unhealthy", 4, 401)

    def test_missing_config_does_not_request_network(self):
        with patch.object(manage, "CONFIG", Mock(is_file=lambda: False)), patch.object(manage, "request") as request:
            value, code = manage.readiness()
        self.assertEqual((value["state"], code), ("awaiting_setup", 2))
        request.assert_not_called()

    def test_old_running_gateway_cannot_be_reported_ready(self):
        cfg = {"server": {"host": "127.0.0.1"}, "proxy": {"default_model": "claude-opus-5-5", "require_opus55": True, "agent_thread": True, "agent_session_v2": True}}
        with patch.object(manage, "CONFIG", Mock(is_file=lambda: True)), patch.object(manage, "EXE", Mock(is_file=lambda: True)), patch.object(manage, "config", return_value=cfg), patch.object(manage, "owned_process", return_value={"pid": 1}), patch.object(manage, "request") as request:
            state, code = manage.readiness()
            self.assertEqual((state["state"], code), ("gateway_needs_v2_restart", 4))
            request.assert_not_called()

    def test_unverified_binary_cannot_report_ready(self):
        with patch.object(manage, "CONFIG", Mock(is_file=lambda: True)), patch.object(manage, "EXE", Mock(is_file=lambda: True)), patch.object(manage, "verify_build", side_effect=RuntimeError("old build")), patch.object(manage, "request") as request:
            state, code = manage.readiness()
            self.assertEqual((state["state"], code), ("gateway_needs_rebuild", 4))
            request.assert_not_called()

    def test_reused_pid_returns_failure_state_without_network(self):
        cfg = {"server": {"host": "127.0.0.1"}, "proxy": {"default_model": "claude-opus-5-5", "require_opus55": True, "agent_thread": True}}
        with patch.object(manage, "CONFIG", Mock(is_file=lambda: True)), patch.object(manage, "EXE", Mock(is_file=lambda: True)), \
             patch.object(manage, "config", return_value=cfg), patch.object(manage, "owned_process", side_effect=RuntimeError("reused PID")), \
             patch.object(manage, "request") as request:
            value, code = manage.readiness()
        self.assertEqual((value["state"], code), ("process_identity_mismatch", 4))
        request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
