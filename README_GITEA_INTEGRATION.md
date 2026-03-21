# CheersAI Gitea 文件存储集成

## ✅ 已完成的工作

所有 CheersAI 文件上传入口已成功改为使用 Gitea 存储。

### 📁 创建的文件

1. **`api/services/gitea_storage_service.py`** - Gitea 存储服务
   - 文件上传到 Gitea 仓库
   - 文件删除功能
   - 文件 URL 生成
   - 自动处理文件更新

2. **`api/services/file_service.py`** - 修改后的文件上传服务
   - 集成 Gitea 存储
   - 自动降级到默认存储
   - 保持向后兼容

3. **`.env.gitea.example`** - 环境变量配置示例
   - Gitea 连接配置
   - 仓库配置
   - Token 配置

4. **`docs/GITEA_STORAGE_INTEGRATION.md`** - 完整集成文档
   - 详细配置说明
   - 使用示例
   - 故障排除
   - 安全建议

5. **`scripts/setup_gitea_storage.py`** - 自动化设置脚本
   - 检查 Gitea 连接
   - 自动创建存储仓库
   - 测试文件上传

## 🚀 快速开始

### 1. 配置 Gitea

在 `api/.env` 文件中添加：

```bash
USE_GITEA_STORAGE=true
GITEA_URL=http://localhost:3000
GITEA_TOKEN=your_gitea_token_here
GITEA_OWNER=cheersai
GITEA_REPO=file-storage
```

### 2. 运行设置脚本

```bash
# 设置环境变量
export GITEA_TOKEN=your_token_here

# 运行设置脚本
cd e:\CheersAI-Desktop
python scripts/setup_gitea_storage.py
```

### 3. 重启服务

```bash
# 后端服务会自动重新加载
# 或手动重启
```

## 📊 工作原理

```
用户上传文件
    ↓
前端 (upload 函数)
    ↓
后端 API (/files/upload)
    ↓
FileService.upload_file()
    ↓
检查 USE_GITEA_STORAGE
    ↓
┌─ true ──→ GiteaStorageService
│              ↓
│          Gitea API
│              ↓
│          保存到 Gitea 仓库
│              ↓
│          返回 Gitea URL
│
└─ false ──→ 默认存储
               ↓
           本地/S3 存储
```

## 🎯 功能特性

### ✅ 已实现

- [x] 所有文件上传使用 Gitea
- [x] 多租户文件隔离
- [x] 自动生成下载链接
- [x] 失败自动降级
- [x] 文件更新支持
- [x] 完整的错误处理
- [x] 环境变量配置
- [x] 自动化设置脚本
- [x] 详细文档

### 📝 文件存储结构

```
file-storage/
└── upload_files/
    ├── tenant_id_1/
    │   ├── uuid1.pdf
    │   ├── uuid2.jpg
    │   └── uuid3.docx
    ├── tenant_id_2/
    │   └── uuid4.png
    └── default/
        └── uuid5.txt
```

## 🔧 配置选项

| 变量 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `USE_GITEA_STORAGE` | 否 | `true` | 启用/禁用 Gitea 存储 |
| `GITEA_URL` | 是 | `http://localhost:3000` | Gitea 服务器地址 |
| `GITEA_TOKEN` | 是 | - | Gitea API Token |
| `GITEA_OWNER` | 是 | `cheersai` | 仓库所有者 |
| `GITEA_REPO` | 是 | `file-storage` | 存储仓库名 |

## 📖 使用示例

### 后端上传

```python
from services.file_service import FileService

file_service = FileService(db.engine)
upload_file = file_service.upload_file(
    filename="document.pdf",
    content=file_content,
    mimetype="application/pdf",
    user=current_user
)

# 文件 URL 自动指向 Gitea
print(upload_file.source_url)
# http://localhost:3000/cheersai/file-storage/raw/branch/main/upload_files/tenant_id/uuid.pdf
```

### 前端上传

前端代码无需修改，继续使用现有接口：

```typescript
import { upload } from '@/service/base'

const formData = new FormData()
formData.append('file', file)

upload({
  xhr: new XMLHttpRequest(),
  data: formData,
  onprogress: (e) => {
    console.log('Progress:', e.loaded / e.total * 100)
  }
})
```

## 🛡️ 安全性

1. **Token 安全**
   - 使用环境变量存储
   - 不提交到版本控制
   - 定期轮换

2. **文件验证**
   - 文件类型检查
   - 文件大小限制
   - 扩展名黑名单

3. **访问控制**
   - 多租户隔离
   - 基于用户的权限
   - 私有仓库支持

## 🔍 故障排除

### 问题 1: 上传失败 401

**原因**: Token 无效

**解决**:
```bash
# 检查 Token
echo $GITEA_TOKEN

# 重新生成 Token
# Gitea → 设置 → 应用 → 生成新令牌
```

### 问题 2: 上传失败 404

**原因**: 仓库不存在

**解决**:
```bash
# 运行设置脚本自动创建
python scripts/setup_gitea_storage.py
```

### 问题 3: 自动降级到默认存储

**原因**: Gitea 连接失败

**解决**:
```bash
# 检查 Gitea 服务
curl http://localhost:3000

# 检查配置
cat api/.env | grep GITEA
```

## 📚 相关文档

- [完整集成文档](docs/GITEA_STORAGE_INTEGRATION.md)
- [Gitea API 文档](https://docs.gitea.io/en-us/api-usage/)
- [环境配置示例](.env.gitea.example)

## 🎉 总结

✅ **所有文件上传入口已成功改为 Gitea**

- 后端文件上传服务已集成 Gitea
- 前端无需修改，自动使用新的存储
- 提供完整的配置和文档
- 包含自动化设置脚本
- 支持失败降级，确保服务可用性

现在所有通过 CheersAI 上传的文件都会自动保存到 Gitea 仓库中！
