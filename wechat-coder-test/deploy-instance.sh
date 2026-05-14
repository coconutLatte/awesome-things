#!/bin/bash
# =============================================================================
# wechat-claude-code 多实例部署脚本
# 每运行一次 = 添加一个微信账号 → Claude Code 的通道
#
# 用法:
#   bash deploy-instance.sh <实例名> [工作目录]
#
# 示例:
#   bash deploy-instance.sh personal                    # 工作目录默认 ~/
#   bash deploy-instance.sh qingtao /root/workspace/qingtao
# =============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*"; exit 1; }

# ---- 参数 ----
INSTANCE_NAME="${1:-}"
WORK_DIR="${2:-${HOME}}"

if [ -z "$INSTANCE_NAME" ]; then
    echo "用法: bash deploy-instance.sh <实例名> [工作目录]"
    echo ""
    echo "示例:"
    echo "  bash deploy-instance.sh personal"
    echo "  bash deploy-instance.sh qingtao /root/workspace/qingtao"
    exit 1
fi

if ! [[ "$INSTANCE_NAME" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    err "实例名只能包含字母、数字、连字符和下划线"
fi

# 展开路径中的 ~
WORK_DIR="${WORK_DIR/#\~/$HOME}"
WORK_DIR="$(realpath -m "$WORK_DIR")"

TEMPLATE_DIR="${HOME}/.claude/skills/wechat-claude-code"
WCC_DATA_DIR="${HOME}/.wechat-claude-code-${INSTANCE_NAME}"
SERVICE_NAME="wechat-claude-code-${INSTANCE_NAME}"
SYSTEMD_SERVICE_FILE="${HOME}/.config/systemd/user/${SERVICE_NAME}.service"
NODE_BIN="$(command -v node)"

# ---- 前置检查 ----
log "检查模板项目..."
if [ ! -f "$TEMPLATE_DIR/dist/main.js" ]; then
    log "模板项目未安装，先运行主部署脚本..."
    DEPLOY_SCRIPT="${HOME}/workspace/cc-custom-plugins/wechat-test/deploy.sh"
    if [ ! -f "$DEPLOY_SCRIPT" ]; then
        err "找不到主部署脚本: $DEPLOY_SCRIPT"
    fi
    bash "$DEPLOY_SCRIPT"
fi

# ---- 创建/验证工作目录 ----
if [ ! -d "$WORK_DIR" ]; then
    mkdir -p "$WORK_DIR"
    log "已创建工作目录: ${WORK_DIR}"
else
    log "工作目录: ${WORK_DIR}"
fi

# ---- 创建数据目录 ----
mkdir -p "${WCC_DATA_DIR}/accounts"
mkdir -p "${WCC_DATA_DIR}/sessions"
mkdir -p "${WCC_DATA_DIR}/logs"

# ---- 写入实例配置 ----
CONFIG_FILE="${WCC_DATA_DIR}/config.env"
cat > "$CONFIG_FILE" <<EOF
workingDirectory=${WORK_DIR}
EOF
log "已写入实例配置: ${CONFIG_FILE} (workingDirectory=${WORK_DIR})"

# ---- 创建 systemd service ----
cat > "$SYSTEMD_SERVICE_FILE" <<SERVICE
[Unit]
Description=WeChat Claude Code Bridge - ${INSTANCE_NAME}
Documentation=https://github.com/Wechat-ggGitHub/wechat-claude-code
After=network.target

[Service]
Type=simple
ExecStart=${NODE_BIN} ${TEMPLATE_DIR}/dist/main.js start
WorkingDirectory=${TEMPLATE_DIR}
Restart=always
RestartSec=10
Environment=PATH=${HOME}/.local/bin:${NODE_BIN%/*}:/usr/local/bin:/usr/bin:/bin
Environment=WCC_DATA_DIR=${WCC_DATA_DIR}
Environment=WCC_SEND_INTERVAL_MS=5000
StandardOutput=append:${WCC_DATA_DIR}/logs/stdout.log
StandardError=append:${WCC_DATA_DIR}/logs/stderr.log
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=default.target
SERVICE

log "已创建 systemd service: ${SYSTEMD_SERVICE_FILE}"

# ---- 重载并启用 ----
systemctl --user daemon-reload
systemctl --user enable "${SERVICE_NAME}"
log "已启用开机自启: ${SERVICE_NAME}"

# ---- 显示信息 ----
echo ""
echo "============================================"
echo "  实例 ${INSTANCE_NAME} 已创建!"
echo "============================================"
echo ""
echo "  实例名:     ${INSTANCE_NAME}"
echo "  工作目录:   ${WORK_DIR}"
echo "  数据目录:   ${WCC_DATA_DIR}"
echo "  服务名:     ${SERVICE_NAME}"
echo ""
echo "接下来扫码绑定微信:"
echo ""
echo "  WCC_DATA_DIR=${WCC_DATA_DIR} node ${TEMPLATE_DIR}/dist/main.js setup"
echo ""
echo "绑定后启动服务:"
echo ""
echo "  systemctl --user start ${SERVICE_NAME}"
echo ""
echo "管理命令:"
echo "  systemctl --user status  ${SERVICE_NAME}   查看状态"
echo "  systemctl --user start   ${SERVICE_NAME}   启动"
echo "  systemctl --user stop    ${SERVICE_NAME}   停止"
echo "  systemctl --user restart ${SERVICE_NAME}   重启"
echo "  journalctl --user -u ${SERVICE_NAME} -f    查看日志"
echo ""

# ---- 列出现有实例 ----
echo "当前所有实例:"
echo ""
echo "  systemd 服务:"
systemctl --user list-unit-files 'wechat-claude-code*' --no-legend 2>/dev/null | awk '{printf "    %-35s %s\n", $1, $2}' || echo "    (无)"
echo ""
echo "  数据目录:"
for d in "${HOME}"/.wechat-claude-code*; do
    if [ -d "$d" ]; then
        wd=$(grep workingDirectory "$d/config.env" 2>/dev/null | cut -d= -f2 || echo "?")
        accounts=$(ls "$d/accounts/"*.json 2>/dev/null | wc -l)
        echo "    ${d}  wd=${wd}  (${accounts} 个微信账号)"
    fi
done
