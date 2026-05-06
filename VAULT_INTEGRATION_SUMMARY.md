# Vault 集成方案总结

## 问题背景

用户登录 Desktop 后，需要从 FileBay 获取配置信息并传递给 Vault，但直接写文件存在权限问题。

## 解决方案

**通过 HTTP API 实现 Desktop 与 Vault 的通信**

1. **Vault 启动时开启本地 HTTP API 服务器** (监听 `http://localhost:7788`)
2. **Desktop 登录后调用 Vault API** 推送 FileBay 配置
3. **Vault 接收配置并写入本地数据库** (SQLite)

## 架构图

```
用户登录 Desktop
       ↓
Desktop API 获取 FileBay 配置
       ↓
HTTP POST → Vault API (localhost:7788)
       ↓
Vault 写入 SQLite 数据库
       ↓
Vault 使用配置进行文件脱敏
```

## 实现文件

### Vault 端 (Rust)

| 文件 | 说明 |
|------|------|
| `src-tauri/src/commands/vault_api_server.rs` | API 服务器实现 |
| `src-tauri/src/commands/mod.rs` | 模块注册 |
| `src-tauri/src/lib.rs` | 启动时自动启动 API 服务器 |
| `src-tauri/Cargo.toml` | 添加 warp 和 hyper 依赖 |

### Desktop 端 (Python)

| 文件 | 说明 |
|------|------|
| `api/controllers/console/vault_integration.py` | Vault 集成控制器 |
| `api/services/filebay_config_service.py` | FileBay 配置服务 (已存在) |
| `api/libs/filebay_user_config.py` | 用户配置辅助函数 (已存在) |

### 前端 (TypeScript/React)

| 文件 | 说明 |
|------|------|
| `web/service/vault.ts` | Vault 服务层 |
| `web/app/components/vault-sync-indicator.tsx` | Vault 同步指示器组件 |

### 文档和测试

| 文件 | 说明 |
|------|------|
| `docs/VAULT_INTEGRATION.md` | 详细技术方案 |
| `docs/VAULT_INTEGRATION_USAGE.md` | 使用指南 |
| `api/test_vault_integration.py` | 集成测试脚本 |

## API 接口

### Vault API (端口 7788)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 |
| POST | `/api/v1/filebay/config` | 保存配置 |
| GET | `/api/v1/filebay/config` | 获取配置 |
| DELETE | `/api/v1/filebay/config` | 删除配置 |

### Desktop API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/console/api/vault/health` | 检查 Vault 状态 |
| POST | `/console/api/vault/sync-config` | 同步配置到 Vault |

## 使用流程

### 1. 启动 Vault

```bash
# Vault 启动时自动启动 API 服务器
# 日志输出: ✅ Vault API Server started successfully on port 7788
```

### 2. 启动 Desktop

```bash
# 启动 API
cd api
python app.py

# 启动 Web
cd web
npm run dev
```

### 3. 用户登录

用户登录 Desktop 后，系统自动:
1. 检查 Vault 是否运行
2. 获取用户的 FileBay 配置
3. 调用 Vault API 推送配置
4. Vault 保存配置到数据库

### 4. 手动同步 (可选)

在设置页面点击"同步到 Vault"按钮，手动触发同步。

## 测试

运行集成测试:

```bash
cd api
python test_vault_integration.py
```

测试覆盖:
- ✅ Vault 健康检查
- ✅ 保存配置
- ✅ 获取配置
- ✅ 删除配置
- ✅ Desktop API 健康检查

## 优势

1. **无权限问题**: 通过 HTTP API 通信，避免文件权限问题
2. **解耦合**: Desktop 和 Vault 通过 API 通信，降低耦合度
3. **可扩展**: 易于添加新的 API 接口
4. **易于测试**: 可以独立测试 API 接口
5. **跨平台**: HTTP API 跨平台兼容

## 安全性

1. **本地通信**: API 只监听 `127.0.0.1`，不对外暴露
2. **数据加密**: 可以对 Token 进行加密存储
3. **访问控制**: 可以添加 API Key 认证
4. **日志审计**: 记录所有 API 调用

## 下一步

### 必须完成

1. ✅ 创建 Vault API 服务器代码
2. ✅ 创建 Desktop API 控制器
3. ✅ 创建前端服务层
4. ✅ 编写测试脚本
5. ✅ 编写文档

### 可选优化

1. ⬜ 添加配置加密
2. ⬜ 添加配置版本管理
3. ⬜ 添加配置同步历史
4. ⬜ 添加自动重试机制
5. ⬜ 添加 WebSocket 实时同步

## 部署清单

### Vault 端

- [ ] 添加 `warp` 和 `hyper` 依赖到 `Cargo.toml`
- [ ] 编译 Vault 应用
- [ ] 测试 API 服务器启动
- [ ] 测试 API 接口

### Desktop 端

- [ ] 注册 Vault 集成控制器
- [ ] 测试 API 接口
- [ ] 在登录流程中添加自动同步
- [ ] 在设置页面添加手动同步按钮

### 测试

- [ ] 运行集成测试脚本
- [ ] 测试登录后自动同步
- [ ] 测试手动同步
- [ ] 测试 Vault 未运行时的行为

## 常见问题

### Q: Vault API 启动失败怎么办?

A: 检查端口 7788 是否被占用，可以修改端口号。

### Q: Desktop 无法连接到 Vault 怎么办?

A: 确保 Vault 应用正在运行，并且 API 服务器已启动。

### Q: 配置同步失败怎么办?

A: 检查 Desktop 和 Vault 的日志，确认错误原因。

### Q: 如何验证配置已同步?

A: 在 Vault 中调用 `get_filebay_config_via_api()` 查看配置。

## 联系方式

如有问题，请联系开发团队。

## 参考文档

- [详细技术方案](./docs/VAULT_INTEGRATION.md)
- [使用指南](./docs/VAULT_INTEGRATION_USAGE.md)
- [FileBay 配置说明](./docs/GITEA_CONFIG_IN_SETTINGS.md)
