"""One official CLI session, native Skill + real Read/Write/Edit, no broad live suite."""
import hashlib
import hmac
import json
import re
import secrets
from pathlib import Path
import subprocess
import sys
import time
import uuid

import claude_full
import manage

ROOT = claude_full.ROOT
SESSION = str(uuid.uuid4())
WORK = ROOT / "demo/full" / SESSION


def main():
    if "--run" not in sys.argv:
        print(json.dumps({"state": "preview", "live_requests": False, "run": "acceptance.ps1 -Run"}, indent=2))
        return 0
    WORK.mkdir(parents=True, exist_ok=True)
    skill = WORK / ".claude/skills/v2-session-proof/SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text("---\nname: v2-session-proof\ndescription: Provides the exact file marker for this explicitly requested adapter verification.\n---\n\nFor this verification only: after reading input.txt, write result.txt containing the exact input line followed by SKILL_V2_719, each on its own line. Then use Edit to append EDIT_V2_OK on a third line. Read the resulting file to verify it. Do not modify anything outside this directory.\n", encoding="utf-8")
    nonce = "NONCE_V2_" + uuid.uuid4().hex
    (WORK / "input.txt").write_text(nonce + "\n", encoding="utf-8")
    prompt = "在当前目录完成这个验证任务：必须先用原生 Skill 工具调用 v2-session-proof，再使用 Read 读取 input.txt，按该 Skill 的要求使用 Write 和 Edit 生成 result.txt，最后 Read 核对。严格只修改当前目录 result.txt。不要使用 Notion 云端文件或命令工具。完成后只回复 V2_CLI_OK。"
    extra, allowed = [], "Read,Write,Edit,Skill"
    mcp = "--mcp" in sys.argv
    if mcp:
        probe = ROOT / "runtime/probes" / SESSION
        probe.mkdir(parents=True)
        key = secrets.token_bytes(32)
        (probe / "mcp-key.txt").write_bytes(key)
        config = probe / "mcp.json"
        manage.save_json(config, {"mcpServers": {"local_probe": {"command": sys.executable, "args": [str(ROOT / "scripts/mcp_probe.py"), str(probe)]}}})
        extra = ["--mcp-config", str(config)]
        allowed += ",mcp__local_probe__challenge"
        prompt += "另外必须实际调用 mcp__local_probe__challenge，nonce 参数为 " + nonce + "。不要读取工具的本地脚本、key 或日志。最后回复 V2_CLI_OK 和工具返回的完整 proof。"
    args, env = claude_full.launch_spec(["-p", prompt, "--session-id", SESSION, "--output-format", "stream-json", "--verbose", "--max-turns", "16", "--allowedTools", allowed, *extra])
    manage.start()
    configured_log = manage.config()["server"].get("log_file")
    log_path = Path(configured_log) if configured_log else ROOT / "logs/gateway.log"
    if not log_path.is_absolute():
        log_path = manage.RUNTIME / log_path
    log_offset = log_path.stat().st_size if log_path.exists() else 0
    evidence = {"started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "official_cli": True,
                "session_id": SESSION, "native_prompt": True, "native_tools": True,
                "configuration_discovery": "native_user_project_local", "base_url": env["ANTHROPIC_BASE_URL"]}
    output_path = ROOT / ("evidence/" + SESSION + "-v2-official-cli-stream.jsonl")
    with output_path.open("wb") as output:
        evidence["returncode"] = claude_full.run_cli(args, env, WORK, stdout=output, timeout=240)
        evidence["timeout"] = evidence["returncode"] == 124
    events = []
    for line in output_path.read_text("utf-8", errors="replace").splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            pass
    tool_uses, tool_results = [], []
    for event in events:
        if event.get("type") == "system" and event.get("subtype") == "init":
            evidence["registered_tools"] = event.get("tools", [])
            evidence["discovered_skills"] = event.get("skills", [])
            evidence["claude_code_version"] = event.get("claude_code_version")
        for block in event.get("message", {}).get("content", []) if isinstance(event.get("message", {}).get("content"), list) else []:
            if block.get("type") == "tool_use":
                tool_uses.append({"id": block.get("id"), "name": block.get("name"), "input": block.get("input")})
            elif block.get("type") == "tool_result":
                tool_results.append({"id": block.get("tool_use_id"), "is_error": block.get("is_error", False)})
        if event.get("type") == "result":
            evidence["result"] = {key: event.get(key) for key in ("is_error", "result", "num_turns", "session_id", "subtype")}
    evidence["tool_uses"], evidence["tool_results"] = tool_uses, tool_results
    target = WORK / "result.txt"
    data = target.read_text("utf-8").replace("\r\n", "\n") if target.is_file() else ""
    evidence["file_exact"] = data.rstrip("\n") == nonce + "\nSKILL_V2_719\nEDIT_V2_OK"
    required = {"Skill", "Read", "Write", "Edit"}
    good_ids = {x["id"] for x in tool_results if not x["is_error"]}
    good_tools = {x["name"] for x in tool_uses if x["id"] in good_ids}
    with log_path.open("rb") as gateway_log:
        gateway_log.seek(log_offset)
        lines = gateway_log.read().decode("utf-8", errors="replace")
    creates = re.findall(r"\[agent-v2\] created .*?requested=(\S+) confirmed=(\S+) selected=(\S+) thread_sha256=(\w+)", lines)
    thread_hashes = set(re.findall(r"\[agent-v2\].*?thread_sha256=(\w+)", lines))
    evidence["one_backend_thread"] = len(creates) == 1 and len(thread_hashes) == 1
    evidence["model_confirmed"] = bool(creates) and all(a == b == c for a, b, c, _ in creates)
    evidence["mcp_checked"] = mcp
    evidence["mcp_proof_exact"] = True
    if mcp:
        expected = hmac.new(key, nonce.encode(), hashlib.sha256).hexdigest()
        calls = probe / "mcp-calls.jsonl"
        rows = [json.loads(x) for x in calls.read_text("utf-8").splitlines()] if calls.exists() else []
        evidence["mcp_proof_exact"] = any(x.get("nonce") == nonce and x.get("proof") == expected for x in rows) and expected in str(evidence.get("result", {}).get("result", ""))
        required.add("mcp__local_probe__challenge")
    evidence["passed"] = (evidence["returncode"] == 0 and not evidence.get("result", {}).get("is_error", True)
                          and evidence["file_exact"] and required <= good_tools and evidence["one_backend_thread"]
                          and evidence["model_confirmed"] and evidence["mcp_proof_exact"])
    manage.save_json(ROOT / ("evidence/" + SESSION + "-v2-official-cli-summary.json"), evidence)
    print(json.dumps({key: evidence.get(key) for key in ("returncode", "passed", "file_exact", "result", "discovered_skills")}, ensure_ascii=False, indent=2))
    return 0 if evidence["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
