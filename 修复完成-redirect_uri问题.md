# 修复完成 - redirect_uri 问题

## 问题原因

云端代码合并后，`web/service/sso-desktop-auth.ts` 中的 `getDesktopCallbackUrl()` 函数被覆盖，返回的是 `/signin/built-in` 而不是 `/oauth-callback`。

这导致 SSO 登录时的 redirect_uri 错误：
- ❌ 错误：`http://localhost:3000/signin/built-in`
- ✅ 正确：`http://localhost:3000/oauth-callback`

## 已修复

修改了 `web/service/sso-desktop-auth.ts`：

```typescript
export const getDesktopCallbackUrl = () => {
  if (typeof window === 'undefined')
    return 'http://localhost:3000/oauth-callback'  // 修改这里

  const { protocol, host } = window.location
  return `${protocol}//${host}/oauth-callback`  // 修改这里
}
```

## 服务状态

- ✅ 后端：http://localhost:5001 (Terminal 3)
- ✅ 前端：http://localhost:3000 (Terminal 5) - 已重启

## 测试步骤

1. **清除浏览器 Cookie**
   - F12 -> Application -> Cookies
   - 删除所有 localhost 的 Cookie

2. **访问登录页面**
   - http://localhost:3000/signin

3. **点击 SSO 登录**
   - 应该跳转到正确的 URL
   - redirect_uri 应该是 `http://localhost:3000/oauth-callback`

4. **完成 SSO 认证**
   - 输入用户名密码
   - 应该成功跳转回 `/oauth-callback`
   - 然后自动跳转到 `/apps`

## 验证 redirect_uri

在点击 SSO 登录后，检查浏览器地址栏的 URL，应该包含：
```
redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Foauth-callback
```

而不是：
```
redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fsignin%2Fbuilt-in
```

---

**现在请清除 Cookie，然后重新测试 SSO 登录！**
