# FileBay Sync Plugin for Dify

一个用于 Dify 的 FileBay 文件同步插件，允许智能体从 FileBay 仓库读取文件并将生成的文件同步回 FileBay。

## 功能特性

### 1. 读取文件 (read_file)
- 从 FileBay 仓库读取文件内容
- 支持文本文件（UTF-8, GBK 等编码）
- 支持二进制文件（Base64 编码）
- 返回文件内容和元数据

### 2. 写入文件 (write_file)
- 创建新文件或更新现有文件
- 支持文本和二进制内容
- 自动处理文件版本控制
- 可自定义提交信息

### 3. 列出文件 (list_files)
- 列出指定目录下的所有文件和子目录
- 显示文件类型、大小等信息
- 支持递归浏览目录结构

## 安装步骤

### 1. 准备 FileBay 凭据

在使用插件前，你需要准备以下信息：

- **FileBay URL**: 你的 FileBay 实例地址（例如：`https://filebay.example.com`）
- **Access Token**: FileBay 访问令牌（在 FileBay 设置中生成）
- **Repository Owner**: 仓库所有者的用户名
- **Repository Name**: 仓库名称（例如：`workspace`）
- **Branch Name**: 分支名称（可选，默认为 `main`）

### 2. 打包插件

使用 Dify 插件开发工具打包插件：

```bash
# 安装 Dify 插件开发工具
# 下载地址: https://github.com/langgenius/dify-plugin-daemon

# 打包插件
dify plugin package ./filebay_plugin

# 这将生成 filebay_plugin.difypkg 文件
```

### 3. 安装插件

#### 方法 1: 通过 Dify Web 界面安装

1. 登录 Dify 管理后台
2. 进入"插件管理"页面
3. 点击"安装插件"
4. 上传 `filebay_plugin.difypkg` 文件
5. 配置 FileBay 凭据
6. 完成安装

#### 方法 2: 远程调试安装（开发模式）

1. 在 Dify 插件管理页面获取远程调试地址和 Key
2. 复制 `.env.example` 为 `.env`
3. 填入远程调试信息：
   ```
   INSTALL_METHOD=remote
   REMOTE_INSTALL_URL=debug.dify.ai:5003
   REMOTE_INSTALL_KEY=your-debug-key
   ```
4. 运行插件：
   ```bash
   python -m main
   ```

## 使用示例

### 在 Agent 中使用

创建一个 Agent 应用，并启用 FileBay Sync 插件。Agent 可以自动调用这些工具：

**示例对话 1: 读取文件**
```
用户: 请读取 documents/report.txt 文件的内容
Agent: [调用 read_file 工具]
      文件路径: documents/report.txt
      编码: utf-8
      
      文件内容已读取，共 1024 字节...
```

**示例对话 2: 创建文件**
```
用户: 请将以下内容保存到 outputs/summary.md 文件中：
      # 项目总结
      这是一个测试项目...
      
Agent: [调用 write_file 工具]
      文件路径: outputs/summary.md
      内容: [用户提供的内容]
      提交信息: Create project summary
      
      文件已成功创建！
```

**示例对话 3: 列出文件**
```
用户: 列出 documents 目录下的所有文件
Agent: [调用 list_files 工具]
      目录路径: documents
      
      找到 5 个文件和 2 个子目录：
      - report.txt (1024 bytes)
      - data.csv (2048 bytes)
      ...
```

### 在 Workflow 中使用

1. 创建 Workflow 应用
2. 添加"工具"节点
3. 选择 FileBay Sync 插件的相应工具
4. 配置输入参数
5. 连接其他节点处理结果

## 技术说明

### SSL/SNI 兼容性

本插件使用自定义的 HTTPS 客户端，禁用了 SNI（Server Name Indication），以解决某些 FileBay 服务器的 SSL 配置问题。这确保了插件可以在各种环境下稳定运行。

### 文件编码

- **文本文件**: 支持 UTF-8、GBK、GB2312 等常见编码
- **二进制文件**: 使用 Base64 编码传输
- **自动检测**: 插件会尝试自动处理编码问题

### 版本控制

- 所有文件操作都会创建 Git 提交
- 更新文件时会自动获取当前文件的 SHA
- 支持自定义提交信息

## 故障排除

### 问题 1: 无法连接到 FileBay

**解决方案**:
- 检查 FileBay URL 是否正确
- 确认网络连接正常
- 验证 Access Token 是否有效

### 问题 2: 文件读取失败

**解决方案**:
- 确认文件路径正确（相对于仓库根目录）
- 检查文件是否存在
- 尝试使用 list_files 工具查看目录结构

### 问题 3: 文件写入失败

**解决方案**:
- 确认有写入权限
- 检查分支名称是否正确
- 确保提交信息不为空

## 开发信息

- **作者**: CheersAI
- **版本**: 0.0.1
- **许可**: MIT
- **支持**: 如有问题，请联系技术支持

## 更新日志

### v0.0.1 (2026-05-10)
- 初始版本发布
- 实现基本的文件读取、写入和列表功能
- 支持文本和二进制文件
- 兼容 FileBay SSL 配置

## 贡献

欢迎提交问题和改进建议！

## 许可证

MIT License
