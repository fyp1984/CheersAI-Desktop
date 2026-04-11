---
name: "cheersai-tech-docs-sync"
description: "Encrypts and syncs CheersAI technical docs to GitHub. Invoke when archiving `CheersAI - docs/技术`, uploading snapshots, or refreshing secure doc backups."
---

# CheersAI Tech Docs Sync

本 Skill 用于把 CheersAI 的技术文档目录打包、加密、上传到 GitHub 私有仓库，并在上传后把仓库同步到本地固定目录，形成稳定的“源目录 -> 加密归档 -> GitHub -> 本地同步副本”闭环。

## 1. 适用场景
- 当用户要求同步 `CheersAI - docs/技术` 目录到 GitHub 时调用
- 当用户要求对技术文档做“加密压缩 + 归档上传”时调用
- 当用户要求生成新的技术文档快照、灾备包、离线备份包时调用
- 当需要固定一套“本地归档 -> GitHub 私有仓库存档 -> 返回一次性口令”的流程时调用

## 2. 核心原则
- **先压缩后加密**：先生成 `tar.gz`，再做强加密，避免目录结构散落
- **强口令一次性显示**：口令必须随机生成，至少 12 位，并同时包含大小写字母、数字、特殊字符
- **口令不落仓库**：口令只能在当前操作窗口显示一次，不得写入 GitHub 仓库、README、日志归档或持久配置
- **私有仓库存档**：归档文件只上传到 GitHub 私有仓库，不上传到公开位置
- **可校验可恢复**：上传前必须本地做一次解密校验，并记录 SHA-256

## 3. 标准输入
- 源目录：默认 `CheersAI - docs/技术`
- 本地同步目录：默认 `CheersAI - docs/CheersAl-Docs-sync`
- 目标仓库：默认 `fyp1984/CheersAI-Docs`
- 目标分支：默认 `main`
- 归档格式：默认 `tar.gz.enc`
- 加密算法：默认 `AES-256-CBC`
- KDF：默认 `PBKDF2`

## 4. 标准流程

### 4.1 盘点源目录与同步目录
- 确认源目录存在
- 统计目录大小与文件数量
- 确认目标 GitHub 仓库存在且可写
- 确认本地同步目录是否存在
- 若本地同步目录不存在，则克隆目标仓库到固定目录
- 若本地同步目录已存在，则校验它是目标仓库的有效 Git 工作副本

### 4.2 生成强口令
- 口令长度建议 16~24 位
- 至少包含：
  - 小写字母
  - 大写字母
  - 数字
  - 特殊字符
- 口令只输出一次，并提醒用户立即保存

### 4.3 压缩与加密
- 先打包：
  - `技术 -> <archive>.tar.gz`
- 再加密：
  - `<archive>.tar.gz -> <archive>.tar.gz.enc`
- 推荐命令：

```bash
tar -czf <archive>.tar.gz 技术
openssl enc -aes-256-cbc -pbkdf2 -salt -in <archive>.tar.gz -out <archive>.tar.gz.enc
```

### 4.4 本地校验
- 使用同一口令做一次解密恢复
- 验证解密后 tar 包能正常列出目录
- 记录：
  - 加密包 SHA-256
  - 加密前 tar 包 SHA-256

### 4.5 上传 GitHub
- 若目标仓库为空，可直接初始化首个提交
- 归档文件建议上传到：
  - `archives/<archive>.tar.gz.enc`
- 同步维护：
  - 根目录 `README.md`
  - `archives/MANIFEST.md`

### 4.6 同步本地副本
- 上传完成后，进入本地同步目录
- 执行：
  - `git fetch --tags origin`
  - `git checkout main`
  - `git reset --hard origin/main`
- 确保本地同步目录与远端仓库 `main` 分支一致
- 默认不要在源目录 `CheersAI - docs/技术` 内执行 Git 命令

### 4.7 返回结果
- 返回 GitHub 仓库地址
- 返回本地同步目录路径
- 返回归档文件相对路径
- 返回 SHA-256
- 返回口令一次
- 明确提醒：
  - “请立刻保存口令；关闭窗口后不再重复显示”

## 5. 固定动作

每次执行该 Skill 时，默认按以下顺序完成：

1. 盘点 `CheersAI - docs/技术`
2. 生成强口令
3. 打包并加密
4. 本地做解密与 SHA 校验
5. 上传到 `fyp1984/CheersAI-Docs`
6. 把远端仓库同步到 `CheersAI - docs/CheersAl-Docs-sync`
7. 返回归档文件、校验值、本地同步目录与一次性口令

## 6. 推荐仓库结构

```text
CheersAI-Docs/
  README.md
  archives/
    <archive>.tar.gz.enc
    MANIFEST.md
```

## 7. 推荐 README 内容
- 仓库用途说明
- 解密命令示例
- 不存储口令的安全说明

## 8. 推荐 MANIFEST 内容
- 源目录
- 本地同步目录
- 归档文件名
- 压缩格式
- 加密算法
- KDF
- 加密包 SHA-256
- 明文 tar 包 SHA-256
- 口令处理策略

## 9. 风险控制
- 不要把口令写入仓库、脚本、提交信息、文档或长期记忆
- 不要上传未加密的明文 tar 包
- 若上传失败，不要删除已成功生成的本地加密包
- 若需要删除临时目录或脚本，优先按工作区安全规则执行
- 如果 GitHub 仓库不存在或不可写，先终止并报告原因
- 如果本地同步目录不是目标仓库副本，先终止并报告原因
- 不要在 `CheersAI - docs/技术` 源目录里执行 `git pull`、`git push`、`git checkout`

## 10. 固定输出模板
- **源目录**：本次归档的目录
- **本地同步目录**：同步后的本地 Git 仓库目录
- **目标仓库**：上传到的 GitHub 仓库
- **归档文件**：加密包文件名与仓库路径
- **校验值**：SHA-256
- **口令**：仅显示一次
- **解密命令**：用户下载后可直接使用的命令
- **提醒**：立即保存口令
