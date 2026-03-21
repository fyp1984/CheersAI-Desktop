# Gitea 文件存储集成指南

## 概述

CheersAI 现已集成 Gitea 作为文件存储后端，所有文件上传将自动保存到 Gitea 仓库中。

## 功能特性

- ✅ 所有文件上传自动保存到 Gitea 仓库
- ✅ 支持多租户文件隔离
- ✅ 自动生成文件下载链接
- ✅ 失败时自动降级到默认存储
- ✅ 支持文件删除和更新

## 前置要求

### 1. Gitea 服务器

确保你有一个运行中的 Gitea 实例：
- Gitea 版本: 1.17+ 推荐
- 访问地址: 例如 `http://localhost:3000`

### 2. 创建存储仓库

在 Gitea 中创建一个专门用于文件存储的仓库：

```bash
# 仓库名称示例
cheersai/file-storage
```

### 3. 生成 API Token

1. 登录 Gitea
2. 进入 **设置** → **应用** → **管理访问令牌**
3. 点击 **生成新令牌**
4. 令牌名称: `CheersAI File Storage`
5. 选择权限: `repo` (读写权限)
6. 点击 **生成令牌**
7. **重要**: 复制并保存生成的令牌

## 配置步骤

### 1. 环境变量配置

在 `api/.env` 文件中添加以下配置：

```bash
# Gitea 存储配置
USE_GITEA_STORAGE=true
GITEA_URL=http://localhost:3000
GITEA_TOKEN=your_gitea_token_here
GITEA_OWNER=cheersai
GITEA_REPO=file-storage
```

### 2. 配置说明

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `USE_GITEA_STORAGE` | 是否启用 Gitea 存储 | `true` / `false` |
| `GITEA_URL` | Gitea 服务器地址 | `http://localhost:3000` |
| `GITEA_TOKEN` | Gitea API 令牌 | `ghp_xxxxxxxxxxxx` |
| `GITEA_OWNER` | 仓库所有者 | `cheersai` |
| `GITEA_REPO` | 存储仓库名称 | `file-storage` |

### 3. 重启服务

```bash
# 重启后端服务
cd api
.venv\Scripts\python.exe -m flask run --host=0.0.0.0 --port=5001 --debug
```

## 文件存储结构

文件将按以下结构存储在 Gitea 仓库中：

```
file-storage/
├── upload_files/
│   ├── tenant_id_1/
│   │   ├── uuid1.pdf
│   │   ├── uuid2.jpg
│   │   └── uuid3.docx
│   ├── tenant_id_2/
│   │   └── uuid4.png
│   └── default/
│       └── uuid5.txt
```

## 使用示例

### 后端 API

文件上传会自动使用 Gitea 存储，无需修改现有代码：

```python
from services.file_service import FileService

# 上传文件
file_service = FileService(db.engine)
upload_file = file_service.upload_file(
    filename="example.pdf",
    content=file_content,
    mimetype="application/pdf",
    user=current_user
)

# 文件 URL 会自动指向 Gitea
print(upload_file.source_url)
# 输出: http://localhost:3000/cheersai/file-storage/raw/branch/main/upload_files/tenant_id/uuid.pdf
```

### 前端上传

前端文件上传组件无需修改，继续使用现有的上传接口：

```typescript
import { upload } from '@/service/base'

// 文件上传
const formData = new FormData()
formData.append('file', file)

upload({
  xhr: new XMLHttpRequest(),
  data: formData,
  onprogress: (e) => {
    // 处理进度
  }
})
```

## 文件访问

### 直接访问

上传成功后，文件可以通过以下 URL 直接访问：

```
http://localhost:3000/{owner}/{repo}/raw/branch/main/{file_path}
```

示例：
```
http://localhost:3000/cheersai/file-storage/raw/branch/main/upload_files/default/abc123.pdf
```

### API 访问

也可以通过 Gitea API 访问：

```bash
curl -H "Authorization: token YOUR_TOKEN" \
  http://localhost:3000/api/v1/repos/cheersai/file-storage/contents/upload_files/default/abc123.pdf
```

## 故障处理

### 自动降级

如果 Gitea 上传失败，系统会自动降级到默认存储：

```python
# 自动降级逻辑
try:
    gitea_service.upload_file(...)
except Exception as e:
    print(f"Gitea upload failed, using default storage: {e}")
    storage.save(file_key, content)
```

### 常见问题

#### 1. 上传失败: 401 Unauthorized

**原因**: API Token 无效或权限不足

**解决方案**:
- 检查 `GITEA_TOKEN` 是否正确
- 确认 Token 有 `repo` 权限
- 重新生成 Token

#### 2. 上传失败: 404 Not Found

**原因**: 仓库不存在

**解决方案**:
- 检查 `GITEA_OWNER` 和 `GITEA_REPO` 配置
- 确认仓库已创建
- 确认 Token 所有者有仓库访问权限

#### 3. 上传失败: 网络错误

**原因**: 无法连接到 Gitea 服务器

**解决方案**:
- 检查 `GITEA_URL` 配置
- 确认 Gitea 服务正在运行
- 检查网络连接和防火墙设置

## 性能优化

### 1. 使用本地 Gitea

为获得最佳性能，建议在本地网络运行 Gitea：

```bash
# 使用 Docker 运行 Gitea
docker run -d --name=gitea \
  -p 3000:3000 \
  -v /var/lib/gitea:/data \
  gitea/gitea:latest
```

### 2. 启用缓存

在 Gitea 中启用缓存可以提高文件访问速度。

### 3. 使用 CDN

对于生产环境，可以在 Gitea 前面配置 CDN 来加速文件访问。

## 安全建议

1. **Token 安全**
   - 不要将 Token 提交到版本控制
   - 定期轮换 Token
   - 使用环境变量存储 Token

2. **仓库权限**
   - 设置适当的仓库访问权限
   - 考虑使用私有仓库
   - 定期审查访问日志

3. **文件验证**
   - 系统已内置文件类型验证
   - 系统已内置文件大小限制
   - 禁止上传可执行文件

## 监控和日志

### 查看上传日志

```bash
# 后端日志
tail -f api/logs/app.log | grep "Gitea"
```

### Gitea 仓库统计

在 Gitea 仓库页面可以查看：
- 文件数量
- 存储空间使用
- 提交历史

## 迁移指南

### 从默认存储迁移到 Gitea

1. 备份现有文件
2. 启用 Gitea 存储
3. 新文件自动使用 Gitea
4. 旧文件继续使用默认存储（兼容模式）

### 从 Gitea 迁移回默认存储

1. 设置 `USE_GITEA_STORAGE=false`
2. 重启服务
3. 新文件使用默认存储

## 技术架构

```
┌─────────────┐
│   前端      │
│  (React)    │
└──────┬──────┘
       │ HTTP POST /files/upload
       ▼
┌─────────────┐
│   后端      │
│  (Flask)    │
└──────┬──────┘
       │
       ├─ USE_GITEA_STORAGE=true ──┐
       │                           ▼
       │                    ┌─────────────┐
       │                    │   Gitea     │
       │                    │   Storage   │
       │                    │   Service   │
       │                    └──────┬──────┘
       │                           │ Gitea API
       │                           ▼
       │                    ┌─────────────┐
       │                    │   Gitea     │
       │                    │   Server    │
       │                    └─────────────┘
       │
       └─ USE_GITEA_STORAGE=false ──┐
                                     ▼
                              ┌─────────────┐
                              │   Default   │
                              │   Storage   │
                              └─────────────┘
```

## 相关文件

- `api/services/gitea_storage_service.py` - Gitea 存储服务
- `api/services/file_service.py` - 文件上传服务
- `.env.gitea.example` - 配置示例
- `docs/GITEA_STORAGE_INTEGRATION.md` - 本文档

## 支持

如有问题，请查看：
- [Gitea 官方文档](https://docs.gitea.io/)
- [Gitea API 文档](https://docs.gitea.io/en-us/api-usage/)
