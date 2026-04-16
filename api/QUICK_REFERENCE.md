# API 工具快速参考

## 🔍 快速查找

### 我想...

#### 检查文档状态
```bash
# 查看所有文档
python check_all_docs_status.py

# 查看错误文档
python check_error_docs.py

# 查看等待处理的文档
python check_waiting_docs.py

# 查看特定文档
python check_specific_doc.py <document_id>

# 统计各状态数量
python check_status_counts.py
```

#### 触发文档处理
```bash
# 触发等待中的文档
python trigger_waiting_docs.py

# 触发单个文档
python trigger_one_doc.py <document_id>

# 简单触发
python trigger_simple.py
```

#### 修复问题
```bash
# 修复文档处理规则
python fix_documents_process_rule.py

# 重新索引所有错误文档
python reindex_all_error_docs.py

# 重试失败的文档
python retry_failed_docs.py

# 重置所有错误
python reset_all_errors.py
```

#### 配置管理
```bash
# 检查插件配置
python check_plugin_config.py

# 检查 Dify Extractor 配置
python check_dify_extractor_config.py

# 检查 Gitea 环境
python check_gitea_env.py

# 保存 Gitea 配置
python save_gitea_config.py
```

#### 管理员操作
```bash
# 创建管理员
python create_admin.py

# 修复管理员角色
python fix_admin_role.py

# 恢复管理员
python restore_admin.py
```

## 📊 常用命令组合

### 完整的文档问题排查流程
```bash
# 1. 查看整体状态
python check_status_counts.py

# 2. 查看错误文档
python check_error_docs.py

# 3. 查看等待文档
python check_waiting_docs.py

# 4. 修复处理规则
python fix_documents_process_rule.py

# 5. 重新索引错误文档
python reindex_all_error_docs.py

# 6. 触发等待文档
python trigger_waiting_docs.py
```

### 新文档上传后的处理
```bash
# 1. 查看最新文档
python check_latest_doc.py

# 2. 触发索引
python trigger_one_doc.py <document_id>

# 3. 检查处理状态
python check_specific_doc.py <document_id>
```

## 🔧 工具分类速查

### 检查类（Check）
| 命令 | 说明 |
|------|------|
| check_all_docs_status.py | 所有文档状态 |
| check_doc_status.py | 单个文档状态 |
| check_doc_details.py | 文档详细信息 |
| check_docs_simple.py | 简单文档列表 |
| check_specific_doc.py | 特定文档 |
| check_latest_doc.py | 最新文档 |
| check_successful_docs.py | 成功的文档 |
| check_error_docs.py | 错误的文档 |
| check_waiting_docs.py | 等待的文档 |
| check_status_counts.py | 状态统计 |
| check_embedding_status.py | 嵌入状态 |
| check_process_rule.py | 处理规则 |

### 触发类（Trigger）
| 命令 | 说明 |
|------|------|
| trigger_index.py | 触发索引 |
| trigger_indexing.py | 触发索引任务 |
| trigger_one_doc.py | 触发单个文档 |
| trigger_simple.py | 简单触发 |
| trigger_waiting_docs.py | 触发等待文档 |
| queue_document.py | 文档入队 |

### 修复类（Fix）
| 命令 | 说明 |
|------|------|
| fix_documents_process_rule.py | 修复处理规则 |
| reindex_all_error_docs.py | 重索引错误文档 |
| reindex_completed_docs.py | 重索引完成文档 |
| reset_all_errors.py | 重置所有错误 |
| reset_docs_for_reindex.py | 重置待重索引 |
| retry_failed_docs.py | 重试失败文档 |

### 配置类（Config）
| 命令 | 说明 |
|------|------|
| check_plugin_config.py | 检查插件配置 |
| check_dify_extractor_config.py | 检查提取器配置 |
| check_gitea_env.py | 检查 Gitea 环境 |
| save_gitea_config.py | 保存 Gitea 配置 |
| test_gitea_config.py | 测试 Gitea 配置 |

### 管理类（Admin）
| 命令 | 说明 |
|------|------|
| create_admin.py | 创建管理员 |
| fix_admin_role.py | 修复管理员角色 |
| restore_admin.py | 恢复管理员 |

## 📚 相关文档

- [完整文档索引](./docs/README.md)
- [脚本整理说明](./SCRIPTS_ORGANIZATION.md)
- [知识库调试工具使用指南](./docs/知识库调试工具使用指南.md)
- [知识库调试快速参考](./docs/知识库调试快速参考.md)
- [自动修复任务说明](./docs/自动修复任务说明.md)

## 💡 提示

1. 所有命令都需要在 `api/` 目录下运行
2. 确保已配置好 `.env` 文件
3. 某些操作需要数据库连接
4. 批量操作前建议先备份数据

## 🆘 常见问题

### Q: 文档一直处于等待状态？
```bash
# 1. 检查等待文档
python check_waiting_docs.py

# 2. 检查处理规则
python check_process_rule.py

# 3. 触发处理
python trigger_waiting_docs.py
```

### Q: 文档索引失败？
```bash
# 1. 查看错误文档
python check_error_docs.py

# 2. 修复处理规则
python fix_documents_process_rule.py

# 3. 重新索引
python reindex_all_error_docs.py
```

### Q: 如何测试文档索引？
```bash
python test_document_indexing.py
```
