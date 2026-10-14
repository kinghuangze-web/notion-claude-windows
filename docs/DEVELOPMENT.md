# 开发与分发

## 源码布局

公开仓库维护 Windows 脚本和最小适配补丁。Setup 将固定上游源码放入 `_source`，应用 `patches/opus55.patch`。上游管理页已构建，不需要 Node.js 前端安装。当前补丁不增加账号注册、工作区切换或套餐管理功能。

补丁涉及 `internal/proxy/agent_model.go`、对应测试、`agent_thread.go`、`config.go`、`tools.go`。请求先查询实时型号并确认返回字段，再交给现有工具协议转换。`require_opus55` 锁住部署入口，基础 Auto helper 保留用于上游回归。

脚本分工：env.ps1 检测工具并设置进程级路径；manage.py 管理配置、端口、HTTP 检查与网关身份；claude_notion.py 设置客户端供应商和工具；acceptance.py 验收真实模型与产物；cleanup.ps1 负责不依赖虚拟环境的清理。

## 检查

安装默认运行适用 Go 回归和启动器测试。修改脚本后可以在项目 PowerShell 进程执行：

```powershell
. .\scripts\env.ps1
.\.venv\Scripts\python.exe -m unittest discover -s scripts -p test_launcher.py -v
.\.venv\Scripts\python.exe .\scripts\test_lifecycle.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test_cleanup.ps1
.\.venv\Scripts\python.exe .\scripts\check_release.py --check-index
```

生命周期测试用独立临时目录和 18081 端口，不导入账号、不发 Notion 推理，检查启动复用、PID 时间校验、停止和重启。该端口若被占用应先检查，不停止其他服务。

真实验收需本人导入可用账号，再显式运行 Acceptance.cmd；不能将本地 HTTP 检查当作已通过上游推理。

## 发布规则

`release-files.txt` 是完整白名单；Git 跟踪文件必须与其相同。分发只包含白名单文件，禁止把整个运行目录压缩上传。所有脚本、文档、补丁均为 UTF-8；PowerShell 5.1 含非 ASCII 的脚本需保留 UTF-8 BOM，文本补丁使用 LF。

原始日志、会话、工作区标识和私人 Git 历史不发布。公开验证记录只保留环境版本、范围、检查结果和合成任务说明。任何二进制分发需另做干净构建及来源核验，不从当前用户 runtime 直接取包。

复现环境和原始验收边界见 VALIDATION.md。许可证和来源见 LICENSE 与 THIRD_PARTY_NOTICES.md。
