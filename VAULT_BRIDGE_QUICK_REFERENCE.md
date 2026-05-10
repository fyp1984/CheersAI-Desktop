# Vault Bridge 快速参考

## 🚀 快速启动

```powershell
# 启动 Vault Bridge
.\start_vault_bridge.ps1

# 验证服务
curl http://localhost:8765/health
```

## 📡 API 端点速查

### 健康检查
```bash
GET http://localhost:8765/health
```

### 保存配置
```bash
POST http://localhost:8765/vault/config/filebay
Content-Type: application/json

{
  "user_id": "123",
  "config": {
    "url": "https://filebay.example.com",
    "username": "user123",
    "repoName": "workspace",
    "email": "user@example.com",
    "token": "ghp_xxxx"
  }
}
```

### 查询配置（用户ID）
```bash
GET http://localhost:8765/vault/config/filebay/123
```

### 查询配置（邮箱）
```bash
GET http://localhost:8765/vault/config/filebay/by-email/user@example.com
```

### 删除配置
```bash
DELETE http://localhost:8765/vault/config/filebay/123
```

## 🗄️ 数据库

**位置**: `~/.cheersai/vault.db` (Windows: `C:\Users\<用户名>\.cheersai\vault.db`)

**查询示例**:
```sql
-- 查看所有配置
SELECT * FROM filebay_configs;

-- 通过邮箱查询
SELECT * FROM filebay_configs WHERE email = 'user@example.com';

-- 通过用户名查询
SELECT * FROM filebay_configs WHERE username = 'user123';
```

## 🔍 调试

### 查看日志
```bash
# 实时日志（控制台）
.\start_vault_bridge.ps1

# 文件日志
type api\vault_bridge.log
```

### 测试配置同步
```javascript
// 浏览器控制台
// 1. 登录后检查日志
// 搜索: [Vault Bridge]

// 2. 手动测试同步
fetch('http://localhost:8765/vault/config/filebay', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: '123',
    config: {
      url: 'https://test.com',
      username: 'test',
      repoName: 'repo',
      email: 'test@test.com',
      token: 'token123'
    }
  })
})
```

## 🛠️ 常用命令

### 启动服务
```powershell
# PowerShell
.\start_vault_bridge.ps1

# Python 直接启动
cd api
python start_vault_bridge.py

# 自定义端口
python start_vault_bridge.py --port 9000

# 调试模式
python start_vault_bridge.py --debug
```

### 检查服务状态
```bash
# 健康检查
curl http://localhost:8765/health

# 检查端口占用
netstat -ano | findstr :8765
```

### 数据库操作
```bash
# 打开数据库
sqlite3 %USERPROFILE%\.cheersai\vault.db

# 查看表结构
.schema filebay_configs

# 查看所有配置
SELECT * FROM filebay_configs;

# 删除所有配置
DELETE FROM filebay_configs;

# 退出
.quit
```

## 🐛 故障排查速查

| 问题 | 检查 | 解决 |
|------|------|------|
| 服务无法启动 | Python 版本 | `python --version` (需要 3.10+) |
| 端口被占用 | 端口状态 | `netstat -ano \| findstr :8765` |
| 配置未同步 | Vault Bridge 运行 | `curl http://localhost:8765/health` |
| CORS 错误 | 浏览器控制台 | 检查 Vault Bridge 版本 |
| 数据库权限 | 目录权限 | `icacls %USERPROFILE%\.cheersai` |

## 📋 集成检查清单

### Vault 系统
- [x] Vault Bridge 服务实现
- [x] 前端客户端实现
- [x] SSO 登录集成
- [x] 启动脚本
- [x] 文档

### 脱敏系统
- [ ] Rust 命令实现
- [ ] TypeScript 绑定
- [ ] UI 集成
- [ ] 测试

## 🔗 相关文档

- [VAULT_BRIDGE_SETUP.md](./VAULT_BRIDGE_SETUP.md) - 详细设置指南
- [VAULT_DESKTOP_INTEGRATION.md](./VAULT_DESKTOP_INTEGRATION.md) - 完整集成方案
- [VAULT_INTEGRATION_STATUS.md](./VAULT_INTEGRATION_STATUS.md) - 实施状态

## 💡 提示

1. **开发环境**: Vault Bridge 在开发时自动启动，无需手动启动
2. **生产环境**: 建议使用 systemd/Windows Service 自动启动
3. **多用户**: 每个用户有独立的数据库文件
4. **安全**: Token 当前明文存储，生产环境建议加密
5. **备份**: 定期备份 `~/.cheersai/vault.db`
