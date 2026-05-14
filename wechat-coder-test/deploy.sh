#!/bin/bash
# =============================================================================
# wechat-claude-code 一键部署脚本 (含开机自启)
# 适用于 WSL / Linux 环境
# =============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*"; exit 1; }

INSTALL_DIR="${HOME}/.claude/skills/wechat-claude-code"
REPO_URL="https://github.com/Wechat-ggGitHub/wechat-claude-code.git"

echo "============================================"
echo "  wechat-claude-code 部署脚本"
echo "============================================"
echo ""

# ---- 1. 检查 Node.js ----
log "检查 Node.js..."
if ! command -v node &>/dev/null; then
    err "未找到 Node.js。请先安装 Node.js >= 18 (https://nodejs.org)"
fi

NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    err "Node.js 版本过低 ($(node -v))，需要 >= 18"
fi
log "Node.js $(node -v)"

# ---- 2. 检查 git ----
if ! command -v git &>/dev/null; then
    err "未找到 git。请先安装 git"
fi

# ---- 3. 检查 Claude Code CLI / Agent SDK ----
log "检查 Claude Code..."
if command -v claude &>/dev/null; then
    log "Claude Code CLI 已安装"
else
    warn "未检测到 claude 命令，daemon 依赖 @anthropic-ai/claude-agent-sdk"
    warn "请确保已设置 ANTHROPIC_API_KEY 或 ANTHROPIC_AUTH_TOKEN 环境变量"
fi

# ---- 4. 检测 WSL 和 systemd ----
IS_WSL=false
if grep -qi microsoft /proc/version 2>/dev/null; then
    IS_WSL=true
    log "检测到 WSL 环境"
fi

HAS_SYSTEMD_USER=false
if systemctl --user list-units &>/dev/null 2>&1; then
    HAS_SYSTEMD_USER=true
    log "systemd user session 可用"
else
    warn "systemd user session 不可用，将使用 nohup 模式"
    if $IS_WSL; then
        warn "WSL 提示: 在 /etc/wsl.conf 中添加 [boot] systemd=true 可启用 systemd"
        warn "然后重启 WSL: wsl --shutdown && wsl"
    fi
fi

# ---- 5. 克隆/更新项目 ----
if [ -d "$INSTALL_DIR/.git" ]; then
    warn "安装目录已存在: $INSTALL_DIR"
    read -r -p "是否覆盖重新安装? [y/N] " REPLY
    if [[ "$REPLY" =~ ^[Yy]$ ]]; then
        log "停止旧服务..."
        (cd "$INSTALL_DIR" && npm run daemon -- stop 2>/dev/null || true)
        cd "$HOME"
        rm -rf "$INSTALL_DIR"
    else
        log "保留现有安装，仅更新依赖..."
        cd "$INSTALL_DIR"
        git pull 2>/dev/null || true
        npm install
        log "更新完成"
        "$INSTALL_DIR/scripts/daemon.sh" restart 2>/dev/null || true
        log "部署完成!"
        exit 0
    fi
fi

mkdir -p "$(dirname "$INSTALL_DIR")"
log "克隆项目到 $INSTALL_DIR ..."
git clone "$REPO_URL" "$INSTALL_DIR"

# ---- 6. 安装依赖 ----
log "安装依赖..."
cd "$INSTALL_DIR"
npm install

# ---- 7. 验证编译 ----
if [ -f "$INSTALL_DIR/dist/main.js" ]; then
    log "编译产物验证通过"
else
    err "编译失败: 未找到 dist/main.js"
fi

# ---- 8. 配置开机自启 ----
setup_autostart() {
    echo ""
    log "配置开机自启..."

    if $HAS_SYSTEMD_USER; then
        # systemd user service (daemon.sh 的 start 会自动创建 service 文件并 enable)
        # 额外确保 lingering 开启（WSL 必须）
        if $IS_WSL; then
            if command -v loginctl &>/dev/null; then
                loginctl enable-linger "$(whoami)" 2>/dev/null && \
                    log "已启用 linger（WSL 开机自启关键）" || \
                    warn "无法启用 linger，请手动执行: loginctl enable-linger $(whoami)"
            fi
        fi
        log "systemd user service 将在首次 start 时自动注册并启用"
    else
        # nohup 模式: 写一个 profile hook
        local PROFILE_HOOK="${HOME}/.wechat-cc-autostart.sh"
        cat > "$PROFILE_HOOK" <<'AUTOSTART'
#!/bin/bash
# wechat-claude-code auto-start (nohup mode)
PID_FILE="${HOME}/.wechat-claude-code/wechat-claude-code.pid"
if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        return 0
    fi
fi
cd "${HOME}/.claude/skills/wechat-claude-code" && npm run daemon -- start
AUTOSTART
        chmod +x "$PROFILE_HOOK"

        # 添加到 .bashrc 和 .zshrc
        for rc in "${HOME}/.bashrc" "${HOME}/.zshrc"; do
            if [ -f "$rc" ]; then
                if ! grep -q "wechat-cc-autostart" "$rc" 2>/dev/null; then
                    echo "" >> "$rc"
                    echo "# wechat-claude-code auto-start" >> "$rc"
                    echo "source ${PROFILE_HOOK}" >> "$rc"
                    log "已添加自启钩子到 $rc"
                fi
            fi
        done
        log "nohup 模式自启已配置（首次打开终端时自动启动）"
    fi
}

# ---- 9. 显示结果 ----
echo ""
echo "============================================"
echo "  部署完成!"
echo "============================================"
echo ""
echo "接下来需要:"
echo ""
echo "  1. 扫码绑定微信（只需一次）:"
echo "     cd ${INSTALL_DIR} && npm run setup"
echo ""
echo "  2. 启动服务:"
echo "     cd ${INSTALL_DIR} && npm run daemon -- start"
echo ""

setup_autostart

echo ""
echo "常用命令:"
echo "  cd ${INSTALL_DIR}"
echo "  npm run daemon -- status   查看运行状态"
echo "  npm run daemon -- logs     查看日志"
echo "  npm run daemon -- restart  重启服务"
echo "  npm run daemon -- stop     停止服务"
echo ""
echo "数据目录: ~/.wechat-claude-code/"
echo "日志目录: ~/.wechat-claude-code/logs/"
echo ""

if ! $HAS_SYSTEMD_USER && $IS_WSL; then
    echo "⚠ WSL 开机自启注意:"
    echo "  当前使用 nohup + shell profile 模式。"
    echo "  每次打开新终端时会自动检查并启动 daemon。"
    echo "  如需真正的系统级自启，请在 WSL 中启用 systemd:"
    echo "    sudo tee -a /etc/wsl.conf <<< '[boot]'"
    echo "    sudo tee -a /etc/wsl.conf <<< 'systemd=true'"
    echo "    然后重启 WSL"
fi

echo ""
echo "安装目录: ${INSTALL_DIR}"
