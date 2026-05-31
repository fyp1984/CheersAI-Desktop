# 故障排除指南

本指南帮助你解决使用文件格式转换插件时可能遇到的常见问题。

## 📋 目录

- [安装问题](#安装问题)
- [PDF 生成问题](#pdf-生成问题)
- [Word 文档问题](#word-文档问题)
- [中文显示问题](#中文显示问题)
- [性能问题](#性能问题)
- [错误消息](#错误消息)

---

## 安装问题

### ❌ 问题: pip install 失败

**症状:**
```bash
ERROR: Could not find a version that satisfies the requirement python-docx
```

**解决方案:**

1. **更新 pip:**
```bash
pip install --upgrade pip
```

2. **使用国内镜像:**
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

3. **检查 Python 版本:**
```bash
python --version  # 需要 3.12+
```

---

### ❌ 问题: WeasyPrint 安装失败

**症状:**
```bash
ERROR: Failed building wheel for weasyprint
```

**解决方案:**

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    python3-cffi \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info

pip install weasyprint
```

**macOS:**
```bash
brew install cairo pango gdk-pixbuf libffi
pip install weasyprint
```

**Windows:**
1. 下载 GTK3 运行时: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
2. 安装 GTK3
3. 重启终端
4. `pip install weasyprint`

---

## PDF 生成问题

### ❌ 问题: PDF 生成失败

**症状:**
```
❌ 生成PDF文档失败：OSError: cannot load library 'gobject-2.0-0'
```

**解决方案:**

1. **检查系统库:**
```bash
# Linux
ldconfig -p | grep cairo
ldconfig -p | grep pango

# macOS
brew list cairo pango
```

2. **重新安装依赖:**
```bash
pip uninstall weasyprint
pip install --no-cache-dir weasyprint
```

3. **设置环境变量 (Windows):**
```bash
set PATH=%PATH%;C:\Program Files\GTK3-Runtime Win64\bin
```

---

### ❌ 问题: PDF 中文显示为方块

**症状:**
PDF 中的中文字符显示为 □□□

**解决方案:**

1. **安装中文字体:**

**Ubuntu/Debian:**
```bash
sudo apt-get install fonts-noto-cjk
```

**macOS:**
```bash
# 系统自带中文字体，无需安装
```

**Windows:**
```bash
# 系统自带中文字体，无需安装
```

2. **修改 PDF 样式:**

编辑 `utils/pdf_utils.py`，添加中文字体：

```python
css_style = """
    body {
        font-family: 'Noto Sans CJK SC', 'Microsoft YaHei', 'SimHei', sans-serif;
    }
"""
```

---

## Word 文档问题

### ❌ 问题: Word 文档无法打开

**症状:**
```
Word 无法打开文档：文件已损坏
```

**解决方案:**

1. **检查文件大小:**
```python
import os
file_size = os.path.getsize('document.docx')
print(f"文件大小: {file_size} 字节")
```

如果文件大小为 0，说明生成失败。

2. **检查 Markdown 语法:**
```python
# 测试简单内容
result = word_export.invoke({
    'markdown_content': '# 测试\n\n这是测试内容',
    'document_name': 'test'
})
```

3. **更新 python-docx:**
```bash
pip install --upgrade python-docx
```

---

### ❌ 问题: 表格格式错乱

**症状:**
Word 文档中的表格显示不正确

**解决方案:**

1. **简化表格:**
```markdown
# 避免复杂的嵌套表格
| 列1 | 列2 |
|-----|-----|
| 值1 | 值2 |
```

2. **检查表格语法:**
- 确保每行的列数相同
- 使用 `|` 分隔列
- 使用 `---` 分隔表头

---

## 中文显示问题

### ❌ 问题: 中文显示乱码

**症状:**
导出的文件中中文显示为乱码或问号

**解决方案:**

1. **检查输入编码:**
```python
# 确保输入是 UTF-8
markdown_content = content.encode('utf-8').decode('utf-8')
```

2. **检查文件编码:**
```python
# 读取文件时指定编码
with open('file.md', 'r', encoding='utf-8') as f:
    content = f.read()
```

3. **检查系统区域设置:**
```bash
# Linux/macOS
locale

# 应该包含 UTF-8
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
```

---

## 性能问题

### ❌ 问题: 转换速度慢

**症状:**
大文档转换需要很长时间

**解决方案:**

1. **分割大文档:**
```python
def split_content(content, max_size=5000):
    """将大文档分割为小块"""
    lines = content.split('\n')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for line in lines:
        line_size = len(line)
        if current_size + line_size > max_size:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [line]
            current_size = line_size
        else:
            current_chunk.append(line)
            current_size += line_size
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks
```

2. **增加内存限制:**

编辑 `manifest.yaml`:
```yaml
resource:
  memory: 536870912  # 512MB
```

3. **使用更快的格式:**
- HTML 最快
- Markdown 次之
- Word 较慢
- PDF 最慢

---

### ❌ 问题: 内存不足

**症状:**
```
MemoryError: Unable to allocate memory
```

**解决方案:**

1. **减小文档大小:**
```python
# 限制内容大小
MAX_SIZE = 5 * 1024 * 1024  # 5MB
if len(content) > MAX_SIZE:
    content = content[:MAX_SIZE]
```

2. **清理临时文件:**
```python
import tempfile
import shutil

# 清理临时目录
temp_dir = tempfile.gettempdir()
shutil.rmtree(temp_dir, ignore_errors=True)
```

3. **使用流式处理:**
```python
# 分批处理
for chunk in chunks:
    result = process_chunk(chunk)
```

---

## 错误消息

### ❌ "错误：Markdown内容不能为空"

**原因:** 输入的 `markdown_content` 为空字符串

**解决方案:**
```python
# 检查内容
if not markdown_content or not markdown_content.strip():
    print("内容为空")
else:
    result = word_export.invoke({
        'markdown_content': markdown_content
    })
```

---

### ❌ "❌ 生成Word文档失败"

**可能原因:**
1. 磁盘空间不足
2. 权限问题
3. Markdown 语法错误
4. 依赖库问题

**解决方案:**

1. **检查磁盘空间:**
```bash
df -h  # Linux/macOS
```

2. **检查权限:**
```bash
ls -la /tmp  # 检查临时目录权限
```

3. **测试简单内容:**
```python
result = word_export.invoke({
    'markdown_content': '# Test',
    'document_name': 'test'
})
```

4. **查看详细错误:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

### ❌ "Server error '502 Bad Gateway'"

**原因:** 插件服务未正常运行

**解决方案:**

1. **重启插件:**
```bash
# 停止插件
pkill -f "python main.py"

# 启动插件
python main.py
```

2. **检查日志:**
```bash
tail -f /var/log/dify/plugin.log
```

3. **检查端口:**
```bash
netstat -tulpn | grep python
```

---

## 调试技巧

### 1. 启用详细日志

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 2. 测试单个功能

```python
# 测试 Markdown 解析
import markdown
html = markdown.markdown('# Test')
print(html)

# 测试 Word 生成
from docx import Document
doc = Document()
doc.add_paragraph('Test')
doc.save('test.docx')

# 测试 PDF 生成
from weasyprint import HTML
HTML(string='<h1>Test</h1>').write_pdf('test.pdf')
```

### 3. 检查依赖版本

```bash
pip list | grep -E "docx|markdown|weasyprint|beautifulsoup4"
```

### 4. 运行测试脚本

```bash
cd file-format-converter-plugin
bash scripts/test.sh
```

---

## 获取帮助

如果以上方法都无法解决问题：

1. **查看文档:**
   - [README.md](../README.md)
   - [API.md](API.md)
   - [QUICKSTART.md](../QUICKSTART.md)

2. **搜索已知问题:**
   - GitHub Issues: https://github.com/cheersai/file-format-converter-plugin/issues

3. **提交新问题:**
   - 包含错误消息
   - 包含系统信息
   - 包含重现步骤
   - 包含相关日志

4. **联系支持:**
   - Email: support@cheersai.com
   - 社区论坛: https://community.cheersai.com

---

## 常见问题 FAQ

**Q: 支持哪些 Markdown 扩展语法？**  
A: 支持 GitHub Flavored Markdown (GFM)，包括表格、代码高亮、任务列表等。

**Q: 可以自定义输出样式吗？**  
A: 可以，编辑 `utils/` 目录下的对应文件。

**Q: 支持批量转换吗？**  
A: 目前需要循环调用，未来版本会添加批量转换功能。

**Q: 文件保存在哪里？**  
A: 文件通过 Blob 消息返回，由 Dify 平台处理存储。

**Q: 支持图片吗？**  
A: HTML 和 PDF 支持图片，Word 和 Markdown 部分支持。

---

**最后更新**: 2026-05-24
