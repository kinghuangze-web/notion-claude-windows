# notion-claude-windows

在 Windows 上将自己的 Notion AI 接入 Claude Code CLI，用固定 Opus 5.5 完成本地文字文件任务。

本项目提供固定版本安装、Opus 5.5 适配、独立启动器、验收和清理脚本。它是基于 [notion_manager](https://github.com/SleepingBag945/notion_manager) 实验性 Agent 通道的 Windows 复现工具包。Notion AI 返回回答和工具指令，Claude Code 在电脑上执行工具。

```text
Claude Code CLI → 本机网关 127.0.0.1:8081 → Notion AI / Opus 5.5
      ↑                   ← 回答或工具指令 ←
      └─ 本机执行 Bash / Read / Edit，再提交工具结果
```

## 开始使用

1. 准备 Windows x64、Git for Windows、Go 1.26+、Python 3.11+、原生 Claude Code CLI。先在自己的 Notion 工作区确认 AI 能用，且可选择 Opus 5.5。
2. 从 **Code → Download ZIP** 下载并解压，放到独立目录，例如 `D:\Projects\notion-claude-windows`。整个项目放在 D 盘，后续缓存和运行数据也跟随项目。
3. 双击 `Setup.cmd`。脚本取得固定上游提交、应用补丁、下载依赖、编译并检查。初次安装需要访问 GitHub、Go 模块服务和 PyPI。
4. 双击 `Start-Gateway.cmd`，在 Chrome 打开 `http://127.0.0.1:8081/dashboard/`。管理密码在本机 `runtime\private\admin-password.txt`。
5. **本人登录 Notion，并将自己的 `token_v2` 仅导入本机管理页**。核对账号和工作区，再用 `Status.cmd` 确认 `usable_accounts` 至少为 1。
6. 双击 `Claude-Code.cmd`，从项目的 `demo` 目录开始测试。默认请求 `claude-opus-5-5`，不降级到 Auto。
7. 按 [验收教程](docs/ACCEPTANCE.md) 执行三个小任务，或双击 `Acceptance.cmd` 运行五项真实验收。真实验收会使用 Notion AI 额度。

首次安装的具体下载选项、命令与成功标志见 [Windows 安装教程](docs/INSTALL_WINDOWS.md)。Cookie 操作见 [账号导入](docs/ACCOUNT_IMPORT.md)。

## 必须本人完成的操作

| 操作 | 原因 |
|---|---|
| 安装已有基础软件，处理安装权限或系统提示 | 安装程序会写入软件目录，本工具包不替用户安装系统软件 |
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
| `Claude-Code.cmd` | 使用固定 Opus 5.5 启动独立 CLI |
| `Status.cmd` | 显示脱敏状态和可用账号数 |
| `Acceptance.cmd` | 五项实际推理与工具验收 |
| `Stop-Gateway.cmd` | 按 PID、exe、启动时间停止本项目网关 |
| `Preview-Cleanup.cmd` | 只显示清理目标，不删除 |

运行后新增 `_source`、`.venv`、`_cache`、`_tmp`、`runtime`、`logs`、`evidence`、`demo`；这些目录均被 Git 排除。项目没有系统服务、计划任务或开机启动。

## 固定模型与能力边界

补丁每次从当前账号的实时模型列表查找 Opus 5.5，显式提交模型 ID，再核对 Notion 返回的 `model`、`selectedModel` 和线程 ID。缺字段、不匹配、型号不可用或请求 Auto，均报错；不会静默降级。实现见 [模型适配](docs/MODEL_AND_LIMITS.md)。

已通过本地 CLI 实测：对话、创建七个中文目录、文件创建与 Read 读回、随机标记盲读、读取 SKILL.md 后执行文件任务。固定模型的依据是 Notion 服务端报告的选择，未独立检查后端模型权重。验证范围见 [验证记录](docs/VALIDATION.md)。

当前精简模式在验收版本中实际提供 Bash、Read、Edit；不自动加载全局配置、插件或外部 MCP。完整插件、MCP、Cowork、原生 Skill 命令、图片/PDF 附件、1M 上下文和长会话稳定性没有纳入本次验收。

## 隐私与清理

本仓库不包含 Cookie、账号、真实配置、API Key、管理密码、会话、原始日志或个人截图。凭证仅在本机 `runtime` 中生成和保存。任务内容及工具返回会通过网关发给 Notion；项目数据目录隔离不等于模型只能访问该目录。

缓存、临时文件、配置和会话随项目目录放置；没有 `setx` 或全局供应商切换。Go、Git、Python、Claude 既有安装可以保留其默认位置，包括 C 盘。Windows、Chrome 和安装器自身仍可能写入 C 盘；没有全盘零写入承诺。

清理先预览，再执行；支持依赖安装失败后清理。具体命令及保留项见 [清理与恢复](docs/CLEANUP.md)。遇到错误先看 [故障排查](docs/TROUBLESHOOTING.md)，分享问题时按 [隐私说明](PRIVACY.md) 脱敏。

## 来源与许可证

- 基础代码：[SleepingBag945/notion_manager](https://github.com/SleepingBag945/notion_manager)，固定提交 `2d6d3dc2fa74f929bd9a8ebd3c1569f5dcca1b88`，对应 [PR #23](https://github.com/SleepingBag945/notion_manager/pull/23)。
- 路线参考：[《Notion AI 接入 Claude Code：从配置到本地任务，手把手跑通》](https://x.com/ElowenY20119/status/2109947661214458149)。原文为 macOS 操作，本项目补充 Windows 流程和固定模型适配。
- 补丁与 Windows 工具包改动说明：[CHANGELOG.md](CHANGELOG.md)。第三方来源：[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

本项目采用与基础代码相同的 [CC BY-NC-SA 4.0](LICENSE)，保留署名、非商业和相同方式共享要求。Claude Code、Go、Python、Git 等软件不随仓库分发。
