#!/bin/bash
# Jarvis test runner - used by Claude Code hooks and /test command
cd /root/workspace/awesome-things/Jarvis
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ -v --tb=short 2>&1
