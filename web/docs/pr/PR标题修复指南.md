# PR 标题修复指南

## 问题描述

GitHub PR 验证失败，错误信息：
```
Error: no release type found in pull request title "V1.2"
```

## 原因

PR 标题 "V1.2" 不符合 [Conventional Commits](https://www.conventionalcommits.org/) 规范。

## 解决方案

### 方法 1: 在 GitHub 上修改 PR 标题（推荐）

1. 打开 PR 页面：https://github.com/fyp1984/CheersAI-Desktop/pull/22
2. 点击 PR 标题旁边的 "Edit" 按钮
3. 修改标题为以下任一格式：

#### 推荐标题（按优先级）：

**选项 1: 强调新功能**
```
feat: Desktop SSO 登录功能集成 (V1.2)
```

**选项 2: 强调功能完成**
```
feat: 完成 Desktop SSO OAuth 登录功能
```

**选项 3: 详细描述**
```
feat: 实现 Desktop SSO 登录、自动创建账户和 FileBay 集成
```

**选项 4: 简洁版**
```
feat(auth): Desktop SSO 登录集成
```

### 方法 2: 关闭当前 PR，创建新的 PR

如果无法编辑标题，可以：

1. 关闭当前 PR #22
2. 创建新的 PR，使用正确的标题
3. 使用以下命令：

```bash
# 确保在 V1.2 分支
git checkout V1.2

# 创建新的 PR（通过 GitHub CLI，如果已安装）
gh pr create \
  --base master \
  --head V1.2 \
  --title "feat: Desktop SSO 登录功能集成 (V1.2)" \
  --body-file PULL_REQUEST.md
```

或者直接访问：
```
https://github.com/fyp1984/CheersAI-Desktop/compare/master...V1.2
```

## Conventional Commits 规范

### 常用前缀

| 前缀 | 说明 | 示例 |
|------|------|------|
| `feat:` | 新功能 | `feat: 添加用户登录功能` |
| `fix:` | 修复 Bug | `fix: 修复登录失败问题` |
| `docs:` | 文档更新 | `docs: 更新 API 文档` |
| `style:` | 代码格式（不影响功能） | `style: 格式化代码` |
| `refactor:` | 重构 | `refactor: 重构登录模块` |
| `perf:` | 性能优化 | `perf: 优化查询性能` |
| `test:` | 测试相关 | `test: 添加单元测试` |
| `chore:` | 构建/工具相关 | `chore: 更新依赖` |
| `ci:` | CI/CD 相关 | `ci: 更新 GitHub Actions` |
| `build:` | 构建系统 | `build: 更新 webpack 配置` |
| `revert:` | 回滚 | `revert: 回滚上次提交` |

### 格式规范

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**示例**：
```
feat(auth): 实现 Desktop SSO 登录

- 添加 OAuth 2.0 授权流程
- 实现自动创建账户和工作空间
- 集成 FileBay 文件同步
- 优化 CORS 配置

Closes #123
```

## 推荐的 PR 标题

根据你的 PR 内容，推荐使用：

### 最佳选择
```
feat: Desktop SSO 登录功能集成 (V1.2)
```

**理由**：
- ✅ 符合 Conventional Commits 规范
- ✅ 清晰说明功能类型（feat）
- ✅ 简洁明了
- ✅ 包含版本号（V1.2）

### 备选方案

**方案 1: 详细版**
```
feat(auth): 实现 Desktop SSO OAuth 登录和自动账户创建
```

**方案 2: 简洁版**
```
feat: 添加 Desktop SSO 登录支持
```

**方案 3: 技术版**
```
feat(sso): 集成 OAuth 2.0 Desktop SSO 登录流程
```

## 快速修复步骤

1. **访问 PR 页面**
   ```
   https://github.com/fyp1984/CheersAI-Desktop/pull/22
   ```

2. **点击标题旁的 "Edit" 按钮**

3. **修改标题为**
   ```
   feat: Desktop SSO 登录功能集成 (V1.2)
   ```

4. **保存**

5. **等待 CI 重新运行**

## 验证

修改后，GitHub Actions 会自动重新运行验证。你应该看到：
- ✅ Validate PR title - 通过
- ✅ 其他检查项

## 注意事项

1. **不要修改分支名称**
   - 分支名 `V1.2` 可以保持不变
   - 只需要修改 PR 标题

2. **不需要重新提交代码**
   - 只修改 PR 标题即可
   - 代码保持不变

3. **标题修改后立即生效**
   - GitHub Actions 会自动重新验证
   - 通常 1-2 分钟内完成

## 相关资源

- [Conventional Commits 规范](https://www.conventionalcommits.org/)
- [Angular Commit 规范](https://github.com/angular/angular/blob/main/CONTRIBUTING.md#commit)
- [Semantic Release](https://semantic-release.gitbook.io/)

---

**修复优先级**: 🔴 高（阻止 PR 合并）  
**预计修复时间**: < 1 分钟  
**难度**: ⭐ 简单
