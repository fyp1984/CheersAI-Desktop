# FileBay 配置入口恢复和 SSL 修复完成

## 已完成的工作

### 1. 恢复 FileBay 配置入口 ✅
- 在侧边栏添加"数据安全"菜单项
- 在数据脱敏页面添加"配置设置"标签页
- 集成了完整的 SandboxConfig 组件

### 2. 修复 SSL 连接问题 ✅
**问题**: Windows schannel 无法连接到 `uat-filebay.cheersai.cloud`
**解决方案**: 使用 pyOpenSSL 强制使用 OpenSSL 后端

**修改的文件**:
- `api/core/ssl_config.py` - 新建，自动配置 SSL
- `api/app_factory.py` - 在启动时加载 SSL 配置
- `api/services/gitea_storage_service.py` - 移除旧的 SSLAdapter
- `docker/filebay_proxy.py` - 重写使用 requests + pyOpenSSL
- `api/controllers/inner_api/gitea.py` - 新建 inner API 端点

### 3. 测试结果 ✅
- SSL 握手成功
- 可以连接到 FileBay 服务器
- 返回 401/403 是业务逻辑（token/权限），不是 SSL 问题

## 当前状态

### SSL 连接: ✅ 正常
```
✓ pyOpenSSL 已注入
✓ SSL 握手成功
✓ 可以连接到 uat-filebay.cheersai.cloud
```

### 认证问题: ⚠️ 需要配置
当前返回 401 错误是因为:
1. Token 可能过期或不正确
2. 用户需要修改密码（403 响应）
3. 权限配置问题

## 下一步操作

### 解决认证问题
1. 检查 `.env` 中的 `GITEA_TOKEN` 是否正确
2. 确认 `GITEA_OWNER` 和 `GITEA_REPO` 配置
3. 如果需要，在 FileBay 中重新生成 token
4. 确保用户已修改初始密码

### 测试步骤
1. 启动 FileBay 代理: `cd docker && python filebay_proxy.py`
2. 启动 API 服务器: `cd api && flask run --port=5001 --debug`
3. 访问前端配置页面测试

## 技术说明

### 为什么需要 pyOpenSSL?
- Windows 默认使用 schannel (系统 SSL 库)
- `uat-filebay.cheersai.cloud` 的 SSL 配置与 schannel 不兼容
- OpenSSL 有更好的兼容性
- Rust 的 rustls 也能工作（脱敏项目使用）

### pyOpenSSL 的作用
```python
import urllib3.contrib.pyopenssl
urllib3.contrib.pyopenssl.inject_into_urllib3()
```
将 urllib3 的 SSL 后端从 schannel 切换到 OpenSSL

## 文件清单

### 核心文件
- `api/core/ssl_config.py` - SSL 配置模块
- `api/app_factory.py` - 应用启动配置
- `api/services/gitea_storage_service.py` - Gitea 存储服务
- `docker/filebay_proxy.py` - FileBay 代理服务

### API 端点
- `/console/api/gitea/config` - Gitea 配置管理
- `/console/api/gitea/config/test` - 连接测试
- `/console/api/gitea/files` - 文件列表
- `/inner/api/enterprise/gitea/config` - 企业版配置

### 前端组件
- `web/app/(commonLayout)/data-masking/page.tsx` - 数据脱敏页面
- `web/app/components/data-masking/sandbox-config.tsx` - FileBay 配置组件
- `web/app/components/header/side-nav/index.tsx` - 侧边栏菜单

## 环境要求

```bash
pip install pyopenssl
```

## 已知问题

1. pyOpenSSL 在 urllib3 2.x 中已弃用（但仍可用）
2. 未来可能需要迁移到其他方案
3. Token 需要定期更新
