# 获取 token_v2 并在本机导入

`token_v2` 是当前 Notion 网页登录的会话凭证。它不是普通 Integration Token，也不是 Anthropic API Key。拥有它的程序可能以该用户身份访问工作区；仅将自己的值导入本机网关，不发到聊天、Issue、截图或远程“验证网站”。

## Windows + Chrome 操作

1. 在 Chrome 打开 [Notion](https://www.notion.so/) 并登录，进入自己的工作区或页面。取值位置是浏览器开发者工具，不是 Notion 设置中的 API Key 页面。
2. 按 `F12`，或按 `Ctrl + Shift + I`。部分笔记本可能需要 `Fn + F12`。快捷键无反应时，点击右上角 `⋮ → 更多工具 → 开发者工具`。
3. 在开发者工具顶部选择 `Application（应用）`。没看到时，点击顶部 `»` 展开隐藏选项；也可加宽开发者工具。
4. 左侧展开 `Storage（存储）→ Cookies`。
5. 点击 Cookies 左侧的小三角展开域名列表，选择当前 Notion 页面对应的域名。例如页面可能位于 `www.notion.so` 或 `app.notion.com`，以地址栏和实际列表为准。不要选本机 `127.0.0.1` 管理页或其他网站。
6. 在右侧表格的 Filter 输入 `token_v2`，查看 Name 列是否出现同名 Cookie。
7. 单击 `token_v2` 所在行。**复制的是这一行完整的 Value，不是 Name 的 token_v2 这几个字。** 列太窄导致值截断时，选中该行后查看下方的值详情区域，从那里复制完整文本；不要只复制可见的一小段。若右键菜单提供 Copy value，也可使用该项。
8. 保留浏览器给出的原始值，不加引号，不在前面加 `token_v2=`，不复制整段 Cookie 请求头，不手工修改或 URL 解码。管理页需要的是这个值本身。
9. 另开本机 `http://127.0.0.1:8081/dashboard/`。在项目的 `runtime\private` 文件夹中打开 `admin-password.txt`，将管理密码直接输入本机登录页。不要把密码或 Cookie 发进 Agent 聊天。
10. 点击“添加账号”，在“粘贴 token_v2 值…”输入框中直接粘贴，提交并等待“添加成功”。随后核对显示的账号和工作区。管理密码、本机 API Key 和 token_v2 是三个不同值。
11. 用 `Status.cmd` 确认 `usable_accounts` 至少为 1；Agent 可用 `project.ps1 -Action ready` 取得相同的就绪判断。然后执行真实验收。导入完成后清除自己剪贴板中的凭证文本，避免误粘贴。

位置示意（没有真实凭证）：

```text
已登录的 Notion 页面
  └─ F12 / Ctrl + Shift + I
      └─ Application（应用；隐藏时点 »）
          └─ Storage → Cookies → 当前 Notion 域名
              └─ Name: token_v2 | Value: [自己的完整登录凭证]
                                      ↓ 仅在本机粘贴
                  本机 dashboard → 添加账号 → token_v2 输入框
```

Chrome 的 Cookie 面板与快捷键位置可参照 [Cookie 官方说明](https://developer.chrome.com/docs/devtools/application/cookies) 和 [开发者工具打开方式](https://developer.chrome.com/docs/devtools/open)。本文不放真实 Cookie 截图。

Mac 教程里的 `Option + Command + I` 在 Windows 应替换为上述快捷键；Cookies 的面板位置相同。没有 `token_v2` 时，先确认浏览器当前确实登录了目标账号，刷新对应页面并核对域名。不要猜一个值，也不要改用别的网站 Cookie。

常见位置问题：

| 现象 | 处理 |
|---|---|
| F12 没反应 | 试 Ctrl + Shift + I 或 Fn + F12，也可从 Chrome 的更多工具菜单进入 |
| 没有 Application | 点击顶部 »，或加宽开发者工具；别在网页自身的设置菜单里找 |
| Cookies 里只有 localhost/127.0.0.1 | 当前开发者工具属于网关页面；切回已登录 Notion 的标签页再打开 |
| 筛选后为空 | 清空 Filter，确认域名与登录状态，刷新 Notion 页面后再次查看 |
| 复制后导入失败 | 核对是否复制完整 Value，是否多了名称、引号、空格或请求头；会话失效则本人重新登录 |
| 添加成功但可用数是 0 | 核对工作区权益和额度，不能把导入成功当成推理成功 |

## 三种凭证，不能混用

| 凭证 | 在本流程中的用途 |
|---|---|
| Notion token_v2 | 本人导入，仅供本机网关访问 Notion 网页端 Agent 通道 |
| 本机网关 API Key | Setup 随机生成，CLI 到 127.0.0.1 网关的鉴权，启动器自动读取 |
| 本机管理密码 | Setup 随机生成，管理页登录使用 |

Notion 官方 OAuth、页面/数据库 Integration Token 不在本实验通道的登录实现中，不能直接填来替代 `token_v2`。

## 多工作区与失效

同一账号可能有多个同名工作区，账号相同不等于额度相同。导入后核对目标工作区是否包含所需 AI 权益。账号能添加成功只能证明导入被接受，还要检查 `usable_accounts` 和实际推理。

Cookie 过期时，由本人重新登录并在本机管理页更新。额度不足时，在 Notion 查看工作区权益或等待恢复；只使用自己有权访问且可用的工作区。不要通过反复重试本机任务把账号不可用误判为程序安装失败。
