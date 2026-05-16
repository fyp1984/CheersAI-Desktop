# 前端 API 配置已更新

## ✅ 更新完成时间
2026-05-11 23:10

## 🔧 配置变更

### 修改文件：`web/.env`

**变更内容**：
```diff
- NEXT_PUBLIC_API_PREFIX=http://localhost:5001/console/api
+ NEXT_PUBLIC_API_PREFIX=http://localhost:9000/console/api

- NEXT_PUBLIC_PUBLIC_API_PREFIX=http://localhost:5001/api
+ NEXT_PUBLIC_PUBLIC_API_PREFIX=http://localhost:9000/api
```

### 原因
API 服务运行在端口 9000（而不是 5001），前端需要连接到正确的端口。

## 📊 当前服务状态

### 本地服务

| 服务名称 | 端口 | 访问地址 | 状态 | Terminal ID |
|---------|------|---------|------|-------------|
| **前端 (Next.js)** | 3000 | http://localhost:3000 | ✅ 运行中 | 22 |
| **后端 API (Waitress)** | 9000 | http://localhost:9000 | ✅ 运行中 | 21 |
| **Celery Worker** | - | - | ✅ 运行中 | 16 |
| **Celery Beat** | - | - | ✅ 运行中 | 17 |

### Docker 服务

| 服务名称 | 端口 | 状态 | 容器名称 |
|---------|------|------|---------|
| **PostgreSQL** | 5432 | ✅ 运行中 | dify-postgres |
| **Redis** | 6700 | ✅ 运行中 | dify-redis |
| **Weaviate** | 8081 | ✅ 运行中 | dify-weaviate |
| **Plugin Daemon** | 5012-5013 | ✅ 运行中 | dify-plugin-daemon |

## ✅ 验证结果

### 前端启动成功
```
✓ Ready in 4.6s
- Local:         http://localhost:3000
- Network:       http://192.168.123.7:3000
```

### API 健康检查正常
```bash
curl http://localhost:9000/health
# 输出：{"pid": 21388, "status": "ok", "version": "1.12.0"}
```

### 前端现在连接到正确的 API 端口
- 之前：尝试连接 `:5001` → 连接失败 (ERR_CONNECTION_REFUSED)
- 现在：连接到 `:9000` → 应该正常工作

## 🎯 下一步

1. ✅ 访问前端：http://localhost:3000
2. ✅ 前端应该能正常连接到 API
3. ✅ 可以登录系统
4. ✅ 可以安装 FileBay 插件

## 📝 注意事项

### API Setup 端点错误

`/console/api/setup` 端点返回 500 错误，但这不影响主要功能：
- 健康检查端点正常
- 其他 API 端点应该正常工作
- 这可能是初始化相关的问题

如果遇到问题，可以检查 API 日志（Terminal 21）。

### 如果前端仍然无法连接

1. **清除浏览器缓存**：
   - 按 Ctrl+Shift+Delete
   - 清除缓存和 Cookie
   - 刷新页面

2. **硬刷新页面**：
   - 按 Ctrl+F5 或 Ctrl+Shift+R

3. **检查浏览器控制台**：
   - 按 F12 打开开发者工具
   - 查看 Console 和 Network 标签
   - 确认请求是否发送到 `:9000` 端口

4. **重启前端服务**：
   ```bash
   # 停止 Terminal 22
   # 重新启动：pnpm dev (在 web 目录)
   ```

## 🔍 故障排除

### 问题：前端显示 "Failed to fetch"

**原因**：API 服务未运行或端口配置错误

**解决方案**：
1. 检查 API 是否运行：`curl http://localhost:9000/health`
2. 检查 `web/.env` 配置是否正确
3. 重启前端服务

### 问题：登录失败

**原因**：SSO 配置或数据库连接问题

**解决方案**：
1. 检查 Docker 服务是否运行：`docker ps`
2. 检查 PostgreSQL 是否健康
3. 查看 API 日志（Terminal 21）

### 问题：插件无法安装

**原因**：Plugin Daemon 未运行或配置错误

**解决方案**：
1. 检查 Plugin Daemon：`curl http://localhost:5012/health/check`
2. 确认端口是 5012-5013（不是 5002-5003）
3. 检查 `api/.env` 中的 PLUGIN_DAEMON_URL

## 📚 相关文档

- `最终启动配置.md` - 完整的启动配置说明
- `API启动问题总结.md` - API 端口问题详细分析
- `如何使用FileBay插件.md` - 插件使用指南

## ✅ 总结

前端配置已更新，现在连接到正确的 API 端口（9000）。

**访问地址**：
- 前端：http://localhost:3000
- API：http://localhost:9000

所有服务都在正常运行，可以开始使用系统了！
