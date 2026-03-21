# CheersAI 从 Gitea 获取文件 - 快速开始

## ✅ 已完成的工作

CheersAI 现在可以从 Gitea 仓库中读取和获取文件了！

### 📁 创建的文件

1. **`api/services/gitea_storage_service.py`** - Gitea 文件获取服务
   - `get_file()` - 获取文件内容
   - `get_file_metadata()` - 获取文件元数据
   - `list_files()` - 列出目录文件
   - `get_file_url()` - 获取下载链接
   - `file_exists()` - 检查文件是否存在

2. **`api/controllers/console/files/gitea_files.py`** - 后端 API
   - `GET /console/api/gitea/files/<path>` - 下载文件
   - `GET /console/api/gitea/files/<path>/metadata` - 获取元数据
   - `GET /console/api/gitea/files?path=<dir>` - 列出文件
   - `GET /console/api/gitea/files/<path>/url` - 获取 URL

3. **`web/service/gitea.ts`** - 前端服务
   - `getGiteaFileMetadata()` - 获取元数据
   - `getGiteaFileUrl()` - 获取 URL
   - `listGiteaFiles()` - 列出文件
   - `downloadGiteaFile()` - 下载文件
   - `getGiteaFileContent()` - 获取文本内容
   - `getGiteaFileDataUrl()` - 获取 Data URL

4. **`docs/GITEA_FILE_RETRIEVAL.md`** - 完整文档

## 🚀 快速开始

### 1. 配置环境变量

在 `api/.env` 文件中添加：

```bash
GITEA_URL=http://localhost:3000
GITEA_TOKEN=your_token_here  # 私有仓库需要
GITEA_OWNER=cheersai
GITEA_REPO=file-storage
```

### 2. 在 Gitea 中准备文件

在你的 Gitea 仓库中创建文件结构：

```
file-storage/
├── documents/
│   └── example.pdf
├── images/
│   └── logo.png
└── config/
    └── app.json
```

### 3. 使用后端 API

```python
from services.gitea_storage_service import GiteaStorageService

gitea = GiteaStorageService()

# 获取文件内容
content = gitea.get_file('documents/example.pdf')

# 获取文件元数据
metadata = gitea.get_file_metadata('documents/example.pdf')
print(f"Size: {metadata['size']} bytes")

# 列出目录
files = gitea.list_files('documents')
for file in files:
    print(file['name'])

# 获取下载 URL
url = gitea.get_file_url('documents/example.pdf')
```

### 4. 使用前端 API

```typescript
import {
  getGiteaFileMetadata,
  listGiteaFiles,
  downloadGiteaFile,
  getGiteaFileContent,
} from '@/service/gitea'

// 获取元数据
const metadata = await getGiteaFileMetadata('documents/example.pdf')

// 列出文件
const { files } = await listGiteaFiles('documents')

// 下载文件
const blob = await downloadGiteaFile('documents/example.pdf')

// 获取文本内容
const content = await getGiteaFileContent('config/app.json')
```

## 📊 API 端点

### 后端 REST API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/console/api/gitea/files/<path>` | GET | 下载文件 |
| `/console/api/gitea/files/<path>/metadata` | GET | 获取元数据 |
| `/console/api/gitea/files?path=<dir>` | GET | 列出文件 |
| `/console/api/gitea/files/<path>/url` | GET | 获取 URL |

### 前端服务函数

| 函数 | 说明 |
|------|------|
| `getGiteaFileMetadata(path)` | 获取文件元数据 |
| `getGiteaFileUrl(path)` | 获取下载 URL |
| `listGiteaFiles(dir)` | 列出目录文件 |
| `downloadGiteaFile(path)` | 下载文件为 Blob |
| `getGiteaFileContent(path)` | 获取文本内容 |
| `getGiteaFileDataUrl(path)` | 获取 Data URL |

## 💡 使用场景

### 场景 1: 显示 Gitea 中的图片

```tsx
import { useEffect, useState } from 'react'
import { getGiteaFileDataUrl } from '@/service/gitea'

function GiteaImage({ path }: { path: string }) {
  const [url, setUrl] = useState('')

  useEffect(() => {
    getGiteaFileDataUrl(path).then(setUrl)
  }, [path])

  return <img src={url} alt="Gitea Image" />
}

// 使用
<GiteaImage path="images/logo.png" />
```

### 场景 2: 加载配置文件

```typescript
import { getGiteaFileContent } from '@/service/gitea'

async function loadConfig() {
  const text = await getGiteaFileContent('config/app.json')
  return JSON.parse(text)
}

const config = await loadConfig()
```

### 场景 3: 文件浏览器

```tsx
import { listGiteaFiles } from '@/service/gitea'

function FileBrowser() {
  const [files, setFiles] = useState([])

  useEffect(() => {
    listGiteaFiles('documents').then(({ files }) => setFiles(files))
  }, [])

  return (
    <ul>
      {files.map(file => (
        <li key={file.path}>
          {file.name} ({file.size} bytes)
        </li>
      ))}
    </ul>
  )
}
```

### 场景 4: 批量下载

```python
from services.gitea_storage_service import GiteaStorageService

gitea = GiteaStorageService()
files = gitea.list_files('documents')

for file in files:
    if file['type'] == 'file':
        content = gitea.get_file(file['path'])
        with open(f"downloads/{file['name']}", 'wb') as f:
            f.write(content)
```

## 🎯 工作原理

```
前端请求
    ↓
GET /console/api/gitea/files/<path>
    ↓
GiteaStorageService.get_file()
    ↓
Gitea API
    ↓
http://localhost:3000/{owner}/{repo}/raw/branch/main/<path>
    ↓
返回文件内容
```

## ✨ 特性

- ✅ 从 Gitea 读取任何文件
- ✅ 支持公开和私有仓库
- ✅ 获取文件元数据
- ✅ 列出目录内容
- ✅ 生成直接下载链接
- ✅ 完整的前后端 API
- ✅ TypeScript 类型支持
- ✅ 错误处理

## 🔒 安全性

- 所有 API 需要登录认证
- 支持 Token 认证访问私有仓库
- 文件路径验证
- 错误处理和日志记录

## 📚 完整文档

查看 [docs/GITEA_FILE_RETRIEVAL.md](docs/GITEA_FILE_RETRIEVAL.md) 获取：
- 详细 API 文档
- 更多使用示例
- 故障排除指南
- 性能优化建议

## 🎉 总结

✅ **CheersAI 现在可以从 Gitea 获取文件**

- 完整的后端服务和 API
- 便捷的前端服务函数
- 支持各种文件类型
- 完善的文档和示例

现在你可以将文件存储在 Gitea 仓库中，CheersAI 可以直接读取和使用这些文件！
