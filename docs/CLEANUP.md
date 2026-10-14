# 清理与恢复

关闭本项目 Claude Code 会话，运行 `Preview-Cleanup.cmd` 查看目标。预览不停止进程，也不删除文件。

## 只清除运行数据和依赖

在项目目录打开 PowerShell：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\cleanup.ps1 -Execute
```

删除项目内的 `runtime`、`_cache`、`_tmp`、`.venv`、`demo`、`_source`。包括本地凭证、配置、Claude 会话、验收示例和取得的上游源码。**有需要的 demo 结果先复制到自己选择的目录。**

保留发布源码（scripts/patches）、文档、许可证、logs 和 evidence。日志/证据可能包含任务内容或个人路径，虽然不进入 Git，保留它们仍需本人管理；整项目清理会一并删除。

清理不用 Python 或 Go，因此依赖安装失败或 .venv 已丢失时仍可运行。会先检查项目标记、绝对目标和符号链接，再检查进程归属；已记录的本项目 CLI 会话还在运行时停止清理。网关只在 PID、exe 和启动时间匹配时停止。

## 整个项目都不要

确认本目录没有需要保留的个人文件后：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\cleanup.ps1 -Execute -RemoveProject
```

此命令删除脚本所在的整个项目目录，包括 Git 数据和本地覆盖文件。不会卸载 Go/Git/Python/Claude，也不会删除通过 WorkDir 指定的外部工作目录。

## 重建

部分清理后重新运行 `Setup.cmd`，再启动网关、本人重新导入账号并验收。新的配置会生成新的管理密码和本机 API Key，旧值不能复用。

本项目没有全局服务、自动启动或供应商切换需要撤销。环境变量只在专用进程里覆盖；退出该进程即可结束影响。保留默认 C 盘软件安装不影响清理项目数据。
