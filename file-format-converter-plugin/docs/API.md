# API 参考文档

## 概述

文件格式转换插件提供了 4 个工具，用于将 Markdown 内容转换为不同的文档格式。

## 工具列表

### 1. word_export - Word 文档导出

将 Markdown 内容转换为 Word 文档 (.docx)。

#### 参数

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `markdown_content` | string | ✅ | - | 要转换的 Markdown 内容 |
| `document_name` | string | ❌ | "document" | 文档名称（不含扩展名） |

#### 返回值

返回一个包含两个元素的列表：
1. **Blob 消息** - 包含生成的 Word 文档
   - `mime_type`: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
   - `filename`: 生成的文件名（含时间戳）
2. **文本消息** - 成功或错误信息

#### 示例

```python
# 基本使用
result = word_export.invoke({
    'markdown_content': '# 标题\n\n这是内容',
    'document_name': '我的文档'
})

# 在工作流中使用
{
    "tool": "word_export",
    "inputs": {
        "markdown_content": "{{llm_output}}",
        "document_name": "会议记录"
    }
}
```

#### 支持的 Markdown 语法

- ✅ 标题 (H1-H6)
- ✅ 段落
- ✅ 粗体 (`**text**`)
- ✅ 斜体 (`*text*`)
- ✅ 内联代码 (`` `code` ``)
- ✅ 代码块 (` ```language `)
- ✅ 无序列表
- ✅ 有序列表
- ✅ 引用块 (`>`)
- ✅ 表格
- ✅ 链接
- ✅ 水平分隔线 (`---`)

---

### 2. pdf_export - PDF 文档导出

将 Markdown 内容转换为 PDF 文档。

#### 参数

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `markdown_content` | string | ✅ | - | 要转换的 Markdown 内容 |
| `document_name` | string | ❌ | "document" | 文档名称（不含扩展名） |

#### 返回值

返回一个包含两个元素的列表：
1. **Blob 消息** - 包含生成的 PDF 文档
   - `mime_type`: `application/pdf`
   - `filename`: 生成的文件名（含时间戳）
2. **文本消息** - 成功或错误信息

#### 示例

```python
# 基本使用
result = pdf_export.invoke({
    'markdown_content': '# 报告\n\n## 数据分析\n...',
    'document_name': '月度报告'
})

# 在智能体中使用
{
    "tools": ["pdf_export"],
    "prompt": "生成报告并导出为 PDF"
}
```

#### 样式特性

- A4 页面格式
- 2cm 页边距
- 专业排版
- 代码语法高亮
- 表格格式化
- 中文字体支持

---

### 3. html_export - HTML 文档导出

将 Markdown 内容转换为 HTML 文档。

#### 参数

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `markdown_content` | string | ✅ | - | 要转换的 Markdown 内容 |
| `document_name` | string | ❌ | "document" | 文档名称（不含扩展名） |
| `include_css` | boolean | ❌ | true | 是否包含 CSS 样式 |

#### 返回值

返回一个包含两个元素的列表：
1. **Blob 消息** - 包含生成的 HTML 文档
   - `mime_type`: `text/html`
   - `filename`: 生成的文件名（含时间戳）
2. **文本消息** - 成功或错误信息

#### 示例

```python
# 带样式的 HTML
result = html_export.invoke({
    'markdown_content': '# 网页内容',
    'document_name': '文章',
    'include_css': True
})

# 纯 HTML（无样式）
result = html_export.invoke({
    'markdown_content': '# 内容',
    'include_css': False
})
```

#### CSS 主题

默认使用 GitHub 风格样式，包括：
- 响应式设计
- 代码高亮
- 表格样式
- 移动端适配

---

### 4. markdown_export - Markdown 文档导出

将 Markdown 内容保存为 .md 文件。

#### 参数

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `markdown_content` | string | ✅ | - | 要保存的 Markdown 内容 |
| `document_name` | string | ❌ | "document" | 文档名称（不含扩展名） |

#### 返回值

返回一个包含两个元素的列表：
1. **Blob 消息** - 包含 Markdown 文件
   - `mime_type`: `text/markdown`
   - `filename`: 生成的文件名（含时间戳）
2. **文本消息** - 成功或错误信息

#### 示例

```python
# 保存 Markdown
result = markdown_export.invoke({
    'markdown_content': '# 文档\n\n内容...',
    'document_name': '笔记'
})
```

#### 特性

- UTF-8 编码
- 跨平台兼容
- 版本控制友好
- 保留原始格式

---

## 错误处理

所有工具都会返回错误消息，而不是抛出异常。

### 常见错误

#### 1. 空内容错误

```python
# 输入
{
    'markdown_content': '',
    'document_name': 'test'
}

# 输出
"错误：Markdown内容不能为空"
```

#### 2. 转换失败

```python
# 输出
"❌ 生成PDF文档失败：[错误详情]"
```

### 错误码

| 错误类型 | 描述 | 解决方案 |
|---------|------|---------|
| 空内容 | Markdown 内容为空 | 提供有效的 Markdown 内容 |
| 文件系统错误 | 无法写入临时文件 | 检查磁盘空间和权限 |
| 转换错误 | Markdown 解析失败 | 检查 Markdown 语法 |
| 内存不足 | 文档过大 | 减小文档大小或增加内存限制 |

---

## 高级用法

### 1. 批量转换

```python
documents = [
    {'content': '# 文档1', 'name': 'doc1'},
    {'content': '# 文档2', 'name': 'doc2'},
]

for doc in documents:
    result = word_export.invoke({
        'markdown_content': doc['content'],
        'document_name': doc['name']
    })
```

### 2. 条件导出

```python
# 根据内容长度选择格式
if len(content) > 10000:
    # 长文档使用 PDF
    result = pdf_export.invoke({
        'markdown_content': content,
        'document_name': 'long_doc'
    })
else:
    # 短文档使用 Word
    result = word_export.invoke({
        'markdown_content': content,
        'document_name': 'short_doc'
    })
```

### 3. 多格式导出

```python
# 同时导出多种格式
formats = [
    ('word_export', '.docx'),
    ('pdf_export', '.pdf'),
    ('html_export', '.html')
]

for tool_name, ext in formats:
    result = tool.invoke({
        'markdown_content': content,
        'document_name': f'document{ext}'
    })
```

---

## 性能优化

### 1. 内容大小限制

建议单个文档不超过 10MB：

```python
MAX_SIZE = 10 * 1024 * 1024  # 10MB

if len(markdown_content.encode('utf-8')) > MAX_SIZE:
    # 分割内容或提示用户
    pass
```

### 2. 并发处理

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [
        executor.submit(word_export.invoke, {'markdown_content': doc})
        for doc in documents
    ]
    results = [f.result() for f in futures]
```

### 3. 缓存策略

```python
import hashlib

def get_cache_key(content):
    return hashlib.md5(content.encode()).hexdigest()

# 检查缓存
cache_key = get_cache_key(markdown_content)
if cache_key in cache:
    return cache[cache_key]

# 生成并缓存
result = word_export.invoke({'markdown_content': markdown_content})
cache[cache_key] = result
```

---

## 限制和注意事项

### 1. 文件大小
- 最大输入: 10MB
- 最大输出: 50MB

### 2. 内存使用
- 单次转换: < 256MB
- 并发限制: 3 个任务

### 3. 格式支持
- 图片: 仅 HTML 和 PDF 支持
- 数学公式: 不支持
- 自定义 HTML: 部分支持

### 4. 字符限制
- 文件名: 100 字符
- 允许字符: 字母、数字、下划线、连字符

---

## 调试

### 启用调试模式

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

### 查看详细错误

```python
try:
    result = word_export.invoke({
        'markdown_content': content
    })
except Exception as e:
    print(f"错误详情: {e}")
    import traceback
    traceback.print_exc()
```

---

## 更新日志

查看 [CHANGELOG.md](../CHANGELOG.md) 了解最新更新。

## 支持

- GitHub Issues: https://github.com/cheersai/file-format-converter-plugin/issues
- 文档: https://docs.cheersai.com
- Email: support@cheersai.com
