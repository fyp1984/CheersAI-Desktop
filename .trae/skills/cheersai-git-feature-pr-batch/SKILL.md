---
name: "cheersai-git-feature-pr-batch"
description: "Splits local repo changes by feature, creates feature branches, commits, pushes, and opens PRs to master. Invoke when user gives a repo and base branch for batched Git delivery."
---

# CheersAI Git Feature PR Batch

## Purpose

在给定仓库路径和目标基线分支后，自动完成以下闭环：

1. 梳理本地未提交改动
2. 按功能拆分为可独立评审的变更组
3. 为每组创建 feature/fix/refactor/chore 分支
4. 仅暂存对应文件并提交
5. 执行最小必要校验
6. 推送远端分支
7. 创建指向基线分支的 Pull Request
8. 输出汇总：分组、分支、提交、校验、PR

## When To Invoke

在以下场景调用：

- 用户只给仓库名或仓库路径，并要求你整理本地变更后分功能提交
- 用户要求从当前脏工作区中拆分多个 Feature/Fix 分支
- 用户要求自动创建 PR 指向 `master` 或其他基线分支
- 用户希望后续复用同一套 Git 提交流程，无需重复解释步骤

不要在以下场景调用：

- 用户只要一条简单的 `git commit` 命令
- 仓库没有本地改动，也没有要拆分的功能
- 用户明确要求直接提交到 `master`

## Inputs

默认输入最少只需要两项：

- `repo`: 本地仓库绝对路径
- `base`: 目标基线分支，例如 `master`

可选输入：

- `repo_name`: 仓库名
- `branch_prefix_policy`: 是否偏向 `feature/fix/refactor/chore`
- `validation_scope`: 是否跑 lint/test/build 或仅跑目标校验

## Standard Flow

### 1. Inspect Repository

必须先检查：

```bash
git status --short
git branch --show-current
git remote -v
git diff --stat
```

目标：

- 确认仓库是 Git 仓库
- 确认当前分支与远端仓库
- 列出所有变更文件

### 2. Group Changes By Feature

按以下原则分组：

- 同一用户问题闭环的文件放一起
- 同一前后端链路放一起
- 能独立回滚的改动单独一组
- 环境/工具/文档类改动尽量不要与业务功能混合

每组必须产出：

- 组名
- 分支名
- Conventional Commit 提交标题
- 文件清单
- 最小校验方案

### 3. Preserve Dirty State Safely

当本地工作区是脏的，且需要拆成多个分支时：

1. 使用 `git stash push -u` 保存全部改动
2. 以基线分支为基础创建每个功能分支
3. 从 stash 中仅恢复当前功能组对应文件
4. 完成提交和推送
5. 继续处理下一组

不要把全部改动一次性带入所有分支。

### 4. Branch Naming Rules

- 新功能：`feature/<scope>-<topic>`
- 缺陷修复：`fix/<scope>-<topic>`
- 重构：`refactor/<scope>-<topic>`
- 维护/流程：`chore/<scope>-<topic>`

规则：

- 全小写
- 使用短横线
- 尽量体现模块和目标

### 5. Stage Only Intended Files

严禁无脑 `git add .`，除非当前分支工作区只有该组文件。

优先使用：

```bash
git add path/to/file1 path/to/file2
```

提交前必须复查：

```bash
git status --short
git diff --cached --stat
git diff --cached
```

### 6. Validation Policy

按“最小必要且足够可信”的原则校验：

- 前端改动：优先跑目标文件 ESLint / Vitest / 必要构建
- 后端改动：优先跑目标测试、语法检查、必要迁移校验
- 脚本类改动：优先跑脚本静态检查或目标命令验证

如果仓库已有明确规则，优先遵循仓库规则。

### 7. Commit Format

统一使用 Conventional Commit：

```text
<type>(<scope>): <summary>
```

示例：

```text
fix(sso): support oauth proxy routes and PKCE token exchange
fix(runtime): restore standalone assets and loading fallback
fix(plugins): improve marketplace stability and provider feedback
chore(skill): add reusable git feature pr batch workflow
```

### 8. Push And Create PR

首次推送：

```bash
git push -u origin <branch>
```

PR 必须指向基线分支，例如：

```text
<branch> -> master
```

PR 描述必须包含：

- Summary
- Why
- Files
- Validation
- Risk
- Rollback

### 9. Final Summary Format

输出时按以下结构汇总：

1. 仓库与基线分支
2. 变更分组结果
3. 每组分支名
4. 每组提交信息
5. 每组校验结果
6. 每组推送状态
7. 每组 PR 链接
8. 剩余未处理改动

## PR Body Template

```markdown
## Summary
- 本 PR 做了什么

## Why
- 解决什么问题

## Files
- 涉及哪些模块

## Validation
- [ ] lint
- [ ] test
- [ ] build
- [ ] manual

## Risk
- 可能影响点

## Rollback
- 回滚方式
```

## Decision Heuristics

- 功能改动过大时，优先拆成多个 PR，而不是一个超大 PR
- 同一问题的前后端改动优先同 PR
- 文档只在能帮助评审理解实现时一并提交
- 纯流程资产或 Skill 更新单独走 `chore`

## Expected Outcome

当用户只提供“仓库名/路径 + 基线分支”时，你应能自动完成：

- 改动梳理
- 分组命名
- 分支创建
- 提交
- 推送
- 创建 PR

并将流程结果一次性汇总给用户。
