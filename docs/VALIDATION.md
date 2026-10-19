# Verification scope / 验证范围

Date / 日期：2026-10-19。Evidence is scoped to the environment and behavior below. Raw sessions, identifiers, account data, user paths and file contents are not distributed.

## Real upstream behavior / 真实上游行为

- Isolated native CLI 2.1.300: native Skill, exact Read/Write/Edit/Read file round-trip and actual local MCP nonce/HMAC passed. One CLI session had 18 successful upstream turns with one Notion thread. Initial tool/Skill registration and later dynamic tool counts are discovery evidence, not proof every tool ran.
- Ordinary installed CLI 2.1.303: tested from the actual user working directory with the existing CC Switch route, normal user configuration and auto mode. No launcher, alternate config directory or process route override. Reply and resumed Read → Write → Edit → Read passed, with exact random file bytes and final success. Six successful upstream turns used one creation and five continuations.
- Requested/confirmed/selected model fields matched the live Opus 5.5 selection. This does not independently verify model weights.
- The older 8081 deployment previously failed with upstream HTTP 400; its actual installation was upgraded. The isolated launcher result had not covered this path. The README incident notice documents the gap.

隔离环境验证过原生 Skill、文件闭环和独立 MCP 证明；普通入口另外在真实用户工作目录、原 CC Switch 路由、auto 模式下验证了对话、文件和恢复。两个环境的证据分开使用，不把工具注册当作执行成功。

## Current agent-only packaging / 本轮 Agent 版本

The transport patch was retained. The supported entry now uses one V2 gateway, preserves native settings discovery and removes the old slim and isolated-directory launchers.

Checks cover:

- Native prompt/tool discovery preserved; parent route/application-data/config-directory variables unchanged; only child API routing changes.
- V2 configuration migration preserves previous values and stores an exact local backup.
- Old running process records cannot report V2 readiness. The executable hash must match its V2 build record; a changed binary requires rebuilding.
- Fresh patch application, older-source migration and repeated setup compatibility.
- Real executable lifecycle on an account-free fixture port: owned startup/reuse/stop/restart, stale-PID refusal and loopback authentication. Zero Notion inference requests.
- Preview-first cleanup, invalid-root refusal, owned session/process checks and preservation of the source of known older Junctions.
- Allowlist/index scanning, full reachable-history/identity scanning, exact known-private-value comparison and a deleted-secret regression.
- Python/PowerShell syntax, inference-free acceptance preview and installed native CLI version execution.

当前改动主要是入口收敛、配置迁移、状态检查和隐私扫描。上述本地检查不构成新的模型推理成功记录；本轮没有为源码审计重复运行大套真实推理。合成验收仍须按 README 在目标部署执行，且不能替代用户真实入口验证。

## Not established / 尚未证明

Complete Anthropic API semantics, every registered plugin/MCP/subtask, image/PDF model attachments, long-context compression, long-term concurrent reliability, token/cost accounting and official cloud features are not certified. The bridge uses Notion Agent's text transport; keeping native prompt text does not independently prove identical upstream role priority.

全部 API 语义、所有插件/MCP/子任务、附件、长上下文压缩、长期并发、Token/费用与官方云功能没有等价认证。新会话仍可能产生可见 Notion 对话；历史聊天不会自动删除。
