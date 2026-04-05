# 仅 SSO 登录模式

**修改时间**: 2026-04-03  
**状态**: ✅ 已完成

---

## 修改概述

根据用户需求，已将登录页面修改为仅支持 SSO 登录，隐藏了邮箱密码登录表单。

---

## 修改内容

### 1. 登录页面修改

**文件**: `web/app/signin/normal-form.tsx`

**主要变更**:

1. **移除邮箱密码登录表单**
   - 删除了 `MailAndPasswordAuth` 组件的引用和使用
   - 移除了邮箱密码登录相关的条件判断

2. **简化登录界面**
   - 只显示 SSO 登录按钮
   - 移除了"或"分隔符（因为只有一种登录方式）
   - 更新提示文字为"请使用 SSO 登录"

3. **优化错误提示**
   - 当 SSO 未配置时，显示友好的错误提示
   - 移除了不再需要的 `allMethodsAreDisabled` 状态

---

## 登录界面变化

### 修改前
```
欢迎回来
请输入您的邮箱和密码

[邮箱输入框]
[密码输入框]
[登录按钮]

或

[使用 SSO 登录按钮]
```

### 修改后
```
欢迎回来
请使用 SSO 登录

[使用 SSO 登录按钮]
```

---

## 功能说明

### SSO 登录流程

1. 用户访问登录页面 http://localhost:3000/signin
2. 页面只显示"使用 SSO 登录"按钮
3. 点击按钮后跳转到 Casdoor SSO 登录页面
4. 用户在 Casdoor 完成认证
5. 回调到系统，自动创建/更新用户并分配角色
6. 跳转到应用主页

### 错误处理

如果 SSO 未配置（`isDesktopSSOEnabled()` 返回 false），页面会显示：

```
SSO 登录未配置
请联系管理员配置 SSO 登录
```

---

## 配置要求

### 前端配置

确保 `web/.env.local` 中配置了 SSO 相关环境变量：

```env
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=http://localhost:8000
NEXT_PUBLIC_DESKTOP_SSO_CLIENT_ID=c98f7150fe9c044bf217
NEXT_PUBLIC_DESKTOP_SSO_REDIRECT_URI=http://localhost:3000/oauth-callback
```

### 后端配置

确保后端 Desktop SSO 登录端点正常工作：
- `POST /console/api/auth/desktop-sso/login`

---

## 测试步骤

1. **清除浏览器缓存和 Cookie**
2. **访问登录页面**: http://localhost:3000/signin
3. **验证界面**:
   - 应该只看到"使用 SSO 登录"按钮
   - 没有邮箱和密码输入框
4. **点击 SSO 登录按钮**
5. **完成 Casdoor 认证**
6. **验证登录成功**:
   - 自动跳转到 /apps 页面
   - 侧边栏显示正确的菜单数量（根据角色）

---

## 恢复邮箱密码登录

如果需要恢复邮箱密码登录功能，可以：

1. **恢复导入**:
   ```typescript
   import MailAndPasswordAuth from './components/mail-and-password-auth'
   ```

2. **恢复登录表单**:
   ```typescript
   {systemFeatures.enable_email_password_login && (
     <MailAndPasswordAuth 
       isInvite={isInviteLink} 
       isEmailSetup={systemFeatures.is_email_setup} 
       allowRegistration={systemFeatures.is_allow_register} 
     />
   )}
   
   {isDesktopSSOEnabled() && systemFeatures.enable_email_password_login && (
     <div className="relative">
       <div className="absolute inset-0 flex items-center">
         <div className="w-full border-t border-gray-300"></div>
       </div>
       <div className="relative flex justify-center text-sm">
         <span className="bg-white px-2 text-gray-500">或</span>
       </div>
     </div>
   )}
   ```

3. **恢复提示文字**:
   ```typescript
   <p className="text-gray-600">请输入您的邮箱和密码</p>
   ```

---

## 相关文档

- [SSO 角色权限设计方案](./角色权限设计方案.md)
- [快速实现说明](./快速实现说明.md)
- [本地 SSO 配置和测试](./本地SSO配置和测试.md)
- [系统当前状态](./系统当前状态.md)

---

**文档版本**: v1.0  
**维护者**: 开发团队
