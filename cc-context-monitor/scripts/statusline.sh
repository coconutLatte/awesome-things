#!/usr/bin/env bash
# statusline.sh — Context window usage display for Claude Code
# Reads JSON from stdin, renders a color-coded progress bar.

set -euo pipefail

# Read all stdin into a variable
input=$(cat)

# Parse fields with jq, defaulting to 0 for null/missing values
pct=$(echo "$input" | jq -r '.context_window.used_percentage // 0')
tokens=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
max_tokens=$(echo "$input" | jq -r '.context_window.context_window_size // 200000')

# Format token counts with k/m suffix
format_tokens() {
  local n=$1
  if [ "$n" -ge 1000000 ]; then
    echo "$(awk "BEGIN {printf \"%.1f\", $n/1000000}")m"
  elif [ "$n" -ge 1000 ]; then
    echo "$(awk "BEGIN {printf \"%.0f\", $n/1000}")k"
  else
    echo "$n"
  fi
}

tokens_fmt=$(format_tokens "$tokens")
max_fmt=$(format_tokens "$max_tokens")

# Pick color based on usage percentage
if   [ "$(echo "$pct < 50" | bc -l 2>/dev/null || echo 0)" -eq 1 ]; then
  color='\033[32m'  # green
elif [ "$(echo "$pct < 70" | bc -l 2>/dev/null || echo 0)" -eq 1 ]; then
  color='\033[33m'  # yellow
elif [ "$(echo "$pct < 85" | bc -l 2>/dev/null || echo 0)" -eq 1 ]; then
  color='\033[38;5;208m'  # orange
else
  color='\033[31m'  # red
fi
reset='\033[0m'
dim='\033[2m'

# Build 10-segment progress bar
bar=""
filled=$(awk "BEGIN {printf \"%d\", int($pct / 10 + 0.5)}")
for i in $(seq 1 10); do
  if [ "$i" -le "$filled" ]; then
    bar="${bar}█"
  else
    bar="${bar}░"
  fi
done

# Output: [progress bar] pct% · tokens / max_tokens
printf "${color}${bar}${reset} ${color}%s%%${reset}${dim} · %s/%s tokens${reset}\n" \
  "$(awk "BEGIN {printf \"%.0f\", $pct}")" \
  "$tokens_fmt" "$max_fmt"
