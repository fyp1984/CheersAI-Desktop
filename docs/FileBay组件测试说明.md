# FileBay 组件测试说明

## 当前运行状态

### 本地服务
- ✅ 前端: http://localhost:3000 (Terminal 10)
- ✅ API: http://localhost:9000 (Terminal 7)
- ✅ Celery Worker (Terminal 3)
- ✅ Celery Beat (Terminal 4)

### Docker 服务
- ✅ PostgreSQL (端口 5432)
- ✅ Redis (端口 6700)
- ✅ Weaviate (端口 8081)
- ✅ Plugin Daemon (端口 5012-5013)

## 为什么看不到附件图标？

### 可能的原因

1. **应用配置问题**
   - 应用可能没有启用文件上传功能
   - 需要在应用配置中启用文件上传

2. **访问错误的URL**
   - 确保访问 http://localhost:3000
   - 不是 Docker 容器中的服务

3. **浏览器缓存**
   - 需要清除缓存或强制刷新

## 如何启用文件上传功能

### 方法 1: 在应用编辑页面启用

1. 访问 http://localhost:3000
2. 进入你的 File Translation 应用
3. 点击右上角的"编辑"按钮
4. 在左侧配置面板中找到"功能"或"Features"
5. 启用"文件上传"功能
6. 配置允许的文件类型和大小
7. 保存并发布

### 方法 2: 检查应用配置

应用的文件上传配置在 `fileConfig` 中：

```typescript
{
  enabled: true,  // 必须为 true
  allowed_file_types: ['pdf', 'doc', 'docx', 'txt'],
  allowed_file_upload_methods: [
    TransferMethod.local_file,  // 从本地上传
    TransferMethod.remote_url,  // 从链接
  ],
  number_limits: 5,  // 最多上传文件数
  filesize_limit: 15  // 文件大小限制 (MB)
}
```

## 测试步骤

### 1. 确认访问正确的URL

打开浏览器，访问：
```
http://localhost:3000
```

### 2. 登录系统

使用管理员账户登录：
- 邮箱: 1@qq.com
- 密码: (你设置的密码)

### 3. 进入应用

1. 点击左侧菜单的"探索"
2. 找到你的 File Translation 应用
3. 点击进入

### 4. 检查聊天输入区域

在聊天输入框的左侧或右侧，应该能看到：
- 📎 附件图标 (如果启用了文件上传)
- 🎤 语音输入图标 (如果启用了语音)

### 5. 点击附件图标

点击后应该弹出菜单，显示：
- 粘贴文件链接
- **从 FileBay 选择** ⭐ (新增)
- 从本地上传

## 如果还是看不到

### 检查应用是否启用文件上传

1. 进入应用编辑页面
2. 查看"功能"配置
3. 确保"文件上传"已启用

### 检查浏览器控制台

1. 按 F12 打开开发者工具
2. 查看 Console 标签
3. 看是否有错误信息
4. 截图发给我

### 检查网络请求

1. 在开发者工具中切换到 Network 标签
2. 刷新页面
3. 查看是否有失败的请求
4. 特别注意 API 请求是否指向 http://localhost:9000

## 创建测试应用

如果现有应用有问题，可以创建一个新的测试应用：

1. 访问 http://localhost:3000
2. 点击"工作室" → "创建应用"
3. 选择"对话型应用"
4. 在"功能"中启用"文件上传"
5. 配置文件上传选项：
   - 允许的文件类型: PDF, DOC, TXT
   - 上传方式: 本地文件、远程链接
   - 最大文件数: 5
   - 文件大小限制: 15MB
6. 保存并发布
7. 测试文件上传功能

## 验证 FileBay 组件

### 检查组件文件

确认以下文件存在：

1. `web/app/components/base/file-uploader/filebay-file-picker/index.tsx`
2. `web/app/components/base/file-uploader/file-from-link-or-local/index.tsx` (已修改)
3. `web/app/components/base/file-uploader/file-uploader-in-chat-input/index.tsx` (已修改)

### 检查前端编译

查看 Terminal 10 的输出，确认没有编译错误。

## 下一步

请提供以下信息：

1. **你访问的URL是什么？**
2. **能否看到聊天输入框？**
3. **聊天输入框附近有哪些图标？**
4. **浏览器控制台有什么错误？** (按F12查看)
5. **截图当前的界面**

这样我可以更准确地帮你解决问题。
