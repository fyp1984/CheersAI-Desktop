# 安装指南

本文档提供详细的安装和部署说明。

## 目录

- [系统要求](#系统要求)
- [安装依赖](#安装依赖)
- [本地测试](#本地测试)
- [打包插件](#打包插件)
- [安装到 Dify](#安装到-dify)
- [故障排除](#故障排除)

## 系统要求

### 基础要求

- **Python**: 3.12 或更高版本
- **操作系统**: Windows / macOS / Linux
- **内存**: 至少 512MB 可用内存
- **磁盘空间**: 至少 100MB 可用空间

### Python 依赖

所有 Python 依赖都在 `requirements.txt` 中定义：

```
python-docx>=0.8.11
markdown>=3.4.1
weasyprint>=59.0
beautifulsoup4>=4.12.2
Pillow>=10.0.0
dify-plugin>=0.1.0
```

## 安装依赖

### 1. 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 安装系统依赖（PDF 功能）

WeasyPrint 需要一些系统库来生成 PDF。

#### Ubuntu/Debian

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
```

#### macOS

```bash
# 使用 Homebrew
brew install cairo pango gdk-pixbuf libffi
```

#### Windows

1. 下载 GTK3 运行时安装器：
   https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer

2. 运行安装器并按照提示完成安装

3. 确保 GTK3 的 bin 目录已添加到系统 PATH

## 本地测试

### 1. 运行测试脚本

```bash
# 在插件根目录下运行
python test_plugin.py
```

测试脚本会：
- 检查所有依赖是否已安装
- 测试所有 4 种格式的导出功能
- 生成测试文件到当前目录
- 显示详细的测试结果

### 2. 手动测试

```python
# 测试 Word 导出
from tools.word_export import WordExportTool

tool = WordExportTool()
result = tool._invoke(
    tool_parameters={
        "markdown_content": "# 测试\n\n这是测试内容。",
        "document_name": "测试文档"
    }
)
print(result.message)
```

### 3. 验证输出文件

测试成功后，会在当前目录生成以下文件：
- `测试文档.docx` - Word 文档
- `测试文档.pdf` - PDF 文档
- `测试文档.html` - HTML 文档
- `测试文档.md` - Markdown 文档

## 打包插件

### 方法 1: 使用 Dify CLI（推荐）

```bash
# 安装 Dify CLI
pip install dify-cli

# 打包插件
dify plugin package ./file-format-converter-plugin

# 输出: file-format-converter-plugin-0.0.1.difypkg
```

### 方法 2: 使用构建脚本

```bash
# 在插件根目录下运行
bash scripts/build.sh
```

构建脚本会：
1. 验证所有必需文件
2. 检查 manifest.yaml 格式
3. 创建 .difypkg 包
4. 显示包的详细信息

### 方法 3: 手动打包

```bash
# 创建 ZIP 压缩包
cd file-format-converter-plugin
zip -r ../file-format-converter-plugin-0.0.1.difypkg \
    manifest.yaml \
    main.py \
    requirements.txt \
    *.yaml \
    tools/ \
    utils/ \
    icon.png

# 重命名为 .difypkg
mv ../file-format-converter-plugin-0.0.1.zip \
   ../file-format-converter-plugin-0.0.1.difypkg
```

## 安装到 Dify

### 方法 1: 通过 Web 界面

1. 登录 Dify 管理后台
2. 进入 **插件管理** 页面
3. 点击 **上传插件** 按钮
4. 选择 `.difypkg` 文件
5. 等待上传和安装完成
6. 启用插件

### 方法 2: 通过 API

```bash
# 使用 curl 上传插件
curl -X POST \
  http://your-dify-instance/api/plugins/upload \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@file-format-converter-plugin-0.0.1.difypkg"
```

### 方法 3: 通过 CLI

```bash
# 使用 Dify CLI 安装
dify plugin install file-format-converter-plugin-0.0.1.difypkg
```

## 验证安装

### 1. 检查插件状态

在 Dify 管理后台：
1. 进入 **插件管理**
2. 找到 **File Format Converter**
3. 确认状态为 **已启用**

### 2. 测试插件功能

创建一个测试工作流：

```yaml
# workflow_test.yaml
name: 测试文件格式转换
steps:
  - name: 生成内容
    type: llm
    model: gpt-3.5-turbo
    prompt: "写一篇关于 AI 的简短文章"
    
  - name: 导出为 Word
    type: tool
    tool: file-format-converter/word_export
    inputs:
      markdown_content: "{{steps.生成内容.output}}"
      document_name: "AI文章"
```

### 3. 检查日志

```bash
# 查看 Dify 日志
tail -f /var/log/dify/plugin.log | grep "file-format-converter"
```

## 故障排除

### 问题 1: PDF 生成失败

**错误信息**: `OSError: cannot load library 'gobject-2.0-0'`

**解决方案**:
```bash
# Ubuntu/Debian
sudo apt-get install libgobject-2.0-0

# macOS
brew install gobject-introspection

# Windows
# 重新安装 GTK3 运行时
```

### 问题 2: 中文显示乱码

**错误信息**: 生成的文档中中文显示为方块或乱码

**解决方案**:
```bash
# 安装中文字体
# Ubuntu/Debian
sudo apt-get install fonts-noto-cjk

# macOS
# 系统自带中文字体

# Windows
# 确保系统已安装中文字体（通常已预装）
```

### 问题 3: 内存不足

**错误信息**: `MemoryError` 或插件崩溃

**解决方案**:
1. 增加插件内存限制（修改 `manifest.yaml`）:
```yaml
resource:
  memory: 536870912  # 512MB
```

2. 分批处理大文件
3. 优化 Markdown 内容大小

### 问题 4: 依赖安装失败

**错误信息**: `pip install` 失败

**解决方案**:
```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像（中国用户）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 单独安装失败的包
pip install weasyprint --no-cache-dir
```

### 问题 5: 插件无法加载

**错误信息**: 插件在 Dify 中不显示或无法启用

**解决方案**:
1. 检查 `manifest.yaml` 格式是否正确
2. 确认所有必需文件都已包含在 `.difypkg` 中
3. 查看 Dify 日志获取详细错误信息
4. 重新打包并上传插件

### 问题 6: 工具调用失败

**错误信息**: 工具执行时报错

**解决方案**:
1. 检查输入参数是否正确
2. 确认 Markdown 内容格式正确
3. 查看插件日志获取详细错误
4. 尝试使用测试脚本本地测试

## 更新插件

### 1. 修改版本号

编辑 `manifest.yaml`:
```yaml
version: 0.0.2  # 更新版本号
```

### 2. 更新代码

进行必要的代码修改和测试。

### 3. 重新打包

```bash
dify plugin package ./file-format-converter-plugin
```

### 4. 上传新版本

在 Dify 管理后台上传新的 `.difypkg` 文件。

## 卸载插件

### 通过 Web 界面

1. 进入 **插件管理**
2. 找到 **File Format Converter**
3. 点击 **卸载** 按钮
4. 确认卸载

### 通过 CLI

```bash
dify plugin uninstall file-format-converter
```

## 获取帮助

如果遇到问题：

1. 查看 [故障排除文档](docs/TROUBLESHOOTING.md)
2. 查看 [API 文档](docs/API.md)
3. 提交 Issue: https://github.com/cheersai/file-format-converter-plugin/issues
4. 发送邮件: support@cheersai.com

## 相关资源

- [Dify 插件开发文档](https://docs.dify.ai/plugins)
- [项目 README](README.md)
- [快速开始指南](QUICKSTART.md)
- [贡献指南](CONTRIBUTING.md)

---

**最后更新**: 2026-05-24  
**版本**: 0.0.1
