# notion-claude-windows

在 Windows 上将自己的 Notion AI 接入 Claude Code CLI，以官方 CLI 框架、默认提示词、原生 Skills 和工具运行本地任务。

V2 新增会话复用、完整模式入口和大型 MCP 工具目录；旧精简入口继续保留。本项目提供固定版本安装、Opus 5.5 适配、独立启动器、验收和清理脚本。它是基于 [notion_manager](https://github.com/SleepingBag945/notion_manager) 实验性 Agent 通道的 Windows 复现工具包。Notion AI 返回回答和工具指令，Claude Code 在电脑上执行工具。

```text
官方 Claude Code CLI → V2 网关 127.0.0.1:8082 → Notion AI / Opus 5.5
      ↑                     ← 同线程续写/工具指令 ←
      └─ 本机执行原生工具 / Skill / MCP，再提交结果
账号管理与旧精简入口：127.0.0.1:8081
```

## 交给 Agent 执行

将仓库链接和下面这段任务交给能执行 Windows 命令的 Agent：

```text
在 Windows 的 D 盘独立目录部署 https://github.com/kinghuangze-web/notion-claude-windows 。
先读取 AGENTS.md 和 docs/AGENT_SETUP.md，检查依赖，执行固定版本安装、启动和本地检查。
账号未导入时，给出本机管理页地址及 token_v2 获取步骤，等我本人在本机导入；不要让我把凭证发到聊天。
导入后使用 V2 Full-Claude 入口并运行 acceptance-full.ps1 -Run，核对原生 Skill、真实文件、上游模型与单线程复用；需要时加 -Mcp。不要修改全局供应商配置，保留清理入口和失败证据。
```

项目已有非交互安装、启动和验收脚本。新增 `doctor.ps1` 返回依赖检查 JSON，`project.ps1 -Action ready` 返回当前阶段和退出码。具体命令及状态处理见 [Agent 执行流程](docs/AGENT_SETUP.md)。`.cmd` 包装器供人工双击使用，Agent 直接运行 `.ps1`，避免 pause 等待。

如果你使用 **CC Switch 切到 Notion，然后在任意目录直接运行 Claude**，请按 [普通命令接入](docs/CC_SWITCH.md) 升级并启用实际 8081 网关。独立 V2 入口测通不会自动改变旧供应商；普通路径已另用 Claude Code 2.1.303、auto 模式和真实文件工具验证。

## 手动开始使用

1. 准备 Windows x64、Git for Windows、Go 1.26+、Python 3.11+、原生 Claude Code CLI。先在自己的 Notion 工作区确认 AI 能用，且可选择 Opus 5.5。
2. 从 **Code → Download ZIP** 下载并解压，放到独立目录，例如 `D:\Projects\notion-claude-windows`。整个项目放在 D 盘，后续缓存和运行数据也跟随项目。
3. 双击 `Setup.cmd`。脚本取得固定上游提交、应用补丁、下载依赖、编译并检查。初次安装需要访问 GitHub、Go 模块服务和 PyPI。
4. 双击 `Start-Gateway.cmd`，在 Chrome 打开 `http://127.0.0.1:8081/dashboard/`。管理密码在本机 `runtime\private\admin-password.txt`。
5. **本人获取并导入 `token_v2`**：在已登录 Notion 的 Chrome 页面按 `F12` 或 `Ctrl + Shift + I`，选择 `Application（应用）→ Storage（存储）→ Cookies → 当前 Notion 域名`，在 Name 列找到 `token_v2`，复制这一行完整的 **Value**，直接粘贴到本机管理页“添加账号”的输入框。看不到 Application 时点击顶部 `»`；[完整位置说明与排错](docs/ACCOUNT_IMPORT.md)。核对账号和工作区，再用 `Status.cmd` 确认 `usable_accounts` 至少为 1。
6. 双击 `Full-Claude.cmd` 使用 V2，从项目的 `demo` 目录开始测试。默认请求 `claude-opus-5-5`，不降级到 Auto。已有版本先停止网关并重新 Setup；[升级与使用](docs/FULL_MODE.md)。
7. 双击 `Acceptance-Full.cmd` 验证原生 Skill、Read/Write/Edit 与单线程复用，或按 [V2 教程](docs/FULL_MODE.md) 加测真实 MCP。验收会使用 Notion AI 额度。旧 `Acceptance.cmd` 仍是 V1 五项套件。

首次安装的具体下载选项、命令与成功标志见 [Windows 安装教程](docs/INSTALL_WINDOWS.md)。Cookie 操作见 [账号导入](docs/ACCOUNT_IMPORT.md)。

## 必须本人完成的操作

| 操作 | 原因 |
|---|---|
| 处理需要交互的安装权限或系统提示 | Agent 可在已授权范围内检查、安装依赖；本工具包不自动安装系统软件 |
| 登录 Notion，确认账号与目标工作区的 AI 权益 | 登录会话和权益属于自己的账号 |
| 在 Chrome 查看并导入自己的 token_v2 | 它是敏感登录凭证，仓库没有预置账号 |
| 在本机管理页核对识别的账号、工作区及可用状态 | 同一账号的不同工作区可能有不同额度 |
| 同意 CLI 的目录信任或工具权限提示 | 本地工具会读写当前工作目录 |
| 验收后查看真实目录和文件，再决定是否用于自己的项目 | 聊天中的“已完成”不能代替文件结果 |

## Windows 的差异

- Chrome 开发者工具：`F12` 或 `Ctrl + Shift + I`；也可从右上角 `⋮ → 更多工具 → 开发者工具` 打开。Mac 的 `Option + Command + I` 不适用于 Windows。
- Cookie 路径：`Application（应用）→ Storage（存储）→ Cookies`，选择当前 Notion 页面对应的域名。顶部没有 Application 时，点击 `»` 展开隐藏选项。
- 项目控制使用 Windows PowerShell 和 `.cmd`；模型执行 Bash 时使用 **Git for Windows 的 Bash**，不要求安装 WSL。Git Bash 中的 `/d/Projects/...` 与 `D:\Projects\...` 可指同一位置。
- 凭证权限使用 NTFS ACL；上游一项 Unix 文件权限断言不适用于 Windows，其余 Go 回归仍执行。

## 文件与入口

| 入口 | 功能 |
|---|---|
| `Setup.cmd` | 安装项目依赖、取得固定源码、应用补丁、编译和检查 |
| `Start-Gateway.cmd` | 启动或复用属于本项目的网关 |
| `Full-Claude.cmd` | V2：官方默认提示词、原生工具和 Skills，自动启动独立 8082 网关 |
| `Claude-Code.cmd` | V1：保留原 Bash/Read/Edit 精简入口 |
| `Acceptance-Full.cmd` | V2 原生 Skill、文件、模型确认与单线程验收 |
| `Stop-Full-Gateway.cmd` | 停止属于本项目的 V2 网关 |
| `Status.cmd` | 显示脱敏状态和可用账号数 |
| `Acceptance.cmd` | 五项实际推理与工具验收 |
| `Stop-Gateway.cmd` | 按 PID、exe、启动时间停止本项目网关 |
| `Preview-Cleanup.cmd` | 只显示清理目标，不删除 |

运行后新增 `_source`、`.venv`、`_cache`、`_tmp`、`runtime`、`logs`、`evidence`、`demo`；这些目录均被 Git 排除。项目没有系统服务、计划任务或开机启动。

## 固定模型与能力边界

补丁每次从当前账号的实时模型列表查找 Opus 5.5，显式提交模型 ID，再核对 Notion 返回的 `model`、`selectedModel` 和线程 ID。缺字段、不匹配、型号不可用或请求 Auto，均报错；不会静默降级。实现见 [模型适配](docs/MODEL_AND_LIMITS.md)。

V2 真实试验通过原生 Skill、连续 Read → Write → Edit → Read、独立 MCP HMAC 和恢复；同一个 CLI 会话 18 个成功上游回合只创建 1 个 Notion 对话。初始 23 项工具、21 项 Skill，动态观察到 252 项总工具，不代表每个工具都执行过。固定模型依据为 Notion 服务端报告，未独立检查后端权重。[V2 验证范围](docs/VALIDATION_V2.md)。

V2 保留官方 CLI 框架和默认提示词，但上游消息仍经过 Notion 文本协议；全部原生角色语义、所有插件/MCP、附件、长上下文压缩和长期并发没有等价认证。新会话通常仍生成一个可见 Notion 对话，旧聊天不会自动删除。旧精简入口的限制与历史证据见 [模型边界](docs/MODEL_AND_LIMITS.md) 和 [V1 验证](docs/VALIDATION.md)。

更新方案与开发过程见 [V2 方案](docs/V2_PLAN.md)、[开发日志](docs/DEVLOG.md)。公开包安装/生命周期检查和先前隔离环境真实推理分开记录，不把本地健康检查当作账号已通过推理。

## 隐私与清理

本仓库不包含 Cookie、账号、真实配置、API Key、管理密码、会话、原始日志或个人截图。凭证仅在本机 `runtime` 中生成和保存。任务内容及工具返回会通过网关发给 Notion；项目数据目录隔离不等于模型只能访问该目录。

缓存、临时文件、配置和会话随项目目录放置；没有 `setx` 或全局供应商切换。Go、Git、Python、Claude 既有安装可以保留其默认位置，包括 C 盘。Windows、Chrome 和安装器自身仍可能写入 C 盘；没有全盘零写入承诺。

清理先预览，再执行；支持依赖安装失败后清理。具体命令及保留项见 [清理与恢复](docs/CLEANUP.md)。遇到错误先看 [故障排查](docs/TROUBLESHOOTING.md)，分享问题时按 [隐私说明](PRIVACY.md) 脱敏。

## 来源与许可证

- 基础代码：[SleepingBag945/notion_manager](https://github.com/SleepingBag945/notion_manager)，固定提交 `2d6d3dc2fa74f929bd9a8ebd3c1569f5dcca1b88`，对应 [PR #23](https://github.com/SleepingBag945/notion_manager/pull/23)。
- 路线参考：[《Notion AI 接入 Claude Code：从配置到本地任务，手把手跑通》](https://x.com/ElowenY20119/status/2109947661214458149)。原文为 macOS 操作，本项目补充 Windows 流程和固定模型适配。
- 补丁与 Windows 工具包改动说明：[CHANGELOG.md](CHANGELOG.md)。第三方来源：[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

本项目采用与基础代码相同的 [CC BY-NC-SA 4.0](LICENSE)，保留署名、非商业和相同方式共享要求。Claude Code、Go、Python、Git 等软件不随仓库分发。
