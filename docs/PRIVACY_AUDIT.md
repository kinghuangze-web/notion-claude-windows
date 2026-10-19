# Privacy review / 隐私复核

Date / 日期：2026-10-19。Scope / 范围：本仓库当前文件、远端可达历史、提交身份，以及公开仓库的附加入口。这里不保存任何匹配值、私人路径或账户标识。

## 已检查 / Checked

- Remote baseline: `main` at `4258be2`, four commits, 106 unique historical blobs. A single remote branch; no tags.
- Current supported tree: 40 allowlisted text files after consolidation.
- Current/public text and historical blobs: personal email patterns, Windows user/private paths, common API/GitHub tokens, credential assignments, cookies and private-key headers.
- Exact comparison against 13 local private values: gateway credentials, account/login fields, workspace/device identifiers and local username. Input stayed in ignored protected storage and was deleted after the check; output contains counts only.
- Commit author/committer identities: GitHub public account with GitHub noreply email; no private contact email found.
- GitHub API inventory: no releases, issues, pull requests, Actions runs or build artifacts. The wiki Git endpoint returned repository-not-found; no public wiki repository was available to inspect.
- Tracked content is text-only; runtime, accounts, credentials, screenshots, raw requests, binaries and logs are excluded by the release allowlist and ignore rules.

## 结论与处理 / Result and action

No personal information or credential leak was found in the inspected scope. No sensitive value was printed by the scanners. No history rewrite or credential revocation was performed. The repository owner's already-public GitHub handle/URL and noreply identity remain as normal repository attribution.

在已检查范围内，未发现个人信息或凭证泄漏。没有为此重写历史或撤销凭证。公开 GitHub 账号、仓库链接和 noreply 提交身份属于既有公开署名，并非私人联系方式。

The obsolete slim implementation and human-oriented launch wrappers were removed from the current supported tree. Their non-sensitive historical revisions remain in Git; removal of an operational method is separate from privacy remediation.

旧精简实现和人工启动入口已从当前支持范围移除；无敏感信息的历史版本仍保留。移除旧运行方式与清理隐私泄漏是两件事。

## 边界 / Boundaries

This is a scoped source/history/public-surface inspection, not a guarantee against every possible encoded secret, external clone, cache or material outside the repository. Known exact values plus pattern checks reduce false negatives but cannot prove the absence of unknown secrets. GitHub's own secret-scanning dashboard was not accessed. Empty public surfaces are a point-in-time observation.

这是对当前源码、历史及公开入口的限定检查；未知编码秘密、仓库外内容、外部克隆和缓存未被穷尽。未访问 GitHub 私有 secret-scanning 控制台。公开入口为空仅表示检查时状态。

Future changes must pass `check_release.py --check-index` and `audit_history.py`. The history scanner has a synthetic regression proving that a secret deleted in a later commit is still found, without echoing it.

未来发布须复查白名单和历史扫描。历史扫描器已有合成回归：即使后续提交删除了秘密，仍能发现旧版本，且不会回显秘密值。
