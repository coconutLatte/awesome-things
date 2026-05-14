# wechat-claude-code Docker 试装实验报告

**实验日期:** 2026-05-08
**测试项目:** [Wechat-ggGitHub/wechat-claude-code](https://github.com/Wechat-ggGitHub/wechat-claude-code) (280⭐, 87 fork)
**测试环境:** Docker (node:22-slim, Debian Bookworm)

---

## 实验结果总览

| 测试项 | 结果 |
|--------|------|
| git clone | ✅ 通过 |
| npm install | ✅ 通过 (41 packages, 0 vulnerabilities) |
| TypeScript 编译 (tsc) | ✅ 通过 (21 个 .js 文件) |
| daemon 无账号启动 | ✅ 正确提示「未找到账号，请先 setup」 |
| daemon status | ✅ 正确输出「Not running」 |
| setup QR 码生成 | ✅ 终端 QR 码渲染成功，URL 有效 |
| npm audit 安全审计 | ✅ 0 vulnerabilities |
| 依赖完整性 | ✅ 6 个依赖全部正确安装 |

## 架构确认

```
微信(手机) ←→ iLink Bot API (ilinkai.weixin.qq.com)
    ←→ Node.js Daemon (main.ts)
    ←→ @anthropic-ai/claude-agent-sdk (v0.1.77)
    ←→ 本地 Claude Code
```

- **微信端通信:** 官方 iLink Bot API，通过 HTTP 长轮询获取消息，**不需要公网 IP**
- **Claude Code 端:** 使用 `@anthropic-ai/claude-agent-sdk` 的 `query()` 函数，支持 streaming、permission broker、session resume
- **认证方式:** 微信扫码 → 获取 Bearer Token → 持久化到 `~/.wechat-claude-code/accounts/`

## QR 码生成验证

在 headless Linux（无 GUI）环境下，`setup` 命令自动检测并使用 `qrcode-terminal` 在终端输出 ASCII QR 码。同时输出可访问的 URL 链接作为备选方案。这是正确的降级行为。

## 无法在 Docker 中验证的部分

| 项目 | 原因 |
|------|------|
| 扫码绑定 | 需要手机微信 App |
| iLink API 实际通信 | 需要扫码后获取的 token |
| Claude Agent SDK 对话 | 需要 `ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN` |
| daemon 实际运行 | 需要有效的 account token |
| launchd/systemd 服务管理 | 需要真实操作系统环境 |

## 关键功能代码审查

### 1. 中断处理
当用户在处理中发送新消息时，通过 `AbortController` 中止当前查询，然后处理新消息。`/clear` 命令可以强制重置卡住的会话状态。

### 2. 权限审批
通过 `PermissionBroker` 实现超时机制（120s），用户在微信回复 y/n 批准或拒绝工具调用。支持 `auto` 模式跳过所有审批。

### 3. 速率限制
发送消息时使用指数退避重试（10s → 20s → 40s → 60s 封顶），最多重试 3 次。

### 4. 会话持久化
SDK session ID 保存在 `~/.wechat-claude-code/sessions/`，支持跨消息恢复上下文。如果 resume 失败（如损坏的 session），自动降级为无 session 重试。

### 5. CRLF 注入防护
WeChat API 层 `baseUrl` 做了白名单校验（仅允许 `weixin.qq.com` 和 `wechat.com` 域名），`token` 通过 Bearer header 传递。

## 结论

**该项目在 Docker 环境中可成功安装和编译。** 代码结构清晰，错误处理完善，安全审计零漏洞。受限的测试项（QR 码绑定、实际 API 通信）需要物理手机和微信账号，无法在 Docker 中自动化，但这些属于平台依赖而非代码缺陷。

**总体评价:** 可以作为 Claude Code 接入微信的生产方案候选。
