"""Exercise fresh install, 1.0.x upgrade and repeated setup on disposable Git trees."""
from pathlib import Path
import subprocess
import tempfile
import unittest

import apply_patches

ROOT = apply_patches.ROOT


class PatchChecks(unittest.TestCase):
    def test_fresh_upgrade_and_idempotence(self):
        patches = [ROOT / "patches/opus55.patch", ROOT / "patches/full-mode-v2.patch"]
        with tempfile.TemporaryDirectory(dir=ROOT / "_tmp", prefix="patch-check-") as directory:
            source = Path(directory) / "source"
            def git(*args):
                return subprocess.run(["git", *map(str, args)], check=True, capture_output=True)
            git("clone", "--shared", "--no-checkout", ROOT / "_source", source)
            git("-C", source, "-c", "core.autocrlf=false", "checkout", "--detach", "2d6d3dc2fa74f929bd9a8ebd3c1569f5dcca1b88")
            self.assertEqual(apply_patches.apply(source, patches), "applied")
            self.assertEqual(apply_patches.apply(source, patches), "already_applied")
            git("-C", source, "apply", "--reverse", patches[1])
            self.assertEqual(apply_patches.apply(source, patches), "applied")
            self.assertEqual(apply_patches.apply(source, patches), "already_applied")
            for name in ("agent_thread.go", "agent_session_v2.go", "anthropic.go", "tools.go"):
                self.assertEqual((source / "internal/proxy" / name).read_bytes(), (ROOT / "_source/internal/proxy" / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
