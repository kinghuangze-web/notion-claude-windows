# 模型适配与能力边界

## 固定 Opus 5.5 的实现

公开基础提交的 Agent 通道采用 Auto，本工具包在该提交上应用 `patches/opus55.patch`：

1. 针对 `claude-opus-5-5`、`opus-5.5`、`claude-opus-5.5`，读取当前账号实时可用模型列表，精确匹配 Opus 5.5；不存在或匹配不唯一则拒绝。
2. 创建 Agent 线程时显式提交查得的模型 ID，推理档位为 medium。
3. 核对返回的线程 ID、`thread.data.agent_provider.model` 与 `selectedModel`。请求 ID 和两个模型字段必须相同。
4. 确认之后才继续收集回答和工具指令。记录无内容的型号确认、线程哈希与完成记录，不记录提示词或 Cookie。

`proxy.require_opus55: true` 限定当前部署只用固定型号。Auto、旧 Opus 或其他未支持型号会报错；不会把请求改回 Auto。内部 ID 来自实时接口，未硬编码。

启动器默认及 Haiku/Sonnet/Opus 档位都映射到同一固定别名，避免客户端档位配置仍指向 Auto。映射不意味着支持独立 Haiku 或 Sonnet 型号。

## 客户端启动方式

专用启动器使用原生 CLI 的 bare 模式，关闭全局 settings 来源与外部 MCP 自动加载，保留 Bash、Read、Edit。验收版本是 Claude Code 2.1.299；后续版本可能调整参数和工具集合，应重新验收。

默认权限模式为 `acceptEdits`，在当前工作目录预批准文件修改，其他命令权限检查仍保留。验收版本的自动权限分类器会额外请求 Sonnet，严格网关会拒绝，所以此入口不用自动分类器，也不使用 `bypassPermissions`。权限模式含义见 [官方说明](https://code.claude.com/docs/en/permission-modes)。

bare 模式中写入文件用 Bash 并 Read 读回；只把 Write、Skill 等名字写到工具参数里不能让未注册工具出现。Skill 路线是读取本地 SKILL.md，然后按依赖调用现有工具，不等于原生 `/skill` 命令。

## 已验证和未验证

此入口不能当作完整 Claude Code 使用，差异同时来自启动器和上游转接：

- `--system-prompt` 用简短 coding prompt 替换默认系统提示词，bare 模式减少自动发现和可用工具；不是只替换了后端地址。
- 系统、用户、助手和工具消息被拼成带标签的文本，工具指令采用文本 JSON，再转为本地调用；没有完整保留原生 API 的角色层级和工具语义。
- 每次推理新建 Notion 线程，重复携带客户端提供的历史；长上下文、压缩、恢复和并发可靠性尚未验证。返回需要分页时，当前实现报错拒绝不完整输出。
- Notion reasoningEffort 固定为 medium，客户端其他思考参数没有完整对应；输出在上游完成后返回，本地取消也不保证取消远端任务。

适用范围以能逐步核对结果的文字和文件任务为主。Bash 可调用已安装的 Python、Git 或搜索工具，因此不只是建目录；真实代码项目、批量任务和长任务的可靠性仍需分别验收。

| 能力 | 状态 |
|---|---|
| 文字对话、Bash 创建目录、Read 读文件、Bash 创建文件并读回 | 原实现真实验收通过 |
| 固定 Opus 5.5、上游双字段确认、失败时禁止降级 | 真实请求与回归通过 |
| 读取 Skill 后完成基本文件任务 | 真实验收通过 |
| Edit 修改已有文件 | 工具已注册，未单独验收此任务 |
| 全套插件、MCP、原生 Skill、自动 CLAUDE.md 发现/记忆 | 当前精简入口未启用或未验收；需要规则时明确读取文件 |
| Claude Desktop、Cowork | 不属于本次 CLI 验收 |
| 1M 上下文、长会话稳定性、其他固定型号 | 未验证 |
| 图片/PDF 作为 Agent 模型附件 | 当前通道不支持；本地提取文字属于另一流程 |
| 真正逐 Token 的上游流式输出 | 先收集结果再转换给客户端，等待时间较明显 |
| 本地取消后同步取消 Notion 任务 | 不保证，重试可能新建额外请求 |

它仍是实验性的网页端 Agent 转接，依赖 Notion 当前协议和账号权益。Notion 订阅没有因此变成 Anthropic 官方 API 账号。本机网关的 usage 数值没有可靠 Token/费用计量，不能从 0 推断免费或没有消耗。
