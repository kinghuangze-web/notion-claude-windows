# CC Switch + 普通 Claude 命令

独立 `Full-Claude.cmd` 测通，不能证明 CC Switch 中旧供应商也已升级。先核对实际 API 地址、对应进程、二进制版本和会话模式；Claude 启动页显示 Opus 不足以确认请求可用。

## 沿用 8081 的正常启动路径

此方式让普通原生 `claude` 命令直接使用 V2 适配，不需要 Full-Claude 包装器；独立 8082 入口仍可保留。

1. 关闭正在请求的 CLI，在本项目停止 8081 网关，更新仓库并运行 Setup，确保实际运行文件来自新版累积补丁。只有 GitHub 文件更新而旧 exe 仍在运行不算部署完成。
2. 在本机 `runtime/config.yaml` 的现有 `proxy` 下增加 `agent_session_v2: true`，保留原地址、Key、账号目录、固定型号及其他设置。该开关由项目进程启动器读取，给网关设置独立持久化目录 `runtime/agent-sessions-v2`。
3. 通过 `Start-Gateway.cmd` 或 `project.ps1 -Action start` 重新启动。旧进程已运行时 start 只复用它，不会自动改变该进程的环境。
4. CC Switch 的 Notion 供应商继续使用 `http://127.0.0.1:8081` 与匹配的本机 Key；保持 Opus 5.5。重开 CMD 和 Claude，让普通进程重新读取当前供应商配置。不要把 Key 发到聊天或 Issue。
5. 在自己的工作目录先测试一句回复，再测试真实 Read/Write/Edit 读回；查看最终进程状态与 V2 续写日志，不能只看模型标题或 health。

启动命令示例（已完成安装和本机配置后）：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\project.ps1 -Action start
Set-Location -LiteralPath "D:\MyNotes\Test"
claude
```

此模式不设置独立 CLAUDE_CONFIG_DIR，不替换官方提示词，也不修改普通用户的 Skills/MCP 发现方式。权限模式由普通 CLI 自身配置决定；实测覆盖 `auto` 模式下的对话和获准文件工具，不代表全部工具权限决策均已验证。

回退时先停止本项目网关，将 `agent_session_v2` 改为 false 或移除，再重启。保留 V2 状态目录供恢复，切勿在待处理请求中途删除它。回退传输会恢复旧模式按推理轮次创建对话的行为。

## 2026-10-19 接入缺口与修正

用户在自己的工作目录以普通 Claude Code 2.1.303 启动，CC Switch 选中 Notion，却连续 API error。检查发现供应商和普通 settings 都指向旧 8081，V2 8082 未运行；旧网关真实日志连续记录 createAgentThread HTTP 400，Key 本身匹配。

备份原二进制、源码、配置和启动器后，将实际 8081 部署升级为 V2 并开启此开关；API 地址、Key、账户目录及用户全局 settings 保持原值。原生 CLI 从同一用户目录直接运行，没有独立启动器，也没有进程级路由覆盖，`auto` 模式下回复测试成功；恢复同一会话完成 Read → Write → Edit → Read，随机标记和精确文件内容、最终成功均通过。合计 6 个成功上游回合，1 次创建、5 次续写，无待处理事件残留。

这次证据覆盖了用户实际启动路径；此前独立启动器结果不能替代这项验证。原始日志和临时文件证明保存在本机，公开仓库只记录脱敏结论。
