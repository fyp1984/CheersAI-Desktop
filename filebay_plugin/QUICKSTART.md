# 快速开始指南

## 5 分钟快速上手 FileBay Sync 插件

### 第一步：打包插件 (1 分钟)

```bash
# 下载并安装 Dify 插件工具（如果还没有）
# macOS ARM64
curl -L https://github.com/langgenius/dify-plugin-daemon/releases/latest/download/dify-plugin-darwin-arm64 -o dify
chmod +x dify
sudo mv dify /usr/local/bin/

# 打包插件
cd filebay_plugin
dify plugin package .
```

你会看到生成了 `filebay_plugin.difypkg` 文件。

### 第二步：安装插件 (2 分钟)

1. 打开 Dify 管理后台
2. 进入 **工作空间设置** → **插件**
3. 点击 **安装插件**
4. 上传 `filebay_plugin.difypkg`
5. 等待安装完成

### 第三步：配置凭据 (2 分钟)

在插件列表中找到 **FileBay Sync**，点击配置：

```
FileBay URL: https://uat-filebay.cheersai.cloud
Access Token: [从 FileBay 设置中生成]
Repository Owner: your-username
Repository Name: workspace
Branch Name: main
```

点击 **验证** → **保存**

### 第四步：测试使用 (立即)

#### 方式 1: 在 Agent 中使用

1. 创建新的 Agent 应用
2. 在工具设置中启用 **FileBay Sync**
3. 开始对话：

```
用户: 请列出仓库中的所有文件
Agent: [自动调用 list_files 工具并返回结果]

用户: 读取 README.md 文件
Agent: [自动调用 read_file 工具并显示内容]

用户: 创建一个新文件 test.txt，内容是 "Hello Dify!"
Agent: [自动调用 write_file 工具并确认创建成功]
```

#### 方式 2: 在 Workflow 中使用

1. 创建新的 Workflow 应用
2. 添加 **工具** 节点
3. 选择 **FileBay Sync** → **read_file**
4. 配置参数：
   - file_path: `README.md`
   - encoding: `utf-8`
5. 运行测试

## 常用场景示例

### 场景 1: 文档助手

创建一个能读取和更新文档的 Agent：

```
系统提示词：
你是一个文档助手，可以帮助用户管理 FileBay 仓库中的文档。
你可以：
1. 读取文档内容
2. 创建新文档
3. 更新现有文档
4. 列出目录中的文件

用户对话示例：
用户: 帮我总结 docs/project-plan.md 的内容
Agent: [读取文件] → [生成总结] → 这是项目计划的总结...

用户: 把总结保存到 docs/summary.md
Agent: [写入文件] → 已保存到 docs/summary.md
```

### 场景 2: 代码审查助手

```
系统提示词：
你是一个代码审查助手，可以读取代码文件并提供改进建议。

用户对话：
用户: 审查 src/main.py 文件
Agent: [读取文件] → [分析代码] → 
      发现以下问题：
      1. 缺少错误处理
      2. 变量命名不规范
      ...
      
用户: 生成改进后的代码并保存到 src/main_improved.py
Agent: [生成代码] → [写入文件] → 已保存改进版本
```

### 场景 3: 自动化报告生成

使用 Workflow 自动生成报告：

```
1. [开始] → 输入：报告主题
2. [LLM] → 生成报告内容
3. [FileBay: write_file] → 保存到 reports/report-{date}.md
4. [FileBay: list_files] → 列出所有报告
5. [结束] → 返回报告列表
```

## 进阶技巧

### 技巧 1: 批量处理文件

```python
# 在 Workflow 中使用循环节点
1. list_files → 获取文件列表
2. 循环处理每个文件
3. read_file → 读取内容
4. LLM → 处理内容
5. write_file → 保存结果
```

### 技巧 2: 版本控制

每次写入文件时使用有意义的提交信息：

```
commit_message: "Update report - Added Q2 data analysis"
```

### 技巧 3: 处理二进制文件

```yaml
# 读取图片
encoding: binary  # 返回 base64

# 写入图片
encoding: binary
content: [base64 encoded data]
```

## 故障排除速查

| 问题 | 解决方案 |
|------|----------|
| 无法连接 | 检查 URL 和网络 |
| 401 错误 | Token 无效，重新生成 |
| 404 错误 | 文件路径错误，使用 list_files 确认 |
| 403 错误 | 权限不足，检查 Token 权限 |
| 编码错误 | 尝试 binary 编码 |

## 获取帮助

- 📖 详细文档：[README.md](README.md)
- 🔧 安装指南：[INSTALL.md](INSTALL.md)
- 🏗️ 项目结构：[STRUCTURE.md](STRUCTURE.md)
- 💬 技术支持：联系开发团队

## 下一步

✅ 插件已安装并配置
✅ 基本功能已测试

现在你可以：
- 🚀 在生产环境中使用
- 🎨 自定义 Agent 提示词
- 🔄 创建自动化 Workflow
- 📊 集成到现有应用

祝使用愉快！🎉
