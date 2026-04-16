# FileBay SSL 连接问题修复说明

## 问题根源

Windows 系统默认使用 schannel 作为 SSL/TLS 后端，但 `uat-filebay.cheersai.cloud` 的 SSL 配置与 schannel 不兼容，导致 SSL 握手失败。

Rust 的 `reqwest` 库使用 `rustls`（纯 Rust TLS 实现）可以正常连接，而 Python 默认使用系统 SSL 库（Windows 上是 schannel）无法连接。

## 解决方案

强制 Python 使用 OpenSSL 而不是 schannel，通过 `pyOpenSSL` 库实现。

## 已完成的修改

### 1. 创建 SSL 配置模块
**文件**: `api/core/ssl_config.py`
- 自动注入 pyOpenSSL 到 urllib3
- 在应用启动时自动配置

### 2. 更新应用工厂
**文件**: `api/app_factory.py`
- 在 `create_app()` 开始时导入并配置 SSL

### 3. 更新 FileBay 代理
**文件**: `docker/filebay_proxy.py`
- 使用 `requests` 库替代 `urllib.request`
- 注入 pyOpenSSL
- 支持所有 HTTP 方法（GET, POST, PUT, DELETE）

### 4. 创建 Inner API 端点
**文件**: `api/controllers/inner_api/gitea.py`
- 新增 `/inner/api/enterprise/gitea/config` 端点
- 根据 beta 用户 email 返回 FileBay 配置

### 5. 注册 Inner API
**文件**: `api/controllers/inner_api/__init__.py`
- 导入并注册 gitea 模块

## 测试结果

```bash
# 直接测试（使用 pyOpenSSL）
python test_pyopenssl.py
# ✓ Success! Status: 403 (SSL 连接成功)

# 代理测试
curl http://localhost:39091/api/v1/repos/.../contents/
# ✓ 返回 JSON 响应（SSL 连接成功）
```

## 使用说明

### 1. 确保安装 pyOpenSSL
```bash
pip install pyopenssl
```

### 2. 启动 FileBay 代理
```bash
cd docker
python filebay_proxy.py
```

### 3. 重启 API 服务
应用会自动使用 OpenSSL 后端

## 环境变量配置

`.env` 文件中的相关配置：
```env
GITEA_URL=https://uat-filebay.cheersai.cloud
GITEA_PROXY_URL=http://localhost:39091
GITEA_OWNER=beta_20260415162204_example_com_9838ca
GITEA_REPO=workspace
GITEA_TOKEN=c260c56115d2a9e32494927672c55eb84cd54d23
GITEA_VERIFY_SSL=false
```

## 技术细节

### 为什么 schannel 失败？
- schannel 是 Windows 原生 SSL/TLS 实现
- 对某些 SSL 配置（如旧版 TLS、特定密码套件）支持有限
- `uat-filebay.cheersai.cloud` 的 SSL 配置触发了 schannel 的兼容性问题

### 为什么 OpenSSL 成功？
- OpenSSL 是跨平台的 SSL/TLS 库
- 对各种 SSL 配置有更好的兼容性
- 支持更多的 TLS 版本和密码套件

### pyOpenSSL 的作用
- 将 urllib3（requests 的底层库）的 SSL 后端从系统默认切换到 OpenSSL
- 通过 `urllib3.contrib.pyopenssl.inject_into_urllib3()` 实现

## 注意事项

1. pyOpenSSL 在 urllib3 2.x 中已被弃用，但目前仍然可用
2. 未来可能需要迁移到其他解决方案（如使用 httpx + httpcore）
3. 代理服务需要保持运行以支持本地开发
