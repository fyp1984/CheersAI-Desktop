# API 路由修复说明

## 🔧 问题

Token 配额 API 路由没有被注册，导致前端无法访问配额信息。

## ✅ 已修复

### 修改文件
`api/controllers/console/__init__.py`

### 修改内容

1. **添加导入**:
```python
from . import (
    # ... 其他导入
    token_billing,
    token_quota,  # 新增
    version,
)
```

2. **添加到导出列表**:
```python
__all__ = [
    # ... 其他导出
    "token_billing",
    "token_quota",  # 新增
    "tool_providers",
    # ...
]
```

### 重启服务
- ✅ 已重启 Flask API 服务
- ✅ API 路由已注册
- ✅ 端点可访问（需要认证）

## 📍 API 端点

现在以下端点可用：

```
POST   /console/api/token-quota/check
POST   /console/api/token-quota/usage/record
GET    /console/api/token-quota/usage/current
GET    /console/api/token-quota/usage/statistics
GET    /console/api/token-quota/configs
POST   /console/api/token-quota/configs
GET    /console/api/token-quota/configs/{id}
PUT    /console/api/token-quota/configs/{id}
DELETE /console/api/token-quota/configs/{id}
POST   /console/api/token-quota/reset
```

## 🎯 前端显示

现在刷新 Token 计费页面，配额状态卡片应该会显示在页面顶部。

### 访问步骤
1. 打开 http://localhost:3000
2. 登录系统
3. 点击右上角头像 → 设置
4. 点击"Token 计费"
5. 在页面顶部应该能看到配额状态卡片

### 显示内容
- ✅ 配额状态（充足/已用完）
- 📊 剩余额度
- ⏰ 重置时间倒计时
- 📈 使用进度条
- 🔄 刷新按钮

## ✅ 完成

API 路由已修复，前端应该可以正常显示配额信息了！

**请刷新浏览器页面查看效果。** 🎉
