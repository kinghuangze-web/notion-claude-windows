# Agent execution contract

Goal: install this Windows x64 toolkit in a dedicated directory, load its locked Opus 5.5 gateway, and verify real file operations. Follow docs/AGENT_SETUP.md; preserve existing runtime configuration and unrelated installations.

- Run PowerShell scripts directly, not the .cmd wrappers that wait for a human keypress.
- Start with scripts/doctor.ps1. Setup checks versions, downloads the pinned source and applies the patch; do not improvise a different upstream version.
- Keep process-local data paths from env.ps1. Do not use setx, change global providers, install services, or stop a process merely because it occupies the desired port.
- Use project.ps1 -Action ready for the state/exit-code contract. awaiting_account is a human handoff, not successful setup of inference.
- Ask the user to follow docs/ACCOUNT_IMPORT.md locally. Do not ask them to paste token_v2 into agent chat or tool arguments, and do not retrieve browser login secrets automatically. This toolkit has no credential-extraction automation.
- After the user reports import completed, inspect readiness again; do not treat their message or HTTP 200 alone as inference verification.
- Prefer scripts/full.ps1 for the V2 native-framework entry. Use scripts/acceptance-full.ps1 -Run (optionally -Mcp) within authorized live-testing scope; it consumes allowance and creates a unique demo directory. Require successful Skill/tool results, exact file bytes, final CLI success, upstream model confirmation and one backend thread. Legacy acceptance.ps1 is the V1 suite and can create many chats.
- Scope subsequent tasks to the user-selected work directory. A process data directory is not a filesystem sandbox.
- Report only redacted states and failure causes. Never publish runtime, logs, evidence, demo, private overrides or cookies. Git tracked paths must equal release-files.txt.
- Preserve failure evidence locally. Cleanup is preview-first and must not remove user task outputs without authorization; use docs/CLEANUP.md.
- Stop both owned gateways before rebuilding; preserve existing runtime configuration. Full mode uses port 8082 and runtime/full, legacy management remains on 8081. Do not migrate CC Switch implicitly.
- Full mode preserves the native CLI prompt and tool registration, with user discovery junctions. Cleanup may only unlink the five recognized leaf junctions without traversing their targets; refuse other redirected entries.
- This remains an experimental Notion Agent transport. Selected native Skill/file/MCP behaviors are verified in the documented environment; do not expand that to all plugins/subagents, complete API semantic equivalence, independently verified backend weights or zero visible Notion chats.
