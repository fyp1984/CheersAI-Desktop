# Git 动态合并脚本使用文档

## 1. 简介
`git_merge_dynamic.sh` 是一个用于自动化Git分支合并的Shell脚本。它旨在简化日常开发分支（如 `feature` 分支）向测试（`branch2B_v1.0`）或主分支（`master`）合并的流程。该脚本支持交互式向导模式，也支持通过命令行参数进行的静默模式，方便集成到CI/CD流水线中。

## 2. 功能特性
- **交互式向导**：引导用户选择源分支、目标分支和输入提交消息。
- **参数化调用**：支持通过 `-b`, `-t`, `-m` 等参数直接指定合并配置。
- **静默模式**：支持 `-s` 选项，用于自动化脚本调用，不进行用户交互。
- **安全检查**：在执行合并前检查工作区状态，防止未提交的更改丢失。
- **冲突处理**：自动检测合并冲突。在交互模式下提示用户解决；在静默模式下自动终止并回滚，保证仓库状态安全。
- **自动推送**：合并成功后自动推送到远程仓库。

## 3. 环境要求
- 操作系统: Linux / macOS / Windows (Git Bash)
- 依赖工具: `git` (必须已安装并配置好SSH/HTTPS权限)

## 4. 快速开始

### 4.1 赋予执行权限
首次使用前，请确保脚本具有执行权限：
```bash
chmod +x scripts/git_merge_dynamic.sh
```

### 4.2 交互式运行 (推荐)
直接运行脚本而不带任何参数，将进入交互式模式：
```bash
./scripts/git_merge_dynamic.sh
```
按照屏幕提示输入源分支、目标分支即可。

### 4.3 常用命令示例

**场景一：将 master 合并到 branch2B_v1.0**
假设默认源分支配置为 `master`，目标为 `branch2B_v1.0`：
```bash
./scripts/git_merge_dynamic.sh
```
(一路回车确认默认值即可)

**场景二：指定分支合并**
将 `feature-login` 合并到 `develop`：
```bash
./scripts/git_merge_dynamic.sh -b feature-login -t develop
```

**场景三：带自定义消息的合并**
```bash
./scripts/git_merge_dynamic.sh -m "Merge: 完成登录功能开发"
```

**场景四：CI/CD 自动化调用 (静默模式)**
在构建脚本中使用，不希望有人工干预：
```bash
./scripts/git_merge_dynamic.sh -s -b dev -t master -m "Auto deploy"
```

## 5. 参数详解

| 参数 | 说明 | 默认值 | 备注 |
| :--- | :--- | :--- | :--- |
| `-b <branch>` | 源分支 (Source Branch) | `master` | 代码变更的来源 |
| `-t <branch>` | 目标分支 (Target Branch) | `branch2B_v1.0` | 代码合并的目的地 |
| `-m <msg>` | 提交消息 (Commit Message) | Git默认生成的消息 | 建议填写清晰的变更说明 |
| `-s` | 静默模式 (Silent Mode) | 关闭 | 启用后禁用所有交互询问 |
| `-h` | 帮助 (Help) | - | 显示帮助信息并退出 |

## 6. 常见问题 (FAQ)

**Q: 脚本提示 "工作区有未提交的更改" 怎么办？**
A: 请先使用 `git add .` 和 `git commit` 提交你的更改，或者使用 `git stash` 暂存更改，保持工作区干净后再运行脚本。

**Q: 合并发生冲突了怎么办？**
A: 
- **交互模式下**：脚本会暂停并提示你手动解决。你可以打开VS Code或其他编辑器解决冲突，然后 `git add` 标记解决，最后提交。
- **静默模式下**：脚本会自动中止合并 (`git merge --abort`) 并退出，以免破坏环境。你需要人工介入处理。

**Q: 如何修改默认分支配置？**
A: 编辑脚本文件 `scripts/git_merge_dynamic.sh`，修改开头的 `DEFAULT_SOURCE_BRANCH` 和 `DEFAULT_TARGET_BRANCH` 变量。

## 7. 更新日志
- **v2.0.0 (2026-03-13)**: 重构脚本，支持参数化输入和静默模式；增加帮助文档。
- **v1.0.0**: 初始版本，仅支持硬编码的分支合并。
