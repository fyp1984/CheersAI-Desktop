# 🚀 部署检查清单

在部署插件到 Dify 之前，请按照此检查清单确保一切就绪。

---

## ✅ 部署前检查

### 1. 文件完整性检查

#### 必需文件 (核心)
- [ ] `manifest.yaml` - 插件清单
- [ ] `main.py` - 主入口文件
- [ ] `requirements.txt` - Python 依赖
- [ ] `icon.png` - 插件图标 (256x256)
- [ ] `LICENSE` - 许可证文件

#### 工具定义文件 (4个)
- [ ] `word_export.yaml`
- [ ] `pdf_export.yaml`
- [ ] `html_export.yaml`
- [ ] `markdown_export.yaml`

#### 工具实现文件 (4个)
- [ ] `tools/__init__.py`
- [ ] `tools/word_export.py`
- [ ] `tools/pdf_export.py`
- [ ] `tools/html_export.py`
- [ ] `tools/markdown_export.py`

#### 工具类文件 (3个)
- [ ] `utils/__init__.py`
- [ ] `utils/docx_utils.py`
- [ ] `utils/pdf_utils.py`
- [ ] `utils/html_utils.py`

### 2. 配置验证

#### manifest.yaml 检查
```bash
# 验证 YAML 格式
python -c "import yaml; yaml.safe_load(open('manifest.yaml'))"
```

- [ ] YAML 格式正确
- [ ] 版本号正确 (0.0.1)
- [ ] 插件类型为 "plugin"
- [ ] 包含所有 4 个工具定义
- [ ] 内存限制设置 (256MB)
- [ ] 图标路径正确

#### requirements.txt 检查
- [ ] python-docx>=0.8.11
- [ ] markdown>=3.4.1
- [ ] weasyprint>=59.0
- [ ] beautifulsoup4>=4.12.2
- [ ] Pillow>=10.0.0
- [ ] dify-plugin>=0.1.0

### 3. 依赖安装检查

```bash
# 检查 Python 依赖
python -c "import docx; print('✅ python-docx')"
python -c "import markdown; print('✅ markdown')"
python -c "import weasyprint; print('✅ weasyprint')"
python -c "from bs4 import BeautifulSoup; print('✅ beautifulsoup4')"
python -c "from PIL import Image; print('✅ Pillow')"
```

- [ ] python-docx 已安装
- [ ] markdown 已安装
- [ ] weasyprint 已安装
- [ ] beautifulsoup4 已安装
- [ ] Pillow 已安装

### 4. 功能测试

```bash
# 运行测试脚本
python test_plugin.py
```

- [ ] Word 导出测试通过
- [ ] PDF 导出测试通过
- [ ] HTML 导出测试通过
- [ ] Markdown 导出测试通过
- [ ] 所有测试 4/4 通过

### 5. 代码质量检查

- [ ] 所有 Python 文件无语法错误
- [ ] 导入语句正确
- [ ] 错误处理完善
- [ ] 代码注释清晰

### 6. 文档检查

- [ ] README.md 存在且完整
- [ ] QUICKSTART.md 存在
- [ ] INSTALLATION.md 存在
- [ ] 所有文档链接有效

---

## 📦 打包步骤

### 方法 1: 使用部署脚本 (推荐)

```bash
# 运行部署脚本
bash deploy.sh
```

脚本会自动：
1. ✅ 检查必需文件
2. ✅ 验证 manifest.yaml
3. ✅ 检查依赖
4. ✅ 运行测试（可选）
5. ✅ 打包插件
6. ✅ 显示包信息

### 方法 2: 使用 Dify CLI

```bash
# 安装 Dify CLI
pip install dify-cli

# 打包插件
dify plugin package ./file-format-converter-plugin

# 输出: file-format-converter-plugin-0.0.1.difypkg
```

### 方法 3: 手动打包

```bash
# 创建临时目录
mkdir -p /tmp/plugin-build
cp -r file-format-converter-plugin /tmp/plugin-build/

# 清理不需要的文件
cd /tmp/plugin-build/file-format-converter-plugin
rm -rf .git __pycache__ *.pyc .pytest_cache
rm -rf docs examples scripts
rm -f test_plugin.py create_icon.py deploy.sh
rm -f *SUMMARY.md INSTALLATION.md QUICKSTART.md CONTRIBUTING.md CHANGELOG.md

# 创建 ZIP 包
cd /tmp/plugin-build
zip -r file-format-converter-plugin-0.0.1.difypkg file-format-converter-plugin

# 移动到原目录
mv file-format-converter-plugin-0.0.1.difypkg ~/
```

### 打包后检查

- [ ] `.difypkg` 文件已生成
- [ ] 文件大小合理 (< 10MB)
- [ ] 文件名格式正确: `{plugin-name}-{version}.difypkg`

---

## 🔧 安装到 Dify

### 前置条件

- [ ] Dify 实例正在运行
- [ ] 有管理员权限
- [ ] 网络连接正常

### 安装步骤

#### 方法 1: Web 界面上传

1. **登录 Dify**
   - [ ] 打开 Dify 管理后台
   - [ ] 使用管理员账号登录

2. **进入插件管理**
   - [ ] 点击左侧菜单 "插件管理"
   - [ ] 或访问 `/admin/plugins`

3. **上传插件**
   - [ ] 点击 "上传插件" 或 "安装插件" 按钮
   - [ ] 选择 `.difypkg` 文件
   - [ ] 等待上传完成

4. **启用插件**
   - [ ] 在插件列表中找到 "File Format Converter"
   - [ ] 点击 "启用" 按钮
   - [ ] 确认状态变为 "已启用"

#### 方法 2: API 上传

```bash
# 使用 curl 上传
curl -X POST \
  http://your-dify-instance/api/plugins/upload \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@file-format-converter-plugin-0.0.1.difypkg"
```

- [ ] API 调用成功
- [ ] 返回插件 ID
- [ ] 插件状态为已安装

#### 方法 3: CLI 安装

```bash
# 使用 Dify CLI
dify plugin install file-format-converter-plugin-0.0.1.difypkg \
  --host http://your-dify-instance \
  --token YOUR_API_KEY
```

- [ ] CLI 安装成功
- [ ] 插件已启用

---

## ✅ 安装后验证

### 1. 检查插件状态

在 Dify 管理后台：
- [ ] 插件显示在列表中
- [ ] 插件名称: "File Format Converter"
- [ ] 版本号: 0.0.1
- [ ] 状态: 已启用
- [ ] 图标正确显示

### 2. 检查工具可用性

在工作流编辑器中：
- [ ] 可以找到 "file-format-converter" 工具组
- [ ] 包含 4 个工具:
  - [ ] word_export
  - [ ] pdf_export
  - [ ] html_export
  - [ ] markdown_export

### 3. 测试基本功能

创建测试工作流：

```yaml
name: 插件测试
steps:
  - name: 测试 Word 导出
    type: tool
    tool: file-format-converter/word_export
    inputs:
      markdown_content: "# 测试\n\n这是测试内容。"
      document_name: "测试文档"
```

- [ ] 工作流创建成功
- [ ] 工具执行成功
- [ ] 文件生成正确
- [ ] 无错误日志

### 4. 检查日志

```bash
# 查看 Dify 日志
tail -f /var/log/dify/plugin.log | grep "file-format-converter"
```

- [ ] 无错误日志
- [ ] 插件加载成功
- [ ] 工具注册成功

---

## 🐛 故障排除

### 问题 1: 上传失败

**可能原因**:
- 文件格式不正确
- 文件太大
- 网络问题

**解决方案**:
1. 检查文件扩展名是否为 `.difypkg`
2. 检查文件大小是否 < 50MB
3. 重试上传
4. 检查网络连接

### 问题 2: 插件无法启用

**可能原因**:
- 依赖缺失
- manifest.yaml 格式错误
- 权限问题

**解决方案**:
1. 查看错误日志
2. 验证 manifest.yaml 格式
3. 检查系统依赖是否已安装
4. 重新打包并上传

### 问题 3: 工具执行失败

**可能原因**:
- Python 依赖未安装
- 系统依赖缺失（PDF）
- 内存不足

**解决方案**:
1. 在 Dify 服务器上安装依赖:
   ```bash
   pip install -r requirements.txt
   ```
2. 安装系统依赖（PDF 功能）
3. 增加插件内存限制
4. 查看详细错误日志

### 问题 4: 中文乱码

**可能原因**:
- 缺少中文字体
- 编码问题

**解决方案**:
1. 安装中文字体:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install fonts-noto-cjk
   ```
2. 确保文件使用 UTF-8 编码

---

## 📋 部署后任务

### 立即任务
- [ ] 通知团队插件已部署
- [ ] 分享使用文档
- [ ] 创建示例工作流
- [ ] 收集初步反馈

### 短期任务
- [ ] 监控插件性能
- [ ] 收集用户反馈
- [ ] 修复发现的 Bug
- [ ] 优化性能

### 长期任务
- [ ] 添加新功能
- [ ] 改进文档
- [ ] 发布新版本
- [ ] 扩展使用场景

---

## 📊 部署清单总结

### 必须完成 (Critical)
- [ ] 所有必需文件存在
- [ ] manifest.yaml 格式正确
- [ ] 依赖已安装
- [ ] 测试全部通过
- [ ] 插件已打包
- [ ] 插件已上传
- [ ] 插件已启用
- [ ] 基本功能验证通过

### 建议完成 (Recommended)
- [ ] 文档已审阅
- [ ] 示例已测试
- [ ] 日志无错误
- [ ] 性能测试通过
- [ ] 团队已培训

### 可选完成 (Optional)
- [ ] 创建演示视频
- [ ] 编写博客文章
- [ ] 分享到社区
- [ ] 收集使用数据

---

## 🎉 部署完成

当所有 "必须完成" 项都勾选后，插件就可以正式使用了！

**下一步**:
1. 📖 查看 [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) 学习使用
2. 🔧 创建你的第一个工作流
3. 📊 监控插件性能
4. 💬 收集用户反馈

---

**部署日期**: ___________  
**部署人员**: ___________  
**Dify 版本**: ___________  
**插件版本**: 0.0.1

**签名**: ___________
