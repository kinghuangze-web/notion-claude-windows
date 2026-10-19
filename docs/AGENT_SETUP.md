# Agent 执行流程

面向具备 Windows 命令执行权限的开发 Agent。安装、编译、启动和状态检查使用非交互 PowerShell 脚本；登录 Notion 与导入 token_v2 是人工步骤。无需额外安装本项目 Skill 或 MCP。

## 1. 取得项目和检查依赖

在用户指定的独立目录克隆仓库；未指定时选择 D 盘新目录，已有同名目录先检查，不覆盖。

```powershell
git clone https://github.com/kinghuangze-web/notion-claude-windows.git D:\Projects\notion-claude-windows
Set-Location -LiteralPath D:\Projects\notion-claude-windows
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\doctor.ps1
```

doctor 输出 JSON：`ready_for_setup`、`missing_dependency` 或 `unsupported_platform`。它检查路径，不创建数据目录或修改环境；版本检查由 Setup 执行。缺依赖时按 [安装教程](INSTALL_WINDOWS.md) 提供准确软件和下载选项，在用户授权范围内处理安装，不把 Go/Python/Git 重装到另一位置。

## 2. 安装、启动和本地检查

依次执行，每条成功后才执行下一条：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\project.ps1 -Action start
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\project.ps1 -Action verify-local
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\project.ps1 -Action ready
```

不用 Setup.cmd、Status.cmd 等带 pause 的包装器。编译前若本项目网关仍在运行，先核对状态并停止该网关；其他程序占用端口时不得直接结束它。网关 API Key 和管理密码由本机生成，不需要用户在聊天中提供。

## 3. 按状态继续或交接

| ready 的 state | 退出码 | 下一步 |
|---|---|---|
| awaiting_setup | 2 | 安装尚未完成，检查配置和 exe 是否生成 |
| awaiting_gateway | 2 | 启动属于本项目的网关 |
| awaiting_account | 3 | 给用户本机 dashboard_url 和账号导入教程，等待本人操作 |
| ready_for_acceptance | 0 | 只表示可开始验收，还不能声明推理已验证 |
| invalid_configuration / gateway_unhealthy / process_identity_mismatch | 4 | 按具体原因修复，不改回 Auto，不停止归属不符的进程 |

`awaiting_account` 时只交接这项必要人工操作：在已登录 Notion 的 Chrome 中取自己的 token_v2，直接粘贴到本机管理页。具体位置和复制方法见 [账号导入](ACCOUNT_IMPORT.md)。不要让用户将值发给 Agent，不自动读取浏览器凭证，不保存包含真实 Cookie 的截图。

用户完成后，重新执行 ready，确认可用账号数。识别的工作区不对或额度不足时，需要本人在本机界面处理；同名工作区也可能有不同权益。

## 4. 实际验收

部署并验证此项目的授权包含真实测试时，执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\acceptance-full.ps1 -Run
```

用户只要求查看或预检时，省略 `-Run`。V2 原生 Skill/文件/单线程验收、原始事件和文件结果写在本机忽略目录中；要求进程成功退出且本次 `evidence/<run-id>-v2-official-cli-summary.json` 的 passed 为 true。加 `-Mcp` 可检查本机 MCP HMAC。旧五项套件保留为 V1，避免用它测试 V2 聊天复用。验收失败需查看本地证据，不能只引用模型“完成了”的回答。测试会使用 Notion AI 额度。

## 5. 后续任务和交付

在用户指定目录执行非交互小任务可使用专用入口，例如：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\full.ps1 -WorkDir "D:\MyNotes\Test" --print "先读取当前目录的 README.md，只返回摘要，不修改文件。"
```

V2 保留原生工具注册与默认提示词，继承已有用户发现目录；旧精简入口才限制为 Bash/Read/Edit。完整用法见 [V2 入口](FULL_MODE.md)。当前桥接的消息、上下文和推理控制限制见 [模型与能力边界](MODEL_AND_LIMITS.md)。任务结束报告状态、验证对象和证据位置；若无需继续运行，分别停止本项目 8081 与 V2 8082 网关。清理前预览并保留用户需要的结果。
