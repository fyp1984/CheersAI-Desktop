# CheersAI 登录说明

## ✅ 管理员账号已创建

### 登录信息

```
邮箱: admin@cheersai.com
密码: admin123
```

## 🚀 如何登录

### 1. 确保服务正在运行

**后端服务** (端口 5001):
```bash
cd e:\CheersAI-Desktop\api
$env:CONSOLE_CORS_ALLOW_ORIGINS="http://localhost:3000"
.venv\Scripts\python.exe -m flask run --host=0.0.0.0 --port=5001 --debug
```

**前端服务** (端口 3000):
```bash
cd e:\CheersAI-Desktop\web
pnpm dev
```

### 2. 访问登录页面

打开浏览器访问: http://localhost:3000

### 3. 输入登录信息

- 邮箱: `admin@cheersai.com`
- 密码: `admin123`

### 4. 点击登录

登录成功后，你将进入 CheersAI 控制台。

## 🔧 问题排查

### 问题 1: 401 未授权错误

**原因**: 未登录或 session 过期

**解决方案**:
1. 清除浏览器缓存和 Cookie
2. 重新访问登录页面
3. 使用上面的管理员账号登录

### 问题 2: CORS 错误

**原因**: 后端未配置 CORS

**解决方案**:
确保启动后端时设置了环境变量：
```bash
$env:CONSOLE_CORS_ALLOW_ORIGINS="http://localhost:3000"
```

或在 `api/.env` 文件中添加：
```bash
CONSOLE_CORS_ALLOW_ORIGINS=http://localhost:3000
```

### 问题 3: 无法连接到后端

**原因**: 后端服务未启动

**解决方案**:
检查后端服务是否在运行：
```bash
curl http://localhost:5001/console/api/ping
```

## 📝 创建更多账号

如果需要创建更多测试账号，运行：

```bash
cd e:\CheersAI-Desktop\api
.venv\Scripts\python.exe create_admin.py
```

或修改 `create_admin.py` 脚本创建不同的账号。

## 🎯 下一步

登录成功后，你可以：

1. ✅ 创建应用
2. ✅ 配置模型
3. ✅ 测试聊天功能
4. ✅ 管理数据集
5. ✅ 使用 Gitea 文件功能

## 🔒 安全提示

⚠️ **重要**: 这是测试账号，密码非常简单。在生产环境中，请：

1. 使用强密码
2. 定期更换密码
3. 启用双因素认证（如果支持）
4. 不要在公网暴露测试账号

## 📚 相关文档

- [CORS 修复指南](CORS_FIX.md)
- [Gitea 文件获取集成](README_GITEA_FILE_RETRIEVAL.md)
- [完整文档](docs/)

---

现在你可以使用 `admin@cheersai.com` / `admin123` 登录 CheersAI 了！🎉
