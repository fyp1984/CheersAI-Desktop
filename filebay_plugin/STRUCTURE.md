# FileBay Sync 插件项目结构

```
filebay_plugin/
├── manifest.yaml              # 插件清单文件（必需）
├── main.py                    # 插件入口文件（必需）
├── requirements.txt           # Python 依赖
├── .env.example              # 环境变量示例
├── README.md                 # 项目说明文档
├── INSTALL.md                # 安装指南
├── STRUCTURE.md              # 本文件
│
├── _assets/                  # 资源文件目录
│   └── icon.svg             # 插件图标
│
├── provider/                 # 工具提供者目录
│   ├── filebay.yaml         # 提供者配置文件
│   └── filebay.py           # 提供者实现代码
│
└── tools/                    # 工具目录
    ├── read_file.yaml       # 读取文件工具配置
    ├── read_file.py         # 读取文件工具实现
    ├── write_file.yaml      # 写入文件工具配置
    ├── write_file.py        # 写入文件工具实现
    ├── list_files.yaml      # 列出文件工具配置
    └── list_files.py        # 列出文件工具实现
```

## 文件说明

### 核心文件

#### `manifest.yaml`
插件的清单文件，定义插件的基本信息：
- 插件名称、版本、作者
- 插件类型和权限
- 包含的工具提供者列表
- 支持的架构平台

#### `main.py`
插件的入口文件，负责：
- 初始化插件环境
- 启动插件服务
- 处理插件生命周期

#### `requirements.txt`
Python 依赖列表，包含：
- `dify-plugin`: Dify 插件 SDK
- 其他必要的第三方库

### 提供者文件

#### `provider/filebay.yaml`
工具提供者的配置文件，定义：
- 提供者的基本信息（名称、描述、图标）
- 凭据配置（FileBay URL、Token 等）
- 包含的工具列表
- 实现代码的路径

#### `provider/filebay.py`
提供者的实现代码，负责：
- 验证用户提供的凭据
- 初始化工具实例
- 处理认证逻辑

### 工具文件

每个工具包含两个文件：

#### `tools/[tool_name].yaml`
工具的配置文件，定义：
- 工具的基本信息（名称、描述）
- 输入参数定义
- 参数类型和验证规则
- 实现代码的路径

#### `tools/[tool_name].py`
工具的实现代码，包含：
- 工具类定义（继承自 `Tool`）
- `_invoke` 方法实现
- 业务逻辑处理
- 错误处理

### 资源文件

#### `_assets/icon.svg`
插件的图标文件：
- SVG 格式
- 推荐尺寸：100x100
- 用于在 Dify 界面中显示

### 文档文件

#### `README.md`
项目说明文档，包含：
- 功能介绍
- 使用示例
- 技术说明
- 故障排除

#### `INSTALL.md`
安装指南，包含：
- 详细的安装步骤
- 配置说明
- 常见问题解答

## 代码组织原则

### 1. 模块化设计
- 每个工具独立实现
- 共享代码提取到公共模块
- 清晰的职责划分

### 2. 配置与代码分离
- YAML 文件定义接口
- Python 文件实现逻辑
- 便于维护和扩展

### 3. 错误处理
- 统一的错误处理机制
- 友好的错误提示
- 详细的日志记录

### 4. 文档完善
- 代码注释清晰
- 文档结构合理
- 示例丰富实用

## 扩展指南

### 添加新工具

1. 在 `tools/` 目录创建新的 YAML 和 PY 文件
2. 在 YAML 中定义工具接口
3. 在 PY 中实现工具逻辑
4. 在 `provider/filebay.yaml` 中注册新工具

示例：

```yaml
# tools/delete_file.yaml
identity:
  name: delete_file
  author: CheersAI
  label:
    en_US: Delete File
    zh_Hans: 删除文件
# ... 其他配置
```

```python
# tools/delete_file.py
from dify_plugin import Tool

class DeleteFileTool(Tool):
    def _invoke(self, tool_parameters):
        # 实现删除逻辑
        pass
```

### 修改凭据配置

在 `provider/filebay.yaml` 的 `credentials_for_provider` 部分添加新字段：

```yaml
credentials_for_provider:
  new_field:
    type: text-input
    required: false
    label:
      en_US: New Field
      zh_Hans: 新字段
```

### 更新图标

替换 `_assets/icon.svg` 文件，确保：
- 使用 SVG 格式
- 尺寸适中（推荐 100x100）
- 颜色搭配合理

## 开发工作流

### 1. 本地开发
```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境
cp .env.example .env
# 编辑 .env 文件

# 运行插件
python -m main
```

### 2. 测试
- 在 Dify 中创建测试应用
- 调用插件工具
- 验证功能正确性

### 3. 打包发布
```bash
# 打包插件
dify plugin package .

# 生成 filebay_plugin.difypkg
```

### 4. 安装测试
- 上传到 Dify 实例
- 配置凭据
- 完整功能测试

## 最佳实践

### 代码质量
- 遵循 PEP 8 编码规范
- 添加类型注解
- 编写单元测试

### 安全性
- 敏感信息使用 `secret-input` 类型
- 验证所有用户输入
- 使用 HTTPS 连接

### 性能
- 合理设置超时时间
- 避免阻塞操作
- 优化大文件处理

### 用户体验
- 提供清晰的错误提示
- 支持多语言
- 文档详细完整

## 版本管理

### 版本号规则
遵循语义化版本（Semantic Versioning）：
- 主版本号：不兼容的 API 修改
- 次版本号：向下兼容的功能性新增
- 修订号：向下兼容的问题修正

### 更新 manifest.yaml
```yaml
version: 0.1.0  # 更新版本号
meta:
  version: 0.1.0  # 同步更新
```

## 贡献指南

欢迎贡献代码！请遵循：
1. Fork 项目
2. 创建特性分支
3. 提交代码
4. 发起 Pull Request

## 许可证

MIT License - 详见 LICENSE 文件
