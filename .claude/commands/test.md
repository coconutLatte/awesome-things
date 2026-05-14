---
description: Run Jarvis tests
argument-hint: [optional-pytest-args]
allowed-tools: [Bash, Read, Grep]
---

# Run Jarvis Tests

Run pytest for the Jarvis project with the following arguments: $ARGUMENTS

## Steps

1. Run `cd /root/workspace/awesome-things/Jarvis && python3 -m pytest tests/ -v --tb=short $ARGUMENTS`
2. Report the results clearly
3. If tests fail, show failure details and suggest fixes
