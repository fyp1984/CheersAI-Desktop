# 快速开始指南

本指南将帮助你在 5 分钟内开始使用文件格式转换插件。

## 📦 安装

### 步骤 1: 下载插件

```bash
# 克隆仓库
git clone https://github.com/cheersai/file-format-converter-plugin.git
cd file-format-converter-plugin
```

### 步骤 2: 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt
```

### 步骤 3: 安装系统依赖（仅 PDF 功能需要）

**Ubuntu/Debian:**
```bash
sudo apt-get install libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0
```

**macOS:**
```bash
brew install cairo pango gdk-pixbuf
```

**Windows:**
- 下载 GTK3 运行时：https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer

## 🚀 使用

### 在 Dify 中安装插件

1. 打开 Dify 控制台
2. 进入"插件"页面
3. 点击"安装本地插件"
4. 选择插件目录
5. 点击"安装"

### 在工作流中使用

#### 示例 1: 导出对话为 Word 文档

```yaml
# 在工作流中添加工具节点
- type: tool
  tool: word_export
  inputs:
    markdown_content: "{{conversation.content}}"
    document_name: "对话记录"
```

#### 示例 2: 生成 PDF 报告

```yaml
- type: tool
  tool: pdf_export
  inputs:
    markdown_content: |
      # 月度报告
      
      ## 数据统计
      {{statistics}}
      
      ## 分析结果
      {{analysis}}
    document_name: "月度报告"
```

#### 示例 3: 导出为 HTML

```yaml
- type: tool
  tool: html_export
  inputs:
    markdown_content: "{{content}}"
    document_name: "网页文档"
    include_css: true
```

## 📝 测试

### 使用测试文件

```bash
# 运行插件
python main.py

# 使用测试文档
cat test_example.md | python -c "
from tools.word_export import WordExportTool
tool = WordExportTool()
result = tool._invoke({
    'markdown_content': open('test_example.md').read(),
    'document_name': 'test'
})
print(result)
"
```

### 在 Dify 中测试

1. 创建一个新的工作流
2. 添加"文本输入"节点
3. 添加"工具"节点，选择导出工具
4. 连接节点
5. 运行测试

## 🎯 常见用例

### 用例 1: 会议记录导出

```python
# 智能体配置
{
  "name": "会议助手",
  "tools": ["word_export"],
  "prompt": "总结会议内容并导出为 Word 文档"
}
```

### 用例 2: 技术文档生成

```python
# 工作流配置
{
  "steps": [
    {"type": "llm", "prompt": "生成技术文档"},
    {"type": "tool", "tool": "pdf_export"}
  ]
}
```

### 用例 3: 批量报告生成

```python
# 循环处理
for item in data:
    result = pdf_export.invoke({
        'markdown_content': generate_report(item),
        'document_name': f'report_{item.id}'
    })
```

## 🔧 配置

### 自定义样式

编辑 `utils/pdf_utils.py` 中的 CSS：

```python
css_style = """
    body {
        font-family: 'Your Font', sans-serif;
        color: #your-color;
    }
"""
```

### 调整内存限制

编辑 `manifest.yaml`：

```yaml
resource:
  memory: 536870912  # 512MB
```

## ❓ 常见问题

### Q: 如何处理大文件？
A: 分批处理或增加内存限制。

### Q: 支持哪些 Markdown 语法？
A: 支持标准 Markdown + 表格、代码高亮、任务列表等扩展语法。

### Q: 如何自定义输出格式？
A: 修改 `utils/` 目录下的对应工具类。

## 📚 更多资源

- [完整文档](README.md)
- [API 参考](docs/API.md)
- [示例集合](examples/)
- [故障排除](docs/TROUBLESHOOTING.md)

## 💡 提示

1. **文件命名**: 使用有意义的文档名称
2. **格式选择**: 
   - Word - 需要编辑
   - PDF - 需要分享
   - HTML - 需要展示
   - Markdown - 需要版本控制
3. **性能优化**: 大文档建议使用 PDF 或 HTML

## 🎉 完成！

现在你已经可以开始使用文件格式转换插件了。

需要帮助？查看 [完整文档](README.md) 或 [提交 Issue](https://github.com/cheersai/file-format-converter-plugin/issues)。
