# Git 动态分支合并脚本使用说明

## 脚本简介
本脚本 (`scripts/git_merge_dynamic.sh`) 是一个通用的 Git 分支合并工具。它允许用户指定**源分支**和**目标分支**，自动化执行合并流程，并提供交互式的冲突解决界面。

## 特性
- **参数化配置**：支持通过命令行参数指定任意分支。
- **自动检查**：自动验证分支名称合法性、工作区状态和目标分支是否存在。
- **交互式冲突解决**：逐个文件展示差异，支持一键选择 `ours` 或 `theirs`，也支持暂停进行手动编辑。
- **安全回滚**：提供退出选项，自动回滚未完成的合并。

## 快速开始

### 1. 赋予执行权限
```bash
chmod +x scripts/git_merge_dynamic.sh
```

### 2. 基本用法
脚本接受两个可选参数：
```bash
./scripts/git_merge_dynamic.sh [source_branch] [target_branch]
```

- **参数 1 (`source_branch`)**: 源分支名称，代码将从这里合并出来。默认值: `master`
- **参数 2 (`target_branch`)**: 目标分支名称，代码将合并到这里。默认值: `branch2B_v1.0`

### 3. 使用示例

#### 场景 A: 使用默认配置 (master -> branch2B_v1.0)
```bash
./scripts/git_merge_dynamic.sh
```
*等效于执行: `git checkout branch2B_v1.0 && git merge origin/master`*

#### 场景 B: 指定自定义分支 (feature-x -> develop)
```bash
./scripts/git_merge_dynamic.sh feature-x develop
```
*将 `feature-x` 分支的代码合并到 `develop` 分支。*

#### 场景 C: 仅指定源分支 (dev -> branch2B_v1.0)
```bash
./scripts/git_merge_dynamic.sh dev
```
*将 `dev` 分支合并到默认的目标分支 `branch2B_v1.0`。*

## 冲突处理指南

当脚本检测到合并冲突时，会暂停并显示冲突文件列表。对于每个冲突文件，您将看到以下选项：

1. **保留当前分支版本 (ours)**
   - 选择此项将忽略源分支的更改，完全保留目标分支（当前分支）的内容。
   - 适用于：您确定目标分支的代码是正确的，或者不需要源分支的该部分变更。

2. **使用源分支版本 (theirs)**
   - 选择此项将使用源分支的内容覆盖目标分支。
   - 适用于：源分支包含更新的修复，或者您希望完全同步源分支的状态。

3. **手动编辑**
   - 脚本会暂停。
   - 您可以使用 IDE (如 VS Code) 打开冲突文件，搜索 `<<<<<<<` 标记，手动合并代码。
   - 保存文件后，回到终端按 **回车键**，脚本会自动执行 `git add` 并继续处理下一个文件。

4. **退出合并**
   - 执行 `git merge --abort`，回滚到合并前的状态。

## 常见错误排查

- **Error: 分支名称包含非法字符**
  - 请检查输入的参数是否包含空格、特殊符号等。仅允许字母、数字、`/`、`-`、`_`、`.`。

- **Error: 目标分支在本地不存在**
  - 请先执行 `git fetch` 和 `git checkout <target_branch>` 确保本地有该分支。

- **Error: 源分支在远程和本地均未找到**
  - 请检查分支名称拼写是否正确，或执行 `git fetch --all` 更新远程分支列表。
