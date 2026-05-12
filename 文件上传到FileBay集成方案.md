# 文件上传到 FileBay 集成方案

## 概述

现在 FileBay 工具已经支持 **write_file** 功能，可以将用户上传的文件保存到 FileBay 仓库中。

## 已实现的功能

### FileBay 工具（内置）

✅ **read_file** - 读取文件
✅ **write_file** - 写入文件（新增）
✅ **list_files** - 列出文件

## 使用场景

### 场景 1: 文件翻译应用

**流程**:
1. 用户上传文档（PDF、Word等）
2. 应用调用 `write_file` 工具将文件保存到 FileBay
3. 应用处理文件（翻译）
4. 应用调用 `write_file` 保存翻译结果
5. 用户可以随时通过 `read_file` 获取原文件或翻译结果

**工作流示例**:
```
[文件上传] → [保存到FileBay] → [文件处理] → [保存结果到FileBay] → [返回结果]
     ↓              ↓                                    ↓
  用户文件      write_file                          write_file
```

### 场景 2: 文档管理应用

**流程**:
1. 用户上传文档
2. 自动保存到 FileBay 的 `uploads/` 目录
3. 使用 `list_files` 浏览已上传的文档
4. 使用 `read_file` 读取文档内容
5. 使用 `write_file` 更新文档

### 场景 3: 数据备份应用

**流程**:
1. 用户上传数据文件
2. 自动备份到 FileBay
3. 定期检查和更新备份
4. 需要时恢复数据

## 在工作流中实现文件上传到 FileBay

### 方法 1: 使用工作流节点

1. **创建工作流应用**
2. **添加文件上传变量**:
   - 类型: File
   - 名称: uploaded_file
3. **添加工具节点 - write_file**:
   - 工具: FileBay → write_file
   - 参数:
     - `file_path`: `uploads/{{uploaded_file.name}}`
     - `content`: `{{uploaded_file.content}}`
     - `commit_message`: `Upload file: {{uploaded_file.name}}`
4. **添加响应节点**:
   - 返回保存结果

### 方法 2: 在对话应用中使用

1. **创建对话应用**
2. **添加 FileBay 工具**
3. **用户对话**:
   ```
   用户: [上传文件] 请帮我保存这个文件到 FileBay
   AI: [调用 write_file] 文件已保存到 FileBay 的 uploads 目录
   ```

## 工作流配置示例

### 完整的文件上传和处理工作流

```yaml
工作流名称: 文件上传到FileBay

输入变量:
  - name: file
    type: file
    label: 上传文件
  - name: target_path
    type: string
    label: 保存路径
    default: "uploads/"

节点:
  1. 开始节点
     ↓
  2. 代码节点 - 准备文件路径
     代码:
       file_name = file.name
       full_path = target_path + file_name
       output = {"full_path": full_path}
     ↓
  3. 工具节点 - 保存到FileBay
     工具: FileBay.write_file
     参数:
       file_path: {{code.full_path}}
       content: {{file.content}}
       commit_message: "Upload: {{file.name}}"
     ↓
  4. 条件节点 - 检查保存结果
     条件: {{write_file.action}} == "created"
     ↓
  5. 响应节点
     成功: "文件已成功保存到 FileBay: {{write_file.file_path}}"
     失败: "文件保存失败，请重试"
```

## 代码示例

### 在自定义代码节点中处理文件

```python
def main(file_content: str, file_name: str) -> dict:
    """
    处理上传的文件并准备保存到 FileBay
    """
    import base64
    
    # 如果文件内容是 base64 编码的，先解码
    try:
        file_bytes = base64.b64decode(file_content)
    except:
        file_bytes = file_content.encode('utf-8')
    
    # 准备保存路径
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = f"uploads/{timestamp}_{file_name}"
    
    return {
        "save_path": save_path,
        "file_size": len(file_bytes),
        "processed": True
    }
```

## API 调用示例

### 直接调用 FileBay 工具 API

```python
import requests

# 调用 write_file 工具
response = requests.post(
    "http://localhost:9000/console/api/workspaces/current/tools/builtin/filebay/write_file",
    headers={
        "Authorization": "Bearer YOUR_TOKEN",
        "Content-Type": "application/json"
    },
    json={
        "file_path": "uploads/document.pdf",
        "content": "base64_encoded_content",
        "commit_message": "Upload document"
    }
)

result = response.json()
print(f"File saved: {result['file_path']}")
```

## 前端集成建议

### 在文件上传组件中集成

如果你想在前端直接集成 FileBay 上传功能，可以：

1. **修改文件上传处理逻辑**:
   - 当前: 文件上传到本地存储
   - 新增: 同时调用 FileBay write_file 工具

2. **添加 FileBay 上传选项**:
   - 在文件上传界面添加"保存到 FileBay"选项
   - 用户可以选择是否同步到 FileBay

3. **实现自动备份**:
   - 所有上传的文件自动备份到 FileBay
   - 在后台异步执行，不影响用户体验

## 配置建议

### FileBay 目录结构建议

```
workspace/
├── uploads/           # 用户上传的原始文件
│   ├── 20260512_document.pdf
│   └── 20260512_image.png
├── processed/         # 处理后的文件
│   ├── 20260512_document_translated.pdf
│   └── 20260512_image_resized.png
├── backups/          # 备份文件
│   └── 20260512/
└── temp/             # 临时文件
```

### 文件命名规范

建议使用以下命名格式：
```
{timestamp}_{original_name}
例如: 20260512_143022_document.pdf
```

这样可以：
- 避免文件名冲突
- 方便按时间排序
- 保留原始文件名信息

## 权限和安全

### FileBay 凭证管理

1. **用户级凭证**: 每个用户使用自己的 FileBay 凭证
2. **应用级凭证**: 应用使用统一的 FileBay 凭证
3. **租户级凭证**: 租户内共享 FileBay 凭证

### 文件访问控制

- 确保用户只能访问自己上传的文件
- 使用目录隔离不同用户的文件
- 定期清理临时文件

## 监控和日志

### 建议记录的信息

- 文件上传时间
- 文件大小
- 保存路径
- 用户信息
- 操作结果（成功/失败）

### 错误处理

常见错误及处理：

1. **文件过大**: 
   - 检查文件大小限制
   - 提示用户压缩文件

2. **FileBay 连接失败**:
   - 重试机制
   - 降级到本地存储

3. **权限不足**:
   - 检查 FileBay Token 权限
   - 提示用户更新凭证

## 性能优化

### 大文件处理

1. **分块上传**: 将大文件分成多个小块上传
2. **异步处理**: 使用 Celery 任务异步上传
3. **压缩传输**: 在上传前压缩文件

### 缓存策略

1. **本地缓存**: 缓存常用文件，减少 FileBay 请求
2. **CDN 加速**: 使用 CDN 加速文件访问
3. **预加载**: 预加载可能需要的文件

## 下一步计划

### 可以扩展的功能

1. **批量上传**: 一次上传多个文件
2. **文件版本管理**: 保留文件的历史版本
3. **文件搜索**: 按名称、类型、日期搜索文件
4. **文件分享**: 生成文件分享链接
5. **文件预览**: 在线预览文件内容
6. **自动分类**: 根据文件类型自动分类存储

## 总结

现在 FileBay 工具已经支持完整的文件操作功能：

✅ **读取** - 从 FileBay 读取文件
✅ **写入** - 向 FileBay 保存文件
✅ **列出** - 浏览 FileBay 文件

你可以在任何 Dify 应用中使用这些功能，实现：
- 文件上传和保存
- 文件管理和组织
- 文件备份和恢复
- 文件处理和转换

**开始使用**: 在你的应用中添加 FileBay 工具，配置凭证，就可以开始使用了！
