"""Dependency-free local MCP stdio probe, with independent call evidence."""
import hashlib
import hmac
import json
from pathlib import Path
import sys
import time

ROOT = Path(sys.argv[1])
KEY = (ROOT / "mcp-key.txt").read_bytes()

for line in sys.stdin:
    message = json.loads(line)
    if "id" not in message:
        continue
    method = message.get("method")
    if method == "initialize":
        result = {"protocolVersion": message.get("params", {}).get("protocolVersion", "2024-11-05"),
                  "capabilities": {"tools": {}}, "serverInfo": {"name": "full-mode-local-probe", "version": "1.0.0"}}
    elif method == "tools/list":
        result = {"tools": [{"name": "challenge", "description": "Return a real local HMAC proof for a nonce. Call this tool; never guess its output.",
                             "inputSchema": {"type": "object", "properties": {"nonce": {"type": "string"}}, "required": ["nonce"], "additionalProperties": False}}]}
    elif method == "tools/call":
        params = message["params"]
        if params["name"] != "challenge":
            raise ValueError("Unknown tool")
        nonce = params["arguments"]["nonce"]
        proof = hmac.new(KEY, nonce.encode(), hashlib.sha256).hexdigest()
        with (ROOT / "mcp-calls.jsonl").open("a", encoding="utf-8") as out:
            out.write(json.dumps({"time": time.time(), "name": "challenge", "nonce": nonce, "proof": proof}) + "\n")
        result = {"content": [{"type": "text", "text": proof}]}
    elif method in ("resources/list", "prompts/list"):
        result = {"resources" if method == "resources/list" else "prompts": []}
    elif method == "ping":
        result = {}
    else:
        print(json.dumps({"jsonrpc": "2.0", "id": message["id"], "error": {"code": -32601, "message": "Method not found"}}), flush=True)
        continue
    print(json.dumps({"jsonrpc": "2.0", "id": message["id"], "result": result}), flush=True)
