# CheersAI 从 Gitea 获取文件集成指南

## 概述

CheersAI 现已集成 Gitea 文件读取功能，可以直接从 Gitea 仓库中获取、下载和访问文件。

## 功能特性

- ✅ 从 Gitea 仓库读取文件内容
- ✅ 获取文件元数据（大小、SHA、类型等）
- ✅ 列出目录中的文件
- ✅ 生成文件下载链接
- ✅ 支持公开和私有仓库
- ✅ 完整的前后端 API

## 配置

### 环境变量

在 `api/.env` 文件中配置：

```bash
# Gitea 配置
GITEA_URL=http://localhost:3000
GITEA_TOKEN=your_gitea_token_here  # 私有仓库需要
GITEA_OWNER=cheersai
GITEA_REPO=file-storage
```

### 配置说明

| 变量 | 必需 | 说明 |
|------|------|------|
| `GITEA_URL` | 是 | Gitea 服务器地址 |
| `GITEA_TOKEN` | 否 | API Token（公开仓库可选） |
| `GITEA_OWNER` | 是 | 仓库所有者 |
| `GITEA_REPO` | 是 | 仓库名称 |

## 后端 API

### 1. 下载文件

**端点**: `GET /console/api/gitea/files/<file_path>`

**示例**:
```bash
curl -X GET http://localhost:5001/console/api/gitea/files/documents/example.pdf \
  -H "Cookie: session=..." \
  --output example.pdf
```

**Python 示例**:
```python
from services.gitea_storage_service import GiteaStorageService

gitea_service = GiteaStorageService()
file_content = gitea_service.get_file('documents/example.pdf')

# 保存到本地
with open('example.pdf', 'wb') as f:
    f.write(file_content)
```

### 2. 获取文件元数据

**端点**: `GET /console/api/gitea/files/<file_path>/metadata`

**响应**:
```json
{
  "name": "example.pdf",
  "path": "documents/example.pdf",
  "size": 1024000,
  "sha": "abc123...",
  "url": "http://localhost:3000/cheersai/file-storage/raw/branch/main/documents/example.pdf",
  "type": "file"
}
```

**Python 示例**:
```python
metadata = gitea_service.get_file_metadata('documents/example.pdf')
print(f"File size: {metadata['size']} bytes")
print(f"Download URL: {metadata['url']}")
```

### 3. 列出目录文件

**端点**: `GET /console/api/gitea/files?path=<directory_path>`

**示例**:
```bash
curl -X GET "http://localhost:5001/console/api/gitea/files?path=documents" \
  -H "Cookie: session=..."
```

**响应**:
```json
{
  "files": [
    {
      "name": "example.pdf",
      "path": "documents/example.pdf",
      "type": "file",
      "size": 1024000,
      "sha": "abc123...",
      "url": "http://..."
    },
    {
      "name": "image.png",
      "path": "documents/image.png",
      "type": "file",
      "size": 512000,
      "sha": "def456...",
      "url": "http://..."
    }
  ]
}
```

**Python 示例**:
```python
files = gitea_service.list_files('documents')
for file in files:
    print(f"{file['name']} - {file['size']} bytes")
```

### 4. 获取文件 URL

**端点**: `GET /console/api/gitea/files/<file_path>/url`

**响应**:
```json
{
  "url": "http://localhost:3000/cheersai/file-storage/raw/branch/main/documents/example.pdf",
  "path": "documents/example.pdf"
}
```

**Python 示例**:
```python
url = gitea_service.get_file_url('documents/example.pdf')
print(f"Direct download URL: {url}")
```

### 5. 检查文件是否存在

**Python 示例**:
```python
exists = gitea_service.file_exists('documents/example.pdf')
if exists:
    print("File exists in Gitea")
else:
    print("File not found")
```

## 前端 API

### 导入服务

```typescript
import {
  getGiteaFileMetadata,
  getGiteaFileUrl,
  listGiteaFiles,
  downloadGiteaFile,
  getGiteaFileContent,
  getGiteaFileDataUrl,
} from '@/service/gitea'
```

### 1. 获取文件元数据

```typescript
const metadata = await getGiteaFileMetadata('documents/example.pdf')
console.log(`File size: ${metadata.size} bytes`)
console.log(`Download URL: ${metadata.url}`)
```

### 2. 获取文件下载 URL

```typescript
const { url } = await getGiteaFileUrl('documents/example.pdf')
console.log(`Direct URL: ${url}`)
```

### 3. 列出目录文件

```typescript
const { files } = await listGiteaFiles('documents')
files.forEach(file => {
  console.log(`${file.name} - ${file.size} bytes`)
})
```

### 4. 下载文件

```typescript
// 下载为 Blob
const blob = await downloadGiteaFile('documents/example.pdf')

// 创建下载链接
const url = URL.createObjectURL(blob)
const a = document.createElement('a')
a.href = url
a.download = 'example.pdf'
a.click()
URL.revokeObjectURL(url)
```

### 5. 获取文本文件内容

```typescript
const content = await getGiteaFileContent('documents/readme.txt')
console.log(content)
```

### 6. 获取图片为 Data URL

```typescript
const dataUrl = await getGiteaFileDataUrl('images/logo.png')

// 在 img 标签中使用
<img src={dataUrl} alt="Logo" />
```

## 使用场景

### 场景 1: 显示 Gitea 中的图片

```typescript
import { useEffect, useState } from 'react'
import { getGiteaFileDataUrl } from '@/service/gitea'

function GiteaImage({ filePath }: { filePath: string }) {
  const [imageUrl, setImageUrl] = useState<string>('')

  useEffect(() => {
    getGiteaFileDataUrl(filePath).then(setImageUrl)
  }, [filePath])

  return <img src={imageUrl} alt="Gitea Image" />
}
```

### 场景 2: 读取配置文件

```typescript
import { getGiteaFileContent } from '@/service/gitea'

async function loadConfig() {
  const configText = await getGiteaFileContent('config/app.json')
  const config = JSON.parse(configText)
  return config
}
```

### 场景 3: 文件浏览器

```typescript
import { useState, useEffect } from 'react'
import { listGiteaFiles, type GiteaFileMetadata } from '@/service/gitea'

function FileBrowser() {
  const [files, setFiles] = useState<GiteaFileMetadata[]>([])
  const [currentPath, setCurrentPath] = useState('')

  useEffect(() => {
    listGiteaFiles(currentPath).then(({ files }) => setFiles(files))
  }, [currentPath])

  return (
    <div>
      <h2>Files in: {currentPath || 'root'}</h2>
      <ul>
        {files.map(file => (
          <li key={file.path}>
            {file.name} ({file.size} bytes)
            <a href={file.url} download>Download</a>
          </li>
        ))}
      </ul>
    </div>
  )
}
```

### 场景 4: 批量下载文件

```python
from services.gitea_storage_service import GiteaStorageService
import os

gitea_service = GiteaStorageService()

# 列出目录中的所有文件
files = gitea_service.list_files('documents')

# 批量下载
for file in files:
    if file['type'] == 'file':
        content = gitea_service.get_file(file['path'])
        
        # 保存到本地
        local_path = f"downloads/{file['name']}"
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        with open(local_path, 'wb') as f:
            f.write(content)
        
        print(f"Downloaded: {file['name']}")
```

## Gitea 仓库结构建议

```
file-storage/
├── documents/
│   ├── user-guide.pdf
│   ├── api-docs.pdf
│   └── terms.pdf
├── images/
│   ├── logo.png
│   ├── banner.jpg
│   └── icons/
│       ├── home.svg
│       └── settings.svg
├── config/
│   ├── app.json
│   └── features.json
└── templates/
    ├── email/
    │   ├── welcome.html
    │   └── reset-password.html
    └── reports/
        └── monthly.xlsx
```

## 安全性

### 1. 访问控制

- 所有 API 端点都需要登录认证
- 使用 `@login_required` 装饰器保护
- 支持基于 Token 的私有仓库访问

### 2. 文件验证

```python
# 检查文件是否存在
if not gitea_service.file_exists(file_path):
    raise FileNotFoundError("File not found")

# 获取元数据验证文件类型
metadata = gitea_service.get_file_metadata(file_path)
if metadata['size'] > MAX_FILE_SIZE:
    raise ValueError("File too large")
```

### 3. 错误处理

```typescript
try {
  const content = await getGiteaFileContent('config/app.json')
  // 处理内容
} catch (error) {
  if (error.message.includes('404')) {
    console.error('File not found')
  } else {
    console.error('Failed to load file:', error)
  }
}
```

## 性能优化

### 1. 缓存文件内容

```typescript
const fileCache = new Map<string, Blob>()

async function getCachedFile(filePath: string): Promise<Blob> {
  if (fileCache.has(filePath)) {
    return fileCache.get(filePath)!
  }
  
  const blob = await downloadGiteaFile(filePath)
  fileCache.set(filePath, blob)
  return blob
}
```

### 2. 使用直接 URL

对于公开文件，可以直接使用 Gitea 的 raw URL：

```typescript
const { url } = await getGiteaFileUrl('images/logo.png')
// 直接在 img 标签中使用
<img src={url} alt="Logo" />
```

## 故障排除

### 问题 1: 文件未找到 (404)

**原因**: 文件路径不正确或文件不存在

**解决**:
```python
# 检查文件是否存在
if gitea_service.file_exists('documents/example.pdf'):
    content = gitea_service.get_file('documents/example.pdf')
else:
    print("File does not exist")
```

### 问题 2: 权限错误 (401/403)

**原因**: Token 无效或权限不足

**解决**:
- 检查 `GITEA_TOKEN` 环境变量
- 确认 Token 有仓库读取权限
- 对于私有仓库，必须提供有效 Token

### 问题 3: 连接超时

**原因**: Gitea 服务器不可达

**解决**:
- 检查 `GITEA_URL` 配置
- 确认 Gitea 服务正在运行
- 检查网络连接

## 相关文件

- `api/services/gitea_storage_service.py` - Gitea 文件服务
- `api/controllers/console/files/gitea_files.py` - Gitea 文件 API
- `web/service/gitea.ts` - 前端 Gitea 服务
- `docs/GITEA_FILE_RETRIEVAL.md` - 本文档

## 总结

✅ **CheersAI 现在可以从 Gitea 仓库获取文件**

- 完整的后端 API 支持
- 便捷的前端服务函数
- 支持文件下载、元数据查询、目录列表
- 适用于各种文件类型（文档、图片、配置等）
- 完善的错误处理和安全控制

现在你可以将文件存储在 Gitea 仓库中，CheersAI 可以直接读取和使用这些文件！
