"""Focused regression checks for real launcher boundaries on this Windows host."""
import os
from pathlib import Path
import tempfile
import unittest

import claude_notion


class LauncherChecks(unittest.TestCase):
    def test_inherited_provider_removed_and_d_drive_state(self):
        before = os.environ.copy()
        os.environ["ANTHROPIC_BASE_URL"] = "https://unrelated-provider.invalid"
        os.environ["ANTHROPIC_AUTH_TOKEN"] = "synthetic-test-value"
        os.environ["CLAUDE_CODE_USE_BEDROCK"] = "1"
        try:
            args, child_env = claude_notion.launch_spec(["--version"])
            self.assertEqual(child_env["ANTHROPIC_BASE_URL"], "http://127.0.0.1:8081")
            self.assertNotIn("ANTHROPIC_AUTH_TOKEN", child_env)
            self.assertNotIn("CLAUDE_CODE_USE_BEDROCK", child_env)
            self.assertEqual(child_env["CLAUDE_CONFIG_DIR"], str(claude_notion.ROOT / "runtime" / "claude"))
            self.assertEqual(child_env["CLAUDE_CODE_TMPDIR"], str(claude_notion.ROOT / "_tmp"))
            self.assertEqual(child_env["DISABLE_UPDATES"], "1")
            self.assertEqual(args[args.index("--model") + 1], "claude-opus-5-5")
            self.assertEqual(child_env["ANTHROPIC_DEFAULT_HAIKU_MODEL"], "claude-opus-5-5")
            self.assertEqual(args[args.index("--permission-mode") + 1], "acceptEdits")
            self.assertTrue(Path(args[0]).is_file())
            self.assertIn("--bare", args)
            self.assertEqual(args[args.index("--setting-sources") + 1], "")
            self.assertEqual(os.environ["ANTHROPIC_BASE_URL"], "https://unrelated-provider.invalid")
        finally:
            os.environ.clear()
            os.environ.update(before)

    def test_unsupported_fixed_model_rejected(self):
        for options in (["--model", "auto"], ["--model=opus"], ["--model=claude-sonnet-5-5"]):
            with self.assertRaisesRegex(RuntimeError, "only fixed Opus 5.5"):
                claude_notion.launch_spec(options)

    def test_available_tools_are_restricted_before_native_dispatch(self):
        args, _ = claude_notion.launch_spec(["--local-tools", "Read,Edit", "--version"])
        self.assertEqual(args[args.index("--tools") + 1], "Read,Edit")
        self.assertEqual(args.count("--tools"), 1)
        self.assertNotIn("--local-tools", args)
        with self.assertRaisesRegex(RuntimeError, "unsupported tool"):
            claude_notion.launch_spec(["--local-tools", "Agent"])
        with self.assertRaisesRegex(RuntimeError, "unsupported tool"):
            claude_notion.launch_spec(["--local-tools", "Write"])

    def test_chinese_skill_is_read_as_utf8(self):
        original = Path.cwd()
        with tempfile.TemporaryDirectory(prefix="launcher-", dir=claude_notion.ROOT / "_tmp") as temporary:
            skill = Path(temporary) / ".claude" / "skills" / "demo" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: 中文技能\ndescription: 读取中文笔记\n---\n测试\n", encoding="utf-8")
            try:
                os.chdir(temporary)
                args, _ = claude_notion.launch_spec([])
                prompt = args[args.index("--append-system-prompt") + 1]
                self.assertIn("中文技能", prompt)
                self.assertIn("读取中文笔记", prompt)
                self.assertIn(str(skill.resolve()), prompt)
            finally:
                os.chdir(original)


if __name__ == "__main__":
    unittest.main()
