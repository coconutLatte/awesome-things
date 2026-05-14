# Setup Context Monitor

Run this command to enable the real-time context window status line:

## Steps

1. Read the user's current settings file at `~/.claude/settings.json`. If it doesn't exist, start with an empty object `{}`.
2. Use `${CLAUDE_PLUGIN_ROOT}` to resolve the absolute path of the plugin's status line script.
3. Add or update the `statusLine` key in the settings to point to `${CLAUDE_PLUGIN_ROOT}/scripts/statusline.sh`. If `${CLAUDE_PLUGIN_ROOT}` is not available (e.g., pre-plugin versions), fall back to the literal installed path.
4. Write the updated settings back to `~/.claude/settings.json`.
5. Tell the user the status line has been configured and will appear on the next message.

The resulting statusLine config should look like:
```json
{
  "statusLine": {
    "type": "command",
    "command": "${CLAUDE_PLUGIN_ROOT}/scripts/statusline.sh"
  }
}
```
