# 📋 快速参考卡片

文件格式转换插件 - 一页速查表

---

## 🚀 快速开始

### 安装
```bash
pip install -r requirements.txt
python test_plugin.py
bash deploy.sh
```

### 在 Dify 中使用
```yaml
tool: file-format-converter/word_export
inputs:
  markdown_content: "# 标题\n\n内容..."
  document_name: "文档名称"
```

---

## 🔧 4 个工具

| 工具 | 输出格式 | 用途 |
|------|---------|------|
| `word_export` | .docx | 正式文档、报告 |
| `pdf_export` | .pdf | 归档、打印 |
| `html_export` | .html | 网页展示 |
| `markdown_export` | .md | 版本控制 |

---

## 📝 参数说明

### 必需参数
- `markdown_content` (string) - Markdown 内容

### 可选参数
- `document_name` (string) - 文件名（不含扩展名）
- `include_css` (boolean) - 是否包含 CSS（仅 HTML）

---

## 💡 使用示例

### Word 导出
```python
{
  "tool": "file-format-converter/word_export",
  "parameters": {
    "markdown_content": "# 会议记录\n\n## 内容\n...",
    "document_name": "周会-2026-05-24"
  }
}
```

### PDF 导出
```python
{
  "tool": "file-format-converter/pdf_export",
  "parameters": {
    "markdown_content": "# 技术文档\n\n...",
    "document_name": "系统架构"
  }
}
```

### HTML 导出
```python
{
  "tool": "file-format-converter/html_export",
  "parameters": {
    "markdown_content": "# 产品介绍\n\n...",
    "document_name": "产品手册",
    "include_css": true
  }
}
```

### Markdown 导出
```python
{
  "tool": "file-format-converter/markdown_export",
  "parameters": {
    "markdown_content": "# 笔记\n\n...",
    "document_name": "学习笔记"
  }
}
```

---

## ✅ 支持的 Markdown 语法

- ✅ 标题 (H1-H6): `# 标题`
- ✅ 粗体: `**粗体**`
- ✅ 斜体: `*斜体*`
- ✅ 代码: `` `代码` ``
- ✅ 代码块: ` ```python ... ``` `
- ✅ 列表: `- 项目` 或 `1. 项目`
- ✅ 引用: `> 引用内容`
- ✅ 表格: `| 列1 | 列2 |`
- ✅ 链接: `[文本](URL)`
- ✅ 分隔线: `---`

---

## 🔍 常见问题

### Q: PDF 生成失败？
**A**: 安装系统依赖
```bash
# Ubuntu/Debian
sudo apt-get install libcairo2 libpango-1.0-0

# macOS
brew install cairo pango
```

### Q: 中文乱码？
**A**: 安装中文字体
```bash
sudo apt-get install fonts-noto-cjk
```

### Q: 内存不足？
**A**: 修改 `manifest.yaml`
```yaml
resource:
  memory: 536870912  # 512MB
```

### Q: 文件名非法？
**A**: 避免使用特殊字符: `/ \ : * ? " < > |`

---

## 📊 性能指标

| 指标 | 值 |
|------|-----|
| 处理速度 | < 5秒 (10KB) |
| 内存使用 | < 256MB |
| 文件大小限制 | 10MB |
| 并发支持 | 3 个任务 |

---

## 🛠️ 测试命令

```bash
# 功能测试
python test_plugin.py

# 打包插件
bash deploy.sh

# 验证 YAML
python -c "import yaml; yaml.safe_load(open('manifest.yaml'))"

# 检查依赖
python -c "import docx, markdown, weasyprint; print('OK')"
```

---

## 📁 项目结构

```
file-format-converter-plugin/
├── manifest.yaml          # 插件清单
├── main.py               # 主入口
├── requirements.txt      # 依赖
├── icon.png             # 图标
├── tools/               # 工具实现
│   ├── word_export.py
│   ├── pdf_export.py
│   ├── html_export.py
│   └── markdown_export.py
└── utils/               # 工具类
    ├── docx_utils.py
    ├── pdf_utils.py
    └── html_utils.py
```

---

## 🔗 文档链接

| 文档 | 用途 |
|------|------|
| [README.md](README.md) | 完整文档 |
| [QUICKSTART.md](QUICKSTART.md) | 快速开始 |
| [INSTALLATION.md](INSTALLATION.md) | 安装指南 |
| [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) | 使用示例 |
| [docs/API.md](docs/API.md) | API 参考 |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | 故障排除 |

---

## 📞 获取帮助

- 📖 文档: [README.md](README.md)
- 🐛 报告问题: GitHub Issues
- 💬 讨论: GitHub Discussions
- 📧 邮件: support@cheersai.com

---

## 📝 工作流模板

### AI 生成 + 导出
```yaml
steps:
  - id: generate
    type: llm
    prompt: "写一篇文章..."
  
  - id: export
    type: tool
    tool: file-format-converter/word_export
    inputs:
      markdown_content: "{{steps.generate.output}}"
      document_name: "AI文章"
```

### 批量导出
```yaml
steps:
  - id: export_word
    type: tool
    tool: file-format-converter/word_export
    inputs:
      markdown_content: "{{input.content}}"
  
  - id: export_pdf
    type: tool
    tool: file-format-converter/pdf_export
    inputs:
      markdown_content: "{{input.content}}"
```

---

## 🎯 使用场景

| 场景 | 推荐格式 |
|------|---------|
| 会议记录 | Word |
| 技术文档 | PDF |
| 博客发布 | HTML |
| 版本控制 | Markdown |
| 正式报告 | PDF |
| 团队协作 | Word |
| 在线展示 | HTML |
| 代码文档 | Markdown |

---

## ⚡ 快捷命令

```bash
# 测试
python test_plugin.py

# 打包
bash deploy.sh

# 安装依赖
pip install -r requirements.txt

# 生成图标
python create_icon.py

# 验证配置
python -c "import yaml; yaml.safe_load(open('manifest.yaml'))"
```

---

## 📊 版本信息

- **当前版本**: 0.0.1
- **发布日期**: 2026-05-24
- **Python 版本**: 3.12+
- **许可证**: MIT

---

## 🎉 快速检查清单

部署前检查：
- [ ] 依赖已安装
- [ ] 测试通过 (4/4)
- [ ] 插件已打包
- [ ] 文档已阅读

部署后检查：
- [ ] 插件已启用
- [ ] 工具可用
- [ ] 基本功能正常
- [ ] 无错误日志

---

**打印此页作为速查表！**

---

*最后更新: 2026-05-24 | 版本: 0.0.1*
