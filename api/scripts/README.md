# API 工具脚本目录

本目录用于存放 API 相关的工具脚本，按功能分类整理。

## 📂 目录结构

```
scripts/
├── README.md                    # 本文件
├── knowledge_base/              # 知识库相关脚本
│   ├── check/                   # 检查工具
│   ├── trigger/                 # 触发工具
│   └── fix/                     # 修复工具
├── config/                      # 配置管理脚本
├── admin/                       # 管理员工具
└── test/                        # 测试脚本
```

## 🔄 迁移说明

为了更好地组织代码，建议将 api 根目录下的工具脚本迁移到此目录：

### 知识库检查工具 → `knowledge_base/check/`
- check_all_docs_status.py
- check_doc_status.py
- check_doc_details.py
- check_docs_simple.py
- check_specific_doc.py
- check_latest_doc.py
- check_successful_doc.py
- check_successful_docs.py
- check_error_docs.py
- check_waiting_docs.py
- check_waiting_simple.py
- check_status_counts.py
- check_embedding_status.py
- check_process_rule.py

### 知识库触发工具 → `knowledge_base/trigger/`
- trigger_index.py
- trigger_indexing.py
- trigger_one_doc.py
- trigger_simple.py
- trigger_waiting_docs.py
- queue_document.py

### 知识库修复工具 → `knowledge_base/fix/`
- fix_documents_process_rule.py
- reindex_all_error_docs.py
- reindex_completed_docs.py
- reset_all_errors.py
- reset_docs_for_reindex.py
- retry_failed_docs.py

### 配置管理工具 → `config/`
- check_plugin_config.py
- check_plugin_declaration.py
- check_dify_extractor_config.py
- check_gitea_env.py
- save_gitea_config.py
- test_gitea_config.py

### 管理员工具 → `admin/`
- create_admin.py
- fix_admin_role.py
- restore_admin.py

### 测试工具 → `test/`
- test_document_indexing.py
- test_gitea_config.py
- check_beta_apps.py

## 📝 使用建议

1. **保持向后兼容**：迁移时可以在原位置保留软链接或导入脚本
2. **更新文档**：迁移后更新相关文档中的路径引用
3. **统一命名**：建议使用统一的命名规范，如 `check_*.py`, `fix_*.py`, `trigger_*.py`
4. **添加说明**：每个脚本建议添加 docstring 说明用途和参数

## 🚀 快速使用

```bash
# 从 api 目录运行
cd api

# 检查文档状态
python scripts/knowledge_base/check/check_all_docs_status.py

# 触发索引
python scripts/knowledge_base/trigger/trigger_waiting_docs.py

# 修复问题
python scripts/knowledge_base/fix/fix_documents_process_rule.py
```
