# Third-party notices

## notion_manager

Source: https://github.com/SleepingBag945/notion_manager

Base commit: `2d6d3dc2fa74f929bd9a8ebd3c1569f5dcca1b88` (PR #23, experimental Agent transport).

License: Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International. The original license text is preserved in LICENSE. This distribution's patch, derived launcher, scripts and documentation are shared under the same license. Changes are described in CHANGELOG.md. No upstream endorsement is implied.

The setup script downloads the pinned source to an ignored local directory; this repository does not include upstream Git history, captured test fixtures, screenshots or account data.

## Protocol reference

Fixed-model request field reference: https://github.com/wycocoyu/notion-code-bridge/blob/f664b96693b2af4f8ba2bd063397dbea38955c37/internal/proxy/agent_thread.go

The patch implements local live-model lookup, explicit selection and response validation. This repository does not redistribute that reference repository or adopt its additional runtime workflows.

## Tutorial reference

Original route: https://x.com/ElowenY20119/status/2109947661214458149 — “Notion AI 接入 Claude Code：从配置到本地任务，手把手跑通”. The Windows documentation is newly written for this tool package; original article text and images are not redistributed.

## External tools

Go, Git for Windows, Python, Chrome and Claude Code are installed separately from their official sources and keep their respective licenses. Python dependency: PyYAML 6.0.3 (MIT); Go dependencies and versions remain governed by the pinned source's go.mod/go.sum. No model weights or Notion credentials are distributed.
