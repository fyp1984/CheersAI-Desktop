# FileBay API 测试说明

## 当前状态

✅ 后端 API 已创建并注册
✅ 前端组件已创建
✅ 认证已添加（credentials: 'include'）
✅ 配置键名已修复（gitea_* 而不是 filebay_*）
✅ 文件处理方式已改为使用下载 URL

## 测试步骤

1. **确认已登录**
   - 打开浏览器开发者工具
   - 检查 Application > Cookies 中是否有登录 cookie

2. **打开 FileBay 文件选择器**
   - 进入任何聊天界面
   - 点击附件按钮（📎）
   - 应该会打开 FileBay 文件选择器

3. **检查网络请求**
   - 打开 Network 标签
   - 查看 `/console/api/filebay/list-files` 请求
   - 检查请求头中是否包含 Cookie
   - 查看响应状态码和内容

4. **检查后端日志**
   - 查看 API 服务器日志
   - 应该能看到 `[FileBay API] ===== LIST FILES REQUEST =====`
   - 查看详细的错误信息

## 可能的问题

### 问题 1: 401 未授权
**原因**: Cookie 未发送或已过期
**解决**: 
- 刷新页面重新登录
- 检查浏览器是否阻止了第三方 cookie

### 问题 2: 500 内部错误
**原因**: 后端代码错误或配置问题
**解决**:
- 检查后端日志中的详细错误信息
- 确认 FileBay 配置已正确设置

### 问题 3: 404 未找到
**原因**: 路由未正确注册
**解决**:
- 重启 API 服务器
- 检查路由注册代码

## 调试命令

### 检查路由注册
```bash
cd api
uv run python -c "from flask import Flask; from controllers.console import api, bp; app = Flask(__name__); app.register_blueprint(bp); [print(f'{rule.rule}') for rule in app.url_map.iter_rules() if 'filebay' in rule.rule.lower()]"
```

### 测试 API 端点（需要登录）
在浏览器控制台中运行：
```javascript
fetch('/console/api/filebay/list-files?path=', {
  method: 'GET',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
  },
})
.then(r => r.json())
.then(d => console.log(d))
.catch(e => console.error(e))
```

## 当前配置

- API 端点: `http://127.0.0.1:9000/console/api/filebay/list-files`
- 前端端口: `http://localhost:3000`
- 认证方式: Cookie-based (credentials: 'include')

## 下一步

如果还有问题，请：
1. 在浏览器中打开 FileBay 文件选择器
2. 复制 Network 标签中的请求详情
3. 复制后端日志中的错误信息
4. 提供这些信息以便进一步调试
