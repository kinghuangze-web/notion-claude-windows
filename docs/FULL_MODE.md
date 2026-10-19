# V2：官方 Claude Code 框架 + Notion Opus 5.5

V2 使用原生 Claude Code CLI、默认系统提示词与原生工具注册，通过本机适配器连接自己的 Notion Opus 5.5。`full` 指启动方式保留官方框架，不表示 Notion 通道已经与 Anthropic API 的所有语义等价。已验证范围见 [V2 验证](VALIDATION_V2.md)。

## 安装与启动

按 [Windows 安装](INSTALL_WINDOWS.md) 执行 Setup，并在 8081 管理页由本人导入账号、核对目标工作区。已有 1.0.x 用户先关闭项目 CLI，停止本项目两个网关，再更新仓库、重新运行 Setup；原有账号配置会保留。不要重新导入已删除的旧账号。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\project.ps1 -Action stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\full.ps1 -Stop
git pull --ff-only
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\full.ps1 -WorkDir "D:\MyNotes\Test"
```

人工可双击 `Full-Claude.cmd`，默认工作目录为项目 `demo`。旧 `Claude-Code.cmd` 继续提供精简模式；它不会自动变成 V2。用户原有 CC Switch 配置不由本次安装迁移，指向 8081 的旧供应商也不会自动获得 V2 会话复用。

| 对象 | V2 行为 |
|---|---|
| 模型 | 固定 `claude-opus-5-5`，不接受 Auto 或静默降级 |
| 后端 | 进程级指向 `127.0.0.1:8082`；复用本项目导入的账号目录 |
| 原管理页/精简入口 | 继续使用 8081；两个入口有各自进程记录 |
| 原生提示词 | 不使用 `--bare` 或替换系统提示词，不设 `--tools` 白名单 |
| 用户配置发现 | 读取用户、项目和本地设置；继承用户 `.claude` 的 skills/plugins/agents/commands/hooks 目录 |
| 数据 | 路由、Claude 状态和会话绑定保存在本项目 `runtime/full` |

用户目录通过 Windows Junction 连接；普通 CLAUDE.md/settings 文件复制到独立配置目录，用户级 MCP 注册项从 `.claude.json` 导入。没有复制 Claude 登录/OAuth 文件。MCP 注册配置及普通 settings 本身可能包含私有环境变量，均只留在本机忽略目录。插件在运行中写入共享插件目录仍属于它自己的行为，不承诺全局目录只读。需要 OAuth 的 MCP 是否能在隔离配置中使用须逐项验证。

`acceptEdits` 预批准文件修改，其他工具仍遵循 CLI 权限检查。配置目录隔离不是文件访问沙箱。完整入口允许正常的原生工具发现，具体工具集合依赖已安装的 CLI 和插件版本。

## 会话与聊天列表

V1 每次推理都调用 `createAgentThread`，一次本地工具任务可能产生很多 Notion 聊天。V2 首次创建后保存绑定，后续通过 `sendEventToAgentThread` 在同一个线程发送增量消息，重启后也读取该状态。

一个新 CLI 会话通常仍会创建一个可见 Notion 对话；独立子任务和不同会话可能各有线程。V2 不隐藏、不删除历史对话，也不承诺 Notion 侧栏零变化。已有旧聊天不会在升级时自动消失。

待处理事件在提交前持久化，结果不明时保留状态并恢复原线程，不自动新建替代聊天；历史回退、分支或账号/工作区变更会明确报错。不要在待处理请求中途删除 `runtime/full/sessions` 来强行重试。`--resume` 的状态依赖本地 Claude 历史和此目录同时保留。

## 大型 MCP 工具集合

原生工具完整描述和 schema 直接提供给 Notion；所有 MCP 工具保留可发现名称及摘要。需要特定 MCP 时，适配器的只读内部动作按需返回该工具的原始完整描述和 schema，实际调用仍由官方 CLI 执行。

此设计应对异步发现大量工具后上游 HTTP 413 的问题，避免每轮重复传整个 MCP 注册表。它会增加获取 schema 的上游回合，不是原生 Anthropic tool search 的等价实现。完整原生工具、单个超大 schema 或过长历史仍可能超限；不会通过删工具或换模型来掩盖错误。

## 验收与停止

默认只预览，显式 `-Run` 才发送真实推理。建议先关闭其他 V2 CLI 会话，便于精确检查日志中的单线程计数。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\acceptance-full.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\acceptance-full.ps1 -Run
# 加测真实本机 MCP HMAC；仍在同一个验收会话内完成
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\acceptance-full.ps1 -Run -Mcp
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\full.ps1 -Stop
```

验收创建唯一的 `demo/full/<run-id>`，核对原生 Skill、成功 Read/Write/Edit 结果、随机标记文件、进程成功、上游型号确认与单线程复用。MCP 模式另检查独立工具日志、随机 nonce 和 HMAC。原始事件与摘要位于本机 `evidence`，不公开。`Acceptance-Full.cmd` 是基础验收的人工入口。

错误先检查 `logs/full-gateway.log`。账号可用数为 0 时核对工作区、登录与权益；Basic 超限不能单独证明整个登录账号已无 AI 权益。旧版 529 可能只是适配器无可用账号的映射，不能直接归因为模型本身过载。官方用量页百分比、内部 Basic 数值、Premium credits 和 Token 不是同一指标。

停止只处理 PID、exe 与启动时间一致的本项目进程。清理识别五个用户目录 Junction，先解除链接再删除本机数据，保留源目录；其他重定向路径仍拒绝。详见 [清理](CLEANUP.md)。
