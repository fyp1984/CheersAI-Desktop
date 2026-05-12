# FileBay Sync 插件安装指南

## 前置要求

1. **Dify 实例**: 确保你有一个运行中的 Dify 实例
2. **FileBay 账号**: 需要有 FileBay 账号和仓库访问权限
3. **Python 环境**: Python 3.12+ (仅开发调试时需要)

## 快速安装（推荐）

### 步骤 1: 下载插件开发工具

从 Dify 官方仓库下载插件开发工具：

```bash
# macOS (ARM64)
wget https://github.com/langgenius/dify-plugin-daemon/releases/latest/download/dify-plugin-darwin-arm64

# macOS (x64)
wget https://github.com/langgenius/dify-plugin-daemon/releases/latest/download/dify-plugin-darwin-amd64

# Linux (x64)
wget https://github.com/langgenius/dify-plugin-daemon/releases/latest/download/dify-plugin-linux-amd64

# Windows (x64)
# 下载 dify-plugin-windows-amd64.exe
```

重命名并添加执行权限：

```bash
# macOS/Linux
mv dify-plugin-* dify
chmod +x dify
sudo mv dify /usr/local/bin/
```

### 步骤 2: 打包插件

在项目根目录执行：

```bash
cd filebay_plugin
dify plugin package .
```

这将生成 `filebay_plugin.difypkg` 文件。

### 步骤 3: 安装到 Dify

#### 方法 A: Web 界面安装

1. 登录 Dify 管理后台
2. 导航到 **工作空间设置** → **插件**
3. 点击 **安装插件** 按钮
4. 选择 `filebay_plugin.difypkg` 文件上传
5. 等待安装完成

#### 方法 B: 命令行安装

```bash
# 使用 Dify CLI 安装
dify plugin install filebay_plugin.difypkg
```

### 步骤 4: 配置插件凭据

安装完成后，需要配置 FileBay 连接信息：

1. 在插件列表中找到 **FileBay Sync**
2. 点击 **配置** 按钮
3. 填写以下信息：

| 字段 | 说明 | 示例 |
|------|------|------|
| FileBay URL | FileBay 实例地址 | `https://uat-filebay.cheersai.cloud` |
| Access Token | 访问令牌 | 从 FileBay 设置中生成 |
| Repository Owner | 仓库所有者 | `your-username` |
| Repository Name | 仓库名称 | `workspace` |
| Branch Name | 分支名称（可选） | `main` |

4. 点击 **验证** 测试连接
5. 点击 **保存** 完成配置

## 开发调试安装

如果你需要修改插件代码或进行调试：

### 步骤 1: 获取远程调试信息

1. 在 Dify 管理后台，进入 **插件管理**
2. 点击 **远程调试** 标签
3. 复制显示的调试地址和 Key

### 步骤 2: 配置环境变量

```bash
cd filebay_plugin
cp .env.example .env
```

编辑 `.env` 文件：

```env
INSTALL_METHOD=remote
REMOTE_INSTALL_URL=debug.dify.ai:5003
REMOTE_INSTALL_KEY=your-debug-key-here
```

### 步骤 3: 安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 4: 运行插件

```bash
python -m main
```

插件将以调试模式运行，你可以在 Dify 中实时测试修改。

## 获取 FileBay Access Token

### 方法 1: 通过 Web 界面

1. 登录 FileBay
2. 点击右上角头像 → **设置**
3. 导航到 **应用** → **访问令牌**
4. 点击 **生成新令牌**
5. 输入令牌名称（例如：`dify-plugin`）
6. 选择权限：
   - ✅ `read:repository`
   - ✅ `write:repository`
7. 点击 **生成令牌**
8. 复制生成的令牌（只显示一次！）

### 方法 2: 使用现有配置

如果你已经在 Dify 系统中配置了 FileBay，可以从 Account 配置中获取：

```python
# 在 Dify 后台执行
from models.account import Account
from extensions.ext_database import db

account = db.session.query(Account).filter_by(email='your-email@example.com').first()
config = account.custom_config_dict
print(f"Token: {config.get('gitea_token')}")
```

## 验证安装

### 测试 1: 列出文件

创建一个简单的 Agent 应用，发送消息：

```
请列出仓库根目录下的所有文件
```

Agent 应该调用 `list_files` 工具并返回文件列表。

### 测试 2: 读取文件

```
请读取 README.md 文件的内容
```

Agent 应该调用 `read_file` 工具并返回文件内容。

### 测试 3: 写入文件

```
请创建一个新文件 test.txt，内容为 "Hello from Dify!"
```

Agent 应该调用 `write_file` 工具，然后你可以在 FileBay 中看到新文件。

## 常见问题

### Q1: 插件安装失败

**A**: 检查以下几点：
- Dify 版本是否支持插件（需要 1.0+）
- 插件包是否完整（重新打包）
- 查看 Dify 日志获取详细错误信息

### Q2: 无法连接到 FileBay

**A**: 
- 确认 FileBay URL 可以访问
- 检查 Access Token 是否有效
- 确认仓库名称和所有者正确
- 查看网络防火墙设置

### Q3: 文件读取返回 404

**A**:
- 确认文件路径正确（相对于仓库根目录）
- 检查分支名称是否正确
- 使用 `list_files` 工具查看实际的文件结构

### Q4: 文件写入失败

**A**:
- 确认 Access Token 有写入权限
- 检查目标路径是否存在（会自动创建目录）
- 确认分支存在且可写入

### Q5: 调试模式无法连接

**A**:
- 确认 REMOTE_INSTALL_URL 和 KEY 正确
- 检查网络连接
- 确认 Dify 实例的调试功能已启用

## 卸载插件

### 通过 Web 界面

1. 进入 **插件管理**
2. 找到 **FileBay Sync** 插件
3. 点击 **卸载** 按钮
4. 确认卸载

### 通过命令行

```bash
dify plugin uninstall filebay_sync
```

## 更新插件

1. 下载新版本的插件包
2. 在插件管理页面点击 **更新**
3. 上传新的 `.difypkg` 文件
4. 等待更新完成
5. 重新配置凭据（如果需要）

## 技术支持

如果遇到问题：

1. 查看 [README.md](README.md) 了解功能详情
2. 检查 Dify 日志：`docker logs dify-api`
3. 查看插件日志（如果在调试模式）
4. 联系技术支持团队

## 下一步

- 阅读 [README.md](README.md) 了解详细功能
- 查看使用示例
- 在 Agent 或 Workflow 中集成插件
- 探索更多高级用法

祝使用愉快！🎉
