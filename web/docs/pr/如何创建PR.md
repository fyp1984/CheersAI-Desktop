# 如何在 GitHub 上创建 Pull Request

## 方法 1: 通过 GitHub 网页界面（推荐）

### 步骤 1: 访问仓库
打开浏览器，访问：
```
https://github.com/fyp1984/CheersAI-Desktop
```

### 步骤 2: 创建 Pull Request
1. 你会看到一个黄色的提示条，显示 "V1.2 had recent pushes"
2. 点击 **"Compare & pull request"** 按钮

   或者：
   
3. 点击顶部的 **"Pull requests"** 标签
4. 点击绿色的 **"New pull request"** 按钮
5. 在 "base" 下拉菜单选择 **master**
6. 在 "compare" 下拉菜单选择 **V1.2**

### 步骤 3: 填写 PR 信息

**标题**:
```
feat: 完成 Desktop SSO 登录功能集成
```

**描述**: 复制 `PULL_REQUEST.md` 的内容，或者使用以下简化版本：

```markdown
## 概述
实现了完整的 Desktop SSO OAuth 登录功能，允许用户通过企业 SSO 系统登录 CheersAI Desktop。

## 主要变更
- ✅ 新增 Desktop SSO 登录端点 (`/auth/desktop-sso/login`)
- ✅ 实现 OAuth 2.0 授权码流程
- ✅ 自动创建账户和工作空间
- ✅ 优化 CORS 配置
- ✅ 完善错误处理和日志

## 测试状态
- ✅ SSO 授权流程正常
- ✅ Token exchange 成功
- ✅ 后端 CORS 配置正确
- ⏳ 待完整端到端测试

## 文档
详见 `PULL_REQUEST.md` 和 `SSO登录-测试步骤.md`

## 审核要点
- 代码质量和规范
- 安全性（State 验证、httpOnly cookies）
- CORS 配置
- 向后兼容性
```

### 步骤 4: 设置审核者
1. 在右侧的 "Reviewers" 部分，点击齿轮图标
2. 选择管理员或团队成员作为审核者

### 步骤 5: 添加标签（可选）
在右侧的 "Labels" 部分，添加相关标签：
- `enhancement` - 新功能
- `authentication` - 认证相关
- `needs-review` - 需要审核

### 步骤 6: 创建 PR
点击绿色的 **"Create pull request"** 按钮

---

## 方法 2: 通过 GitHub CLI（如果已安装）

```bash
gh pr create \
  --base master \
  --head V1.2 \
  --title "feat: 完成 Desktop SSO 登录功能集成" \
  --body-file PULL_REQUEST.md \
  --reviewer @管理员用户名
```

---

## 方法 3: 通过 Git 命令行（生成 URL）

```bash
# 这个命令会输出一个 URL，直接在浏览器中打开
git push origin V1.2 -o merge_request.create \
  -o merge_request.target=master \
  -o merge_request.title="feat: 完成 Desktop SSO 登录功能集成"
```

---

## PR 创建后

### 1. 等待审核
管理员会收到通知，并审核你的代码。

### 2. 响应反馈
如果管理员提出修改建议：
1. 在本地修改代码
2. 提交更改：`git commit -m "fix: 根据审核意见修改"`
3. 推送：`git push origin V1.2`
4. PR 会自动更新

### 3. 合并
审核通过后，管理员会合并 PR 到 master 分支。

---

## 快速链接

**直接创建 PR**:
```
https://github.com/fyp1984/CheersAI-Desktop/compare/master...V1.2
```

**查看所有 PR**:
```
https://github.com/fyp1984/CheersAI-Desktop/pulls
```

---

## 注意事项

1. ✅ 代码已推送到远程仓库（V1.2 分支）
2. ✅ Commit 信息清晰明确
3. ✅ 包含详细的文档和测试指南
4. ⚠️ 确保 `.env` 文件中的敏感信息已脱敏（如果需要）
5. ⚠️ 提醒管理员查看 `PULL_REQUEST.md` 了解完整信息

---

**当前状态**: ✅ 代码已推送，可以立即创建 PR
