# Windows 安装教程

## 1. 确认账号条件

在自己的 Notion 页面进入准备使用的工作区，确认 AI 可以正常回答，并确认当前可用模型包含 Opus 5.5。订阅名称、账号导入成功和该工作区实际可用是三件不同的事。没有可用工作区时，先解决账号权益或额度问题，本机编译不能补充额度。

## 2. 安装基础软件（本人操作）

| 软件 | 官方入口 | 下载与选择 |
|---|---|---|
| Go | [go.dev/dl](https://go.dev/dl/) | 普通 Intel/AMD Windows 电脑下载 `windows-amd64.msi`；要求 1.26 或以上，默认安装目录可以保留 |
| Git for Windows | [git-scm.com/install/windows](https://git-scm.com/install/windows) | Windows x64 安装器，保留 Git Bash，并允许从命令行使用 Git |
| Python | [python.org/downloads/windows](https://www.python.org/downloads/windows/) | Python 3.11+ 的 64 位安装器或官方安装管理器，安装 py 启动器；避免只留下 Microsoft Store 别名 |
| Claude Code CLI | [官方安装说明](https://code.claude.com/docs/en/setup) | 原生 Windows CLI；安装桌面聊天 App 不能代替 CLI |
| Chrome | [google.com/chrome](https://www.google.com/chrome/) | 用于本人登录和查看 Cookie |

当前工具包在 Windows x64 上验证，未做 ARM64 端到端验收。无需 WSL、Node.js、npm、Docker 或单独构建前端。上游固定提交已包含管理页构建文件。

安装完成后重新打开 PowerShell，分别执行：

```powershell
go version
git --version
py -3 --version
claude --version
```

都应返回版本号。Go 默认安装在 `C:\Program Files\Go` 可以保留；项目数据集中到 D 盘不要求搬走已有软件。

## 3. 取得项目

在仓库首页点击 `Code → Download ZIP`，在资源管理器选择“全部提取”，放进独立目录，例如 `D:\Projects\notion-claude-windows`。确保 `Setup.cmd` 与 `scripts` 在同一层。不要在 ZIP 预览窗口中直接运行脚本。

熟悉终端时，也可以：

```powershell
git clone https://github.com/kinghuangze-web/notion-claude-windows.git D:\Projects\notion-claude-windows
Set-Location -LiteralPath D:\Projects\notion-claude-windows
```

目录不存在时才执行克隆；已有同名目录则换一个新名字，避免覆盖现有运行数据。

## 4. 安装和编译

双击 `Setup.cmd`。也可在 PowerShell 执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

脚本会自动检测工具路径。非默认安装可将 `tools.local.ps1.example` 复制为 `tools.local.ps1`，只填需要覆盖的完整 exe 路径。该本地文件不会进入 Git。

安装会完成：固定上游提交下载、Opus 补丁校验与应用、Python 独立环境创建、PyYAML 安装、Go 编译、Windows 适用回归和启动器检查。出现 `Setup complete` 才算这一步完成；第一次依赖下载可能较慢。

PowerShell 执行策略只对这次进程使用 Bypass，没有永久修改系统策略。如果系统阻止下载文件，在 ZIP 文件属性中勾选“解除锁定”后重新解压；不要把关闭系统保护当作安装步骤。组织管理策略阻止脚本时，按组织允许的方式处理。

成功后会生成 `runtime\notion-manager.exe` 和本机随机配置。安装不会启动推理，也不会自动购买套餐、登录账号或导入 Cookie。

## 5. 启动、导入、验收

1. 双击 `Start-Gateway.cmd`，看到本机管理页地址。
2. 按 [账号导入](ACCOUNT_IMPORT.md) 处理自己的登录凭证并核对工作区。
3. 双击 `Status.cmd`：网关应运行，HTTP 检查应为 200，`usable_accounts` 至少为 1。
4. 双击 `Claude-Code.cmd`，按 [验收教程](ACCEPTANCE.md) 做实际任务。

默认端口是 8081。若本机已经有网关占用它，脚本会报错，不会停止其他程序。关闭自己原来的网关，或在本机 `runtime\config.yaml` 中更换 `server.port`；启动器会读取同一配置。真实配置含凭证，不要上传。

## 6. 日常使用

双击 `Claude-Code.cmd` 进入项目 demo。想进入自己的工作目录，明确选择已有目录后执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\project.ps1 -Action claude -WorkDir "D:\MyNotes\Test"
```

先在新建的小目录验收，再进入正式笔记库。外部工作目录中的结果不由项目清理脚本管理。

配置变更后关闭旧 CLI 窗口再重新启动。退出 CLI 后，用 `Stop-Gateway.cmd` 停止网关。关闭浏览器管理页不会停止后台进程。

本工具包的专用入口直接读取本机配置，不要求安装 CC Switch。已有 CC Switch 可以保留；若另行设置入口，默认模型和各档位必须指向 `claude-opus-5-5`，但本文验收对应专用启动器。
