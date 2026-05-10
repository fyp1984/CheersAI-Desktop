# Vault 与 Desktop 脱敏系统集成

## 📖 概述

本项目实现了 CheersAI-Desktop (Vault 系统) 与 cheersai-desktop (脱敏系统) 的自动配置同步功能。用户通过 Desktop SSO 登录后，FileBay 配置会自动同步到本地数据库，供脱敏系统使用，无需手动导入配置文件。

## 🎯 目标

- ✅ 用户登录后自动获取 FileBay 配置
- ✅ 配置自动同步到本地 Vault 数据库
- ⏳ 脱敏系统自动读取配置
- ⏳ 无需手动导入配置文件

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    用户 Desktop SSO 登录                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Vault Web (Next.js + TypeScript)                │
│  - 交换 SSO Token                                             │
│  - 获取用户信息和 FileBay 配置                                │
│  - 检查 Vault Bridge 健康状态                                 │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP POST
                      ▼
┌─────────────────────────────────────────────────────────────┐
│         Vault Bridge (Python Flask + SQLite)                 │
│  - 监听 localhost:8765                                        │
│  - 接收配置并保存到数据库                                      │
│  - 提供配置查询 API                                           │
└─────────────────────┬───────────────────────────────────────┘
                      │ 写入
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Vault Database (SQLite)                         │
│  - 位置: ~/.cheersai/vault.db                                │
│  - 存储用户 FileBay 配置                                      │
└─────────────────────┬───────────────────────────────────────┘
                      │ 读取
                      ▼
┌─────────────────────────────────────────────────────────────┐
│         脱敏系统 (Tauri + Rust + React)                       │
│  - 读取 Vault 配置                                            │
│  - 文件脱敏                                                   │
│  - 上传到 FileBay                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 1. 启动 Vault Bridge 服务

```powershell
# Windows PowerShell
.\start_vault_bridge.ps1
```

或

```bash
# Linux/Mac 或直接使用 Python
cd api
python start_vault_bridge.py
```

### 2. 验证服务运行

```bash
curl http://localhost:8765/health
```

预期响应：
```json
{
  "status": "ok",
  "service": "vault-bridge",
  "version": "1.0.0",
  "database": "~/.cheersai/vault.db",
  "database_exists": true
}
```

### 3. 启动 Vault Web 服务

```bash
cd web
pnpm dev
```

### 4. 测试登录

1. 访问 http://localhost:3000
2. 使用 Desktop SSO 登录
3. 打开浏览器开发者工具 (F12)
4. 查看 Console，搜索 `[Vault Bridge]`
5. 应该看到配置同步成功的日志

## 📁 项目结构

```
CheersAI-Desktop/
├── api/
│   ├── services/
│   │   └── vault_bridge_service.py      # Vault Bridge 服务实现
│   └── start_vault_bridge.py            # Python 启动脚本
│
├── web/
│   ├── service/
│   │   └── vault-bridge.ts              # Vault Bridge 客户端
│   └── app/
│       └── oauth-callback/
│           └── page.tsx                 # SSO 登录集成
│
├── start_vault_bridge.ps1               # PowerShell 启动脚本
│
└── 文档/
    ├── VAULT_DESKTOP_INTEGRATION.md     # 完整集成方案
    ├── VAULT_BRIDGE_SETUP.md            # 快速设置指南
    ├── VAULT_INTEGRATION_STATUS.md      # 实施状态
    ├── VAULT_BRIDGE_QUICK_REFERENCE.md  # 快速参考
    ├── IMPLEMENTATION_SUMMARY.md        # 实施总结
    ├── INTEGRATION_CHECKLIST.md         # 检查清单
    └── README_VAULT_INTEGRATION.md      # 本文档
```

## 📚 文档导航

### 新手入门
1. **[README_VAULT_INTEGRATION.md](./README_VAULT_INTEGRATION.md)** (本文档) - 项目概述
2. **[VAULT_BRIDGE_SETUP.md](./VAULT_BRIDGE_SETUP.md)** - 快速设置指南

### 开发者
1. **[VAULT_DESKTOP_INTEGRATION.md](./VAULT_DESKTOP_INTEGRATION.md)** - 完整技术方案
2. **[VAULT_INTEGRATION_STATUS.md](./VAULT_INTEGRATION_STATUS.md)** - 详细实施状态
3. **[INTEGRATION_CHECKLIST.md](./INTEGRATION_CHECKLIST.md)** - 开发检查清单

### 日常使用
1. **[VAULT_BRIDGE_QUICK_REFERENCE.md](./VAULT_BRIDGE_QUICK_REFERENCE.md)** - 快速参考手册
2. **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)** - 实施总结

## 🔧 技术栈

### Vault 系统 (CheersAI-Desktop)
- **后端**: Python 3.13, Flask 3.1.3, SQLite3
- **前端**: Next.js, TypeScript, React
- **通信**: HTTP REST API (localhost:8765)

### 脱敏系统 (cheersai-desktop) - 待实现
- **后端**: Rust, Tauri
- **前端**: React, TypeScript
- **数据库**: rusqlite

## 📊 实施进度

| 模块 | 状态 | 完成度 |
|------|------|--------|
| Vault Bridge 服务 | ✅ 完成 | 100% |
| 前端集成 | ✅ 完成 | 100% |
| 文档 | ✅ 完成 | 100% |
| 脱敏系统集成 | ⏳ 待实现 | 0% |
| 端到端测试 | ⏳ 进行中 | 30% |

**总体进度**: 61.6%

## 🎯 下一步

### 立即执行
1. 在脱敏系统中实现 Rust 命令读取 Vault 配置
2. 在 UI 中添加自动加载配置功能
3. 进行端到端测试

### 详细步骤
参考 [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) 中的"下一步工作"部分。

## 🔒 安全考虑

- ✅ Vault Bridge 只监听 localhost (127.0.0.1)
- ✅ 数据库存储在用户主目录 (~/.cheersai/)
- ✅ CORS 配置只允许本地访问
- ⏳ Token 当前明文存储（待加密）

## 🐛 故障排查

### 常见问题

**Q: Vault Bridge 无法启动**
```bash
# 检查 Python 版本
python --version  # 需要 3.10+

# 检查依赖
pip install flask flask-cors

# 检查端口占用
netstat -ano | findstr :8765
```

**Q: 配置未同步**
```bash
# 1. 检查 Vault Bridge 是否运行
curl http://localhost:8765/health

# 2. 查看浏览器控制台日志
# 搜索: [Vault Bridge]

# 3. 检查数据库
sqlite3 ~/.cheersai/vault.db "SELECT * FROM filebay_configs;"
```

更多问题请参考 [VAULT_BRIDGE_SETUP.md](./VAULT_BRIDGE_SETUP.md) 的"故障排查"部分。

## 📞 支持

### 文档
- [快速设置指南](./VAULT_BRIDGE_SETUP.md)
- [快速参考手册](./VAULT_BRIDGE_QUICK_REFERENCE.md)
- [完整技术方案](./VAULT_DESKTOP_INTEGRATION.md)

### 日志
- **控制台**: 实时日志输出
- **文件**: `api/vault_bridge.log`

## 🎉 成就

- ✅ Vault Bridge 服务完整实现
- ✅ 自动配置同步功能
- ✅ 完整的文档体系
- ✅ 测试验证通过

## 📝 许可

本项目是 CheersAI-Desktop 的一部分，遵循相同的许可协议。

---

**最后更新**: 2026-05-06  
**版本**: 1.0.0  
**状态**: Vault 系统完成 ✅，脱敏系统待实现 ⏳
