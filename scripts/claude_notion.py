"""Windows launcher adapted from upstream; no global provider changes."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import yaml
from manage import process_info, save_json

ROOT = Path(__file__).resolve().parents[1]


def launch_spec(extra_args):
    extra_args = list(extra_args)
    # Verified against Claude Code 2.1.299 bare-mode init: these are actually registered.
    tool_names = "Bash,Read,Edit"
    if "--local-tools" in extra_args:
        index = extra_args.index("--local-tools")
        if index + 1 == len(extra_args):
            raise RuntimeError("--local-tools requires a comma-separated tool list.")
        selected = extra_args[index + 1].split(",")
        if not selected or any(name not in tool_names.split(",") for name in selected):
            raise RuntimeError("--local-tools contains an unsupported tool name.")
        tool_names = ",".join(dict.fromkeys(selected))
        del extra_args[index:index + 2]
    cfg = yaml.safe_load((ROOT / "runtime" / "config.yaml").read_text(encoding="utf-8"))
    if cfg["server"]["host"] != "127.0.0.1" or not cfg["proxy"].get("agent_thread"):
        raise RuntimeError("This launcher requires the project loopback Agent configuration.")
    if not cfg["server"]["api_key"]:
        raise RuntimeError("Gateway local API key is not initialized.")
    supported_models = ("claude-opus-5-5", "opus-5.5", "claude-opus-5.5")
    model = cfg["proxy"].get("default_model")
    if model not in supported_models or cfg["proxy"].get("require_opus55") is not True:
        raise RuntimeError("This project requires a configured, locked Opus 5.5 gateway.")
    for index, arg in enumerate(extra_args):
        if arg == "--model":
            if index + 1 == len(extra_args) or extra_args[index + 1] not in supported_models:
                raise RuntimeError("This project permits only fixed Opus 5.5; Auto fallback is prohibited.")
            model = extra_args[index + 1]
        if arg.startswith("--model="):
            if arg.split("=", 1)[1] not in supported_models:
                raise RuntimeError("This project permits only fixed Opus 5.5; Auto fallback is prohibited.")
            model = arg.split("=", 1)[1]
    env = os.environ.copy()
    for name in list(env):
        if name.startswith("ANTHROPIC_") or name in (
            "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY",
            "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST",
        ):
            env.pop(name, None)
    env.update(
        ANTHROPIC_BASE_URL=f"http://127.0.0.1:{cfg['server']['port']}",
        ANTHROPIC_API_KEY=cfg["server"]["api_key"],
        ANTHROPIC_MODEL=model,
        ANTHROPIC_DEFAULT_HAIKU_MODEL=model,
        ANTHROPIC_DEFAULT_SONNET_MODEL=model,
        ANTHROPIC_DEFAULT_OPUS_MODEL=model,
        CLAUDE_CONFIG_DIR=str(ROOT / "runtime" / "claude"),
        CLAUDE_CODE_TMPDIR=str(ROOT / "_tmp"),
        CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1",
        DISABLE_UPDATES="1", DISABLE_AUTOUPDATER="1",
        NO_PROXY="127.0.0.1,localhost",
    )
    # Discover project-local skills only; avoid loading a large unrelated global catalog.
    catalog = []
    for directory in (Path.cwd() / ".claude" / "skills", ROOT / "runtime" / "claude" / "skills"):
        if directory.is_dir():
            for source in sorted(directory.glob("*/SKILL.md")):
                try:
                    text = source.read_text(encoding="utf-8")
                    metadata = yaml.safe_load(text.split("---", 2)[1]) if text.startswith("---") else {}
                    metadata = metadata if isinstance(metadata, dict) else {}
                    catalog.append(f"- {metadata.get('name', source.parent.name)}: {metadata.get('description', '')}\n  Source: {source.resolve()}")
                except (OSError, ValueError, yaml.YAMLError):
                    continue
    claude = os.environ.get("NOTION_CLAUDE_EXE") or shutil.which("claude.exe") or shutil.which("claude")
    if not claude:
        raise RuntimeError("Claude Code is not available on PATH.")
    args = [claude, "--bare", "--setting-sources", "", "--strict-mcp-config", "--model", model,
            "--permission-mode", "acceptEdits",
            "--tools", tool_names,
            "--system-prompt", "You are a coding assistant helping the user work in their current directory. Use local tools to read before editing and to run relevant tests. Report observed results honestly.",
            "--append-system-prompt", "Read the exact local SKILL.md before following it. Do not modify skill sources.\n" + "\n".join(catalog)]
    return args + extra_args, env


def main():
    args, env = launch_spec(sys.argv[1:])
    evidence = {
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "cwd": str(Path.cwd()),
        "claude_executable": args[0], "base_url": env["ANTHROPIC_BASE_URL"],
        "config_dir": env["CLAUDE_CONFIG_DIR"], "tmp_dir": env["CLAUDE_CODE_TMPDIR"],
        "requested_tool_names": args[args.index("--tools") + 1],
        "requested_model": args[args.index("--model") + 1],
        "model_lock": "Opus 5.5; no Auto fallback",
        "permission_mode": "acceptEdits",
        "global_settings_loaded": False, "external_mcp_loaded": False,
    }
    (ROOT / "evidence" / "last-claude-launch.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Windows native executable: use subprocess so exit status and Ctrl+C remain observable.
    records = ROOT / "runtime" / "claude-processes"
    records.mkdir(exist_ok=True)
    child = subprocess.Popen(args, env=env)
    record_path = records / f"{child.pid}.json"
    identity = process_info(child.pid)
    if identity:
        save_json(record_path, {"pid": child.pid, "exe": args[0],
                               "creation_date": identity["CreationDate"]})
    try:
        return child.wait()
    except KeyboardInterrupt:
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.terminate()
            child.wait(timeout=5)
        return 130
    finally:
        record_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
