# API 文档目录

本目录包含 Dify API 相关的文档和工具说明。

> 💡 **快速导航**: 
> - 查找工具脚本？请看 [脚本总索引](../SCRIPTS_INDEX.md)
> - 需要快速参考？请看 [快速参考手册](../QUICK_REFERENCE.md)
> - 想了解最佳实践？请看 [最佳实践指南](../scripts/BEST_PRACTICES.md)

## 📚 文档列表

### 知识库相关
- [知识库调试工具使用指南](./知识库调试工具使用指南.md) - 详细的知识库调试工具使用说明
- [知识库调试快速参考](./知识库调试快速参考.md) - 快速参考手册
- [自动修复任务说明](./自动修复任务说明.md) - 自动修复任务的配置和使用

### 插件配置
- [dify_extractor插件配置说明](./dify_extractor插件配置说明.md) - Dify Extractor 插件的配置指南

## 🛠️ 工具脚本

### 知识库检查工具（位于 api/ 根目录）

#### 文档状态检查
- `check_all_docs_status.py` - 检查所有文档的状态
- `check_doc_status.py` - 检查单个文档状态
- `check_doc_details.py` - 查看文档详细信息
- `check_docs_simple.py` - 简单查看文档列表
- `check_specific_doc.py` - 检查特定文档
- `check_latest_doc.py` - 检查最新文档
- `check_successful_doc.py` / `check_successful_docs.py` - 检查成功的文档
- `check_error_docs.py` - 检查错误的文档
- `check_waiting_docs.py` / `check_waiting_simple.py` - 检查等待处理的文档
- `check_status_counts.py` - 统计各状态文档数量
- `check_embedding_status.py` - 检查嵌入状态
- `check_process_rule.py` - 检查处理规则

#### 文档索引操作
- `trigger_index.py` - 触发索引
- `trigger_indexing.py` - 触发索引任务
- `trigger_one_doc.py` - 触发单个文档索引
- `trigger_simple.py` - 简单触发
- `trigger_waiting_docs.py` - 触发等待中的文档
- `queue_document.py` - 将文档加入队列
- `test_document_indexing.py` - 测试文档索引

#### 文档修复工具
- `fix_documents_process_rule.py` - 修复文档处理规则
- `reindex_all_error_docs.py` - 重新索引所有错误文档
- `reindex_completed_docs.py` - 重新索引已完成的文档
- `reset_all_errors.py` - 重置所有错误
- `reset_docs_for_reindex.py` - 重置文档以便重新索引
- `retry_failed_docs.py` - 重试失败的文档

### 配置和管理工具

#### 插件配置
- `check_plugin_config.py` - 检查插件配置
- `check_plugin_declaration.py` - 检查插件声明
- `check_dify_extractor_config.py` - 检查 Dify Extractor 配置

#### Gitea 配置
- `check_gitea_env.py` - 检查 Gitea 环境配置
- `save_gitea_config.py` - 保存 Gitea 配置
- `test_gitea_config.py` - 测试 Gitea 配置

#### 用户管理
- `create_admin.py` - 创建管理员用户
- `fix_admin_role.py` - 修复管理员角色
- `restore_admin.py` - 恢复管理员

#### 应用管理
- `check_beta_apps.py` - 检查 Beta 应用

## 📁 目录结构

```
api/
├── docs/                          # 文档目录（本目录）
│   ├── README.md                  # 本文件
│   ├── 知识库调试工具使用指南.md
│   ├── 知识库调试快速参考.md
│   ├── 自动修复任务说明.md
│   └── dify_extractor插件配置说明.md
├── tools/                         # 工具目录
│   └── knowledge_base_tools.py    # 知识库工具集合
├── schedule/                      # 定时任务
│   ├── auto_bypass_dify_extractor.py
│   ├── auto_fix_documents_process_rule.py
│   └── auto_fix_extractor_errors.py
└── [各种检查和修复脚本].py       # 根目录下的工具脚本
```

## 🚀 快速开始

### 检查文档状态
```bash
# 查看所有文档状态
python check_all_docs_status.py

# 查看特定文档
python check_specific_doc.py <document_id>

# 查看错误文档
python check_error_docs.py
```

### 触发文档索引
```bash
# 触发等待中的文档
python trigger_waiting_docs.py

# 触发单个文档
python trigger_one_doc.py <document_id>
```

### 修复问题
```bash
# 修复文档处理规则
python fix_documents_process_rule.py

# 重新索引错误文档
python reindex_all_error_docs.py
```

## 📝 注意事项

1. 运行脚本前请确保已配置好 `.env` 文件
2. 某些操作可能需要管理员权限
3. 批量操作前建议先备份数据库
4. 详细使用说明请参考各文档的具体说明

## 🔗 相关链接

- [主项目文档](../../README.md)
- [API 启动说明](../START_SERVICES.md)
