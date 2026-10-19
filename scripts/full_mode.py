"""Full Claude Code CLI experiment; routing and state are process-local."""
import json
import os
from pathlib import Path
import shutil

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GATEWAY = ROOT
MODEL = "claude-opus-5-5"
ALIASES = {MODEL, "opus-5.5", "claude-opus-5.5"}


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def gateway_config(gateway):
    cfg = yaml.safe_load((gateway / "runtime/config.yaml").read_text(encoding="utf-8"))
    if cfg["server"]["host"] != "127.0.0.1" or not cfg["server"].get("api_key"):
        raise RuntimeError("An authenticated loopback gateway is required")
    if not cfg["proxy"].get("agent_thread") or cfg["proxy"].get("require_opus55") is not True or cfg["proxy"].get("default_model") not in ALIASES:
        raise RuntimeError("A fixed Opus 5.5 Agent gateway is required; no Auto fallback")
    return cfg


def child_environment(gateway):
    cfg = gateway_config(gateway)
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("ANTHROPIC_") or key in {
            "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY",
            "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST",
            "CLAUDE_CODE_SIMPLE", "CLAUDE_CODE_SAFE_MODE",
        }:
            env.pop(key, None)
    env.update({
        "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{cfg['server']['port']}",
        "ANTHROPIC_API_KEY": cfg["server"]["api_key"],
        "ANTHROPIC_MODEL": MODEL,
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": MODEL,
        "ANTHROPIC_DEFAULT_SONNET_MODEL": MODEL,
        "ANTHROPIC_DEFAULT_OPUS_MODEL": MODEL,
        "CLAUDE_CONFIG_DIR": str(ROOT / "runtime/claude"),
        "CLAUDE_CODE_TMPDIR": str(ROOT / "_tmp"),
        "CLAUDE_CODE_DEBUG_LOGS_DIR": str(ROOT / "logs/claude"),
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "DISABLE_UPDATES": "1", "DISABLE_AUTOUPDATER": "1", "DO_NOT_TRACK": "1",
        "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
        "PYTHONPYCACHEPREFIX": str(ROOT / "_cache/pycache"),
        "TEMP": str(ROOT / "_tmp"), "TMP": str(ROOT / "_tmp"), "TMPDIR": str(ROOT / "_tmp"),
        "APPDATA": str(ROOT / "runtime/appdata/Roaming"),
        "LOCALAPPDATA": str(ROOT / "runtime/appdata/Local"),
        "XDG_CACHE_HOME": str(ROOT / "_cache/xdg"),
        "XDG_CONFIG_HOME": str(ROOT / "runtime/xdg-config"),
        "XDG_DATA_HOME": str(ROOT / "runtime/xdg-data"),
        "XDG_STATE_HOME": str(ROOT / "runtime/xdg-state"),
        "NO_PROXY": ",".join(filter(None, [env.get("NO_PROXY", ""), "127.0.0.1", "localhost"])),
    })
    for candidate in (Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe",
                      Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Git/bin/bash.exe"):
        if candidate.is_file():
            env["CLAUDE_CODE_GIT_BASH_PATH"] = str(candidate)
            break
    for key in ("CLAUDE_CONFIG_DIR", "CLAUDE_CODE_TMPDIR", "CLAUDE_CODE_DEBUG_LOGS_DIR", "PYTHONPYCACHEPREFIX",
                "APPDATA", "LOCALAPPDATA", "XDG_CACHE_HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME"):
        Path(env[key]).mkdir(parents=True, exist_ok=True)
    return env


def launch_spec(gateway, arguments):
    # Preserve native prompt and tool registration. Do not replace them with a short prompt.
    for index, arg in enumerate(arguments):
        if arg in ("--bare", "--safe-mode", "--system-prompt", "--system-prompt-file", "--tools") or arg.startswith(("--system-prompt=", "--system-prompt-file=", "--tools=")):
            raise RuntimeError("This entry preserves the native full prompt and tool set")
        if arg == "--model" and (index + 1 == len(arguments) or arguments[index + 1] not in ALIASES):
            raise RuntimeError("Only the locked Opus 5.5 model is supported")
        if arg.startswith("--model=") and arg.split("=", 1)[1] not in ALIASES:
            raise RuntimeError("Only the locked Opus 5.5 model is supported")
    exe = os.environ.get("NOTION_CLAUDE_EXE") or shutil.which("claude.exe") or shutil.which("claude")
    if not exe:
        raise RuntimeError("Claude Code CLI was not found")
    env = child_environment(gateway)
    return [exe, "--model", MODEL, "--permission-mode", "acceptEdits", "--setting-sources", "user,project,local", *arguments], env
