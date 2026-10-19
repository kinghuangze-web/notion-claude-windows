"""Real account-free V2 process lifecycle in an isolated fixture, zero inference."""
import json
from pathlib import Path
import secrets
import shutil
import tempfile
from unittest.mock import patch

import yaml
import full_mode
import full_mode_v2

project = full_mode.ROOT
with tempfile.TemporaryDirectory(dir=project / "_tmp", prefix="full-lifecycle-") as directory:
    root = Path(directory)
    (root / "runtime/private/accounts").mkdir(parents=True)
    (root / "logs").mkdir()
    shutil.copy2(project / "runtime/notion-manager.exe", root / "runtime/notion-manager.exe")
    cfg = {"server": {"host": "127.0.0.1", "port": "8081", "api_key": secrets.token_hex(16),
                       "admin_password": secrets.token_hex(16), "accounts_dir": str(root / "runtime/private/accounts")},
           "proxy": {"agent_thread": True, "require_opus55": True, "default_model": "claude-opus-5-5"}}
    (root / "runtime/config.yaml").write_text(yaml.safe_dump(cfg), "utf-8")
    overrides = {"ROOT": root, "V2": root / "logs", "RUNTIME": root / "runtime/full",
                 "EXE": root / "runtime/notion-manager.exe", "GLOBAL": root / "profile/.claude"}
    with patch.multiple(full_mode_v2, **overrides), patch.object(full_mode, "DEFAULT_GATEWAY", root), patch.object(Path, "home", return_value=root / "profile"):
        record_path = full_mode_v2.RUNTIME / "gateway-process.json"
        try:
            cfg, _, _ = full_mode_v2.prepare()
            first = full_mode_v2.ensure_gateway(cfg)
            assert first.get("available", 0) == 0
            record = json.loads(record_path.read_text("utf-8"))
            full_mode_v2.ensure_gateway(cfg)
            assert json.loads(record_path.read_text("utf-8"))["pid"] == record["pid"]
            full_mode.save(record_path, dict(record, creation_date="wrong"))
            try:
                full_mode_v2.stop_gateway()
            except RuntimeError:
                pass
            else:
                raise AssertionError("Stale PID time was accepted")
            finally:
                full_mode.save(record_path, record)
            full_mode_v2.stop_gateway()
            assert not record_path.exists()
            assert full_mode_v2.process_identity(record["pid"]) is None
            full_mode_v2.ensure_gateway(cfg)
            full_mode_v2.stop_gateway()
            print(json.dumps({"passed": True, "owned_start_reuse_stop_restart": True,
                              "stale_pid_refused": True, "notion_inference_requests": 0}))
        finally:
            full_mode_v2.stop_gateway()
