# 文件格式转换插件 (File Format Converter Plugin)

一个功能强大的 Dify 插件，用于将 Markdown 内容转换为多种文档格式。

## 功能特性

### 支持的格式

1. **Word 文档 (.docx)**
   - 完整的格式支持（标题、段落、列表、表格等）
   - 代码块高亮
   - 引用块样式
   - 内联格式（粗体、斜体、代码）

2. **PDF 文档 (.pdf)**
   - 专业的排版样式
   - 自定义 CSS 样式
   - 支持中文字体
   - A4 页面格式

3. **HTML 文档 (.html)**
   - 响应式设计
   - GitHub 风格样式
   - 可选 CSS 样式
   - 代码高亮支持

4. **Markdown 文档 (.md)**
   - 原始 Markdown 格式保存
   - UTF-8 编码
   - 便于版本控制

## 安装

### 前置要求

- Python 3.12+
- Dify Plugin SDK

### 安装依赖

```bash
pip install -r requirements.txt
```

### 系统依赖（PDF 生成）

WeasyPrint 需要一些系统库：

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

**macOS:**
```bash
brew install cairo pango gdk-pixbuf libffi
```

**Windows:**
- 下载并安装 GTK3 运行时：https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer

## 使用方法

### 1. Word 文档导出

```python
# 在 Dify 工作流中使用
tool: word_export
parameters:
  markdown_content: "# 标题\n\n这是内容..."
  document_name: "我的文档"  # 可选
```

### 2. PDF 文档导出

```python
tool: pdf_export
parameters:
  markdown_content: "# 标题\n\n这是内容..."
  document_name: "我的文档"  # 可选
```

### 3. HTML 文档导出

```python
tool: html_export
parameters:
  markdown_content: "# 标题\n\n这是内容..."
  document_name: "我的文档"  # 可选
  include_css: true  # 可选，默认 true
```

### 4. Markdown 文档导出

```python
tool: markdown_export
parameters:
  markdown_content: "# 标题\n\n这是内容..."
  document_name: "我的文档"  # 可选
```

## 支持的 Markdown 语法

- ✅ 标题 (H1-H6)
- ✅ 段落和换行
- ✅ 粗体和斜体
- ✅ 代码块和内联代码
- ✅ 列表（有序和无序）
- ✅ 引用块
- ✅ 表格
- ✅ 链接
- ✅ 水平分隔线
- ✅ 图片（HTML 和 PDF）

## 开发

### 项目结构

```
file-format-converter-plugin/
├── manifest.yaml           # 插件清单
├── requirements.txt        # Python 依赖
├── main.py                # 主入口
├── word_export.yaml       # Word 工具定义
├── pdf_export.yaml        # PDF 工具定义
├── html_export.yaml       # HTML 工具定义
├── markdown_export.yaml   # Markdown 工具定义
├── tools/                 # 工具实现
│   ├── word_export.py
│   ├── pdf_export.py
│   ├── html_export.py
│   └── markdown_export.py
└── utils/                 # 工具类
    ├── docx_utils.py
    ├── pdf_utils.py
    └── html_utils.py
```

### 测试

```bash
# 运行插件
python main.py
```

### 打包

```bash
# 使用 Dify CLI 打包
dify plugin package ./file-format-converter-plugin
```

## 配置

### 内存限制

插件默认分配 256MB 内存。如需调整，修改 `manifest.yaml`：

```yaml
resource:
  memory: 268435456  # 256MB
```

### 样式自定义

可以修改以下文件来自定义输出样式：

- `utils/pdf_utils.py` - PDF 样式
- `utils/html_utils.py` - HTML 样式
- `utils/docx_utils.py` - Word 样式

## 常见问题

### Q: PDF 生成失败？
A: 确保已安装所有系统依赖。参考"系统依赖"部分。

### Q: 中文显示乱码？
A: 所有文件都使用 UTF-8 编码。确保系统支持中文字体。

### Q: 文件太大？
A: 考虑分批处理或增加内存限制。

## 许可证

MIT License

## 作者

CheersAI Team

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v0.0.1 (2026-05-24)
- 初始版本
- 支持 Word、PDF、HTML、Markdown 格式导出
- 完整的 Markdown 语法支持
- 自定义样式支持
