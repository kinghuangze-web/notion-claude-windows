"""Exercise the real gateway lifecycle in a separate disposable D-drive fixture."""
import json
from pathlib import Path
import shutil
import tempfile

import yaml

import manage

project_root = manage.ROOT
binary = manage.EXE
fixture_parent = (project_root / "_tmp").resolve()
with tempfile.TemporaryDirectory(prefix="lifecycle-", dir=fixture_parent) as directory:
    fixture = Path(directory).resolve()
    if not fixture.is_relative_to(fixture_parent):
        raise RuntimeError("Lifecycle fixture escaped the disposable project directory.")
    for name in ("runtime", "logs", "evidence"):
        (fixture / name).mkdir()
    manage.ROOT = fixture
    manage.RUNTIME = fixture / "runtime"
    manage.EXE = manage.RUNTIME / "notion-manager.exe"
    manage.CONFIG = manage.RUNTIME / "config.yaml"
    manage.PROCESS_FILE = manage.RUNTIME / "gateway-process.json"
    shutil.copy2(binary, manage.EXE)
    manage.initialize()
    cfg = manage.config()
    cfg["server"]["port"] = "18081"
    manage.CONFIG.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    try:
        manage.start()
        first = manage.owned_process()
        manage.start()
        assert manage.owned_process()["pid"] == first["pid"], "Repeated start created a duplicate process"
        manage.verify_local()
        # A stale creation time must fail closed without stopping the process.
        invalid = dict(first, creation_date="/Date(0)/")
        manage.save_json(manage.PROCESS_FILE, invalid)
        try:
            manage.owned_process()
        except RuntimeError as error:
            assert "reused" in str(error)
        else:
            raise AssertionError("Stale PID creation time was accepted")
        finally:
            manage.save_json(manage.PROCESS_FILE, first)
        manage.stop()
        assert manage.process_info(first["pid"]) is None
        assert not manage.PROCESS_FILE.exists()
        manage.start()
        second = manage.owned_process()
        assert manage.request("/v1/models", cfg["server"]["api_key"])[0] == 200
        manage.stop()
        assert manage.process_info(second["pid"]) is None
        outcome = {
            "passed": True, "fixture_port": 18081,
            "real_executable_started": True, "idempotent_start": True,
            "stale_pid_refused": True, "stop_verified": True, "restart_verified": True,
            "notion_inference_requests": 0,
        }
        manage.save_json(project_root / "evidence" / "lifecycle-verification.json", outcome)
        print(json.dumps(outcome, indent=2))
    finally:
        if manage.owned_process():
            manage.stop()
