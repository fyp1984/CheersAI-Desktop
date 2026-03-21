# CORS 跨域问题修复指南

## 问题描述

前端 (http://localhost:3000) 无法访问后端 API (http://localhost:5001)，出现 CORS 错误：

```
Access to fetch at 'http://localhost:5001/console/api/system-features' from origin 'http://localhost:3000' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## 原因

后端的 `CONSOLE_CORS_ALLOW_ORIGINS` 环境变量未配置，导致 CORS 中间件拒绝来自前端的请求。

## 解决方案

### 方法 1: 修改 .env 文件（推荐）

在 `api/.env` 文件中添加以下配置：

```bash
# CORS 配置 - 允许前端访问
CONSOLE_CORS_ALLOW_ORIGINS=http://localhost:3000
```

如果需要允许多个源，使用逗号分隔：

```bash
CONSOLE_CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 方法 2: 使用环境变量

在启动后端服务前设置环境变量：

**Windows (PowerShell)**:
```powershell
$env:CONSOLE_CORS_ALLOW_ORIGINS="http://localhost:3000"
cd api
.venv\Scripts\python.exe -m flask run --host=0.0.0.0 --port=5001 --debug
```

**Linux/Mac**:
```bash
export CONSOLE_CORS_ALLOW_ORIGINS="http://localhost:3000"
cd api
.venv/bin/python -m flask run --host=0.0.0.0 --port=5001 --debug
```

### 方法 3: 开发环境允许所有源（仅用于开发）

⚠️ **警告**: 仅在开发环境使用，生产环境不要这样配置！

```bash
CONSOLE_CORS_ALLOW_ORIGINS=*
```

## 完整的 CORS 相关配置

在 `api/.env` 文件中添加：

```bash
# Console Web URL
CONSOLE_WEB_URL=http://localhost:3000

# CORS 配置
CONSOLE_CORS_ALLOW_ORIGINS=http://localhost:3000

# Web API CORS 配置
WEB_API_CORS_ALLOW_ORIGINS=http://localhost:3000,*
```

## 重启服务

修改配置后，需要重启后端服务：

1. 停止当前运行的后端服务（Ctrl+C）
2. 重新启动：

```bash
cd api
.venv\Scripts\python.exe -m flask run --host=0.0.0.0 --port=5001 --debug
```

## 验证修复

1. 打开浏览器开发者工具（F12）
2. 访问 http://localhost:3000
3. 查看 Network 标签
4. 应该能看到成功的 API 请求，响应头中包含：
   ```
   Access-Control-Allow-Origin: http://localhost:3000
   Access-Control-Allow-Credentials: true
   ```

## 技术说明

### CORS 配置位置

后端 CORS 配置在以下文件中：

- `api/extensions/ext_blueprints.py` - Blueprint CORS 配置
- `api/configs/feature/__init__.py` - CORS 配置定义

### Console API CORS 配置

```python
# ext_blueprints.py
_apply_cors_once(
    console_app_bp,
    resources={r"/*": {"origins": dify_config.CONSOLE_CORS_ALLOW_ORIGINS}},
    supports_credentials=True,
    allow_headers=list(AUTHENTICATED_HEADERS),
    methods=["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"],
    expose_headers=list(EXPOSED_HEADERS),
)
```

### 配置优先级

1. 环境变量 `CONSOLE_CORS_ALLOW_ORIGINS`
2. 如果未设置，回退到 `CONSOLE_WEB_URL`
3. 默认值为空字符串（拒绝所有跨域请求）

## 常见问题

### Q1: 修改后仍然报错？

**A**: 确保：
1. 已重启后端服务
2. 清除浏览器缓存（Ctrl+Shift+Delete）
3. 硬刷新页面（Ctrl+F5）

### Q2: 允许多个前端地址？

**A**: 使用逗号分隔：
```bash
CONSOLE_CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://192.168.1.100:3000
```

### Q3: 生产环境如何配置？

**A**: 使用具体的域名，不要使用 `*`：
```bash
CONSOLE_CORS_ALLOW_ORIGINS=https://app.yourdomain.com
```

### Q4: OPTIONS 预检请求失败？

**A**: 确保配置中包含 `OPTIONS` 方法：
```python
methods=["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"]
```

## 相关文件

- `api/.env` - 环境变量配置文件
- `api/.env.example` - 配置示例文件
- `api/extensions/ext_blueprints.py` - CORS 中间件配置
- `api/configs/feature/__init__.py` - 配置定义

## 快速修复命令

```bash
# 1. 进入 API 目录
cd e:\CheersAI-Desktop\api

# 2. 编辑 .env 文件，添加以下行
# CONSOLE_CORS_ALLOW_ORIGINS=http://localhost:3000

# 3. 重启服务
.venv\Scripts\python.exe -m flask run --host=0.0.0.0 --port=5001 --debug
```
