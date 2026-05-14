# Claude Code WebUI 远程访问方案

通过frp内网穿透，在手机上使用Claude Code。

## 架构说明

```
手机 (浏览器)
    ↓
云服务器 (frps + 可选Nginx)
    ↑ frp隧道
公司电脑 WSL (frpc + Claude Code WebUI)
```

## 目录结构

```
cc-in-mobile/
├── server/                 # 云服务器配置
│   ├── docker-compose-frps.yml
│   ├── setup-server.sh
│   └── (运行后生成)
│       ├── config/
│       │   ├── frps.ini
│       │   └── nginx/
│       └── data/
│           ├── letsencrypt/
│           └── certbot/
│
├── client/                 # 本地WSL配置
│   ├── docker-compose.yml
│   ├── setup-local.sh
│   ├── frpc.ini.template
│   └── (运行后生成)
│       ├── .env
│       └── frpc.ini
│
└── README.md
```

## 使用步骤

### 第一步：配置云服务器

1. 将 `server/` 目录上传到云服务器
2. 执行脚本：
   ```bash
   cd server
   sudo bash setup-server.sh
   ```
3. 按提示配置，**记下输出的服务器地址和token**

### 第二步：配置本地WSL

1. 将 `client/` 目录复制到WSL
2. 执行脚本：
   ```bash
   cd client
   bash setup-local.sh
   ```
3. 输入云服务器地址和token

### 第三步：手机访问

- 如配置了HTTPS：`https://你的域名`
- 如未配置HTTPS：`http://服务器IP:3000`

## 常用命令

### 云服务器

```bash
cd server

# 查看状态
docker compose -f docker-compose-frps.yml ps

# 查看日志
docker compose -f docker-compose-frps.yml logs -f

# 重启服务
docker compose -f docker-compose-frps.yml restart

# 停止服务
docker compose -f docker-compose-frps.yml down
```

### 本地WSL

```bash
cd client

# 启动服务
bash setup-local.sh start

# 停止服务
bash setup-local.sh stop

# 重启服务
bash setup-local.sh restart

# 查看状态
bash setup-local.sh status

# 查看日志
bash setup-local.sh logs
```

## frps Dashboard

访问 `http://服务器IP:7500` 查看frp状态：
- 用户名：admin
- 密码：安装时设置的token

## 故障排除

### 无法访问服务

1. 检查本地服务：
   ```bash
   cd client
   docker compose ps
   curl http://localhost:3000
   ```

2. 检查frpc连接：
   ```bash
   docker compose logs frpc
   # 应看到 "proxy success"
   ```

3. 检查frps状态：
   ```bash
   cd server
   docker compose -f docker-compose-frps.yml ps
   docker compose -f docker-compose-frps.yml logs
   ```

4. 检查防火墙：
   ```bash
   ufw status
   ```

## 许可证

MIT License
