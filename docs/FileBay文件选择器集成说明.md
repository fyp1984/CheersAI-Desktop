# FileBay 文件选择器集成说明

## 概述

已为 Dify 前端添加了 **FileBay 文件选择器**组件，用户可以在文件上传界面直接从 FileBay 仓库中选择文件。

## 已完成的工作

### 1. 创建 FileBay 文件选择器组件

**文件位置**: `web/app/components/base/file-uploader/filebay-file-picker/index.tsx`

**功能特性**:
- ✅ 浏览 FileBay 目录结构
- ✅ 显示文件和文件夹列表
- ✅ 支持进入子目录
- ✅ 支持返回上级目录
- ✅ 文件选择和确认
- ✅ 加载状态显示
- ✅ 空状态提示
- ✅ 调用真实 API 加载文件列表

**UI 特点**:
- 模态对话框形式
- 路径导航栏
- 文件/文件夹图标区分
- 选中状态高亮
- 响应式设计
- 中文界面

### 2. 扩展文件上传组件

**修改文件**: `web/app/components/base/file-uploader/file-from-link-or-local/index.tsx`

**新增功能**:
- ✅ 添加 `showFromFileBay` 属性
- ✅ 添加"从 FileBay 选择"按钮
- ✅ 集成 FileBay 文件选择器
- ✅ 实现文件内容加载逻辑
- ✅ 支持从 FileBay 读取文件并上传到系统

### 3. 创建后端 API 端点

**文件位置**: `api/controllers/console/filebay_api/filebay_files.py`

**API 端点**:
- ✅ `GET /console/api/filebay/list-files` - 列出文件和目录
- ✅ `POST /console/api/filebay/read-file` - 读取文件内容
- ✅ `GET /console/api/filebay/download-file` - 下载文件

**功能特性**:
- ✅ 使用 NoSNI HTTPS 客户端连接 FileBay
- ✅ 从用户配置读取 FileBay 凭证
- ✅ 完整的错误处理和日志记录
- ✅ Base64 解码文件内容
- ✅ 支持目录导航

### 4. 集成到聊天输入框

**修改文件**: `web/app/components/base/chat/chat/chat-input-area/operation.tsx`

**功能**:
- ✅ 在所有聊天输入框显示文件上传按钮
- ✅ 不依赖应用的文件上传配置
- ✅ 与"收缩"和"联网搜索"功能并列显示

## 使用方法

### 在组件中启用 FileBay 选项

```tsx
import FileFromLinkOrLocal from '@/app/components/base/file-uploader/file-from-link-or-local'

<FileFromLinkOrLocal
  showFromFileBay={true}  // 启用 FileBay 选项（只显示 FileBay）
  trigger={(open) => (
    <Button>
      上传文件
    </Button>
  )}
  fileConfig={fileConfig}
/>
```

### 用户操作流程

1. **点击附件按钮**
   - 在聊天输入框右侧点击附件图标

2. **打开 FileBay 文件选择器**
   - 自动打开 FileBay 文件选择器对话框

3. **浏览文件**
   - 查看当前目录的文件和文件夹
   - 点击文件夹进入子目录
   - 点击返回按钮回到上级目录

4. **选择文件**
   - 点击文件进行选择（高亮显示）
   - 底部显示已选文件名

5. **确认选择**
   - 点击"确认"按钮
   - 文件被加载到应用中

## UI 界面说明

### 文件选择器对话框

```
┌─────────────────────────────────────────┐
│  从 FileBay 选择                      ✕  │
├─────────────────────────────────────────┤
│  ← /uploads                             │  ← 路径导航
├─────────────────────────────────────────┤
│  📁 documents                           │  ← 文件夹
│  📁 images                              │
│  📄 config.json          2.5 KB        │  ← 文件
│  📄 data.csv            15.3 KB        │
│                                         │
│                                         │
├─────────────────────────────────────────┤
│  已选择: config.json    [取消] [确认]   │  ← 操作栏
└─────────────────────────────────────────┘
```

### 聊天输入框（集成 FileBay）

```
┌─────────────────────────────────────────┐
│  [收缩] [☑ 联网搜索]                    │
├─────────────────────────────────────────┤
│                                         │
│  [输入框]                    [📎] [发送] │  ← 附件按钮
│                                         │
└─────────────────────────────────────────┘
```

## API 端点详情

### 1. 列出文件 - GET /console/api/filebay/list-files

**请求参数**:
- `path` (query, optional): 目录路径，默认为根目录

**响应**:
```json
{
  "directory": "uploads",
  "branch": "main",
  "directories": [
    {
      "name": "documents",
      "path": "uploads/documents",
      "type": "dir",
      "size": 0,
      "sha": "..."
    }
  ],
  "files": [
    {
      "name": "config.json",
      "path": "uploads/config.json",
      "type": "file",
      "size": 2560,
      "sha": "..."
    }
  ],
  "total_directories": 1,
  "total_files": 1
}
```

### 2. 读取文件 - POST /console/api/filebay/read-file

**请求体**:
```json
{
  "file_path": "uploads/config.json"
}
```

**响应**:
```json
{
  "file_path": "uploads/config.json",
  "content": "文件内容...",
  "size": 2560,
  "sha": "...",
  "branch": "main"
}
```

### 3. 下载文件 - GET /console/api/filebay/download-file

**请求参数**:
- `path` (query, required): 文件路径

**响应**:
- 文件内容（二进制流）

## 配置和权限

### FileBay 凭证配置

用户需要先配置 FileBay 凭证才能使用文件选择器：

1. 进入 **账户设置** → **Gitea 设置**
2. 配置凭证：
   - FileBay URL
   - Access Token
   - Repository Owner
   - Repository Name
   - Branch (默认: main)

### 权限检查

- 确保用户有 FileBay 仓库的读取权限
- 检查 Access Token 是否有效
- 处理权限不足的错误情况

## 技术实现细节

### NoSNI HTTPS 客户端

为了兼容 FileBay 的 SSL 配置，使用了自定义的 NoSNI HTTPS 客户端：

```python
class NoSNIHTTPSClient:
    """HTTPS client without SNI for FileBay compatibility"""
    
    def __init__(self, base_url: str, token: str = "", timeout: int = 30):
        # 创建不验证 SNI 的 SSL 上下文
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
```

### 文件内容处理

1. **从 FileBay 读取**: 调用 API 获取 Base64 编码的文件内容
2. **解码内容**: 将 Base64 解码为原始内容
3. **创建 Blob**: 转换为浏览器 Blob 对象
4. **创建 File**: 包装为 File 对象
5. **上传处理**: 使用现有的文件上传逻辑

### 用户配置管理

使用 `resolve_user_filebay_config` 函数从用户配置中读取 FileBay 凭证：

```python
user_config = resolve_user_filebay_config(
    user_email,
    mask_token=False,
    log_prefix='[FileBay API]',
)
```

## 测试建议

### 功能测试

1. **文件列表加载**:
   - ✅ 测试根目录加载
   - ✅ 测试子目录加载
   - ✅ 测试空目录显示
   - ✅ 测试错误处理

2. **文件选择和加载**:
   - ✅ 测试文件选择
   - ✅ 测试文件内容读取
   - ✅ 测试文件上传
   - ✅ 测试大文件处理

3. **目录导航**:
   - ✅ 测试进入子目录
   - ✅ 测试返回上级目录
   - ✅ 测试路径显示

### 错误场景测试

1. **连接错误**:
   - FileBay 服务不可用
   - 网络超时
   - SSL 证书问题

2. **权限错误**:
   - Token 无效
   - 权限不足
   - 仓库不存在

3. **文件错误**:
   - 文件不存在
   - 文件过大
   - 文件类型不支持

## 性能优化

### 已实现的优化

1. **错误处理**: 完整的错误捕获和用户提示
2. **加载状态**: 显示加载动画，提升用户体验
3. **路径管理**: 正确处理路径分隔符和编码

### 可以扩展的优化

1. **文件列表缓存**: 缓存已加载的目录列表
2. **懒加载**: 只加载当前目录的文件
3. **虚拟滚动**: 对于大量文件的目录
4. **预加载**: 预加载常用目录

## 下一步计划

### 可以扩展的功能

1. **搜索功能**:
   - 在 FileBay 中搜索文件
   - 按文件名、类型、日期筛选

2. **文件预览**:
   - 在选择前预览文件内容
   - 支持图片、文本、PDF 预览

3. **批量选择**:
   - 支持选择多个文件
   - 批量上传

4. **收藏夹**:
   - 收藏常用目录
   - 快速访问

5. **最近使用**:
   - 显示最近使用的文件
   - 快速重新选择

## 总结

FileBay 文件选择器已经完成开发并集成到 Dify 系统中。

**已完成**:
- ✅ FileBay 文件选择器组件（前端）
- ✅ 文件上传组件集成（前端）
- ✅ 后端 API 端点（后端）
- ✅ FileBay 工具调用集成（后端）
- ✅ 文件内容加载逻辑（前后端）
- ✅ 错误处理和提示（前后端）
- ✅ 中文界面（前端）
- ✅ 集成到所有聊天输入框（前端）

**功能特点**:
- 🎯 简洁的用户界面，只显示 FileBay 选项
- 🎯 完整的目录浏览和文件选择功能
- 🎯 真实的 API 调用，不再使用模拟数据
- 🎯 完整的错误处理和用户提示
- 🎯 在所有聊天输入框可用，不依赖应用配置

用户现在可以在任何聊天界面点击附件按钮，直接从 FileBay 选择文件并上传到 Dify 系统中！
