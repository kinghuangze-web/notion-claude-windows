"""Opt-in real inference acceptance. Results and raw events remain local and ignored."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import time
import uuid

from manage import ROOT, config, request, save_json

CONFIRM = re.compile(r"\[agent-model\] alias=(\S+) requested=(\S+) confirmed=(\S+) selected=(\S+) thread_sha256=(\S+)")
COMPLETE = re.compile(r"\[agent-model\] completed requested=(\S+) thread_sha256=(\S+)")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def snapshot_global():
    home = Path(os.environ["USERPROFILE"])
    result = []
    for path in (home / ".claude.json", home / ".claude/settings.json", home / ".claude/history.jsonl"):
        item = {"exists": path.exists()}
        if path.exists():
            stat = path.stat()
            item.update(size=stat.st_size, mtime_ns=stat.st_mtime_ns, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        result.append(item)
    return result


def run(stage, prompt, directory, tools=(), expected_paths=()):
    offset = (ROOT / "logs/gateway.log").stat().st_size
    args = [str(ROOT / ".venv/Scripts/python.exe"), str(ROOT / "scripts/claude_notion.py"),
            "--print", "--output-format", "stream-json", "--verbose", "--session-id", str(uuid.uuid4())]
    if tools:
        args += ["--local-tools", ",".join(dict.fromkeys(x.split("(", 1)[0] for x in tools)), "--allowedTools", *tools]
    args += ["--", prompt]
    prefix = ROOT / "logs" / f"acceptance-{stage}-{time.strftime('%Y%m%d-%H%M%S')}"
    before = snapshot_global()
    with prefix.with_suffix(".jsonl").open("wb") as out, prefix.with_suffix(".stderr.txt").open("wb") as err:
        child = subprocess.Popen(args, cwd=directory, stdout=out, stderr=err)
        try:
            code = child.wait(timeout=240)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill.exe", "/PID", str(child.pid), "/T", "/F"], capture_output=True)
            child.wait(timeout=10)
            raise RuntimeError(f"{stage} timed out; the upstream task may still continue. Inspect local logs before retrying.")
    events = []
    for line in prefix.with_suffix(".jsonl").read_text(encoding="utf-8").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    results = [x for x in events if x.get("type") == "result"]
    init = next((x for x in events if x.get("type") == "system" and x.get("subtype") == "init"), {})
    calls, successful, failed = {}, [], []
    for event in events:
        for block in event.get("message", {}).get("content", []):
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                calls[block["id"]] = {"name": block.get("name"), "input": block.get("input", {})}
            elif block.get("type") == "tool_result":
                call = calls.get(block.get("tool_use_id"))
                if call:
                    (failed if block.get("is_error") else successful).append(call)
    with (ROOT / "logs/gateway.log").open("rb") as log:
        log.seek(offset)
        tail = log.read().decode("utf-8", errors="replace")
    rounds = [dict(zip(("alias", "requested", "confirmed", "selected", "thread_hash"), m.groups())) for m in CONFIRM.finditer(tail)]
    completed = {m.group(2) for m in COMPLETE.finditer(tail)}
    outcome = {"stage": stage, "returncode": code, "client_model": init.get("model"), "successful_tools": successful,
               "failed_tools": failed, "model_confirmations": rounds, "global_claude_files_unchanged": snapshot_global() == before,
               "result": results[-1] if results else None}
    save_json(ROOT / "evidence" / f"acceptance-{stage}.json", outcome)
    require(code == 0 and results and not results[-1].get("is_error"), f"{stage}: native inference failed")
    require(init.get("model") == "claude-opus-5-5", "Native client model differs")
    require(rounds and all(x["requested"] == x["confirmed"] == x["selected"] and x["thread_hash"] in completed for x in rounds), "Missing or mismatched upstream model confirmation")
    require(not failed, "A tool result failed or was denied; inspect local evidence")
    require(outcome["global_claude_files_unchanged"], "An existing global Claude configuration/history file changed")
    for expected in expected_paths:
        require(any(x["name"] == "Read" and Path(x["input"].get("file_path", "")).name == expected for x in successful), f"No successful Read for {expected}")
    print(f"PASS {stage}: {len(rounds)} upstream model confirmations; tools {[x['name'] for x in successful]}", flush=True)
    return results[-1].get("result", ""), len(rounds), successful


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Authorize five real Notion AI stages; consumes account allowance")
    options = parser.parse_args()
    if not options.run:
        print("Preview: connection, seven folders, article file/readback, blind random read, Read-based Skill. Use --run for real inference.")
        return
    cfg = config()
    require(cfg["proxy"].get("require_opus55") is True and cfg["proxy"]["default_model"] == "claude-opus-5-5", "Locked Opus 5.5 configuration is required")
    status, body = request("/health")
    require(status == 200 and json.loads(body).get("available", 0) > 0, "Import an eligible Notion workspace before live acceptance")
    directory = ROOT / "demo" / ("acceptance-" + uuid.uuid4().hex[:12])
    directory.mkdir()
    total = 0
    text, count, _ = run("connection", "请只回复：连接成功。", directory)
    require(text.strip().rstrip("。") == "连接成功", "Connection answer differs")
    total += count
    _, count, tools = run("directories", "先用 pwd 确认当前目录。在当前目录创建日常记录，里面创建周一到周日七个子目录，最后执行 ls 列出核验。只操作当前目录。", directory,
                          ["Bash(pwd:*)", "Bash(mkdir:*)", "Bash(ls:*)"])
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    require(sorted(x.name for x in (directory / "日常记录").iterdir()) == sorted(weekdays), "Directory set differs")
    require(any(x["name"] == "Bash" for x in tools), "No successful Bash result")
    total += count
    marker = "NOTION_LOCAL_TEST_20261013"
    note = directory / "日常记录/周一/测试笔记.md"
    require(not note.exists(), "Refusing to overwrite an existing article test file")
    _, count, _ = run("write", "在日常记录/周一创建测试笔记.md，只有一行：\n" + marker + "\n使用 Bash 的 noclobber 防止覆盖，再调用 Read 读回；只操作当前目录。", directory,
                      ["Read", "Bash(set:*)", "Bash(printf:*)", "Bash(test:*)", "Bash(if:*)", "Bash(ls:*)"], ["测试笔记.md"])
    require(note.read_bytes() == (marker + "\n").encode(), "Article file bytes differ")
    total += count
    blind = "BLIND_" + secrets.token_hex(16)
    (directory / "blind-read.txt").write_text(blind + "\n", encoding="utf-8")
    text, count, _ = run("blind-read", "调用 Read 读取当前目录的 blind-read.txt，只返回真实内容，不修改文件。", directory, ["Read"], ["blind-read.txt"])
    require(blind in text, "Random marker absent from answer")
    total += count
    skill = directory / ".claude/skills/file-check/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: file-check\ndescription: Read 输入、创建文件并读回。\n---\n依赖 Read/Bash，仅操作当前目录。先 Read skill-input.txt，再用 Bash noclobber 创建 Skill结果.md，内容与输入原样一致；最后 Read 读回。已有输出则停止，不覆盖。\n", encoding="utf-8")
    skill_marker = "SKILL_" + secrets.token_hex(12)
    (directory / "skill-input.txt").write_text(skill_marker + "\n", encoding="utf-8")
    _, count, _ = run("skill", "先 Read .claude/skills/file-check/SKILL.md，核对工具依赖，然后执行并读回结果。只操作当前目录。", directory,
                      ["Read", "Bash(set:*)", "Bash(printf:*)", "Bash(test:*)", "Bash(if:*)"], ["SKILL.md", "skill-input.txt", "Skill结果.md"])
    require((directory / "Skill结果.md").read_bytes() == (skill_marker + "\n").encode(), "Skill output bytes differ")
    total += count
    save_json(ROOT / "evidence/acceptance-summary.json", {"passed": True, "model": "claude-opus-5-5", "confirmed_rounds": total,
        "fixture": str(directory), "article_file_sha256": hashlib.sha256(note.read_bytes()).hexdigest(), "notion_backend_weights_verified": False})
    print("All five stages passed. Results are local under demo/, logs/ and evidence/.")


if __name__ == "__main__":
    main()
