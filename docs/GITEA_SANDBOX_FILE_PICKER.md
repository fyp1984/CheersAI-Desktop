# Gitea 沙箱文件选择器使用指南

## 概述

沙箱文件选择器现已集成 Gitea，可以直接从 Gitea 仓库中选择文件，而不是从本地文件系统。

## 功能特性

- ✅ 从 Gitea 仓库浏览文件
- ✅ 支持文件类型过滤
- ✅ 支持单选/多选文件
- ✅ 实时显示文件大小
- ✅ 自动下载选中的文件

## 使用方法

### 1. 配置 Gitea

确保在 `api/.env` 中配置了 Gitea 连接信息：

```bash
GITEA_URL=http://localhost:3000
GITEA_TOKEN=your_token_here
GITEA_OWNER=cheersai
GITEA_REPO=file-storage
```

### 2. 在 Gitea 中准备文件

在你的 Gitea 仓库中上传文件，例如：

```
file-storage/
├── documents/
│   ├── report.pdf
│   ├── data.csv
│   └── notes.md
└── images/
    ├── chart.png
    └── diagram.jpg
```

### 3. 使用文件选择器

在应用中点击"选择文件"按钮，会弹出 Gitea 文件选择对话框：

1. **浏览文件**: 查看 Gitea 仓库中的文件列表
2. **选择文件**: 点击文件进行选择（支持多选）
3. **确认选择**: 点击"确认选择"按钮下载文件

### 4. 文件路径配置

可以通过设置 `sandboxPath` 来指定 Gitea 仓库中的子目录：

```typescript
// 例如只浏览 documents 目录
localStorage.setItem('sandbox_path', 'documents')
```

## 界面说明

### 对话框组件

```
┌─────────────────────────────────────┐
│ 🛡️ Gitea 文件选择                   │
├─────────────────────────────────────┤
│ 📁 Gitea: documents          🔄     │
├─────────────────────────────────────┤
│                                     │
│ 📄 report.pdf          1.2 MB   ✓  │
│ 📄 data.csv            800 B       │
│ 📄 notes.md            3.4 KB      │
│                                     │
├─────────────────────────────────────┤
│ 已选择 1 个文件    [取消] [确认选择] │
└─────────────────────────────────────┘
```

### 功能按钮

- **🔄 刷新**: 重新加载文件列表
- **取消**: 关闭对话框
- **确认选择**: 下载并使用选中的文件

## 代码示例

### 基本使用

```typescript
import { SandboxFilePicker } from '@/app/components/base/sandbox-file-picker'

function MyComponent() {
  const [open, setOpen] = useState(false)

  const handleSelect = (files: File[]) => {
    console.log('Selected files:', files)
    // 处理选中的文件
  }

  return (
    <>
      <button onClick={() => setOpen(true)}>
        选择文件
      </button>
      
      <SandboxFilePicker
        open={open}
        onClose={() => setOpen(false)}
        onSelect={handleSelect}
      />
    </>
  )
}
```

### 指定文件类型

```typescript
<SandboxFilePicker
  open={open}
  onClose={() => setOpen(false)}
  onSelect={handleSelect}
  accept=".pdf,.docx,.txt"  // 只显示这些类型的文件
/>
```

### 多选模式

```typescript
<SandboxFilePicker
  open={open}
  onClose={() => setOpen(false)}
  onSelect={handleSelect}
  multiple={true}  // 允许选择多个文件
/>
```

### 指定目录

```typescript
// 在组件外设置
localStorage.setItem('sandbox_path', 'documents/reports')

<SandboxFilePicker
  open={open}
  onClose={() => setOpen(false)}
  onSelect={handleSelect}
/>
```

## API 接口

### 获取文件列表

```
GET /console/api/gitea/files?path=<directory_path>
```

**响应**:
```json
{
  "files": [
    {
      "name": "report.pdf",
      "size": 1024000,
      "type": "file"
    }
  ]
}
```

### 下载文件

```
GET /console/api/gitea/files/<file_path>
```

**响应**: 文件内容（Blob）

## 工作流程

```
用户点击选择文件
    ↓
显示 Gitea 文件选择器
    ↓
从 Gitea API 获取文件列表
    ↓
用户选择文件
    ↓
从 Gitea 下载文件内容
    ↓
转换为 File 对象
    ↓
回调 onSelect 函数
```

## 文件过滤

### 自动过滤

- 自动过滤掉目录（只显示文件）
- 自动过滤掉 `.mapping.json` 文件
- 根据 `accept` 参数过滤文件类型

### 示例

```typescript
// 只显示图片文件
accept=".jpg,.jpeg,.png,.gif"

// 只显示文档文件
accept=".pdf,.docx,.txt,.md"

// 只显示数据文件
accept=".csv,.json,.xml"
```

## 错误处理

### 常见错误

#### 1. 无法加载文件列表

**错误信息**: "无法从 Gitea 加载文件列表，请确认 Gitea 配置正确"

**原因**:
- Gitea 服务未启动
- Gitea 配置错误
- 网络连接问题

**解决方案**:
```bash
# 检查 Gitea 配置
cat api/.env | grep GITEA

# 测试 Gitea 连接
curl http://localhost:3000/api/v1/repos/cheersai/file-storage/contents
```

#### 2. 读取文件失败

**错误信息**: "从 Gitea 读取文件失败"

**原因**:
- 文件不存在
- 权限不足
- Token 无效

**解决方案**:
- 检查文件是否存在于 Gitea 仓库
- 确认 Token 有读取权限
- 重新生成 Token

#### 3. 401 未授权

**原因**: 未登录或 session 过期

**解决方案**:
- 重新登录应用
- 检查 CORS 配置

## 性能优化

### 1. 文件列表缓存

文件列表在对话框打开时加载，可以点击刷新按钮重新加载。

### 2. 懒加载

文件内容只在用户确认选择后才下载，避免不必要的网络请求。

### 3. 批量下载

多个文件并行下载，提高效率：

```typescript
const filePromises = Array.from(selected).map(async (name) => {
  // 并行下载
  return downloadFile(name)
})
const files = await Promise.all(filePromises)
```

## 安全性

### 1. 认证

所有 API 请求都需要登录认证：

```typescript
fetch(url, {
  credentials: 'include',  // 包含认证 cookie
})
```

### 2. 文件标记

从 Gitea 下载的文件会被标记为沙箱文件：

```typescript
(file as any)._fromSandbox = true
```

这样可以在后续处理中识别文件来源。

### 3. 类型验证

支持通过 `accept` 参数限制文件类型，防止上传不安全的文件。

## 相关文件

- `web/app/components/base/sandbox-file-picker/index.tsx` - 文件选择器组件
- `api/controllers/console/gitea_api/gitea_files.py` - Gitea 文件 API
- `api/services/gitea_storage_service.py` - Gitea 存储服务
- `web/service/gitea.ts` - 前端 Gitea 服务

## 总结

✅ **沙箱文件选择器现已集成 Gitea**

- 直接从 Gitea 仓库浏览和选择文件
- 支持文件类型过滤和多选
- 自动下载并转换为 File 对象
- 完整的错误处理和用户反馈

现在你可以在应用中使用 Gitea 作为文件源，安全地选择和使用文件！
