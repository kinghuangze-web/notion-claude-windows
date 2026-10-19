"""The ordinary dashboard route must explicitly activate persistent V2 transport."""
import os
import unittest
from unittest.mock import patch

import manage


class GatewayEnvironmentChecks(unittest.TestCase):
    def test_opt_in_activates_the_ordinary_route_without_changing_parent(self):
        with patch.object(manage, "config", return_value={"proxy": {"agent_session_v2": True}}), patch.dict(os.environ, {"ANTHROPIC_BASE_URL": "http://synthetic.invalid", "NOTION_AGENT_SESSION_DIR": "foreign", "NOTION_TOKEN_V2_2": "synthetic-only"}):
            child = manage.gateway_environment()
            self.assertEqual(child["NOTION_AGENT_SESSION_DIR"], str(manage.RUNTIME / "agent-sessions-v2"))
            self.assertNotIn("NOTION_TOKEN_V2_2", child)
            self.assertEqual(os.environ["NOTION_AGENT_SESSION_DIR"], "foreign")
            self.assertEqual(os.environ["ANTHROPIC_BASE_URL"], "http://synthetic.invalid")

    def test_legacy_configuration_cannot_silently_start(self):
        with patch.object(manage, "config", return_value={"proxy": {}}), patch.dict(os.environ, {"NOTION_AGENT_SESSION_DIR": "foreign"}):
            with self.assertRaisesRegex(RuntimeError, "V2"):
                manage.gateway_environment()


if __name__ == "__main__":
    unittest.main()
