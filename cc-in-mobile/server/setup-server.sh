#!/bin/bash
set -e

# Claude Code WebUI 云服务器配置脚本 (Docker版)

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

# 检查Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        log_info "安装命令: curl -fsSL https://get.docker.com | sh"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker服务未启动"
        log_info "启动命令: sudo systemctl start docker"
        exit 1
    fi

    log_info "Docker已就绪"
}

# 收集配置信息
collect_config() {
    log_input "请输入用于frp认证的token（留空自动生成）: "
    read -r AUTH_TOKEN

    if [ -z "$AUTH_TOKEN" ]; then
        AUTH_TOKEN=$(openssl rand -hex 16)
        log_info "已生成token: $AUTH_TOKEN"
    fi

    log_input "是否配置HTTPS？需要域名 (y/n): "
    read -r SETUP_HTTPS

    if [ "$SETUP_HTTPS" = "y" ] || [ "$SETUP_HTTPS" = "Y" ]; then
        log_input "请输入域名（例如: claude.yourdomain.com）: "
        read -r DOMAIN

        if [ -z "$DOMAIN" ]; then
            log_error "域名不能为空"
            exit 1
        fi

        log_input "请输入邮箱（用于SSL证书）: "
        read -r EMAIL

        log_input "请输入Basic Auth用户名: "
        read -r AUTH_USER

        log_input "请输入Basic Auth密码: "
        read -rs AUTH_PASS
        echo ""
    fi

    log_info "配置信息收集完成"
    echo ""
    log_info "认证token: $AUTH_TOKEN"
    [ "$SETUP_HTTPS" = "y" ] && log_info "域名: $DOMAIN"
    echo ""

    log_input "确认以上信息正确？(y/n): "
    read -r CONFIRM
    if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
        log_info "已取消"
        exit 0
    fi

    # 保存配置
    cat > "$CONFIG_FILE" << EOF
# Claude Code WebUI 云服务器配置
AUTH_TOKEN=$AUTH_TOKEN
SETUP_HTTPS=$SETUP_HTTPS
DOMAIN=$DOMAIN
EMAIL=$EMAIL
AUTH_USER=$AUTH_USER
AUTH_PASS=$AUTH_PASS
EOF
}

# 生成frps配置
generate_frps_config() {
    log_info "生成frps配置..."

    mkdir -p "$SCRIPT_DIR/config"
    cat > "$SCRIPT_DIR/config/frps.ini" << EOF
[common]
bind_port = 7000
token = $AUTH_TOKEN
dashboard_port = 7500
dashboard_user = admin
dashboard_pwd = $AUTH_TOKEN
EOF

    log_info "frps配置已生成"
}

# 配置Nginx (HTTPS)
setup_nginx() {
    log_info "配置Nginx..."

    # 创建目录
    mkdir -p "$SCRIPT_DIR/nginx/conf.d"
    mkdir -p "$SCRIPT_DIR/nginx/ssl"
    mkdir -p "$SCRIPT_DIR/certbot/www"

    # 生成Basic Auth密码文件
    if command -v htpasswd &> /dev/null; then
        htpasswd -cb "$SCRIPT_DIR/nginx/.htpasswd" "$AUTH_USER" "$AUTH_PASS"
    else
        # 使用Docker生成
        docker run --rm -it httpd:alpine htpasswd -nb "$AUTH_USER" "$AUTH_PASS" > "$SCRIPT_DIR/nginx/.htpasswd"
    fi

    # 先创建HTTP配置（用于申请证书）
    cat > "$SCRIPT_DIR/nginx/conf.d/claude-code.conf" << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF

    # 启动Nginx
    docker compose -f docker-compose-frps.yml up -d nginx

    # 等待Nginx启动
    sleep 5

    log_info "Nginx配置完成"
}

# 申请SSL证书
setup_ssl() {
    log_info "申请SSL证书..."

    # 使用certbot申请证书
    docker compose -f docker-compose-frps.yml run --rm certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        -d "$DOMAIN"

    # 更新Nginx配置为HTTPS
    cat > "$SCRIPT_DIR/nginx/conf.d/claude-code.conf" << EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Basic Auth
    auth_basic "Claude Code";
    auth_basic_user_file /etc/nginx/.htpasswd;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://frps:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket支持
        proxy_read_timeout 86400;
    }
}
EOF

    # 重启Nginx
    docker compose -f docker-compose-frps.yml restart nginx

    log_info "SSL证书配置完成"
}

# 启动服务
start_service() {
    log_info "启动frps服务..."

    if [ "$SETUP_HTTPS" = "y" ] || [ "$SETUP_HTTPS" = "Y" ]; then
        docker compose -f docker-compose-frps.yml up -d
    else
        docker compose -f docker-compose-frps.yml up -d frps
    fi

    # 等待服务启动
    sleep 5

    # 检查服务状态
    if docker compose -f docker-compose-frps.yml ps | grep -q "Up"; then
        log_info "服务启动成功！"
    else
        log_error "服务启动失败，请检查日志"
        docker compose -f docker-compose-frps.yml logs
        exit 1
    fi
}

# 配置防火墙
setup_firewall() {
    log_info "配置防火墙..."

    if command -v ufw &> /dev/null; then
        ufw allow 22/tcp    # SSH
        ufw allow 7000/tcp  # frps
        ufw allow 7500/tcp  # Dashboard

        if [ "$SETUP_HTTPS" = "y" ] || [ "$SETUP_HTTPS" = "Y" ]; then
            ufw allow 80/tcp
            ufw allow 443/tcp
        else
            ufw allow 3000/tcp  # 直接访问
        fi

        ufw --force enable
        log_info "防火墙配置完成"
    else
        log_warn "ufw未安装，请手动配置防火墙"
    fi
}

# 显示配置摘要
show_summary() {
    # 获取公网IP
    PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "无法获取")

    echo ""
    echo "=========================================="
    log_info "配置完成！"
    echo "=========================================="
    echo ""
    log_info "frps服务状态:"
    docker compose -f docker-compose-frps.yml ps
    echo ""
    log_info "========================================="
    log_info "重要：请保存以下信息用于客户端配置"
    log_info "========================================="
    log_info "服务器地址: $PUBLIC_IP"
    log_info "认证Token: $AUTH_TOKEN"
    echo ""

    if [ "$SETUP_HTTPS" = "y" ] || [ "$SETUP_HTTPS" = "Y" ]; then
        log_info "访问地址: https://$DOMAIN"
        log_info "用户名: $AUTH_USER"
        log_info "frps Dashboard: http://$PUBLIC_IP:7500"
    else
        log_info "访问地址: http://$PUBLIC_IP:3000"
        log_info "frps Dashboard: http://$PUBLIC_IP:7500"
    fi

    log_info "Dashboard用户名: admin"
    log_info "Dashboard密码: $AUTH_TOKEN"
    echo ""
    log_info "下一步:"
    log_info "1. 在公司电脑运行 setup-local.sh"
    log_info "2. 输入上面的服务器地址和token"
    log_info "3. 手机访问上面的地址"
    echo ""
    log_info "常用命令:"
    log_info "  查看状态: docker compose -f docker-compose-frps.yml ps"
    log_info "  查看日志: docker compose -f docker-compose-frps.yml logs -f"
    log_info "  重启服务: docker compose -f docker-compose-frps.yml restart"
    log_info "  停止服务: docker compose -f docker-compose-frps.yml down"
    echo ""
}

# 显示帮助
show_help() {
    echo "Claude Code WebUI 云服务器配置脚本 (Docker版)"
    echo ""
    echo "用法: sudo $0 [命令]"
    echo ""
    echo "命令:"
    echo "  install    - 安装并配置所有组件"
    echo "  start      - 启动服务"
    echo "  stop       - 停止服务"
    echo "  restart    - 重启服务"
    echo "  status     - 查看服务状态"
    echo "  logs       - 查看日志"
    echo "  help       - 显示此帮助信息"
    echo ""
}

# 主函数
main() {
    case "${1:-install}" in
        install)
            check_docker
            collect_config
            generate_frps_config
            start_service
            setup_firewall

            if [ "$SETUP_HTTPS" = "y" ] || [ "$SETUP_HTTPS" = "Y" ]; then
                setup_nginx
                setup_ssl
            fi

            show_summary
            ;;
        start)
            check_docker
            docker compose -f docker-compose-frps.yml up -d
            ;;
        stop)
            docker compose -f docker-compose-frps.yml down
            ;;
        restart)
            docker compose -f docker-compose-frps.yml restart
            ;;
        status)
            docker compose -f docker-compose-frps.yml ps
            ;;
        logs)
            docker compose -f docker-compose-frps.yml logs -f
            ;;
        help|*)
            show_help
            ;;
    esac
}

main "$@"
