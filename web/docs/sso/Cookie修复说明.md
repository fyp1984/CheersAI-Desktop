# SSO Cookie 设置修复说明

**修复时间**: 2026-04-03  
**问题**: SSO 登录后出现 401 未授权错误

---

## 问题描述

用户通过 Desktop SSO 登录后，虽然登录接口返回成功，但后续的 API 请求返回 401 未授权错误：

```
2026-04-03 13:44:19 POST /console/api/refresh-token HTTP/1.1" 200
2026-04-03 13:44:19 GET /console/api/tags?type=app HTTP/1.1" 401
```

---

## 根本原因

在 `api/controllers/console/auth/desktop_sso.py` 中，Cookie 设置使用了自定义的 `response.set_cookie()` 方法，而不是系统标准的 Cookie 设置函数。这导致 Cookie 的格式、名称或属性与系统其他部分不一致。

### 问题代码

```python
# 错误的方式：手动设置 Cookie
response.set_cookie(
    'access_token',  # 可能缺少前缀或格式不正确
    value=token_pair.access_token,
    httponly=False,
    domain=None,
    secure=False,
    samesite='Lax',
    max_age=int(60 * 60 * 24),
    path="/",
)
```

---

## 解决方案

使用系统提供的标准 Cookie 设置函数，这些函数已经在 `libs/token.py` 中定义，并被其他登录端点使用：

- `set_access_token_to_cookie()`
- `set_refresh_token_to_cookie()`
- `set_csrf_token_to_cookie()`

### 修复后的代码

```python
# 正确的方式：使用标准 Dify Cookie 函数
from flask import make_response
response = make_response({'result': 'success'})

# 使用标准函数确保 Cookie 格式正确
set_access_token_to_cookie(request, response, token_pair.access_token)
set_refresh_token_to_cookie(request, response, token_pair.refresh_token)
set_csrf_token_to_cookie(request, response, token_pair.csrf_token)
```

---

## 标准 Cookie 函数的优势

1. **统一的 Cookie 命名**
   - 自动添加正确的前缀（如 `console_token` 而不是 `access_token`）
   - 与系统其他部分保持一致

2. **正确的安全属性**
   - 根据环境自动设置 `httponly`、`secure`、`samesite`
   - 符合安全最佳实践

3. **环境适配**
   - 自动根据开发/生产环境调整设置
   - 处理跨域和同源策略

4. **维护性**
   - 如果系统更新 Cookie 策略，所有端点自动受益
   - 减少代码重复

---

## 测试步骤

### 1. 清除浏览器缓存和 Cookie

在浏览器开发者工具中：
1. 打开 Application/Storage 标签
2. 清除所有 localhost:3000 和 localhost:5001 的 Cookie
3. 清除 Local Storage 和 Session Storage

### 2. 重新登录

1. 访问 http://localhost:3000
2. 点击 "Desktop SSO Login"
3. 使用 Tech 账户登录（6c6u33@example.com）

### 3. 验证 Cookie 设置

在浏览器开发者工具的 Application 标签中，检查 Cookie：

应该看到以下 Cookie（名称可能有前缀）：
- `console_token` 或类似名称（access token）
- `console_refresh_token` 或类似名称（refresh token）
- `csrf_token`

### 4. 验证 API 请求

在 Network 标签中，检查后续的 API 请求：
- `/console/api/tags?type=app` 应该返回 200 而不是 401
- 请求头应该包含正确的 Cookie

### 5. 验证菜单显示

登录成功后，应该看到：
- Tech 账户：7 个菜单项（无审计日志）
- 侧边栏正常显示
- 可以正常访问各个页面

---

## 预期结果

修复后，SSO 登录流程应该完全正常：

```
✅ POST /auth/desktop-sso/login → 200 (设置 Cookie)
✅ POST /console/api/refresh-token → 200 (使用 Cookie)
✅ GET /console/api/tags?type=app → 200 (使用 Cookie)
✅ GET /console/api/workspaces/current → 200 (返回角色信息)
```

---

## 相关文件

- **修复文件**: `api/controllers/console/auth/desktop_sso.py`
- **参考实现**: `api/controllers/console/auth/login.py`
- **Cookie 函数**: `api/libs/token.py`

---

## 后续优化

如果仍然遇到 Cookie 问题，可以考虑：

1. **检查 Cookie 域名设置**
   - 确保前端和后端在同一域名下
   - 或者正确配置 CORS 和 Cookie 跨域

2. **检查 SameSite 策略**
   - 本地开发可能需要 `SameSite=Lax`
   - 生产环境可能需要 `SameSite=None; Secure`

3. **检查 Cookie 大小**
   - 如果 token 过大，可能超过浏览器限制
   - 考虑使用 Session Storage 或 Redis

---

**文档版本**: v1.0  
**维护者**: 开发团队
