# 实际验收

管理页可打开、账号可导入、模型界面显示 Opus 都不足以证明本地任务能跑。验收要核对真实工具结果、文件和上游模型记录。

## 手动按文章验收

通过 `Claude-Code.cmd` 进入 demo；下面三个任务分别输入 **Claude Code 对话框**，不是 PowerShell。每项完成后检查真实产物。

### 1. 连接

```text
请只回复：连接成功。
```

应有实际回复；HTTP 错误或模拟返回不能算通过。

### 2. 中文目录

```text
先执行 pwd 确认当前目录。在当前目录下创建“日常记录”，里面创建周一、周二、周三、周四、周五、周六、周日七个子目录。完成后执行 ls 列出并核验。只操作当前目录；已有目录则先说明，不覆盖已有内容。
```

在资源管理器打开 demo，确认七个目录确实存在。同时检查 CLI 中是否有成功的 Bash 工具结果。

### 3. 文件写入和读回

```text
在“日常记录/周一”创建“测试笔记.md”，内容只有一行：
NOTION_LOCAL_TEST_20261013
通过 Bash 的 noclobber 防止覆盖，然后调用 Read 工具重新读取文件，把真实读到的内容原样返回。若同名文件已存在，停止，不覆盖。只操作当前目录。
```

打开实际文件，应只有该标记加一个换行；CLI 中要有成功的写入工具结果和 Read 结果。只有模型在聊天里返回命令或声称写好了不算通过。

## 自动五项验收

账号导入并可用后，双击 `Acceptance.cmd`，或：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\acceptance.ps1 -Run
```

省略 `-Run` 只预览阶段，不发推理请求。每次实际运行新建独立 demo 目录，不覆盖以前结果；会消耗 Notion AI 额度。

五项包括文章上述三项，再加：

- **随机盲读**：本机生成随机内容，提示词只给文件名，要求 Read 返回真实内容，防止模型根据提示词复述。
- **Read-based Skill**：先读取 SKILL.md，再读取随机输入、用 Bash 创建结果、用 Read 读回；核对输出与输入精确字节相同。

脚本同时检查原生客户端型号、成功工具结果、上游模型确认与完成记录，及三份既有全局 Claude 配置/历史文件是否改变。成功后本机生成 `evidence\acceptance-summary.json`；原始事件存于 logs，均不会上传。

## 固定型号的判据

查看本机 `logs\gateway.log` 中的 `[agent-model]` 记录：

```text
alias=claude-opus-5-5 requested=<live-id> confirmed=<live-id> selected=<live-id>
```

请求、model 和 selectedModel 必须匹配，且来自当前实时模型列表的 Opus 5.5。客户端显示名或模型自述不能替代该检查。补丁不把某次内部 ID 当成永久编号。

这个判据证明 Notion 服务端报告选择了该型号，没有独立检查后端权重。验收失败时保留本机证据，按 [故障排查](TROUBLESHOOTING.md) 定位；避免未看失败原因就连续重复推理。
