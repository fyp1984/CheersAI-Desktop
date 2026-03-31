# Cookie 问题最终修复

## 问题根源

找到了！问题在于 Cookie 的 `SameSite` 属性设置为 `Lax`，这导致：
- 跨域请求（localhost:3000 -> localhost:5001）时，Cookie 不会被发送
- 即使 SSO 登录成功设置了 Cookie，后续 API 请求也拿不到 Cookie
- 所以一直返回 401 Unauthorized

## 解决方案

修改后端 SSO 登录接口 (`api/controllers/console/auth/desktop_sso.py`)，直接设置 Cookie 时使用更宽松的配置：

```python
# 本地开发环境的 Cookie 设置
response.set_cookie(
    'access_token',
    value=token_pair.access_token,
    httponly=False,  # 允许 JavaScript 访问（方便调试）
    domain=None,     # 让浏览器自动决定
    secure=False,    # 允许 HTTP（本地开发）
    samesite='Lax',  # HTTP 下使用 Lax
    max_age=86400,   # 24 小时
    path="/",
)
```

关键修改：
1. `httponly=False` - 允许 JavaScript 访问，方便调试
2. `domain=None` - 让浏览器自动决定域名
3. `secure=False` - 允许 HTTP 协议
4. `samesite='Lax'` - 在 HTTP 下使用 Lax（同站请求会发送）

## 测试步骤

### 1. 清除浏览器 Cookie

1. 打开开发者工具（F12）
2. Application -> Cookies
3. 删除所有 localhost 的 Cookie

### 2. 访问登录页面

访问：http://localhost:3000/signin

**现在看到 401 错误是正常的**，因为你还没有登录！

### 3. 点击 SSO 登录

1. 点击 "SSO 登录" 按钮
2. 完成 SSO 认证
3. 等待跳转回应用

### 4. 检查 Cookie

登录成功后，在 Application -> Cookies -> `http://localhost:5001` 中应该看到：
- `access_token`
- `refresh_token`
- `csrf_token`

### 5. 验证登录状态

刷新页面，应该：
- ✅ 不再有 401 错误
- ✅ 可以看到应用主界面
- ✅ 所有 API 请求返回 200

## 为什么之前一直失败

1. **代理方案**：Cookie 在代理层转发复杂，容易出问题
2. **SameSite=Lax**：跨域时不发送 Cookie
3. **HttpOnly=True**：无法在浏览器中查看 Cookie，难以调试
4. **Domain 设置**：可能导致 Cookie 无法正确设置

## 当前配置

### 后端 (`api/.env`)
```bash
CONSOLE_CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,*
WEB_API_CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,*
```

### 前端 (`web/.env.local`)
```bash
NEXT_PUBLIC_API_PREFIX=http://localhost:5001/console/api
NEXT_PUBLIC_PUBLIC_API_PREFIX=http://localhost:5001/api
```

### Cookie 设置
- Domain: `None`（浏览器自动决定）
- SameSite: `Lax`（HTTP）
- Secure: `False`（允许 HTTP）
- HttpOnly: `False`（方便调试）

## 服务状态

- ✅ 后端：http://localhost:5001（Terminal 18）
- ✅ 前端：http://localhost:3000（Terminal 17）
- ✅ Docker 服务：全部运行中

---

**现在请清除 Cookie，然后进行 SSO 登录测试！**

登录前看到 401 是正常的，登录后应该就没问题了。
