"""Native Claude Code with local V2 routing; preserve normal user discovery."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import manage

ROOT = Path(__file__).resolve().parents[1]
MODEL = "claude-opus-5-5"
ALIASES = {MODEL, "opus-5.5", "claude-opus-5.5"}


def launch_spec(arguments):
    for index, arg in enumerate(arguments):
        if arg in ("--bare", "--tools", "--system-prompt", "--system-prompt-file", "--settings", "--setting-sources") or arg.startswith(("--tools=", "--system-prompt=", "--system-prompt-file=", "--settings=", "--setting-sources=")):
            raise RuntimeError("This entry preserves native prompt, tool registration and settings discovery")
        if arg == "--model" and (index + 1 == len(arguments) or arguments[index + 1] not in ALIASES):
            raise RuntimeError("Only fixed Opus 5.5 is supported")
        if arg.startswith("--model=") and arg.split("=", 1)[1] not in ALIASES:
            raise RuntimeError("Only fixed Opus 5.5 is supported")
    cfg = manage.config()
    if cfg["server"]["host"] != "127.0.0.1" or not cfg["server"].get("api_key") or cfg["proxy"].get("require_opus55") is not True or cfg["proxy"].get("agent_thread") is not True or cfg["proxy"].get("agent_session_v2") is not True or cfg["proxy"].get("default_model") not in ALIASES:
        raise RuntimeError("An authenticated loopback V2 gateway locked to Opus 5.5 is required")
    exe = os.environ.get("NOTION_CLAUDE_EXE") or shutil.which("claude.exe") or shutil.which("claude")
    if not exe:
        raise RuntimeError("Native Claude Code CLI is not installed")
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("ANTHROPIC_") or key in ("CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY", "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST", "CLAUDE_CODE_SIMPLE", "CLAUDE_CODE_SAFE_MODE"):
            env.pop(key, None)
    route = {
        "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{cfg['server']['port']}",
        "ANTHROPIC_API_KEY": cfg["server"]["api_key"],
        "ANTHROPIC_AUTH_TOKEN": cfg["server"]["api_key"],
        "ANTHROPIC_MODEL": MODEL,
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": MODEL,
        "ANTHROPIC_DEFAULT_SONNET_MODEL": MODEL,
        "ANTHROPIC_DEFAULT_OPUS_MODEL": MODEL,
        "CLAUDE_CODE_USE_BEDROCK": "0", "CLAUDE_CODE_USE_VERTEX": "0", "CLAUDE_CODE_USE_FOUNDRY": "0",
    }
    env.update(route)
    env["NO_PROXY"] = ",".join(filter(None, [env.get("NO_PROXY", ""), "127.0.0.1", "localhost"]))
    route_path = ROOT / "runtime/claude-route.json"
    manage.save_json(route_path, {"env": route})
    # No alternate CLAUDE_CONFIG_DIR, application-data redirects or directory links.
    return [exe, "--settings", str(route_path), "--model", MODEL, "--setting-sources", "user,project,local", *arguments], env


def run_cli(args, env, workdir, stdout=None, timeout=None):
    child = subprocess.Popen(args, cwd=workdir, env=env, stdout=stdout,
                             stderr=subprocess.STDOUT if stdout else None)
    record_path = ROOT / "runtime/claude-processes" / (str(child.pid) + ".json")
    try:
        identity = manage.process_info(child.pid)
        if identity is None and child.poll() is None:
            raise RuntimeError("Cannot verify the native CLI process identity")
        if identity:
            record_path.parent.mkdir(parents=True, exist_ok=True)
            manage.save_json(record_path, {"pid": child.pid, "exe": identity["ExecutablePath"], "creation_date": identity["CreationDate"]})
        return child.wait(timeout=timeout)
    except (KeyboardInterrupt, subprocess.TimeoutExpired):
        if child.poll() is None:
            subprocess.run(["taskkill.exe", "/PID", str(child.pid), "/T", "/F"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            child.wait()
        return 124 if timeout else 130
    except Exception:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=10)
        raise
    finally:
        record_path.unlink(missing_ok=True)


def main():
    if not Path.cwd().is_dir():
        raise RuntimeError("Working directory is missing")
    args, env = launch_spec(sys.argv[1:])
    return run_cli(args, env, Path.cwd())


if __name__ == "__main__":
    sys.exit(main())
