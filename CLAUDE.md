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

## Conventions

- All scripts use `set -euo pipefail` and color-coded logging helpers (`log`, `warn`, `err`)
- Scripts are designed for Linux/WSL environments
