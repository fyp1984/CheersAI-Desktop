# 重新创建 PR 指南

## 🎯 目标
创建一个符合 Conventional Commits 规范的新 PR

## 📝 PR 信息

### 标题（必须使用）
```
feat: Desktop SSO 登录功能集成 (V1.2)
```

### 描述
使用 `新PR说明.md` 的内容

## 🚀 创建步骤

### 方法 1: 通过 GitHub 网页（推荐）

#### 步骤 1: 访问创建 PR 页面
打开浏览器，访问：
```
https://github.com/fyp1984/CheersAI-Desktop/compare/master...V1.2
```

#### 步骤 2: 填写 PR 信息

**标题**（复制使用）:
```
feat: Desktop SSO 登录功能集成 (V1.2)
```

**描述**（复制 `新PR说明.md` 的内容，或使用简化版）:

```markdown
## 概述
实现了完整的 Desktop SSO OAuth 登录功能，允许用户通过企业 SSO 系统登录 CheersAI Desktop。

## 主要变更
- ✅ 新增 Desktop SSO 登录端点 (`/auth/desktop-sso/login`)
- ✅ 实现 OAuth 2.0 授权码流程
- ✅ 自动创建账户和工作空间
- ✅ 优化 CORS 配置
- ✅ 修复 Weaviate 端口冲突
- ✅ 与 master 分支同步

## 技术细节
- **SSO URL**: https://uat-sso.cheersai.cloud
- **Protocol**: OAuth 2.0
- **安全性**: State 验证、httpOnly cookies、CORS 配置

## 测试状态
- ✅ SSO 授权流程正常
- ✅ Token exchange 成功
- ✅ 后端 CORS 配置正确
- ⏳ 待完整端到端测试

## 文档
详见 `新PR说明.md` 和 `SSO登录-测试步骤.md`

## 变更统计
- 76 files changed
- 3590 insertions(+)
- 4739 deletions(-)

## 审核要点
- 代码质量和规范
- 安全性（State 验证、httpOnly cookies）
- CORS 配置
- 向后兼容性
- 与 master 分支同步
```

#### 步骤 3: 设置审核者
1. 在右侧的 "Reviewers" 部分，点击齿轮图标
2. 选择管理员或团队成员作为审核者

#### 步骤 4: 添加标签（可选）
在右侧的 "Labels" 部分，添加相关标签：
- `enhancement` - 新功能
- `authentication` - 认证相关

#### 步骤 5: 创建 PR
点击绿色的 **"Create pull request"** 按钮

---

### 方法 2: 通过 GitHub CLI（如果已安装）

```bash
gh pr create \
  --base master \
  --head V1.2 \
  --title "feat: Desktop SSO 登录功能集成 (V1.2)" \
  --body-file 新PR说明.md \
  --reviewer @管理员用户名
```

---

### 方法 3: 关闭旧 PR 后创建新 PR

如果旧的 PR #22 还存在：

#### 步骤 1: 关闭旧 PR
1. 访问 https://github.com/fyp1984/CheersAI-Desktop/pull/22
2. 滚动到底部
3. 点击 "Close pull request"
4. 添加评论：
   ```
   关闭此 PR，将使用符合规范的标题重新创建。
   新 PR 标题：feat: Desktop SSO 登录功能集成 (V1.2)
   ```

#### 步骤 2: 创建新 PR
按照方法 1 的步骤创建新 PR

---

## ✅ 验证清单

创建 PR 后，确认以下内容：

### PR 标题
- [ ] 以 `feat:` 开头
- [ ] 清晰描述功能
- [ ] 包含版本号 (V1.2)

### PR 描述
- [ ] 包含概述
- [ ] 列出主要变更
- [ ] 说明测试状态
- [ ] 提供文档链接

### GitHub Actions
- [ ] "Validate PR title" 检查通过 ✅
- [ ] 其他 CI 检查运行正常

### 审核者
- [ ] 已添加审核者
- [ ] 审核者收到通知

---

## 🎯 预期结果

创建成功后，你应该看到：

1. **PR 页面**
   - 标题：`feat: Desktop SSO 登录功能集成 (V1.2)`
   - 状态：Open
   - 检查：✅ All checks passed

2. **GitHub Actions**
   - ✅ Validate PR title
   - ✅ 其他检查项

3. **通知**
   - 审核者收到邮件通知
   - 相关人员收到 GitHub 通知

---

## 🔗 快速链接

**创建 PR**:
```
https://github.com/fyp1984/CheersAI-Desktop/compare/master...V1.2
```

**查看所有 PR**:
```
https://github.com/fyp1984/CheersAI-Desktop/pulls
```

**旧 PR #22**（如需关闭）:
```
https://github.com/fyp1984/CheersAI-Desktop/pull/22
```

---

## 💡 提示

1. **标题最重要**
   - 必须以 `feat:` 开头
   - 这是验证失败的主要原因

2. **描述可以简化**
   - 核心信息即可
   - 详细内容可以链接到文档

3. **不要修改代码**
   - 代码已经是最新的
   - 只需要创建新 PR

4. **验证会自动运行**
   - 创建 PR 后自动触发
   - 1-2 分钟内完成

---

**准备好了吗？** 点击下面的链接开始创建 PR：

👉 https://github.com/fyp1984/CheersAI-Desktop/compare/master...V1.2

记得使用标题：`feat: Desktop SSO 登录功能集成 (V1.2)`
