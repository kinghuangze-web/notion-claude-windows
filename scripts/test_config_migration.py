"""V2 activation must preserve account/route values and back up the prior config."""
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch

import yaml
import manage


class ConfigurationMigrationChecks(unittest.TestCase):
    def test_changed_binary_requires_a_new_build_record(self):
        with tempfile.TemporaryDirectory(dir=manage.ROOT / "_tmp", prefix="build-check-") as directory:
            runtime = Path(directory)
            binary = runtime / "synthetic.bin"
            binary.write_bytes(b"synthetic-v2")
            (runtime / "build-info.json").write_text(json.dumps({"transport": "agent-session-v2", "exe_sha256": hashlib.sha256(binary.read_bytes()).hexdigest()}), "utf-8-sig")
            with patch.object(manage, "RUNTIME", runtime), patch.object(manage, "EXE", binary):
                manage.verify_build()
                binary.write_bytes(b"different-binary")
                with self.assertRaisesRegex(RuntimeError, "build record"):
                    manage.verify_build()

    def test_old_configuration_is_backed_up_and_only_v2_flag_changes(self):
        with tempfile.TemporaryDirectory(dir=manage.ROOT / "_tmp", prefix="config-check-") as directory:
            runtime = Path(directory)
            path = runtime / "config.yaml"
            original = {"server": {"port": "18081", "api_key": "synthetic-only", "accounts_dir": "keep-accounts"}, "proxy": {"default_model": "claude-opus-5-5"}}
            path.write_text(yaml.safe_dump(original), "utf-8")
            before = path.read_bytes()
            with patch.object(manage, "CONFIG", path), patch.object(manage, "RUNTIME", runtime):
                manage.initialize()
                current = manage.config()
                self.assertTrue(current["proxy"].pop("agent_session_v2"))
                self.assertEqual(current, original)
                backups = list((runtime / "private/backups").glob("*/config.yaml"))
                self.assertEqual(len(backups), 1)
                self.assertEqual(backups[0].read_bytes(), before)
                manage.initialize()
                self.assertEqual(len(list((runtime / "private/backups").glob("*/config.yaml"))), 1)


if __name__ == "__main__":
    unittest.main()
