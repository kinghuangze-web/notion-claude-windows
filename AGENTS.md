# Agent execution contract

Goal: install this Windows x64 toolkit in a dedicated directory, load its locked Opus 5.5 gateway, and verify real file operations. Follow docs/AGENT_SETUP.md; preserve existing runtime configuration and unrelated installations.

- Run PowerShell scripts directly, not the .cmd wrappers that wait for a human keypress.
- Start with scripts/doctor.ps1. Setup checks versions, downloads the pinned source and applies the patch; do not improvise a different upstream version.
- Keep process-local data paths from env.ps1. Do not use setx, change global providers, install services, or stop a process merely because it occupies the desired port.
- Use project.ps1 -Action ready for the state/exit-code contract. awaiting_account is a human handoff, not successful setup of inference.
- Ask the user to follow docs/ACCOUNT_IMPORT.md locally. Do not ask them to paste token_v2 into agent chat or tool arguments, and do not retrieve browser login secrets automatically. This toolkit has no credential-extraction automation.
- After the user reports import completed, inspect readiness again; do not treat their message or HTTP 200 alone as inference verification.
- Run acceptance.ps1 -Run within an authorized live-testing scope. It consumes allowance and creates local demo files. Require actual successful tool results, file bytes and upstream model confirmations before reporting verified.
- Scope subsequent tasks to the user-selected work directory. A process data directory is not a filesystem sandbox.
- Report only redacted states and failure causes. Never publish runtime, logs, evidence, demo, private overrides or cookies. Git tracked paths must equal release-files.txt.
- Preserve failure evidence locally. Cleanup is preview-first and must not remove user task outputs without authorization; use docs/CLEANUP.md.
- This is an experimental minimal CLI bridge. Do not claim full Claude Code, native Skill/MCP/plugin/subagent support or independently verified backend weights.
