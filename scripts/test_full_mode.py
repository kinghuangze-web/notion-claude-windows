"""Full entry invariants; synthetic settings, no accounts or inference."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml
import full_mode
import full_mode_v2


class FullModeChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=full_mode.ROOT / "_tmp", prefix="full-check-")
        self.root = Path(self.temp.name)
        (self.root / "runtime").mkdir()
        (self.root / "logs").mkdir()
        (self.root / "scripts").mkdir()
        (self.root / "scripts/link_directory.ps1").write_text((full_mode.ROOT / "scripts/link_directory.ps1").read_text("utf-8"), "utf-8")
        self.user = self.root / "profile/.claude"
        self.user.mkdir(parents=True)
        self.cfg = {"server": {"host": "127.0.0.1", "port": "8081", "api_key": "synthetic-only"},
                    "proxy": {"agent_thread": True, "require_opus55": True, "default_model": "claude-opus-5-5"}}
        (self.root / "runtime/config.yaml").write_text(yaml.safe_dump(self.cfg), "utf-8")
        self.patches = [patch.object(full_mode, "ROOT", self.root),
                        patch.object(full_mode, "DEFAULT_GATEWAY", self.root),
                        patch.object(full_mode_v2, "ROOT", self.root),
                        patch.object(full_mode_v2, "RUNTIME", self.root / "runtime/full"),
                        patch.object(full_mode_v2, "V2", self.root / "logs"),
                        patch.object(full_mode_v2, "GLOBAL", self.user)]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def test_native_prompt_tools_and_process_route(self):
        with patch.dict(os.environ, {"NOTION_CLAUDE_EXE": "synthetic-claude.exe", "ANTHROPIC_AUTH_TOKEN": "synthetic-only", "CLAUDE_CODE_USE_BEDROCK": "1"}):
            args, env, cfg, _ = full_mode_v2.launch_spec(["--version"])
            self.assertNotIn("--bare", args)
            self.assertNotIn("--tools", args)
            self.assertNotIn("--system-prompt", args)
            self.assertEqual(args[args.index("--setting-sources") + 1], "user,project,local")
            self.assertEqual(env["ANTHROPIC_BASE_URL"], "http://127.0.0.1:8082")
            self.assertNotIn("ANTHROPIC_AUTH_TOKEN", env)
            self.assertNotIn("CLAUDE_CODE_USE_BEDROCK", env)
            self.assertEqual(cfg["server"]["port"], "8082")
            route = json.loads(Path(args[args.index("--settings") + 1]).read_text("utf-8"))
            self.assertEqual(route["env"]["ANTHROPIC_MODEL"], "claude-opus-5-5")
            self.assertIn("ANTHROPIC_AUTH_TOKEN", os.environ)
        original = yaml.safe_load((self.root / "runtime/config.yaml").read_text("utf-8"))
        self.assertEqual(original, self.cfg)

    def test_unsupported_prompt_tools_and_model_overrides_fail(self):
        for args in (["--bare"], ["--system-prompt", "short"], ["--tools=Read"], ["--model", "auto"]):
            with self.assertRaises(RuntimeError):
                full_mode.launch_spec(self.root, args)

    def test_wrong_process_never_stopped_or_adopted(self):
        full_mode.save(full_mode_v2.RUNTIME / "gateway-process.json", {"pid": 999, "creation_date": "old"})
        current = {"ExecutablePath": "unrelated.exe", "CreationDate": "new"}
        with patch.object(full_mode_v2, "process_identity", return_value=current), patch.object(full_mode_v2.subprocess, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "ownership"):
                full_mode_v2.stop_gateway()
            with self.assertRaisesRegex(RuntimeError, "ownership"):
                full_mode_v2.ensure_gateway(self.cfg)
            run.assert_not_called()

    def test_stale_record_removed_without_kill(self):
        record = full_mode_v2.RUNTIME / "gateway-process.json"
        full_mode.save(record, {"pid": 999})
        with patch.object(full_mode_v2, "process_identity", return_value=None), patch.object(full_mode_v2.subprocess, "run") as run:
            full_mode_v2.stop_gateway()
            self.assertFalse(record.exists())
            run.assert_not_called()

    def test_gateway_does_not_inherit_foreign_account_or_logging_overrides(self):
        foreign = {name: "synthetic-only" for name in ("NOTION_TOKEN_V2_2", "NOTION_SPACE_ID", "ACCOUNTS_DIR", "NOTION_API_BASE", "API_LOG_INPUT", "DEBUG_LOGGING")}
        with patch.dict(os.environ, foreign):
            env = full_mode_v2.gateway_environment()
            self.assertFalse(set(foreign) & env.keys())
            self.assertEqual(env["NOTION_AGENT_SESSION_DIR"], str(full_mode_v2.RUNTIME / "sessions"))
            self.assertEqual(os.environ["NOTION_TOKEN_V2_2"], "synthetic-only")

    def test_discovery_keeps_user_files_and_does_not_copy_oauth(self):
        (self.user / "skills").mkdir()
        (self.user / "skills/keep.txt").write_text("preserve", "utf-8")
        (self.user / "settings.json").write_text('{"permissions":{}}', "utf-8")
        (self.user / ".credentials.json").write_text('{"oauth":"synthetic-only"}', "utf-8")
        (self.user.parent / ".claude.json").write_text('{"mcpServers":{"synthetic":{}},"oauth":"synthetic-only"}', "utf-8")
        with patch.object(Path, "home", return_value=self.user.parent):
            _, config_dir, inherited = full_mode_v2.prepare()
        self.assertIn("skills", inherited)
        self.assertEqual((config_dir / "skills").resolve(), (self.user / "skills").resolve())
        self.assertEqual((self.user / "skills/keep.txt").read_text("utf-8"), "preserve")
        self.assertFalse((config_dir / ".credentials.json").exists())
        self.assertEqual(json.loads((config_dir / ".claude.json").read_text("utf-8")), {"mcpServers": {"synthetic": {}}})


if __name__ == "__main__":
    unittest.main()
