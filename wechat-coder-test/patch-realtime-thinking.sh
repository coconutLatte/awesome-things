#!/bin/bash
# =============================================================================
# wechat-claude-code 思考过程实时推送补丁
# 将消息推送间隔从 36 秒改为可通过环境变量控制，默认 5 秒
# =============================================================================
set -euo pipefail

GREEN='\033[0;32m'
NC='\033[0m'
log() { echo -e "${GREEN}[✓]${NC} $*"; }

TEMPLATE_DIR="${HOME}/.claude/skills/wechat-claude-code"
SEND_INTERVAL="${WCC_SEND_INTERVAL_MS:-5000}"

# ---- 1. 打补丁 ----
log "修补源码: SEND_INTERVAL_MS 可配置化..."
cd "$TEMPLATE_DIR"

# 修改 src/main.ts
sed -i 's/const SEND_INTERVAL_MS = 36_000;/const SEND_INTERVAL_MS = parseInt(process.env.WCC_SEND_INTERVAL_MS || "'"${SEND_INTERVAL}"'", 10);/' src/main.ts

# 重新编译
log "重新编译 TypeScript..."
npm run build

# 验证
if grep -q 'WCC_SEND_INTERVAL_MS' dist/main.js; then
    log "源码补丁生效"
else
    echo "⚠️ 补丁未生效，请检查 src/main.ts"
    exit 1
fi

# ---- 2. 更新所有现有 systemd service 文件 ----
log "更新 systemd service 环境变量..."

UPDATED=0
for service_file in "${HOME}/.config/systemd/user/wechat-claude-code"*.service; do
    [ -f "$service_file" ] || continue
    service_name=$(basename "$service_file" .service)

    if grep -q 'WCC_SEND_INTERVAL_MS' "$service_file"; then
        log "  ${service_name}: 已有 WCC_SEND_INTERVAL_MS，跳过"
        continue
    fi

    # 在 Environment=WCC_DATA_DIR 后面插入一行
    sed -i '/Environment=WCC_DATA_DIR=/a Environment=WCC_SEND_INTERVAL_MS='"${SEND_INTERVAL}"'' "$service_file"
    log "  ${service_name}: 已添加 WCC_SEND_INTERVAL_MS=${SEND_INTERVAL}"
    UPDATED=$((UPDATED + 1))
done

if [ "$UPDATED" -eq 0 ]; then
    log "没有需要更新的 service 文件"
fi

# ---- 3. 重载 systemd ----
systemctl --user daemon-reload

# ---- 4. 重启所有实例 ----
log "重启所有实例..."
RESTARTED=0
for service_file in "${HOME}/.config/systemd/user/wechat-claude-code"*.service; do
    [ -f "$service_file" ] || continue
    service_name=$(basename "$service_file" .service)
    if systemctl --user is-active --quiet "$service_name" 2>/dev/null; then
        systemctl --user restart "$service_name"
        log "  已重启: ${service_name}"
        RESTARTED=$((RESTARTED + 1))
    else
        log "  未运行，跳过: ${service_name}"
    fi
done

# ---- 5. 结果 ----
echo ""
echo "============================================"
echo "  补丁完成!"
echo "============================================"
echo ""
echo "  消息推送间隔: ${SEND_INTERVAL}ms"
echo "  已更新 service: ${UPDATED} 个"
echo "  已重启实例: ${RESTARTED} 个"
echo ""
echo "调整间隔: 修改 systemd service 里的"
echo "  Environment=WCC_SEND_INTERVAL_MS=${SEND_INTERVAL}"
echo "然后 systemctl --user daemon-reload && systemctl --user restart <服务名>"
echo ""
