# Privacy / 隐私

Credentials are imported by the owner locally. Never request login cookies in chat or extract browser credentials automatically. Gateway/API/admin values are generated or stored only in ignored runtime data, protected with the current user's and SYSTEM's NTFS ACL.

凭证仅由所有者在本机导入，不要求聊天发送 Cookie，也不自动提取浏览器凭证。网关 Key、管理密码和账号文件仅留在忽略的 runtime，并使用当前用户与 SYSTEM 的 NTFS ACL。

The native child entry preserves ordinary user configuration discovery. It does not copy user settings, OAuth files or plugin directories into another profile. Its private runtime route file does contain local credentials and must never be published. Tasks, read files and tool results are sent to Notion; routing/data placement is not a filesystem sandbox.

原生子进程入口保留正常用户配置发现，不复制用户设置、OAuth 文件或插件目录建立另一套资料。私有路由文件含本机凭证，不得发布。任务、文件和工具结果会发送给 Notion；数据目录不是文件沙箱。

Publish only release-files.txt: no runtime, logs, evidence, demo, private path overrides, accounts, raw requests, screenshots, binaries or downloaded client bundles. Historical source and commit identities must also be checked. Scanner findings report locations/rules only, never matched secrets. Review results and limits are in docs/PRIVACY_AUDIT.md.

只发布白名单文件；运行数据、日志、证据、测试夹、路径覆盖、账号、原始请求、截图、二进制和下载的客户端 bundle 均不公开。历史源码和提交身份也须检查。扫描发现只报告位置和规则，不回显秘密。审计范围和边界见 docs/PRIVACY_AUDIT.md。

If an actual secret is ever published, removing its current file is insufficient: revoke/rotate it locally and determine the necessary historical cleanup. No actual leak was found in the current review.

如未来确认泄漏，删除当前文件不足以补救，应在本机撤销/轮换凭证并判断历史清理范围。本次检查未发现实际泄漏。
