# notion-claude-windows

[中文 Agent 教程](#中文agent-教程) · [English agent guide](#english-agent-guide)

## 中文：Agent 教程

### 目标与约束

在 Windows x64 上，将用户自己的 **Notion Opus 5.5** 接入**原生 Claude Code**，保留默认系统提示词、原生工具和正常的用户/项目 Skills、插件与 MCP 发现。同一会话通过持久化线程增量续写。

本仓库面向执行 Agent，只支持 V2。已移除 bare 精简启动器、受限工具白名单、双击包装器及重复教程；默认只有一个 `127.0.0.1:8081` 网关。不要为了通过测试而替换模型后端、框架或用户实际入口。

型号依赖 Notion 服务端字段确认，未独立验证权重。上游仍是 Notion Agent 文本协议，全部 API 语义、插件、附件和长期稳定性没有等价认证。[验证范围](docs/VALIDATION.md) · [开发日志](docs/DEVLOG.md) · [隐私审计](docs/PRIVACY_AUDIT.md)。

### 1. 定位真实安装并检查依赖

先读 [AGENTS.md](AGENTS.md)，确认用户真正使用的工作目录、CLI 命令、供应商选择、本机地址和所属安装。已有安装先检查进程与 Git 状态，保留个人文件和未提交改动；不按端口直接结束未知进程。

新安装使用独立目录，已有仓库则复用：

```powershell
git clone https://github.com/kinghuangze-web/notion-claude-windows.git D:\Projects\notion-claude-windows
Set-Location -LiteralPath D:\Projects\notion-claude-windows
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\doctor.ps1
```

依赖：Git for Windows、Go 1.26+、Python 3.11+、原生 Claude Code CLI。`doctor` 返回 JSON；在任务授权内处理具体缺项。路径覆盖可用忽略的 `tools.local.ps1`，模板为 `tools.local.ps1.example`。不修改系统代理、全局环境、其他供应商或安装开机服务。

### 2. 编译并启动实际 V2 网关

升级前先停止本安装已记录的网关。已在使用的安装应在原位置升级，不能用另一个测试网关代替。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\project.ps1 -Action stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\project.ps1 -Action start
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\project.ps1 -Action verify-local
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\project.ps1 -Action ready
```

Setup 固定上游提交 `2d6d3dc2fa74f929bd9a8ebd3c1569f5dcca1b88`，应用累积补丁后编译。旧源码补丁仅用于升级，不保留旧运行模式。已有配置先备份，只补齐 V2 开关，保留地址、Key、账号目录和其他字段。构建记录会绑定实际 exe 的 SHA-256，缺失或不匹配时必须重建；旧进程不能被当成 V2 就绪。

| 状态 | 退出码 | Agent 下一步 |
|---|---:|---|
| `awaiting_setup` / `awaiting_gateway` | 2 | 完成构建或启动正确网关 |
| `awaiting_account` | 3 | 请所有者在本机登录/导入自己的 Notion 会话并核对工作区，再重新检查；不索要聊天凭证，不自动提取浏览器凭证 |
| `ready_for_acceptance` | 0 | 仅可开始验收，尚未验证推理 |
| `gateway_needs_rebuild` | 4 | 缺少或不匹配的 V2 构建记录，重新 Setup |
| `gateway_needs_v2_restart` | 4 | 确认归属后停止、重启；改文件不等于进程已加载 |
| 其他错误 | 4 | 按具体配置、归属、认证或健康原因修复，不降级 Auto |

管理页地址由状态返回，密码只留在本机 `runtime/private/admin-password.txt`。Cookie、Key、密码、工作区标识和原始日志不得公开。Basic 数值、Premium credits、官方用量百分比与 Token 不可混用；同一登录下的工作区权益可能不同。

### 3. 接入用户真实入口

**用户使用 CC Switch 后直接启动 Claude 时：**核对实际选中的 Notion 供应商、普通 Claude 生效配置、地址和 Key。需要改动时，只在所请求的接入范围内备份并更新该 Notion 供应商，保留其他供应商和普通设置；凭证只在本机处理。重开普通 CLI 后，按原目录和原启动方式验证，不用另一个配置目录或临时路由覆盖替代。

**Agent 自己需要非交互调用时：**下列入口只给子进程设置本机路由，保留完整原生 CLI、配置发现和权限，不改 CC Switch 或全局 settings：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\project.ps1 -Action claude -WorkDir "D:\Projects\Target" --print "读取当前目录 README.md，只返回摘要，不修改文件。"
```

这不等于用户普通入口已验证。已有自定义 `CLAUDE_CONFIG_DIR` 会保留；本项目不建立另一套 Claude 用户目录或 Junction。固定 `claude-opus-5-5`，禁止 Auto/其他型号，不使用 bare、替换系统提示词或工具白名单。

### 4. 真实验收与完成条件

授权包含真实测试时，验证原生 Skill、Read/Write/Edit 和单线程复用。默认仅预览，显式 `-Run` 才消耗 Notion 额度；`-Mcp` 加测实际本机 MCP 的随机 nonce/HMAC：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\acceptance.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\acceptance.ps1 -Run
# 需要 MCP 验证时再执行；不重复已满足要求的检查
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\acceptance.ps1 -Run -Mcp
```

必须同时满足：CLI 返回 0、最终 `is_error=false`、实际成功的 Skill/Read/Write/Edit 事件、随机输入对应的精确文件字节、上游型号一致，以及一个会话只有一次线程创建。MCP 还需独立调用日志和 HMAC 一致。避免其他会话干扰日志计数，但不能结束不属于本任务的会话。

随后在**用户真实工作目录和普通入口**做最小对话、随机文件读写及恢复验证。保留配置前后摘要、实际结果和失败证据；只清除本任务创建且不再需要的临时夹。所有原始事件与证明留在忽略目录。

### 事故注意事项：独立入口成功不等于用户能用

曾出现：独立 V2 测通并上传仓库，但 CC Switch 仍指向运行中的旧 `8081`，独立新网关未启动。用户普通 Claude 持续重试，上游 HTTP 400。把局部测试描述为日常可用，超出了证据范围。

修正升级了**实际使用的网关**，保留地址、Key、账号和用户 settings。原生 CLI 2.1.303 在用户目录、auto 模式下完成对话及 `Read → Write → Edit → Read`，6 个成功上游回合仅创建 1 个线程。当前流程默认启用 V2、拒绝旧进程就绪，并增加迁移回归。

交付前逐项核对：**用户入口 → 生效配置 → API 地址 → 进程/二进制 → V2 启动方式 → 真实上游 → 工具和文件 → 最终成功**。模型标题/列表、HTTP 200、GitHub 提交或中间文件均不充分。新会话通常仍产生一个 Notion 对话；不自动删除旧聊天。

### 5. 发布、隐私与清理

```powershell
.\.venv\Scripts\python.exe .\scripts\check_release.py --check-index
.\.venv\Scripts\python.exe .\scripts\audit_history.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\cleanup.ps1
```

只发布 `release-files.txt` 白名单，核对当前内容、Git 跟踪范围、历史内容与提交身份。精确私有值匹配可用 `audit_history.py --private-values-file`，输入只可放在忽略的 `runtime/private`，输出不展示匹配值。历史删除不能撤销凭证；本次未发现需要清理的泄漏，因此未重写历史。

清理默认预览；已有删除授权且结果保留后再加 `-Execute`，整项目删除另加 `-RemoveProject`。保护进程归属和目标边界；旧 Junction 仅作安全解链接兼容。凭证、日志、会话和测试数据不发布。应用数据隔离不是文件沙箱，也不承诺 Windows 全盘零写入。

许可证：[CC BY-NC-SA 4.0](LICENSE)；来源：[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## English: Agent guide

### Goal and constraints

Connect the owner's **Notion Opus 5.5** to **native Claude Code** on Windows x64. Preserve the default system prompt, native tools and normal user/project Skills, plugin and MCP discovery. Persist the backend thread and submit incremental turns.

This repository is for execution agents. V2 is the only supported runtime. Bare/slim launchers, restricted tool lists, double-click wrappers and duplicate tutorials are removed. The default is a single `127.0.0.1:8081` gateway. Do not substitute another model provider, framework or user entry point to make a test pass.

Model confirmation uses Notion's reported fields, not independent weight verification. Messages still use the Notion Agent text protocol; complete API equivalence, every plugin, attachments and long-term reliability are not certified. See [validation](docs/VALIDATION.md), [development log](docs/DEVLOG.md) and [privacy audit](docs/PRIVACY_AUDIT.md).

### 1. Locate the actual installation and check dependencies

Read [AGENTS.md](AGENTS.md). Identify the user's real directory, CLI command, selected provider, local address and owning installation. Inspect existing processes and Git changes; preserve personal files and uncommitted work. Never kill an unknown listener merely because it owns the desired port.

Use a dedicated directory for a new installation, or reuse the existing checkout:

```powershell
git clone https://github.com/kinghuangze-web/notion-claude-windows.git D:\Projects\notion-claude-windows
Set-Location -LiteralPath D:\Projects\notion-claude-windows
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\doctor.ps1
```

Requirements: Git for Windows, Go 1.26+, Python 3.11+, native Claude Code CLI. `doctor` returns JSON; resolve specific missing dependencies within task authorization. Optional paths belong in ignored `tools.local.ps1`; use `tools.local.ps1.example`. Do not change system proxies, global environment, unrelated providers or startup services.

### 2. Build and start the actual V2 gateway

Stop this installation's recorded gateways before upgrading. Upgrade an in-use installation in its actual location rather than substituting an unrelated test instance.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\project.ps1 -Action stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\project.ps1 -Action start
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\project.ps1 -Action verify-local
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\project.ps1 -Action ready
```

Setup pins upstream `2d6d3dc2fa74f929bd9a8ebd3c1569f5dcca1b88`, applies the cumulative patch and builds it. The older-source patch is migration-only. Existing configuration is backed up before enabling V2, preserving address, Key, accounts and other values. A build record binds the actual executable SHA-256; missing or mismatched records require rebuilding. An old process cannot count as V2 readiness.

| State | Exit | Agent action |
|---|---:|---|
| `awaiting_setup` / `awaiting_gateway` | 2 | Build or start the correct gateway |
| `awaiting_account` | 3 | Ask the owner to authenticate/import locally and confirm the workspace, then recheck. Never request credentials in chat or automatically extract browser credentials |
| `ready_for_acceptance` | 0 | Acceptance may begin; inference is not verified |
| `gateway_needs_rebuild` | 4 | 缺少或不匹配的 V2 构建记录，重新 Setup |
| `gateway_needs_rebuild` | 4 | Missing/mismatched V2 build record: rerun setup |
| `gateway_needs_v2_restart` | 4 | Verify ownership, stop and restart; edited files do not prove a process reloaded them |
| Other errors | 4 | Fix the specific configuration, ownership, authentication or health failure without Auto fallback |

Status returns the dashboard address; its password stays in `runtime/private/admin-password.txt`. Never publish cookies, Keys, passwords, workspace identifiers or raw logs. Basic counts, Premium credits, official usage percentages and tokens are different measurements. Workspaces under one login can have different entitlements.

### 3. Connect the actual user entry point

**For CC Switch followed by ordinary Claude:** verify the selected Notion provider, effective ordinary Claude settings, address and Key against the actual gateway. Within the requested integration scope, back up and update only that Notion provider when necessary; preserve unrelated providers and settings. Handle secrets locally. Restart ordinary Claude and test the original directory/startup method without alternate config directories or temporary route overrides.

**For an agent's own non-interactive call:** the following routes only the child process. It preserves the full native CLI, configuration discovery and permissions, without changing CC Switch or global settings:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\project.ps1 -Action claude -WorkDir "D:\Projects\Target" --print "Read the current README.md and summarize it without editing files."
```

This does not establish that the user's ordinary entry works. An existing custom `CLAUDE_CONFIG_DIR` is retained; no alternate Claude user directory or Junction is created. The model is fixed to `claude-opus-5-5`: no Auto/other-model fallback, bare mode, replacement system prompt or tool whitelist.

### 4. Live acceptance and completion

When live tests are authorized, verify native Skill, Read/Write/Edit and one-thread reuse. The default is an inference-free preview; `-Run` consumes Notion allowance. `-Mcp` adds a real local MCP nonce/HMAC proof:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\acceptance.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\acceptance.ps1 -Run
# Add MCP verification only when needed; do not repeat sufficient checks
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\acceptance.ps1 -Run -Mcp
```

Require exit 0, final `is_error=false`, successful native Skill/Read/Write/Edit events, exact file bytes from random input, matching upstream model confirmation and one backend thread creation. MCP also needs an independent call log and matching HMAC. Avoid unrelated activity when counting logs, but never terminate another task's sessions.

Then verify a minimal reply, random file round-trip and resume through the **actual user directory and ordinary entry point**. Keep configuration summaries, actual results and failures. Remove only temporary artifacts owned by this task. Raw events and proofs remain in ignored directories.

### Incident notice: isolated success did not establish user usability

An isolated V2 test passed and was published, while CC Switch still pointed at a running old `8081` gateway and the separate new gateway was not running. Ordinary Claude retried and the old upstream returned HTTP 400. Calling that isolated result working daily use exceeded the evidence.

The fix upgraded the **gateway actually used**, preserving address, Key, accounts and user settings. Native CLI 2.1.303 in the user's directory, auto mode, passed a reply and `Read → Write → Edit → Read`; six successful upstream turns used one thread. The current flow enables V2 by default, rejects old-process readiness and tests migration.

Before delivery, verify **user entry → effective settings → API address → process/binary → V2 startup mode → real upstream → tools/files → final success**. A model title/list, HTTP 200, GitHub commit or intermediate file is insufficient. A new session normally still creates a Notion conversation; old conversations are not deleted automatically.

### 5. Release, privacy and cleanup

```powershell
.\.venv\Scripts\python.exe .\scripts\check_release.py --check-index
.\.venv\Scripts\python.exe .\scripts\audit_history.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\cleanup.ps1
```

Release only the `release-files.txt` allowlist. Check current contents, tracked paths, history and commit identities. Optional exact matching uses `audit_history.py --private-values-file`; input must stay in ignored `runtime/private`, and matched values are never printed. Removing history does not revoke credentials. No leak requiring history cleanup was found in this review, so history was not rewritten.

Cleanup previews by default. Once deletion is authorized and needed results are preserved, add `-Execute`; use `-RemoveProject` only for whole-project removal. Enforce ownership and path boundaries. Older Junctions are recognized solely for safe unlinking. Credentials, logs, sessions and test data are never published. Application data isolation is not a filesystem sandbox or a zero-system-drive-write guarantee.

License: [CC BY-NC-SA 4.0](LICENSE). Attribution: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
