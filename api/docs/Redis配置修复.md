# Redis 配置修复

## 问题描述

SSO 登录时返回 500 错误，Flask 日志显示：

```
redis.exceptions.AuthenticationError: Client sent AUTH, but no password is set
```

## 根本原因

**Redis 端口映射不匹配**

1. **Docker Compose 配置**（`docker-compose.dev.yaml`）：
   ```yaml
   redis:
     ports:
       - "6700:6379"  # Redis 容器映射到主机的 6700 端口
   ```

2. **之前的 .env 配置**（错误）：
   ```env
   REDIS_PORT=6379  # ❌ 尝试连接 6379，但 Redis 实际在 6700
   ```

3. **结果**：Flask 尝试连接 `127.0.0.1:6379`，但 Redis 实际监听在 `127.0.0.1:6700`

## 修复方案

修改 `api/.env` 文件，将 Redis 端口改回 6700：

```env
# === Redis 配置 ===
REDIS_HOST=127.0.0.1
REDIS_PORT=6700  # ✅ 修复：使用正确的端口
REDIS_DB=0
REDIS_PASSWORD=difyai123456
REDIS_USE_SSL=false
REDIS_SERIALIZATION_PROTOCOL=2

# Celery (使用 Redis)
CELERY_BROKER_URL=redis://:difyai123456@127.0.0.1:6700/1  # ✅ 修复
CELERY_BACKEND=redis
```

## 验证步骤

1. **重启 Flask**
   ```bash
   # 停止旧进程
   # 启动新进程
   cd api
   python -m flask run --host 0.0.0.0 --port=5001 --debug
   ```

2. **检查日志**
   - ✅ 没有 Redis 认证错误
   - ✅ Flask 成功启动
   - ✅ 所有扩展加载成功

3. **测试 SSO 登录**
   - 刷新浏览器
   - 点击 SSO 登录
   - 应该成功登录并自动配置 FileBay

## 技术细节

### Docker 端口映射

```yaml
ports:
  - "主机端口:容器端口"
  - "6700:6379"  # 主机 6700 → 容器 6379
```

- **容器内部**：Redis 监听 6379
- **主机访问**：需要连接 6700

### 为什么之前能工作？

之前的配置可能一直使用 6700，只是在某次修改时错误地改成了 6379。

## 相关文件

- `api/.env` - Flask 环境配置（已修复）
- `docker-compose.dev.yaml` - Docker 服务配置
- `api/controllers/console/auth/desktop_sso.py` - SSO 登录控制器

## 状态

✅ **已修复** - Flask 已重启，Redis 连接正常

## 下一步

**请刷新浏览器并测试 SSO 登录**
