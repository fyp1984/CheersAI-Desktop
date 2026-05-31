# 使用示例

本文档提供详细的使用示例，帮助您快速上手文件格式转换插件。

## 目录

- [基础使用](#基础使用)
- [工作流集成](#工作流集成)
- [智能体集成](#智能体集成)
- [高级用法](#高级用法)
- [实际场景](#实际场景)

## 基础使用

### 示例 1: 导出 Word 文档

```python
# 在 Dify 工作流中使用
{
  "tool": "file-format-converter/word_export",
  "parameters": {
    "markdown_content": "# 会议记录\n\n## 参会人员\n- 张三\n- 李四\n\n## 讨论内容\n1. 项目进度\n2. 下周计划",
    "document_name": "周会记录-2026-05-24"
  }
}
```

**输出**:
- 文件名: `周会记录-2026-05-24.docx`
- 格式: Microsoft Word 文档
- 包含: 完整的格式和样式

### 示例 2: 导出 PDF 文档

```python
{
  "tool": "file-format-converter/pdf_export",
  "parameters": {
    "markdown_content": "# 技术文档\n\n## 系统架构\n\n```python\ndef main():\n    print('Hello')\n```",
    "document_name": "系统架构文档"
  }
}
```

**输出**:
- 文件名: `系统架构文档.pdf`
- 格式: PDF 文档
- 特点: 高质量排版，代码高亮

### 示例 3: 导出 HTML 文档

```python
{
  "tool": "file-format-converter/html_export",
  "parameters": {
    "markdown_content": "# 产品介绍\n\n这是一个**创新**的产品。",
    "document_name": "产品介绍",
    "include_css": true
  }
}
```

**输出**:
- 文件名: `产品介绍.html`
- 格式: HTML 文档
- 特点: 响应式设计，GitHub 风格

### 示例 4: 导出 Markdown 文档

```python
{
  "tool": "file-format-converter/markdown_export",
  "parameters": {
    "markdown_content": "# 笔记\n\n今天学习了 Dify 插件开发。",
    "document_name": "学习笔记"
  }
}
```

**输出**:
- 文件名: `学习笔记.md`
- 格式: Markdown 文档
- 特点: UTF-8 编码，便于版本控制

## 工作流集成

### 场景 1: AI 生成内容并导出

```yaml
name: AI 内容生成与导出
description: 使用 AI 生成内容并导出为多种格式

steps:
  # 步骤 1: 生成内容
  - id: generate_content
    name: 生成文章
    type: llm
    config:
      model: gpt-4
      prompt: |
        写一篇关于人工智能的技术文章，包括：
        1. 简介
        2. 核心技术
        3. 应用场景
        4. 未来展望
        
        要求：
        - 使用 Markdown 格式
        - 包含代码示例
        - 包含表格对比
      
  # 步骤 2: 导出为 Word
  - id: export_word
    name: 导出 Word 文档
    type: tool
    tool: file-format-converter/word_export
    inputs:
      markdown_content: "{{steps.generate_content.output}}"
      document_name: "AI技术文章"
  
  # 步骤 3: 导出为 PDF
  - id: export_pdf
    name: 导出 PDF 文档
    type: tool
    tool: file-format-converter/pdf_export
    inputs:
      markdown_content: "{{steps.generate_content.output}}"
      document_name: "AI技术文章"
  
  # 步骤 4: 导出为 HTML
  - id: export_html
    name: 导出 HTML 文档
    type: tool
    tool: file-format-converter/html_export
    inputs:
      markdown_content: "{{steps.generate_content.output}}"
      document_name: "AI技术文章"
      include_css: true

outputs:
  - word_file: "{{steps.export_word.output}}"
  - pdf_file: "{{steps.export_pdf.output}}"
  - html_file: "{{steps.export_html.output}}"
```

### 场景 2: 会议记录整理

```yaml
name: 会议记录整理
description: 将会议录音转文字后整理并导出

steps:
  # 步骤 1: 语音转文字
  - id: transcribe
    name: 转录会议录音
    type: tool
    tool: speech-to-text
    inputs:
      audio_file: "{{workflow.input.audio}}"
  
  # 步骤 2: AI 整理
  - id: organize
    name: 整理会议记录
    type: llm
    config:
      model: gpt-4
      prompt: |
        请将以下会议录音转录内容整理成结构化的会议记录：
        
        {{steps.transcribe.output}}
        
        要求：
        1. 提取关键信息
        2. 分类整理（参会人员、讨论内容、决议事项、待办事项）
        3. 使用 Markdown 格式
        4. 包含时间戳
  
  # 步骤 3: 导出为 Word
  - id: export
    name: 导出会议记录
    type: tool
    tool: file-format-converter/word_export
    inputs:
      markdown_content: "{{steps.organize.output}}"
      document_name: "会议记录-{{workflow.input.date}}"

outputs:
  - meeting_notes: "{{steps.export.output}}"
```

### 场景 3: 批量报告生成

```yaml
name: 批量报告生成
description: 根据数据批量生成格式化报告

steps:
  # 步骤 1: 获取数据
  - id: fetch_data
    name: 获取报告数据
    type: code
    code: |
      # 从数据库或 API 获取数据
      data = fetch_report_data()
      return data
  
  # 步骤 2: 生成报告内容
  - id: generate_report
    name: 生成报告
    type: llm
    config:
      model: gpt-4
      prompt: |
        根据以下数据生成分析报告：
        
        {{steps.fetch_data.output}}
        
        报告结构：
        1. 执行摘要
        2. 数据分析
        3. 趋势图表
        4. 结论和建议
        
        使用 Markdown 格式，包含表格和图表说明。
  
  # 步骤 3: 导出为 PDF（正式版）
  - id: export_pdf
    name: 导出 PDF 报告
    type: tool
    tool: file-format-converter/pdf_export
    inputs:
      markdown_content: "{{steps.generate_report.output}}"
      document_name: "分析报告-{{workflow.input.period}}"
  
  # 步骤 4: 导出为 HTML（在线版）
  - id: export_html
    name: 导出 HTML 报告
    type: tool
    tool: file-format-converter/html_export
    inputs:
      markdown_content: "{{steps.generate_report.output}}"
      document_name: "分析报告-{{workflow.input.period}}"
      include_css: true

outputs:
  - pdf_report: "{{steps.export_pdf.output}}"
  - html_report: "{{steps.export_html.output}}"
```

## 智能体集成

### 示例 1: 文档助手智能体

```python
# agent_config.py
from dify_agent import Agent

class DocumentAssistant(Agent):
    """文档助手智能体"""
    
    def __init__(self):
        super().__init__(
            name="文档助手",
            description="帮助用户创建和导出各种格式的文档"
        )
        
        # 注册工具
        self.register_tool("file-format-converter/word_export")
        self.register_tool("file-format-converter/pdf_export")
        self.register_tool("file-format-converter/html_export")
        self.register_tool("file-format-converter/markdown_export")
    
    def process(self, user_input):
        """处理用户请求"""
        # 1. 理解用户意图
        intent = self.understand_intent(user_input)
        
        # 2. 生成内容
        if intent.action == "create":
            content = self.generate_content(intent.topic)
        elif intent.action == "convert":
            content = intent.content
        
        # 3. 导出文档
        results = []
        for format in intent.formats:
            if format == "word":
                result = self.call_tool(
                    "file-format-converter/word_export",
                    markdown_content=content,
                    document_name=intent.filename
                )
            elif format == "pdf":
                result = self.call_tool(
                    "file-format-converter/pdf_export",
                    markdown_content=content,
                    document_name=intent.filename
                )
            # ... 其他格式
            
            results.append(result)
        
        return results

# 使用示例
agent = DocumentAssistant()

# 用户: "帮我写一份产品介绍并导出为 Word 和 PDF"
response = agent.process("帮我写一份产品介绍并导出为 Word 和 PDF")
```

### 示例 2: 知识库管理智能体

```python
class KnowledgeBaseAgent(Agent):
    """知识库管理智能体"""
    
    def export_knowledge(self, topic, format="markdown"):
        """导出知识库内容"""
        # 1. 从知识库检索相关内容
        content = self.retrieve_knowledge(topic)
        
        # 2. 整理成 Markdown 格式
        markdown = self.format_as_markdown(content)
        
        # 3. 导出为指定格式
        tool_map = {
            "word": "file-format-converter/word_export",
            "pdf": "file-format-converter/pdf_export",
            "html": "file-format-converter/html_export",
            "markdown": "file-format-converter/markdown_export"
        }
        
        result = self.call_tool(
            tool_map[format],
            markdown_content=markdown,
            document_name=f"知识库-{topic}"
        )
        
        return result

# 使用示例
agent = KnowledgeBaseAgent()
agent.export_knowledge("Python 编程", format="pdf")
```

## 高级用法

### 1. 自定义样式

```python
# 修改 PDF 样式
from utils.pdf_utils import PdfConverter

# 自定义 CSS
custom_css = """
body {
    font-family: 'Microsoft YaHei', sans-serif;
    font-size: 14px;
    line-height: 1.8;
    color: #333;
}

h1 {
    color: #2c3e50;
    border-bottom: 3px solid #3498db;
    padding-bottom: 10px;
}

code {
    background-color: #f8f9fa;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Consolas', monospace;
}
"""

converter = PdfConverter()
pdf_content = converter.convert(
    markdown_content="# 标题\n\n内容...",
    custom_css=custom_css
)
```

### 2. 批量处理

```python
# 批量导出多个文档
from tools.word_export import WordExportTool

tool = WordExportTool()

documents = [
    {"title": "文档1", "content": "# 文档1\n\n内容..."},
    {"title": "文档2", "content": "# 文档2\n\n内容..."},
    {"title": "文档3", "content": "# 文档3\n\n内容..."},
]

for doc in documents:
    result = tool._invoke(
        tool_parameters={
            "markdown_content": doc["content"],
            "document_name": doc["title"]
        }
    )
    print(f"✅ {doc['title']} 导出完成")
```

### 3. 模板系统

```python
# 使用模板生成文档
template = """
# {title}

**作者**: {author}  
**日期**: {date}

## 摘要

{summary}

## 正文

{content}

## 结论

{conclusion}
"""

# 填充模板
document = template.format(
    title="技术报告",
    author="张三",
    date="2026-05-24",
    summary="这是摘要...",
    content="这是正文...",
    conclusion="这是结论..."
)

# 导出
tool = WordExportTool()
result = tool._invoke(
    tool_parameters={
        "markdown_content": document,
        "document_name": "技术报告"
    }
)
```

## 实际场景

### 场景 1: 技术博客发布

```python
# 1. 在 Markdown 编辑器中写作
blog_content = """
# 深入理解 Python 装饰器

## 什么是装饰器？

装饰器是 Python 中的一个强大特性...

## 基础用法

```python
def my_decorator(func):
    def wrapper():
        print("Before")
        func()
        print("After")
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")
```

## 高级技巧

...
"""

# 2. 导出为 HTML 用于网站发布
html_tool = HtmlExportTool()
html_result = html_tool._invoke(
    tool_parameters={
        "markdown_content": blog_content,
        "document_name": "python-decorators",
        "include_css": True
    }
)

# 3. 导出为 PDF 用于离线阅读
pdf_tool = PdfExportTool()
pdf_result = pdf_tool._invoke(
    tool_parameters={
        "markdown_content": blog_content,
        "document_name": "python-decorators"
    }
)
```

### 场景 2: 项目文档生成

```python
# 自动生成项目文档
def generate_project_docs(project_path):
    """生成项目文档"""
    # 1. 扫描项目结构
    structure = scan_project_structure(project_path)
    
    # 2. 提取代码注释
    api_docs = extract_api_docs(project_path)
    
    # 3. 生成 Markdown 文档
    markdown = f"""
# {project_name} 项目文档

## 项目结构

{structure}

## API 文档

{api_docs}

## 使用示例

...
"""
    
    # 4. 导出为多种格式
    formats = ["word", "pdf", "html"]
    for fmt in formats:
        export_document(markdown, f"项目文档", fmt)
```

### 场景 3: 学习笔记整理

```python
# AI 辅助整理学习笔记
def organize_study_notes(raw_notes):
    """整理学习笔记"""
    # 1. AI 整理笔记
    organized = ai_organize(raw_notes)
    
    # 2. 添加目录和索引
    with_toc = add_table_of_contents(organized)
    
    # 3. 导出为 Markdown（便于后续编辑）
    md_tool = MarkdownExportTool()
    md_tool._invoke(
        tool_parameters={
            "markdown_content": with_toc,
            "document_name": f"学习笔记-{date.today()}"
        }
    )
    
    # 4. 导出为 PDF（便于打印）
    pdf_tool = PdfExportTool()
    pdf_tool._invoke(
        tool_parameters={
            "markdown_content": with_toc,
            "document_name": f"学习笔记-{date.today()}"
        }
    )
```

## 最佳实践

### 1. 文件命名

```python
# ✅ 好的命名
"会议记录-2026-05-24"
"技术文档-v1.0"
"产品介绍-最终版"

# ❌ 避免的命名
"文档1"  # 不够描述性
"test"   # 太通用
"我的文档!!!"  # 包含特殊字符
```

### 2. 内容组织

```markdown
# ✅ 好的结构
# 标题

## 摘要
简短的摘要...

## 目录
- 第一部分
- 第二部分

## 正文
### 第一部分
内容...

### 第二部分
内容...

## 结论
总结...

# ❌ 避免的结构
标题
内容内容内容...
（缺乏层次结构）
```

### 3. 性能优化

```python
# ✅ 分批处理大量文档
def batch_export(documents, batch_size=10):
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        for doc in batch:
            export_document(doc)
        time.sleep(1)  # 避免过载

# ❌ 一次性处理所有文档
for doc in documents:  # 可能导致内存问题
    export_document(doc)
```

## 常见问题

### Q: 如何处理大文件？

A: 建议将大文件分割成多个小文件，或者增加插件内存限制。

### Q: 支持自定义字体吗？

A: 支持。可以修改 `utils/` 中的转换工具类来自定义字体。

### Q: 可以添加水印吗？

A: 目前不支持。这是一个计划中的功能。

### Q: 如何批量转换？

A: 参考"高级用法 - 批量处理"部分的示例代码。

---

**更多示例**: 查看 `examples/` 目录  
**API 文档**: 查看 `docs/API.md`  
**问题反馈**: https://github.com/cheersai/file-format-converter-plugin/issues
