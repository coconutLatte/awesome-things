# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of tools, scripts, and plugins for extending and operating **Claude Code**. There is no build system, package manager, or test suite — the repo contains operational Bash scripts and a Claude Code plugin.

## Sub-projects

### cc-context-monitor

A Claude Code plugin that displays real-time context window usage in the status line.

- Plugin metadata: `.claude-plugin/plugin.json`
- Slash command `/setup` defined in `commands/setup.md` — configures `statusLine` in `~/.claude/settings.json`
- Core script: `scripts/statusline.sh` — reads JSON from stdin, parses token usage with `jq`, renders a color-coded progress bar
- Dependencies: `jq`, `bc` must be available on the system

### wechat-coder-test

Deployment scripts for the [wechat-claude-code](https://github.com/Wechat-ggGitHub/wechat-claude-code) bridge (WeChat <-> Claude Code).

Key commands:
- `bash deploy.sh` — one-click deployment (requires Node.js >= 18, git)
- `bash deploy-instance.sh <name> [workdir]` — add a multi-instance deployment for another WeChat account
- `bash patch-realtime-thinking.sh` — patch message push interval (default 36s -> 5s), configurable via `WCC_SEND_INTERVAL_MS` env var

Architecture: WeChat app <-> iLink Bot API <-> Node.js daemon <-> Claude Agent SDK <-> local Claude Code

WSL-aware: detects WSL, offers systemd vs nohup fallback, enables `loginctl linger` for persistence.

## Conventions

- All scripts use `set -euo pipefail` and color-coded logging helpers (`log`, `warn`, `err`)
- Scripts are designed for Linux/WSL environments
- wechat-claude-code installs to `~/.claude/skills/wechat-claude-code`
- Data persists in `~/.wechat-claude-code/` (accounts, sessions, logs)
- Multi-instance data directories: `~/.wechat-claude-code-<name>/`
