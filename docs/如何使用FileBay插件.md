# 如何使用 FileBay 插件

## 插件的作用

FileBay 插件为 Dify 的 **Agent（智能体）** 提供了三个工具：

1. **read_file** - 从 FileBay 读取文件内容
2. **write_file** - 将内容写入 FileBay
3. **list_files** - 列出 FileBay 中的文件

## 使用步骤

### 第一步：配置插件凭证

1. 访问 http://localhost:3000
2. 点击右上角头像 → **设置**
3. 找到 **插件** 或 **工具** 部分
4. 找到 **FileBay Sync** 插件
5. 点击配置，填入以下信息：
   - **FileBay URL**: `https://uat-filebay.cheersai.cloud`
   - **Access Token**: （需要从 FileBay 生成个人访问令牌）
   - **Repository Owner**: 你的 FileBay 用户名
   - **Repository Name**: `workspace`（或其他仓库名）
   - **Branch Name**: `main`

### 第二步：创建 Agent 应用

1. 在 Dify 首页点击 **创建应用**
2. 选择 **Agent** 类型（不是 Chatbot 或 Workflow）
3. 给应用命名，例如 "FileBay 助手"

### 第三步：为 Agent 添加工具

1. 在 Agent 编辑页面，找到 **工具** 部分
2. 点击 **添加工具**
3. 在工具列表中找到 **FileBay Sync** 插件
4. 勾选你需要的工具：
   - ✅ read_file
   - ✅ write_file
   - ✅ list_files
5. 点击确认

### 第四步：配置 Agent 提示词

在 Agent 的系统提示词中，可以这样写：

```
你是一个文件管理助手，可以帮助用户管理 FileBay 中的文件。

你可以使用以下工具：
- read_file: 读取 FileBay 中的文件内容
- write_file: 将内容写入 FileBay
- list_files: 列出指定目录下的文件

当用户要求读取、写入或查看文件时，主动使用这些工具。
```

### 第五步：使用 Agent

现在你可以和 Agent 对话，例如：

**用户**: "帮我读取 README.md 文件"
**Agent**: （自动调用 read_file 工具，传入 path="README.md"）

**用户**: "列出根目录下的所有文件"
**Agent**: （自动调用 list_files 工具，传入 path=""）

**用户**: "创建一个新文件 test.txt，内容是 Hello World"
**Agent**: （自动调用 write_file 工具，传入 path="test.txt", content="Hello World"）

## 为什么普通应用看不到插件功能？

- **Chatbot 应用**：只能进行对话，不能使用工具
- **Workflow 应用**：可以使用工具，但需要在工作流中手动配置工具节点
- **Agent 应用**：可以根据对话内容**自动决定**何时使用哪个工具

## 获取 FileBay Access Token

1. 登录 FileBay: https://uat-filebay.cheersai.cloud
2. 点击右上角头像 → **设置**
3. 找到 **访问令牌** 或 **Personal Access Tokens**
4. 点击 **生成新令牌**
5. 给令牌命名（如 "Dify Plugin"）
6. 选择权限：
   - ✅ repo（仓库读写权限）
7. 点击生成
8. **复制令牌**（只显示一次，请妥善保存）

## 示例对话

```
用户：帮我看看项目根目录有哪些文件？

Agent：好的，让我查看一下。
[调用 list_files 工具，path=""]
根目录下有以下文件：
- README.md
- package.json
- src/
- docs/

用户：读取 README.md 的内容

Agent：好的，让我读取这个文件。
[调用 read_file 工具，path="README.md"]
README.md 的内容如下：
# 项目名称
这是一个示例项目...

用户：在 docs 目录下创建一个 API.md 文件，写入 API 文档的标题

Agent：好的，我来创建这个文件。
[调用 write_file 工具，path="docs/API.md", content="# API 文档\n\n"]
文件已创建成功！
```

## 注意事项

1. **插件不会在界面上显示按钮** - 这是 Dify 插件的设计方式
2. **必须使用 Agent 类型的应用** - 其他类型无法自动调用工具
3. **需要配置凭证** - 插件需要 FileBay 的访问令牌才能工作
4. **Agent 会自动决定何时使用工具** - 你只需要用自然语言描述需求

## 如果找不到插件配置

如果在设置中找不到插件配置入口，可能需要：

1. 在创建 Agent 时，直接在工具选择界面配置
2. 或者在 Agent 编辑页面，点击工具 → 配置凭证

## 总结

FileBay 插件的价值在于：
- ✅ Agent 可以**自动**读取 FileBay 中的文件作为上下文
- ✅ Agent 生成的内容可以**自动**保存到 FileBay
- ✅ 用户只需用自然语言描述需求，无需手动操作

这就是为什么它是一个"插件"而不是一个"按钮"的原因。
