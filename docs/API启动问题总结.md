# API 启动问题总结

## 问题描述

API 服务无法启动，持续出现错误：
```
以一种访问权限不允许的方式做了一个访问套接字的尝试。
```

这是 Windows 的 socket 权限错误（WSAEACCES，错误代码 10013）。

## 已尝试的解决方案

### 1. ✅ 关闭占用端口的 Docker 容器
- 停止了 `docker-api-1` 和 `docker-worker-1`
- 这两个容器占用了端口 5001

### 2. ❌ 更改绑定地址
- 尝试从 `0.0.0.0` 改为 `127.0.0.1`
- 结果：仍然失败

### 3. ❌ 更改端口
- 尝试从 5001 改为 8000
- 结果：仍然失败

### 4. ❌ 禁用 Debug 模式
- 尝试 `debug=False`
- 结果：仍然失败

### 5. ❌ 使用不同的启动方式
- 尝试 `flask run`
- 尝试 `python app.py`
- 结果：都失败

## 问题分析

这个错误通常由以下原因引起：

### 1. Windows 防火墙或安全软件
- Windows Defender 或第三方防火墙可能阻止 Python 绑定端口
- 需要添加 Python 到防火墙白名单

### 2. Windows 保留端口
- 某些端口被 Windows 系统保留
- 使用 `netsh interface ipv4 show excludedportrange protocol=tcp` 查看
- 已确认：5002-5003 在保留范围内（4907-5006）
- 但 5001 和 8000 不在保留范围内

### 3. Hyper-V 或 WSL2 网络冲突
- Hyper-V 虚拟交换机可能占用端口范围
- WSL2 的网络配置可能导致冲突

### 4. 权限不足
- Python 进程可能需要管理员权限才能绑定端口
- 特别是在企业环境或有安全策略的系统上

### 5. 网络适配器问题
- 某些网络适配器配置可能导致绑定失败
- VPN 或虚拟网络适配器可能干扰

## 当前服务状态

### ✅ 正常运行的服务

| 服务 | 端口 | 状态 | Terminal ID |
|------|------|------|-------------|
| 前端 (Next.js) | 3000 | ✅ Running | 2 |
| Celery Worker | - | ✅ Running | 3 |
| Celery Beat | - | ✅ Running | 4 |
| PostgreSQL | 5432 | ✅ Running | Docker (dify-postgres) |
| Redis | 6700 | ✅ Running | Docker (dify-redis) |
| Weaviate | 8081 | ✅ Running | Docker (dify-weaviate) |
| Plugin Daemon | 5012-5013 | ✅ Running | Docker (dify-plugin-daemon) |

### ❌ 无法启动的服务

| 服务 | 端口 | 状态 | 问题 |
|------|------|------|------|
| 后端 API (Flask) | 5001/8000 | ❌ Failed | Socket 权限错误 |

## 推荐解决方案

### 方案 1：以管理员身份运行（推荐）

1. 关闭当前 PowerShell
2. 右键点击 PowerShell → **以管理员身份运行**
3. 重新启动 API 服务

### 方案 2：添加防火墙规则

```powershell
# 以管理员身份运行
New-NetFirewallRule -DisplayName "Python Flask API" -Direction Inbound -Program "C:\path\to\python.exe" -Action Allow
```

### 方案 3：使用 Docker 运行 API

由于 Docker 容器可以正常运行，可以使用 Docker 来运行 API：

```bash
# 启动已有的 docker-api-1 容器
docker start docker-api-1

# API 将在 http://localhost:15001 可用
```

然后修改前端配置，将 API URL 指向 `http://localhost:15001`。

### 方案 4：禁用 Hyper-V 动态端口范围

```powershell
# 以管理员身份运行
netsh int ipv4 set dynamic tcp start=49152 num=16384
netsh int ipv6 set dynamic tcp start=49152 num=16384

# 重启电脑
```

### 方案 5：检查并关闭冲突的服务

```powershell
# 检查哪个进程在监听端口
Get-NetTCPConnection -State Listen | Where-Object {$_.LocalPort -eq 5001}

# 或使用 netstat
netstat -ano | findstr :5001
```

## 临时解决方案（立即可用）

### 使用 Docker API 容器

```bash
# 启动 Docker API 容器
docker start docker-api-1

# API 地址：http://localhost:15001
```

### 修改前端配置

修改 `web/.env` 或前端配置文件：
```
NEXT_PUBLIC_API_URL=http://localhost:15001
```

## 下一步行动

1. **立即**：使用 Docker API 容器作为临时解决方案
2. **短期**：以管理员身份运行 PowerShell 并重试
3. **长期**：配置防火墙规则，允许 Python 绑定端口

## 相关文件

- `api/app.py` - 已修改为使用 127.0.0.1:8000
- `docker-compose.dev.yaml` - Plugin Daemon 端口已改为 5012-5013
- `api/.env` - Plugin Daemon URL 已更新为 5012

## 系统信息

- 操作系统：Windows
- Shell：PowerShell (bash)
- Python：通过 uv 管理
- Docker：Docker Desktop

## 错误代码参考

- **WSAEACCES (10013)**：尝试以被禁止的方式访问套接字
- 常见原因：
  - 端口已被占用
  - 防火墙阻止
  - 权限不足
  - 系统保留端口
