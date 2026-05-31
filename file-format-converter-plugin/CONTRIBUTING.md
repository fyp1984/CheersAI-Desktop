# 贡献指南

感谢你考虑为文件格式转换插件做出贡献！

## 如何贡献

### 报告 Bug

如果你发现了 bug，请创建一个 Issue 并包含以下信息：

1. **Bug 描述** - 清晰简洁地描述问题
2. **重现步骤** - 详细的重现步骤
3. **期望行为** - 你期望发生什么
4. **实际行为** - 实际发生了什么
5. **环境信息** - 操作系统、Python 版本等
6. **截图** - 如果适用，添加截图

### 提出新功能

如果你有新功能的想法：

1. 先检查是否已有相关 Issue
2. 创建一个新的 Feature Request Issue
3. 详细描述功能和使用场景
4. 说明为什么这个功能有用

### 提交代码

1. **Fork 项目**
   ```bash
   git clone https://github.com/your-username/file-format-converter-plugin.git
   cd file-format-converter-plugin
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **编写代码**
   - 遵循现有的代码风格
   - 添加必要的注释
   - 更新相关文档

4. **测试**
   ```bash
   # 运行测试
   python -m pytest tests/
   
   # 检查代码风格
   flake8 .
   black .
   ```

5. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加新功能描述"
   ```

6. **推送到 GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **创建 Pull Request**
   - 提供清晰的 PR 描述
   - 关联相关的 Issue
   - 等待代码审查

## 代码规范

### Python 代码风格

- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- 使用 [Black](https://github.com/psf/black) 格式化代码
- 使用 [Flake8](https://flake8.pycqa.org/) 检查代码质量
- 使用类型提示（Type Hints）

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具相关

示例：
```
feat: 添加 EPUB 格式支持
fix: 修复 PDF 中文显示问题
docs: 更新安装指南
```

### 文档规范

- 使用清晰简洁的语言
- 提供代码示例
- 保持中英文文档同步
- 更新 CHANGELOG.md

## 开发环境设置

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖
```

### 2. 安装开发工具

```bash
pip install black flake8 pytest pytest-cov mypy
```

### 3. 配置 Git Hooks

```bash
# 安装 pre-commit
pip install pre-commit
pre-commit install
```

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_word_export.py

# 生成覆盖率报告
pytest --cov=. --cov-report=html
```

### 编写测试

- 为新功能编写单元测试
- 确保测试覆盖率 > 80%
- 使用有意义的测试名称

## 发布流程

1. 更新版本号（manifest.yaml）
2. 更新 CHANGELOG.md
3. 创建 Git tag
4. 打包插件
5. 发布到插件市场

## 获取帮助

- 查看 [README.md](README.md)
- 查看现有的 Issues
- 在 Discussions 中提问

## 行为准则

- 尊重所有贡献者
- 保持友好和专业
- 接受建设性的批评
- 关注对项目最有利的事情

感谢你的贡献！🎉
