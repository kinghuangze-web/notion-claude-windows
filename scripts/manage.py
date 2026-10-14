"""Local project lifecycle; credentials stay under runtime, evidence is redacted."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import time
import urllib.error
import urllib.request

import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
EXE = RUNTIME / "notion-manager.exe"
CONFIG = RUNTIME / "config.yaml"
PROCESS_FILE = RUNTIME / "gateway-process.json"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def config():
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def request(path, key=None):
    port = int(config()["server"]["port"])
    headers = {"Authorization": "Bearer " + key} if key else {}
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", headers=headers)
    try:
        with OPENER.open(req, timeout=5) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def initialize():
    if CONFIG.exists():
        print("Configuration already exists; preserved.")
        return
    private = RUNTIME / "private"
    (private / "accounts").mkdir(parents=True, exist_ok=True)
    password = secrets.token_urlsafe(20)
    cfg = {
        "server": {
            "host": "127.0.0.1", "port": "8081",
            "accounts_dir": str(private / "accounts"),
            "token_file": str(private / "token.txt"),
            "api_key": "sk-" + secrets.token_hex(16),
            "admin_password": password,
            "debug_logging": False, "api_log_input": False, "api_log_output": False,
            "notion_log_request": False, "notion_log_response": False,
            "dump_api_input": False,
        },
        "proxy": {
            "agent_thread": True,
            "require_opus55": True,
            "notion_api_base": "https://app.notion.com/api/v3",
            "default_model": "claude-opus-5-5",
        },
        "timeouts": {"inference_timeout": 120, "api_timeout": 30, "tls_dial_timeout": 30},
        "register": {"history_file": str(private / "accounts" / ".register_history.json")},
    }
    with CONFIG.open("x", encoding="utf-8") as output:
        yaml.safe_dump(cfg, output, allow_unicode=True, sort_keys=False)
    with (private / "admin-password.txt").open("x", encoding="utf-8") as output:
        output.write(password + "\n")
    print("Configuration created. Dashboard password is in runtime/private/admin-password.txt.")


def process_info(pid):
    # PID is an integer, never interpolate untrusted command text into PowerShell.
    command = (
        f"$p = Get-CimInstance Win32_Process -Filter 'ProcessId = {int(pid)}'; "
        "if ($p) { $p | Select-Object ProcessId,ExecutablePath,CreationDate | ConvertTo-Json -Compress }"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", command],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if result.returncode:
        raise RuntimeError("Cannot inspect the recorded process; refusing to stop an unknown process.")
    return json.loads(result.stdout) if result.stdout.strip() else None


def owned_process():
    if not PROCESS_FILE.exists():
        return None
    record = json.loads(PROCESS_FILE.read_text(encoding="utf-8"))
    current = process_info(record["pid"])
    if current is None:
        return None
    if Path(current.get("ExecutablePath") or "").resolve() != EXE.resolve():
        raise RuntimeError("Recorded PID now belongs to a different executable; refusing to touch it.")
    if current["CreationDate"] != record["creation_date"]:
        raise RuntimeError("Recorded PID has been reused; refusing to touch it.")
    return record


def start():
    if not EXE.is_file():
        raise RuntimeError("Windows gateway executable has not been built.")
    initialize()
    key = config()["server"]["api_key"]
    existing = owned_process()
    if existing:
        code, _ = request("/v1/models", key)
        if code != 200:
            raise RuntimeError("Recorded gateway is running but not healthy; inspect logs/gateway.log.")
        print(f"Project gateway already running: PID {existing['pid']}.")
        return
    port = int(config()["server"]["port"])
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", port))
    child_env = os.environ.copy()
    # The project config is the only source for routing, logging and accounts.
    for name in ("HOST", "PORT", "API_KEY", "ACCOUNTS_DIR", "TOKEN_FILE", "LOG_FILE",
                 "DEBUG_LOGGING", "API_LOG_INPUT", "API_LOG_OUTPUT", "NOTION_LOG_REQUEST",
                 "NOTION_LOG_RESPONSE", "DUMP_API_INPUT", "AGENT_THREAD", "NOTION_API_BASE",
                 "DEFAULT_MODEL", "NOTION_PROXY", "INFERENCE_TIMEOUT", "API_TIMEOUT",
                 "TLS_DIAL_TIMEOUT", "NOTION_TOKEN_V2"):
        child_env.pop(name, None)
    for name in list(child_env):
        if name.startswith(("NOTION_TOKEN_V2_", "NOTION_SPACE_ID", "NOTION_ACTIVE_USER_ID",
                            "NOTION_EXPECTED_EMAIL")):
            child_env.pop(name, None)
    log_path = ROOT / "logs" / "gateway.log"
    with log_path.open("ab") as output:
        process = subprocess.Popen(
            [str(EXE)], cwd=RUNTIME, env=child_env,
            stdout=output, stderr=output, creationflags=subprocess.CREATE_NO_WINDOW,
        )
    identity = process_info(process.pid)
    if not identity:
        raise RuntimeError("Gateway exited at startup; inspect logs/gateway.log.")
    save_json(PROCESS_FILE, {
        "pid": process.pid, "exe": str(EXE), "cwd": str(RUNTIME),
        "creation_date": identity["CreationDate"], "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    })
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            code, _ = request("/v1/models", key)
            if code == 200:
                print(f"Gateway running: PID {process.pid}; dashboard http://127.0.0.1:{port}/dashboard/")
                return
        except (OSError, urllib.error.URLError):
            pass
        if process.poll() is not None:
            raise RuntimeError("Gateway exited; inspect logs/gateway.log.")
        time.sleep(0.25)
    raise RuntimeError("Gateway did not become ready; stop it with Stop-Gateway.cmd and inspect its log.")


def stop():
    record = owned_process()
    if record:
        # Re-check ownership immediately before using Stop-Process.
        owned_process()
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", f"Stop-Process -Id {int(record['pid'])} -ErrorAction Stop"],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode:
            raise RuntimeError("Unable to stop the project gateway.")
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and process_info(record["pid"]):
            time.sleep(0.2)
        if process_info(record["pid"]):
            raise RuntimeError("Project gateway still exists after stop.")
    PROCESS_FILE.unlink(missing_ok=True)
    print("Project gateway stopped; process record cleared.")


def status():
    value = {
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "root": str(ROOT),
        "config_exists": CONFIG.exists(), "executable_exists": EXE.exists(),
        "gateway_running": bool(owned_process()),
    }
    if value["gateway_running"]:
        code, body = request("/health")
        value["health_http"] = code
        health = json.loads(body)
        # Deliberately retain counts only: /health can include account details.
        value["accounts_total"] = health.get("accounts", health.get("total_accounts"))
        value["usable_accounts"] = health.get("available")
        value["models_http"] = request("/v1/models", config()["server"]["api_key"])[0]
    save_json(ROOT / "evidence" / "local-status.json", value)
    print(json.dumps(value, ensure_ascii=False, indent=2))


def verify_local():
    if not owned_process():
        raise RuntimeError("Start the gateway before local verification.")
    key = config()["server"]["api_key"]
    checks = {
        "dashboard_200": request("/dashboard/")[0] == 200,
        "health_200": request("/health")[0] == 200,
        "models_authenticated_200": request("/v1/models", key)[0] == 200,
        "models_missing_key_401": request("/v1/models")[0] == 401,
        "models_wrong_key_401": request("/v1/models", "invalid-project-test-key")[0] == 401,
        "host_is_loopback": config()["server"]["host"] == "127.0.0.1",
        "agent_transport_enabled": config()["proxy"]["agent_thread"] is True,
        "default_model_is_opus55": config()["proxy"]["default_model"] == "claude-opus-5-5",
        "opus55_lock_enabled": config()["proxy"].get("require_opus55") is True,
        "exe_sha256": hashlib.sha256(EXE.read_bytes()).hexdigest(),
    }
    checks["passed"] = all(value is True for name, value in checks.items() if name != "exe_sha256")
    checks["notion_inference_verified"] = False
    save_json(ROOT / "evidence" / "local-verification.json", checks)
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    if not checks["passed"]:
        raise RuntimeError("Local verification failed.")


def readiness():
    """Return a redacted state and exit code; never import credentials or infer."""
    value = {"state": "awaiting_setup", "notion_inference_verified": False}
    code = 2
    if CONFIG.is_file() and EXE.is_file():
        cfg = config()
        if cfg.get("server", {}).get("host") != "127.0.0.1" or cfg.get("proxy", {}).get("default_model") != "claude-opus-5-5" or cfg.get("proxy", {}).get("require_opus55") is not True or cfg.get("proxy", {}).get("agent_thread") is not True:
            value["state"], code = "invalid_configuration", 4
        else:
            try:
                running = owned_process()
            except RuntimeError:
                value["state"] = "process_identity_mismatch"
                return value, 4
            if not running:
                value["state"] = "awaiting_gateway"
                return value, 2
            value["dashboard_url"] = f"http://127.0.0.1:{cfg['server']['port']}/dashboard/"
            try:
                http, body = request("/health")
                model_http, _ = request("/v1/models", cfg["server"]["api_key"])
                value["health_http"], value["models_http"] = http, model_http
                if http != 200 or model_http != 200:
                    value["state"], code = "gateway_unhealthy", 4
                else:
                    health = json.loads(body)
                    value["usable_accounts"] = health.get("available", 0)
                    if value["usable_accounts"] > 0:
                        value["state"], code = "ready_for_acceptance", 0
                    else:
                        value["state"], code = "awaiting_account", 3
                        value["human_step"] = "Import your own token_v2 in the local dashboard; see docs/ACCOUNT_IMPORT.md."
            except (OSError, ValueError, urllib.error.URLError):
                value["state"], code = "gateway_unhealthy", 4
    return value, code


def ready():
    value, code = readiness()
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("init", "start", "stop", "status", "ready", "verify-local"))
    action = parser.parse_args().action
    result = globals()[action.replace("-", "_") if action != "init" else "initialize"]()
    if isinstance(result, int):
        raise SystemExit(result)


if __name__ == "__main__":
    main()
