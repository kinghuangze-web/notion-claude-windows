"""Deleted sensitive content must still be found without echoing its value."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from audit_history import ROOT, audit


class HistoryAuditChecks(unittest.TestCase):
    def test_deleted_secret_is_detected_without_printing_it(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "_tmp", prefix="audit-check-") as directory:
            root = Path(directory)
            def git(*args):
                subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)
            git("init", "--quiet")
            git("config", "user.name", "audit-fixture")
            git("config", "user.email", "audit-fixture@users.noreply.github.com")
            secret = "ghp_" + "Z" * 36
            (root / "removed.txt").write_text(secret, "utf-8")
            git("add", "removed.txt")
            git("commit", "--quiet", "-m", "fixture containing synthetic secret")
            git("rm", "removed.txt")
            git("commit", "--quiet", "-m", "remove synthetic secret")
            result = audit(root, [secret])
            self.assertFalse(result["passed"])
            self.assertEqual(result["commits"], 2)
            self.assertIn("github_token", {x["rule"] for x in result["issues"]})
            self.assertIn("exact_local_private_value", {x["rule"] for x in result["issues"]})
            self.assertNotIn(secret, json.dumps(result))


if __name__ == "__main__":
    unittest.main()
