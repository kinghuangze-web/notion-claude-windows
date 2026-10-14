# Changelog

## 1.0.1 — 2026-10-14

- Make the README start with the Agent execution path; retain manual Windows entry points.
- Add an execution contract, non-mutating dependency discovery and redacted readiness states with exit codes.
- Load the current PowerShell host's security module explicitly when Agent subprocesses inherit another edition's module paths.
- Expand token_v2 retrieval and dashboard import instructions, including Windows shortcuts, domain selection, complete Value copying and failed-import checks.
- Clarify minimal prompt, text protocol, fresh-thread context and reasoning-control limits.

## 1.0.0 — 2026-10-14

- Pin the experimental notion_manager Agent transport to its reproducible base commit.
- Add live Opus 5.5 model resolution, explicit request selection, thread/model/selectedModel validation and a no-Auto deployment lock.
- Add Windows setup, executable discovery, project-local cache/config/session paths, NTFS ACLs and process identity tracking.
- Use the verified bare CLI tool set and acceptEdits permission mode; leave global provider settings untouched.
- Add opt-in five-stage live acceptance and local-only evidence.
- Add preview-first cleanup that works without a virtual environment and rejects redirected paths or reused PIDs.
- Document Windows Chrome account import, manual steps, troubleshooting, privacy, source attribution and verification limits.
