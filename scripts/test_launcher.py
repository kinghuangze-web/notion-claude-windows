"""Native discovery, fixed routing and prompt/tool preservation without inference."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import claude_full


class NativeLauncherChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=claude_full.ROOT / "_tmp", prefix="native-check-")
        self.root = Path(self.temp.name)
        (self.root / "runtime").mkdir()
        self.cfg = {"server": {"host": "127.0.0.1", "port": "8081", "api_key": "synthetic-only"},
                    "proxy": {"agent_thread": True, "agent_session_v2": True, "require_opus55": True, "default_model": "claude-opus-5-5"}}
        self.patches = [patch.object(claude_full, "ROOT", self.root), patch.object(claude_full.manage, "config", return_value=self.cfg)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.temp.cleanup()

    def test_native_discovery_and_parent_environment_are_preserved(self):
        inherited = {"NOTION_CLAUDE_EXE": "native-claude.exe", "APPDATA": "native-appdata",
                     "CLAUDE_CONFIG_DIR": "custom-user-config", "ANTHROPIC_AUTH_TOKEN": "foreign-synthetic"}
        with patch.dict(os.environ, inherited):
            args, env = claude_full.launch_spec(["--version"])
            self.assertNotIn("--bare", args)
            self.assertNotIn("--tools", args)
            self.assertNotIn("--system-prompt", args)
            self.assertEqual(env["APPDATA"], inherited["APPDATA"])
            self.assertEqual(env["CLAUDE_CONFIG_DIR"], inherited["CLAUDE_CONFIG_DIR"])
            self.assertEqual(env["ANTHROPIC_BASE_URL"], "http://127.0.0.1:8081")
            self.assertEqual(env["ANTHROPIC_AUTH_TOKEN"], "synthetic-only")
            self.assertEqual(os.environ["ANTHROPIC_AUTH_TOKEN"], "foreign-synthetic")
            route = json.loads(Path(args[args.index("--settings") + 1]).read_text("utf-8"))
            self.assertEqual(route["env"]["ANTHROPIC_API_KEY"], "synthetic-only")

    def test_no_alternate_config_directory_is_created(self):
        with patch.dict(os.environ, {"NOTION_CLAUDE_EXE": "native-claude.exe"}):
            args, env = claude_full.launch_spec([])
        self.assertFalse((self.root / "runtime/claude").exists())
        self.assertEqual(args[args.index("--setting-sources") + 1], "user,project,local")

    def test_slim_prompt_tool_or_route_overrides_are_rejected(self):
        for args in (["--bare"], ["--tools=Read"], ["--system-prompt", "short"], ["--model=auto"], ["--settings", "foreign.json"]):
            with self.assertRaises(RuntimeError):
                claude_full.launch_spec(args)

    def test_legacy_gateway_configuration_is_rejected(self):
        self.cfg["proxy"]["agent_session_v2"] = False
        with self.assertRaisesRegex(RuntimeError, "V2"):
            claude_full.launch_spec([])


if __name__ == "__main__":
    unittest.main()
