# Vault 与 Desktop 集成方案

## 📖 概述

本方案实现了 Desktop 与 Vault 的无缝集成，使得用户登录 Desktop 后，可以自动将 FileBay 配置同步到 Vault 本地数据库，解决了文件权限问题。

## 🎯 目标

- ✅ 用户登录 Desktop 后自动同步 FileBay 配置到 Vault
- ✅ 避免文件权限问题
- ✅ 提供手动同步功能
- ✅ 不影响用户登录流程
- ✅ 提供清晰的同步状态反馈

## 🏗️ 架构

```
Desktop (Web + API) ──HTTP──> Vault (API Server) ──> SQLite Database
```

### 核心组件

1. **Vault API Server** (Rust/Warp)
   - 监听 `http://localhost:7788`
   - 提供 RESTful API 接口
   - 处理配置的增删改查

2. **Desktop API Controller** (Python/Flask)
   - 获取用户 FileBay 配置
   - 调用 Vault API 推送配置
   - 提供健康检查接口

3. **Desktop Web Service** (TypeScript/React)
   - 自动同步逻辑
   - 手动同步按钮
   - 同步状态显示

## 📁 文件清单

### 新增文件

#### Vault 端
- `src-tauri/src/commands/vault_api_server.rs` - API 服务器实现
- `src-tauri/Cargo.toml` - 添加 warp 和 hyper 依赖

#### Desktop 端
- `api/controllers/console/vault_integration.py` - API 控制器
- `api/test_vault_integration.py` - 集成测试脚本
- `web/service/vault.ts` - 前端服务层
- `web/app/components/vault-sync-indicator.tsx` - UI 组件

#### 文档
- `docs/VAULT_INTEGRATION.md` - 详细技术方案
- `docs/VAULT_INTEGRATION_USAGE.md` - 使用指南
- `docs/VAULT_INTEGRATION_DIAGRAM.md` - 架构图
- `VAULT_INTEGRATION_SUMMARY.md` - 方案总结
- `VAULT_INTEGRATION_CHECKLIST.md` - 实施检查清单
- `VAULT_INTEGRATION_QUICK_REFERENCE.md` - 快速参考
- `VAULT_INTEGRATION_README.md` - 本文件

#### 脚本
- `scripts/test-vault-integration.ps1` - PowerShell 测试脚本

### 修改文件

#### Vault 端
- `src-tauri/src/commands/mod.rs` - 添加模块注册
- `src-tauri/src/lib.rs` - 添加启动逻辑和命令注册

## 🚀 快速开始

### 1. 安装依赖

#### Vault 端
```bash
cd src-tauri
cargo build
```

#### Desktop 端
```bash
# API (如果需要新依赖)
cd api
pip install requests

# Web (如果需要新依赖)
cd web
npm install
```

### 2. 启动服务

```bash
# 1. 启动 Vault (会自动启动 API 服务器)
# 查看日志确认: ✅ Vault API Server started successfully on port 7788

# 2. 启动 Desktop API
cd api
python app.py

# 3. 启动 Desktop Web
cd web
npm run dev
```

### 3. 测试集成

```bash
# Python 测试
python api/test_vault_integration.py

# PowerShell 测试
.\scripts\test-vault-integration.ps1
```

### 4. 使用功能

1. 用户登录 Desktop
2. 系统自动检查 Vault 是否运行
3. 如果 Vault 运行，自动同步配置
4. 在设置页面可以手动触发同步

## 📚 文档导航

### 开始使用
1. 📖 [方案总结](./VAULT_INTEGRATION_SUMMARY.md) - 快速了解方案
2. 🚀 [快速参考](./VAULT_INTEGRATION_QUICK_REFERENCE.md) - 常用命令和代码
3. ✅ [检查清单](./VAULT_INTEGRATION_CHECKLIST.md) - 实施步骤

### 深入了解
4. 📋 [详细方案](./docs/VAULT_INTEGRATION.md) - 完整技术方案
5. 📖 [使用指南](./docs/VAULT_INTEGRATION_USAGE.md) - 详细使用说明
6. 🎨 [架构图](./docs/VAULT_INTEGRATION_DIAGRAM.md) - 可视化架构

### 开发和测试
7. 🧪 [测试脚本](./api/test_vault_integration.py) - Python 测试
8. 🧪 [测试脚本](./scripts/test-vault-integration.ps1) - PowerShell 测试

## 🔌 API 接口

### Vault API (localhost:7788)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 |
| POST | `/api/v1/filebay/config` | 保存配置 |
| GET | `/api/v1/filebay/config` | 获取配置 |
| DELETE | `/api/v1/filebay/config` | 删除配置 |

### Desktop API (localhost:5001)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/console/api/vault/health` | 检查 Vault 状态 |
| POST | `/console/api/vault/sync-config` | 同步配置到 Vault |

## 💡 使用示例

### 前端 - 自动同步
```typescript
import { autoSyncToVault } from '@/service/vault'

// 登录成功后
const result = await autoSyncToVault()
if (result.synced) {
  console.log('配置已同步到 Vault')
}
```

### 前端 - 添加同步指示器
```tsx
import VaultSyncIndicator from '@/app/components/vault-sync-indicator'

<VaultSyncIndicator 
  autoSync={true}
  userEmail={currentUser.email}
/>
```

### curl - 测试 API
```bash
# 健康检查
curl http://localhost:7788/api/v1/health

# 保存配置
curl -X POST http://localhost:7788/api/v1/filebay/config \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://uat-filebay.cheersai.cloud",
    "username": "test_user",
    "repo_name": "workspace",
    "email": "test@example.com",
    "token": "test_token",
    "downloaded_at": "",
    "version": "1.0"
  }'
```

## 🧪 测试

### 运行测试
```bash
# Python 测试 (推荐)
cd api
python test_vault_integration.py

# PowerShell 测试
.\scripts\test-vault-integration.ps1
```

### 测试覆盖
- ✅ Vault 健康检查
- ✅ 保存配置
- ✅ 获取配置
- ✅ 删除配置
- ✅ Desktop API 健康检查

## 🐛 故障排查

### Vault API 无法连接
1. 确认 Vault 应用正在运行
2. 检查日志确认 API 服务器已启动
3. 检查端口 7788 是否被占用
4. 尝试访问 `http://localhost:7788/api/v1/health`

### 配置同步失败
1. 查看 Desktop 日志
2. 查看 Vault 日志
3. 确认用户的 FileBay 配置是否完整
4. 手动测试 API 接口

### 配置未生效
1. 在 Vault 中调用 `get_filebay_config_via_api()`
2. 检查数据库文件是否存在
3. 查看数据库中的 `user_settings` 表

详细故障排查请参考 [使用指南](./docs/VAULT_INTEGRATION_USAGE.md#故障排查)

## 🔒 安全性

- ✅ API 只监听 `127.0.0.1`，不对外暴露
- ✅ Token 存储在本地数据库，受操作系统权限保护
- ✅ 无敏感信息泄露到日志
- ✅ 可选的 Token 加密存储

## 📊 性能

| 指标 | 目标 |
|------|------|
| API 响应时间 | < 1 秒 |
| 同步时间 | < 2 秒 |
| 数据库操作 | < 100ms |

## 🎯 优势

1. **无权限问题**: 通过 HTTP API 通信，避免文件权限问题
2. **解耦合**: Desktop 和 Vault 通过 API 通信，降低耦合度
3. **可扩展**: 易于添加新的 API 接口
4. **易于测试**: 可以独立测试 API 接口
5. **跨平台**: HTTP API 跨平台兼容
6. **不影响登录**: 同步失败不影响用户登录

## 🔄 未来优化

- [ ] 配置加密存储
- [ ] 配置版本管理
- [ ] 配置同步历史记录
- [ ] 自动重试机制
- [ ] WebSocket 实时同步
- [ ] 配置验证和测试
- [ ] 多用户配置支持
- [ ] 配置冲突解决

## 📞 获取帮助

### 文档
- [详细方案](./docs/VAULT_INTEGRATION.md)
- [使用指南](./docs/VAULT_INTEGRATION_USAGE.md)
- [快速参考](./VAULT_INTEGRATION_QUICK_REFERENCE.md)

### 测试
```bash
python api/test_vault_integration.py
```

### 调试
```bash
# 启用详细日志
export RUST_LOG=debug  # Vault
export FLASK_DEBUG=1   # Desktop API
```

## 👥 贡献

欢迎提交 Issue 和 Pull Request!

## 📄 许可证

[许可证信息]

---

**快速链接**:
- 📖 [方案总结](./VAULT_INTEGRATION_SUMMARY.md)
- 🚀 [快速参考](./VAULT_INTEGRATION_QUICK_REFERENCE.md)
- ✅ [检查清单](./VAULT_INTEGRATION_CHECKLIST.md)
- 📋 [详细方案](./docs/VAULT_INTEGRATION.md)
- 📖 [使用指南](./docs/VAULT_INTEGRATION_USAGE.md)
- 🎨 [架构图](./docs/VAULT_INTEGRATION_DIAGRAM.md)
