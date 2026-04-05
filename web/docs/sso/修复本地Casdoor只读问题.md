# 修复本地 Casdoor 只读问题

## 问题

本地 Casdoor 运行在演示模式（`isDemoMode=true`），无法创建或修改应用和用户。

## 🎯 解决方案

### 方案 1：使用云端 SSO（推荐）

最简单的方法是继续使用云端 SSO，因为它已经配置好了。

修改 `web/.env.local`：

```env
# 改回云端 SSO
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=https://uat-sso.cheersai.cloud
```

然后重启前端服务。

**优点**：
- 无需配置
- 已经有应用配置
- 可以直接创建用户测试

---

### 方案 2：重启本地 Casdoor（关闭演示模式）

如果一定要用本地 SSO：

#### 步骤 1：停止当前容器

```bash
docker stop cheersai-sso-casdoor-1
docker rm cheersai-sso-casdoor-1
```

#### 步骤 2：启动新的 Casdoor

```bash
# 使用新的配置启动
docker-compose -f docker-compose.casdoor.yaml up -d
```

#### 步骤 3：初始化 Casdoor

1. 访问 http://localhost:18000
2. 首次访问会自动初始化
3. 使用默认账号登录：
   - 用户名：`admin`
   - 密码：`123`

#### 步骤 4：创建应用

1. 登录后台
2. 点击 "Applications"
3. 点击 "Add" 创建应用
4. 填写配置（见下方）

---

## 📝 应用配置

如果使用本地 Casdoor，需要创建应用：

**基本信息**：
- Name: `CheersAI-Desktop`
- Organization: `built-in`

**OAuth 配置**：
- Client ID: `c98f7150fe9c044bf217`
- Client secret: `13b46d1129c1e20cb951616a04c76a7757d01296`
- Redirect URIs: `http://localhost:3000/oauth-callback`
- Grant types: `authorization_code`
- Token format: `JWT`

**Scopes**：
- openid
- profile
- email

---

## 🎯 推荐方案

**建议使用云端 SSO**，因为：

1. ✅ 已经配置好应用
2. ✅ 无需本地数据库
3. ✅ 可以直接创建用户
4. ✅ 配置简单

只需要：
1. 改回云端 SSO URL
2. 在云端创建测试用户
3. 测试角色权限

---

## 🚀 快速切换回云端 SSO

修改 `web/.env.local`：

```env
NEXT_PUBLIC_DESKTOP_SSO_LOGIN_URL=https://uat-sso.cheersai.cloud
```

重启前端：
```bash
# 停止前端
Ctrl+C

# 重新启动
pnpm dev
```

然后就可以在云端 Casdoor 创建用户测试了！

---

**推荐**: 使用云端 SSO  
**原因**: 配置简单，已经可用  
**状态**: 可以立即测试
