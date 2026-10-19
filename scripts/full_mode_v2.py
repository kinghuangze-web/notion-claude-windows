"""Official Claude Code + persistent Notion Opus 5.5 gateway, isolated on port 8082."""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

import yaml
import full_mode

ROOT = full_mode.ROOT
V2 = ROOT / "logs"
RUNTIME = ROOT / "runtime/full"
EXE = ROOT / "runtime/notion-manager.exe"
GLOBAL = Path.home() / ".claude"


def process_identity(pid):
    result = subprocess.run(["powershell.exe", "-NoProfile", "-Command",
                             f"Get-CimInstance Win32_Process -Filter 'ProcessId = {int(pid)}' | Select-Object ProcessId,ExecutablePath,CreationDate | ConvertTo-Json -Compress"],
                            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise RuntimeError("Cannot verify V2 process identity")
    return json.loads(result.stdout) if result.stdout.strip() else None


def stop_gateway():
    record_path = RUNTIME / "gateway-process.json"
    if not record_path.is_file():
        return
    record = json.loads(record_path.read_text(encoding="utf-8"))
    current = process_identity(record["pid"])
    if current is None:
        record_path.unlink()
        return
    if Path(current.get("ExecutablePath") or "").resolve() != EXE.resolve() or not record.get("creation_date") or current["CreationDate"] != record["creation_date"]:
        raise RuntimeError("V2 process ownership does not match the saved record")
    result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", f"Stop-Process -Id {int(record['pid'])} -ErrorAction Stop"],
                            capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise RuntimeError("V2 process did not stop")
    deadline = time.monotonic() + 10
    while process_identity(record["pid"]):
        if time.monotonic() > deadline:
            raise RuntimeError("V2 process remains active")
        time.sleep(0.1)
    record_path.unlink(missing_ok=True)
    print("Owned V2 gateway stopped")


def prepare():
    RUNTIME.mkdir(parents=True, exist_ok=True)
    cfg = full_mode.gateway_config(full_mode.DEFAULT_GATEWAY)
    cfg["server"]["port"] = "8082"
    cfg["server"]["log_file"] = str(V2 / "full-gateway.log")
    cfg["server"]["debug_logging"] = False
    path = RUNTIME / "config.yaml"
    path.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    config_dir = RUNTIME / "claude"
    config_dir.mkdir(exist_ok=True)
    inherited = []
    for name in ("skills", "plugins", "agents", "commands", "hooks"):
        source, target = GLOBAL / name, config_dir / name
        if source.is_dir():
            if not target.exists():
                # Directory junctions require no developer mode or elevation.
                # Pass filesystem values as arguments, never interpolate shell code.
                result = subprocess.run(["powershell.exe", "-NoProfile", "-File", str(ROOT / "scripts/link_directory.ps1"), "-LinkPath", str(target), "-SourcePath", str(source)],
                                        capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode:
                    raise RuntimeError("Cannot connect existing user " + name)
            if target.resolve() != source.resolve():
                raise RuntimeError("Existing V2 discovery path points elsewhere: " + name)
            inherited.append(name)
    for name in ("CLAUDE.md", "settings.json", "settings.local.json"):
        source = GLOBAL / name
        if source.is_file():
            shutil.copy2(source, config_dir / name)
    # Preserve global MCP discovery without copying login/OAuth credentials.
    global_state = Path.home() / ".claude.json"
    if global_state.is_file():
        data = json.loads(global_state.read_text(encoding="utf-8"))
        state_path = config_dir / ".claude.json"
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.is_file() else {}
        if "mcpServers" in data:
            state["mcpServers"] = data["mcpServers"]
        full_mode.save(state_path, state)
    return cfg, config_dir, inherited


def gateway_environment():
    env = os.environ.copy()
    for key in ("HOST", "PORT", "API_KEY", "ACCOUNTS_DIR", "TOKEN_FILE", "LOG_FILE",
                "DEBUG_LOGGING", "API_LOG_INPUT", "API_LOG_OUTPUT", "NOTION_LOG_REQUEST",
                "NOTION_LOG_RESPONSE", "DUMP_API_INPUT", "AGENT_THREAD", "NOTION_API_BASE",
                "DEFAULT_MODEL", "NOTION_PROXY", "INFERENCE_TIMEOUT", "API_TIMEOUT",
                "TLS_DIAL_TIMEOUT", "NOTION_TOKEN_V2"):
        env.pop(key, None)
    for key in list(env):
        if key.startswith(("NOTION_TOKEN_V2_", "NOTION_SPACE_ID", "NOTION_ACTIVE_USER_ID", "NOTION_EXPECTED_EMAIL")):
            env.pop(key, None)
    env["NOTION_AGENT_SESSION_DIR"] = str(RUNTIME / "sessions")
    return env


def ensure_gateway(cfg):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    url = "http://127.0.0.1:8082/health"
    record_path = RUNTIME / "gateway-process.json"
    if record_path.is_file():
        record = json.loads(record_path.read_text(encoding="utf-8"))
        # Require executable identity; do not adopt another service on the port.
        current = process_identity(record["pid"])
        if current and Path(current.get("ExecutablePath") or "").resolve() == EXE.resolve() and record.get("creation_date") and current["CreationDate"] == record["creation_date"]:
            with opener.open(url, timeout=10) as response:
                return json.load(response)
        if current:
            raise RuntimeError("V2 process ownership mismatch; refusing to adopt or replace it")
    if not EXE.is_file():
        raise RuntimeError("Run Setup.cmd to build the V2-capable gateway first")
    try:
        with socket.create_connection(("127.0.0.1", 8082), timeout=0.5):
            raise RuntimeError("Port 8082 is occupied by an unowned listener")
    except OSError:
        pass
    # Let the real Go listener bind. A Python bind probe can reject a Windows
    # TIME_WAIT endpoint after restarting this gateway even when Go can bind it.
    env = gateway_environment()
    with (V2 / "full-gateway.log").open("ab") as output:
        child = subprocess.Popen([str(EXE)], cwd=RUNTIME, env=env, stdout=output, stderr=output,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        identity = process_identity(child.pid)
    except Exception:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=10)
        raise
    if not identity:
        raise RuntimeError("V2 gateway exited during startup")
    full_mode.save(record_path, {"pid": child.pid, "exe": str(EXE), "creation_date": identity["CreationDate"], "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if child.poll() is not None:
            raise RuntimeError("V2 gateway exited; inspect logs/full-gateway.log")
        try:
            with opener.open(url, timeout=2) as response:
                health = json.load(response)
            if child.poll() is not None:
                raise RuntimeError("V2 listener failed; refusing another service response")
            return health
        except OSError:
            time.sleep(0.25)
    raise RuntimeError("V2 startup deadline exceeded")


def launch_spec(arguments):
    cfg, config_dir, inherited = prepare()
    args, env = full_mode.launch_spec(full_mode.DEFAULT_GATEWAY, arguments)
    env["ANTHROPIC_BASE_URL"] = "http://127.0.0.1:8082"
    env["CLAUDE_CONFIG_DIR"] = str(config_dir)
    route = {"env": {key: value for key, value in env.items() if key.startswith("ANTHROPIC_")}}
    route_path = RUNTIME / "route-settings.json"
    full_mode.save(route_path, route)
    args = [*args[:1], "--settings", str(route_path), *args[1:]]
    return args, env, cfg, inherited


def run_cli(args, env, workdir, stdout=None, timeout=None):
    child = subprocess.Popen(args, cwd=workdir, env=env, stdout=stdout,
                             stderr=subprocess.STDOUT if stdout else None)
    record = ROOT / "runtime/claude-processes" / (str(child.pid) + ".json")
    try:
        identity = process_identity(child.pid)
    except Exception:
        if child.poll() is None:
            subprocess.run(["taskkill.exe", "/PID", str(child.pid), "/T", "/F"],
                           capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            child.wait()
        raise
    if identity is None and child.poll() is None:
        child.terminate()
        child.wait(timeout=10)
        raise RuntimeError("Cannot identify the native CLI process")
    if identity:
        full_mode.save(record, {"pid": child.pid, "exe": identity["ExecutablePath"],
                                "creation_date": identity["CreationDate"]})
    try:
        return child.wait(timeout=timeout)
    except (KeyboardInterrupt, subprocess.TimeoutExpired):
        subprocess.run(["taskkill.exe", "/PID", str(child.pid), "/T", "/F"],
                       capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        child.wait()
        return 124 if timeout else 130
    finally:
        record.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", type=Path, default=ROOT / "demo")
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--start-only", action="store_true")
    parser.add_argument("--stop", action="store_true")
    options, arguments = parser.parse_known_args()
    if options.stop:
        stop_gateway()
        return 0
    if arguments[:1] == ["--"]:
        arguments = arguments[1:]
    args, env, cfg, inherited = launch_spec(arguments)
    evidence = {"base_url": env["ANTHROPIC_BASE_URL"], "config_dir": env["CLAUDE_CONFIG_DIR"],
                "inherited_user_directories": inherited, "native_prompt": True, "native_tools": True,
                "model": full_mode.MODEL, "existing_gateway_8081_modified": False}
    if options.inspect:
        print(json.dumps(evidence, ensure_ascii=False, indent=2))
        return 0
    health = ensure_gateway(cfg)
    if health.get("available", 0) < 1:
        raise RuntimeError("V2 has no usable imported Notion workspace")
    full_mode.save(ROOT / "evidence/last-v2-launch.json", evidence)
    if options.start_only:
        print("V2 gateway ready on 127.0.0.1:8082")
        return 0
    if not options.workdir.is_dir():
        raise RuntimeError("Working directory does not exist")
    return run_cli(args, env, options.workdir.resolve())


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("V2 error: " + str(error), file=sys.stderr)
        sys.exit(1)
