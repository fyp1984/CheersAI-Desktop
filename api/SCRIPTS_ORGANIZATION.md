# API 脚本整理说明

## 📋 概述

api 目录下有大量工具脚本（40+ 个 Python 文件），为了更好地管理和维护，建议进行如下整理。

## 🎯 整理目标

1. **分类清晰**：按功能将脚本分类到不同目录
2. **易于查找**：通过目录结构快速定位所需工具
3. **便于维护**：相关脚本集中管理，方便更新
4. **保持兼容**：不影响现有使用方式

## 📁 新的目录结构

```
api/
├── docs/                                    # 📚 文档目录
│   ├── README.md                            # 文档索引（已创建）
│   ├── 知识库调试工具使用指南.md
│   ├── 知识库调试快速参考.md
│   ├── 自动修复任务说明.md
│   └── dify_extractor插件配置说明.md
│
├── scripts/                                 # 🛠️ 工具脚本目录（新建）
│   ├── README.md                            # 脚本索引（已创建）
│   │
│   ├── knowledge_base/                      # 知识库相关
│   │   ├── check/                           # 检查工具（14个脚本）
│   │   │   ├── check_all_docs_status.py
│   │   │   ├── check_doc_status.py
│   │   │   ├── check_doc_details.py
│   │   │   ├── check_docs_simple.py
│   │   │   ├── check_specific_doc.py
│   │   │   ├── check_latest_doc.py
│   │   │   ├── check_successful_doc.py
│   │   │   ├── check_successful_docs.py
│   │   │   ├── check_error_docs.py
│   │   │   ├── check_waiting_docs.py
│   │   │   ├── check_waiting_simple.py
│   │   │   ├── check_status_counts.py
│   │   │   ├── check_embedding_status.py
│   │   │   └── check_process_rule.py
│   │   │
│   │   ├── trigger/                         # 触发工具（6个脚本）
│   │   │   ├── trigger_index.py
│   │   │   ├── trigger_indexing.py
│   │   │   ├── trigger_one_doc.py
│   │   │   ├── trigger_simple.py
│   │   │   ├── trigger_waiting_docs.py
│   │   │   └── queue_document.py
│   │   │
│   │   └── fix/                             # 修复工具（6个脚本）
│   │       ├── fix_documents_process_rule.py
│   │       ├── reindex_all_error_docs.py
│   │       ├── reindex_completed_docs.py
│   │       ├── reset_all_errors.py
│   │       ├── reset_docs_for_reindex.py
│   │       └── retry_failed_docs.py
│   │
│   ├── config/                              # 配置管理（6个脚本）
│   │   ├── check_plugin_config.py
│   │   ├── check_plugin_declaration.py
│   │   ├── check_dify_extractor_config.py
│   │   ├── check_gitea_env.py
│   │   ├── save_gitea_config.py
│   │   └── test_gitea_config.py
│   │
│   ├── admin/                               # 管理员工具（3个脚本）
│   │   ├── create_admin.py
│   │   ├── fix_admin_role.py
│   │   └── restore_admin.py
│   │
│   └── test/                                # 测试工具（2个脚本）
│       ├── test_document_indexing.py
│       └── check_beta_apps.py
│
├── tools/                                   # 工具模块（保持不变）
│   ├── knowledge_base_tools.py
│   └── ...
│
├── schedule/                                # 定时任务（保持不变）
│   ├── auto_bypass_dify_extractor.py
│   ├── auto_fix_documents_process_rule.py
│   └── auto_fix_extractor_errors.py
│
└── [核心应用文件]                           # 保持在根目录
    ├── app.py
    ├── app_factory.py
    ├── dify_app.py
    ├── commands.py
    └── ...
```

## 🔄 迁移步骤

### 方案 A：完全迁移（推荐）

```bash
# 1. 创建目录结构（已完成）
# 2. 移动文件到对应目录
# 3. 更新导入路径
# 4. 更新文档引用
```

### 方案 B：软链接（保持兼容）

```bash
# 在原位置保留软链接，指向新位置
# Windows 使用 mklink
# Linux/Mac 使用 ln -s
```

### 方案 C：渐进式迁移

1. 新脚本直接放到 `scripts/` 目录
2. 旧脚本逐步迁移
3. 在根目录保留常用脚本的快捷方式

## 📝 脚本分类详情

### 知识库检查工具（14个）
用于检查文档和知识库的各种状态

| 脚本名 | 功能 | 使用频率 |
|--------|------|----------|
| check_all_docs_status.py | 检查所有文档状态 | ⭐⭐⭐ |
| check_error_docs.py | 检查错误文档 | ⭐⭐⭐ |
| check_waiting_docs.py | 检查等待处理的文档 | ⭐⭐⭐ |
| check_specific_doc.py | 检查特定文档 | ⭐⭐ |
| check_status_counts.py | 统计状态数量 | ⭐⭐ |
| 其他 | 各种检查功能 | ⭐ |

### 知识库触发工具（6个）
用于触发文档索引和处理

| 脚本名 | 功能 | 使用频率 |
|--------|------|----------|
| trigger_waiting_docs.py | 触发等待中的文档 | ⭐⭐⭐ |
| trigger_one_doc.py | 触发单个文档 | ⭐⭐ |
| queue_document.py | 文档加入队列 | ⭐⭐ |
| 其他 | 各种触发功能 | ⭐ |

### 知识库修复工具（6个）
用于修复文档处理问题

| 脚本名 | 功能 | 使用频率 |
|--------|------|----------|
| fix_documents_process_rule.py | 修复处理规则 | ⭐⭐⭐ |
| reindex_all_error_docs.py | 重新索引错误文档 | ⭐⭐⭐ |
| retry_failed_docs.py | 重试失败文档 | ⭐⭐ |
| 其他 | 各种修复功能 | ⭐ |

### 配置管理工具（6个）
用于管理插件和系统配置

### 管理员工具（3个）
用于管理员账户管理

### 测试工具（2个）
用于测试功能

## 🚀 使用示例

### 迁移前
```bash
cd api
python check_all_docs_status.py
python trigger_waiting_docs.py
```

### 迁移后
```bash
cd api
python scripts/knowledge_base/check/check_all_docs_status.py
python scripts/knowledge_base/trigger/trigger_waiting_docs.py

# 或者使用别名/快捷脚本
python scripts/kb-check-all
python scripts/kb-trigger-waiting
```

## 💡 建议

1. **创建快捷脚本**：在 `scripts/` 根目录创建常用命令的快捷方式
2. **统一命名规范**：使用 `动词_对象_描述.py` 格式
3. **添加文档字符串**：每个脚本添加清晰的 docstring
4. **参数标准化**：使用 argparse 统一参数处理
5. **日志规范**：统一日志格式和输出

## ✅ 下一步行动

- [ ] 决定采用哪种迁移方案
- [ ] 创建迁移脚本自动化处理
- [ ] 更新相关文档
- [ ] 通知团队成员
- [ ] 更新 CI/CD 配置（如果有）

## 📞 联系

如有问题或建议，请联系开发团队。
