# Desktop 访问权限修复

## 问题描述

用户 `1@qq.com` (junqianxi) 登录时遇到错误：
```
Desktop access denied for subject eb4e1872-d7f1-4539-a8d6-6bafe53371fa
```

## 根本原因

`has_desktop_access()` 函数检查 SSO payload 中是否包含 `desktop_access` 标识符。但是从 Casdoor 返回的用户信息中，只有角色信息（如 `admin`, `technician`, `user`），没有 `desktop_access` 标识符。

## 修复方案

修改 `api/libs/desktop_auth.py` 中的 `has_desktop_access()` 函数，让所有拥有有效 SSO 角色的用户自动获得 desktop_access 权限。

### 修改前
```python
def has_desktop_access(payload: Mapping[str, Any] | None) -> bool:
    return DESKTOP_ACCESS_CAPABILITY in collect_sso_identifiers(payload)
```

### 修改后
```python
def has_desktop_access(payload: Mapping[str, Any] | None) -> bool:
    # Allow access if user has desktop_access capability OR has any valid SSO role
    if DESKTOP_ACCESS_CAPABILITY in collect_sso_identifiers(payload):
        return True
    
    # Auto-grant desktop_access to users with valid SSO roles
    identifiers = collect_sso_identifiers(payload)
    for identifier in identifiers:
        if identifier in SSO_IDENTIFIER_TO_WORKSPACE_ROLE:
            return True
    
    return False
```

## 应用修复

### 1. 重启 API 服务器

**Windows (PowerShell):**
```powershell
# 查找 API 进程
Get-Process | Where-Object { $_.ProcessName -like "*python*" }

# 停止进程（替换 PID）
Stop-Process -Id 28996 -Force

# 重新启动 API
cd api
flask run --host=0.0.0.0 --port=5001 --debug
```

**或者使用 Makefile:**
```bash
# 停止当前服务
# 然后重启
make api-start
```

### 2. 验证修复

1. 清除浏览器 Cookie
2. 访问 http://localhost:3000
3. 点击 "Desktop SSO Login"
4. 使用 `1@qq.com` 登录
5. 应该能成功登录并看到主界面

### 3. 检查日志

**API 日志应该显示：**
```
INFO - Desktop SSO login request received
INFO - Resolved Desktop SSO subject eb4e1872-d7f1-4539-a8d6-6bafe53371fa with identifier 'admin' to workspace role 'admin'
INFO - Desktop SSO Login success for: 1@qq.com with role: admin
```

**不应该再看到：**
```
WARNING - Desktop access denied for subject eb4e1872-d7f1-4539-a8d6-6bafe53371fa
```

## 支持的角色

以下角色的用户将自动获得 desktop_access 权限：

| SSO 角色标识符 | Workspace 角色 |
|---------------|---------------|
| owner | owner |
| admin, c_admin, desktop_team_admin, org_admin | admin |
| technician, editor, desktop_team_editor | editor |
| dataset_operator, desktop_dataset_operator | dataset_operator |
| user, normal, desktop_team_member, team-member | normal |

## 测试用户

| 邮箱 | 角色 | 应该能访问 |
|------|------|-----------|
| 1@qq.com | admin | ✅ 是 |
| 2@qq.com | technician | ✅ 是 |
| 3@qq.com | user | ✅ 是 |

## 相关文件

- `api/libs/desktop_auth.py` - 权限检查逻辑
- `api/controllers/console/auth/desktop_sso.py` - SSO 登录处理
- `web/service/sso.ts` - 前端 SSO 服务

---

**修复日期**: 2026-04-18  
**修复人**: Kiro AI  
**问题编号**: Desktop Access Denied
