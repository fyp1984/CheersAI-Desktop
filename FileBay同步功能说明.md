# FileBay 同步功能说明

## 功能概述

在聊天界面的 AI 回复消息中，现在提供了两个按钮：
1. **下载按钮** - 将 AI 回复保存为 Markdown 文件到本地
2. **同步到 FileBay 按钮** - 直接将 AI 回复同步到 FileBay 仓库

## 使用方法

### 1. 同步到 FileBay

1. 在聊天界面中，当 AI 回复完成后，将鼠标悬停在回复消息上
2. 在消息右侧会出现操作按钮栏
3. 点击 **数据库图标**（RiDatabase2Line）按钮
4. 系统会自动将回复内容上传到 FileBay 仓库的 `ai-replies/` 目录下
5. 文件名格式：`reply-{消息ID前8位}.md`

### 2. 下载到本地

1. 点击 **下载图标**（RiDownloadLine）按钮
2. 如果配置了沙箱路径，文件会保存到指定目录
3. 否则会触发浏览器下载

## 技术实现

### 前端实现

**文件位置**: `web/app/components/base/chat/chat/answer/operation.tsx`

- 添加了 `RiDatabase2Line` 图标导入
- 在下载按钮后添加了同步按钮
- 使用 Tooltip 显示"同步到 FileBay"提示
- 点击时调用 `/console/api/filebay/sync-reply` API

**关键代码**:
```typescript
import Cookies from 'js-cookie'
import { CSRF_COOKIE_NAME, CSRF_HEADER_NAME } from '@/config'

<Tooltip popupContent="同步到 FileBay">
  <ActionButton onClick={async () => {
    const fileName = `reply-${id.slice(0, 8)}.md`
    
    // 获取 CSRF token（使用 js-cookie 库）
    const csrfToken = Cookies.get(CSRF_COOKIE_NAME())
    
    if (!csrfToken) {
      Toast.notify({ type: 'error', message: '无法获取认证信息' })
      return
    }

    // 准备请求头
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    headers[CSRF_HEADER_NAME] = csrfToken

    // 调用同步 API
    const response = await fetch(`${API_PREFIX}/console/api/filebay/sync-reply`, {
      method: 'POST',
      headers,
      credentials: 'include',
      body: JSON.stringify({
        file_name: fileName,
        content,
      }),
    })
  }}>
    <RiDatabase2Line className="h-4 w-4" />
  </ActionButton>
</Tooltip>
```

### 后端实现

**文件位置**: `api/controllers/console/filebay_api/filebay_files.py`

新增端点：`/console/api/filebay/sync-reply`

**功能**:
1. 接收文件名和内容
2. 获取用户的 FileBay 配置（URL、Token、Owner、Repo、Branch）
3. 使用 NoSNI HTTPS 客户端连接 FileBay
4. 检查文件是否已存在
5. 如果存在，获取 SHA 并更新文件
6. 如果不存在，创建新文件
7. 文件保存到 `ai-replies/` 目录

**关键代码**:
```python
@console_ns.route('/filebay/sync-reply')
class FileBaySyncReplyApi(Resource):
    @setup_required
    @login_required
    def post(self):
        # 获取用户配置
        user_config = _get_user_filebay_config()
        
        # 创建 NoSNI 客户端
        client = NoSNIHTTPSClient(filebay_url, filebay_token)
        
        # 检查文件是否存在
        remote_path = f"ai-replies/{file_name}"
        status_code, response = client.get(api_path + params)
        
        # 编码内容为 base64
        content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # 准备请求体
        body = {
            "branch": filebay_branch,
            "content": content_base64,
            "message": f"Update AI reply: {file_name}"
        }
        
        # 如果文件存在，包含 SHA 用于更新
        if status_code == 200:
            body["sha"] = response.get('sha', '')
        
        # 上传/更新文件
        status_code, response = client._make_request("PUT", api_path, body)
```

## 配置要求

### FileBay 配置

用户需要在账户设置中配置 FileBay：
- FileBay URL
- Access Token
- Owner（用户名）
- Repository（仓库名）
- Branch（分支名，默认 main）

配置路径：账户设置 → FileBay 设置

### 权限要求

- 用户必须登录
- 用户必须有 FileBay 的写入权限
- Token 必须有仓库的 `repo` 权限

### CSRF 认证

系统使用 CSRF token 进行请求认证：
- 使用 `js-cookie` 库读取 cookie 中的 CSRF token
- 使用配置常量 `CSRF_COOKIE_NAME()` 和 `CSRF_HEADER_NAME` 
- 请求时必须包含 `credentials: 'include'` 以发送 cookie
- 这与项目中其他 console API 调用方式保持一致（参考 FileBay 文件选择器实现）

## 文件组织

同步的文件会保存在 FileBay 仓库的以下位置：

```
your-repo/
└── ai-replies/
    ├── reply-abc12345.md
    ├── reply-def67890.md
    └── ...
```

## 错误处理

### 常见错误

1. **"FileBay 未配置"**
   - 原因：用户未配置 FileBay 或配置不完整
   - 解决：前往账户设置配置 FileBay

2. **"无法获取认证信息"**
   - 原因：CSRF token 获取失败
   - 解决：刷新页面重试

3. **"同步失败，请检查 FileBay 配置"**
   - 原因：网络问题或 FileBay 服务不可用
   - 解决：检查网络连接和 FileBay 服务状态

## 与下载功能的区别

| 功能 | 下载 | 同步到 FileBay |
|------|------|----------------|
| 存储位置 | 本地文件系统 | FileBay 远程仓库 |
| 版本控制 | 无 | 有（Git） |
| 多设备访问 | 否 | 是 |
| 需要配置 | 可选（沙箱路径） | 必需（FileBay 配置） |
| 文件管理 | 手动 | 自动（在 ai-replies 目录） |

## 参考实现

本功能参考了 `e:\CheersAI脱敏\cheersai-desktop` 项目中的文件上传实现：
- `src/components/file/FileManager.tsx` - 批量同步功能
- `src/services/gitea.ts` - Gitea API 封装

## 未来改进

1. 支持自定义保存目录
2. 支持批量同步多条回复
3. 添加同步历史记录
4. 支持同步到多个 FileBay 仓库
5. 添加同步进度提示
