#!/bin/bash
set -e

# Claude Code WebUI 本地安装/启动脚本 (systemd版)
# 适用于 WSL in Windows

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_input() {
    echo -e "${BLUE}[INPUT]${NC} $1"
}

# 配置文件
CONFIG_FILE="$SCRIPT_DIR/.env"

# 加载配置
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
    fi
}

# 保存配置
save_config() {
    cat > "$CONFIG_FILE" << EOF
# Claude Code WebUI 配置文件
SERVER_ADDR=$SERVER_ADDR
AUTH_TOKEN=$AUTH_TOKEN
EOF
    log_info "配置已保存到 $CONFIG_FILE"
}

# 收集配置信息
collect_config() {
    load_config

    if [ -z "$SERVER_ADDR" ]; then
        log_input "请输入云服务器IP或域名: "
        read -r SERVER_ADDR
    else
        log_info "使用已配置的云服务器地址: $SERVER_ADDR"
        log_input "是否更改？(y/n): "
        read -r CHANGE
        if [ "$CHANGE" = "y" ] || [ "$CHANGE" = "Y" ]; then
            log_input "请输入云服务器IP或域名: "
            read -r SERVER_ADDR
        fi
    fi

    if [ -z "$AUTH_TOKEN" ]; then
        log_input "请输入frp认证token（在云服务器setup-server.sh中设置）: "
        read -r AUTH_TOKEN
    else
        log_info "使用已配置的认证token"
        log_input "是否更改？(y/n): "
        read -r CHANGE
        if [ "$CHANGE" = "y" ] || [ "$CHANGE" = "Y" ]; then
            log_input "请输入frp认证token: "
            read -r AUTH_TOKEN
        fi
    fi

    if [ -z "$SERVER_ADDR" ] || [ -z "$AUTH_TOKEN" ]; then
        log_error "服务器地址和token不能为空"
        exit 1
    fi

    save_config
}

# 安装claude-code-webui
install_claude_code_webui() {
    log_info "检查claude-code-webui..."

    # 检查npm prefix是否正确
    NPM_PREFIX=$(npm config get prefix)
    NODE_BIN_DIR=$(dirname $(which node))

    if [ "$NPM_PREFIX" != "$NODE_BIN_DIR/.." ]; then
        log_warn "npm prefix配置为 $NPM_PREFIX，正在修正为 $NODE_BIN_DIR/.."
        npm config set prefix "$NODE_BIN_DIR/.."
    fi

    # 检查是否已安装
    if command -v claude-code-webui &> /dev/null; then
        CURRENT_VERSION=$(claude-code-webui --version 2>/dev/null || echo "unknown")
        log_info "已安装 claude-code-webui: $CURRENT_VERSION"
        log_input "是否更新到最新版本？(y/n): "
        read -r UPDATE
        if [ "$UPDATE" = "y" ] || [ "$UPDATE" = "Y" ]; then
            npm install -g claude-code-webui@latest
        fi
    else
        log_info "安装claude-code-webui..."
        npm install -g claude-code-webui
    fi

    log_info "claude-code-webui安装完成"
}

# 安装frpc
install_frpc() {
    log_info "安装frpc..."

    # 获取最新版本
    FRP_VERSION=$(curl -s https://api.github.com/repos/fatedier/frp/releases/latest | grep '"tag_name"' | sed -E 's/.*"v([^"]+)".*/\1/')
    log_info "最新版本: v$FRP_VERSION"

    cd /tmp
    wget -q "https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/frp_${FRP_VERSION}_linux_amd64.tar.gz"
    tar -xzf "frp_${FRP_VERSION}_linux_amd64.tar.gz"
    sudo cp "frp_${FRP_VERSION}_linux_amd64/frpc" /usr/local/bin/
    sudo chmod +x /usr/local/bin/frpc
    rm -rf "frp_${FRP_VERSION}_linux_amd64"*

    log_info "frpc安装完成"
}

# 生成frpc配置
generate_frpc_config() {
    log_info "生成frpc配置..."
    sed -e "s/__SERVER_ADDR__/$SERVER_ADDR/g" \
        -e "s/__AUTH_TOKEN__/$AUTH_TOKEN/g" \
        "$SCRIPT_DIR/frpc.toml.template" > "$SCRIPT_DIR/frpc.toml"
    log_info "frpc配置已生成"
}

# 创建systemd服务
setup_systemd_services() {
    log_info "创建systemd服务..."

    # 获取当前用户
    CURRENT_USER=$(whoami)

    # 获取claude-code-webui路径
    CLAUDE_WEBUI_BIN=$(which claude-code-webui 2>/dev/null)
    if [ -z "$CLAUDE_WEBUI_BIN" ]; then
        log_error "claude-code-webui未安装或不在PATH中"
        exit 1
    fi
    NODE_BIN_DIR=$(dirname $(which node))

    # claude-code-webui服务
    sudo tee /etc/systemd/system/claude-code-webui.service > /dev/null << EOF
[Unit]
Description=Claude Code WebUI
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$CLAUDE_WEBUI_BIN --port 3000 --host 0.0.0.0
Restart=on-failure
RestartSec=5s
Environment=NODE_ENV=production
Environment=PATH=$NODE_BIN_DIR:/root/.hermes/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

[Install]
WantedBy=multi-user.target
EOF

    # frpc服务
    sudo tee /etc/systemd/system/frpc.service > /dev/null << EOF
[Unit]
Description=frpc client
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
ExecStart=/usr/local/bin/frpc -c $SCRIPT_DIR/frpc.toml
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

    # 重载systemd
    sudo systemctl daemon-reload

    # 启用服务
    sudo systemctl enable claude-code-webui
    sudo systemctl enable frpc

    log_info "systemd服务创建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    sudo systemctl start claude-code-webui
    sudo systemctl start frpc

    # 等待服务启动
    sleep 5

    # 检查服务状态
    if systemctl is-active --quiet claude-code-webui && systemctl is-active --quiet frpc; then
        log_info "服务启动成功！"
        log_info "本地访问: http://localhost:3000"
        log_info "远程访问: http://$SERVER_ADDR:3000"
    else
        log_error "服务启动失败，请检查日志"
        sudo systemctl status claude-code-webui frpc
        exit 1
    fi
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    sudo systemctl stop frpc
    sudo systemctl stop claude-code-webui
    log_info "服务已停止"
}

# 查看状态
show_status() {
    echo "=== Claude Code WebUI ==="
    sudo systemctl status claude-code-webui --no-pager
    echo ""
    echo "=== frpc ==="
    sudo systemctl status frpc --no-pager
}

# 查看日志
show_logs() {
    journalctl -u claude-code-webui -u frpc -f
}

# 测试连接
test_connection() {
    log_info "测试连接..."

    # 测试本地服务
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200\|301\|302"; then
        log_info "✓ 本地服务正常"
    else
        log_warn "✗ 本地服务异常"
    fi

    # 测试frpc连接
    if journalctl -u frpc --no-pager -n 20 | grep -q "proxy success"; then
        log_info "✓ frpc连接正常"
    else
        log_warn "✗ frpc连接异常"
    fi
}

# 显示帮助
show_help() {
    echo "Claude Code WebUI 管理脚本 (systemd版)"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  install    - 安装并启动服务"
    echo "  start      - 启动服务"
    echo "  stop       - 停止服务"
    echo "  restart    - 重启服务"
    echo "  status     - 查看服务状态"
    echo "  logs       - 查看服务日志"
    echo "  config     - 修改配置"
    echo "  test       - 测试连接"
    echo "  uninstall  - 卸载服务"
    echo "  help       - 显示此帮助信息"
    echo ""
}

# 卸载服务
uninstall_services() {
    log_info "卸载服务..."

    sudo systemctl stop frpc 2>/dev/null || true
    sudo systemctl stop claude-code-webui 2>/dev/null || true
    sudo systemctl disable frpc 2>/dev/null || true
    sudo systemctl disable claude-code-webui 2>/dev/null || true

    sudo rm -f /etc/systemd/system/frpc.service
    sudo rm -f /etc/systemd/system/claude-code-webui.service
    sudo systemctl daemon-reload

    log_info "服务已卸载"
}

# 主函数
main() {
    case "${1:-install}" in
        install)
            collect_config
            install_claude_code_webui
            install_frpc
            generate_frpc_config
            setup_systemd_services
            start_services
            echo ""
            log_info "安装完成！"
            log_info "远程访问地址: http://$SERVER_ADDR:3000"
            ;;
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            stop_services
            start_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        config)
            collect_config
            generate_frpc_config
            log_info "配置已更新，请运行 '$0 restart' 重启服务"
            ;;
        test)
            test_connection
            ;;
        uninstall)
            uninstall_services
            ;;
        help|*)
            show_help
            ;;
    esac
}

main "$@"
