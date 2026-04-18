# API 脚本和文档总索引

欢迎使用 Dify API 工具脚本集合！本文档是所有脚本和文档的入口。

## 📚 文档导航

### 快速开始
- **[快速参考手册](./QUICK_REFERENCE.md)** ⭐ - 最常用命令速查
- **[最佳实践指南](./scripts/BEST_PRACTICES.md)** - 使用建议和注意事项

### 详细文档
- **[脚本详细目录](./scripts/SCRIPTS_CATALOG.md)** - 所有38个脚本的完整说明
- **[脚本整理方案](./SCRIPTS_ORGANIZATION.md)** - 目录结构和迁移计划
- **[文档目录](./docs/README.md)** - 知识库和插件相关文档

### 专题文档
- [知识库调试工具使用指南](./docs/知识库调试工具使用指南.md)
- [知识库调试快速参考](./docs/知识库调试快速参考.md)
- [自动修复任务说明](./docs/自动修复任务说明.md)
- [dify_extractor插件配置说明](./docs/dify_extractor插件配置说明.md)

---

## 🎯 按使用场景查找

### 我想检查文档状态
```bash
# 整体状态
python check_status_counts.py          # 统计各状态数量
python check_all_docs_status.py        # 详细状态分组

# 特定状态
python check_error_docs.py             # 错误文档
python check_waiting_simple.py         # 等待文档
python check_successful_docs.py        # 成功文档

# 具体文档
python check_specific_doc.py           # 查看文档详情
python check_latest_doc.py             # 最新文档
```

### 我想触发文档处理
```bash
python trigger_waiting_docs.py         # 触发所有等待文档
python trigger_one_doc.py <doc_id>     # 触发单个文档
python queue_document.py               # 文档入队
```

### 我想修复问题
```bash
python fix_documents_process_rule.py   # 修复处理规则
python reindex_all_error_docs.py       # 重新索引错误文档
python reset_all_errors.py             # 重置错误状态
python retry_failed_docs.py            # 重试失败文档
```

### 我想检查配置
```bash
python check_process_rule.py           # 处理规则
python check_plugin_config.py          # 插件配置
python check_dify_extractor_config.py  # Extractor配置
python check_gitea_env.py              # Gitea环境变量
```

### 我想管理用户
```bash
python create_admin.py                 # 创建管理员
python fix_admin_role.py               # 修复管理员角色
python restore_admin.py                # 恢复管理员
```

---

## 📊 脚本分类统计

| 类别 | 数量 | 说明 |
|------|------|------|
| 检查脚本 | 19个 | check_*.py |
| 触发脚本 | 6个 | trigger_*.py, queue_*.py |
| 修复脚本 | 7个 | fix_*.py, reset_*.py, reindex_*.py, retry_*.py |
| 测试脚本 | 2个 | test_*.py |
| 配置脚本 | 1个 | save_*.py |
| 管理脚本 | 3个 | create_*.py, restore_*.py |
| **总计** | **38个** | |

---

## 🔍 按功能分类

### 文档状态检查（14个）
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

### 配置检查（5个）
- check_plugin_config.py
- check_plugin_declaration.py
- check_dify_extractor_config.py
- check_gitea_env.py
- check_beta_apps.py

### 文档触发（6个）
- trigger_index.py
- trigger_indexing.py
- trigger_one_doc.py
- trigger_simple.py
- trigger_waiting_docs.py
- queue_document.py

### 文档修复（6个）
- fix_documents_process_rule.py
- reindex_all_error_docs.py
- reindex_completed_docs.py
- reset_all_errors.py
- reset_docs_for_reindex.py
- retry_failed_docs.py

### 测试工具（2个）
- test_document_indexing.py
- test_gitea_config.py

### 配置管理（1个）
- save_gitea_config.py

### 用户管理（3个）
- create_admin.py
- fix_admin_role.py
- restore_admin.py

---

## 🚀 常用工作流

### 日常监控
```bash
# 1. 查看整体状态
python check_status_counts.py

# 2. 如果有错误，查看详情
python check_error_docs.py

# 3. 如果有等待，查看详情
python check_waiting_simple.py
```

### 问题排查
```bash
# 1. 查看问题文档
python check_error_docs.py

# 2. 查看具体文档详情
python check_specific_doc.py

# 3. 检查配置
python check_process_rule.py
python check_embedding_status.py
```

### 批量修复
```bash
# 1. 修复配置
python fix_documents_process_rule.py

# 2. 重置错误
python reset_all_errors.py

# 3. 触发处理
python trigger_waiting_docs.py

# 4. 验证结果
python check_status_counts.py
```

---

## 📁 目录结构

```
api/
├── SCRIPTS_INDEX.md                    # 本文件 - 总索引
├── QUICK_REFERENCE.md                  # 快速参考
├── SCRIPTS_ORGANIZATION.md             # 整理方案
│
├── docs/                               # 文档目录
│   ├── README.md                       # 文档索引
│   ├── 知识库调试工具使用指南.md
│   ├── 知识库调试快速参考.md
│   ├── 自动修复任务说明.md
│   └── dify_extractor插件配置说明.md
│
├── scripts/                            # 脚本目录（新建）
│   ├── README.md                       # 脚本索引
│   ├── SCRIPTS_CATALOG.md              # 脚本详细目录
│   ├── BEST_PRACTICES.md               # 最佳实践
│   │
│   ├── knowledge_base/                 # 知识库相关
│   │   ├── check/                      # 检查工具
│   │   ├── trigger/                    # 触发工具
│   │   └── fix/                        # 修复工具
│   │
│   ├── config/                         # 配置管理
│   ├── admin/                          # 管理工具
│   └── test/                           # 测试工具
│
├── tools/                              # 工具模块
│   └── knowledge_base_tools.py
│
├── schedule/                           # 定时任务
│   ├── auto_bypass_dify_extractor.py
│   ├── auto_fix_documents_process_rule.py
│   └── auto_fix_extractor_errors.py
│
└── [工具脚本].py                       # 根目录下的38个脚本
```

---

## ⚠️ 重要提示

### 使用前必读
1. **硬编码问题**: 大部分脚本硬编码了 `dataset_id`，使用前需要修改
2. **数据库连接**: 部分脚本硬编码了数据库密码
3. **备份数据**: 执行修复类脚本前建议备份数据
4. **测试环境**: 建议先在测试环境验证

### 推荐阅读顺序
1. [快速参考手册](./QUICK_REFERENCE.md) - 了解常用命令
2. [最佳实践指南](./scripts/BEST_PRACTICES.md) - 学习正确使用方法
3. [脚本详细目录](./scripts/SCRIPTS_CATALOG.md) - 查找具体脚本说明

---

## 🔗 相关资源

### 内部文档
- [API 启动说明](./START_SERVICES.md)
- [主项目文档](../README.md)

### 工具模块
- [知识库工具集](./tools/knowledge_base_tools.py)

### 定时任务
- [自动绕过Extractor](./schedule/auto_bypass_dify_extractor.py)
- [自动修复处理规则](./schedule/auto_fix_documents_process_rule.py)
- [自动修复Extractor错误](./schedule/auto_fix_extractor_errors.py)

---

## 💡 获取帮助

### 查看脚本用途
```bash
# 查看脚本开头的docstring
head -20 check_all_docs_status.py
```

### 查看详细说明
参考 [脚本详细目录](./scripts/SCRIPTS_CATALOG.md)

### 查看使用示例
参考 [快速参考手册](./QUICK_REFERENCE.md)

### 查看最佳实践
参考 [最佳实践指南](./scripts/BEST_PRACTICES.md)

---

## 📝 更新日志

- 2026-04-13: 创建脚本索引和分类文档
- 2026-04-13: 添加最佳实践指南
- 2026-04-13: 创建详细的脚本目录

---

## 🤝 贡献

如果你创建了新的工具脚本，请：
1. 将脚本放到合适的目录
2. 更新相关文档
3. 添加清晰的docstring
4. 遵循最佳实践

---

**快速开始**: 从 [快速参考手册](./QUICK_REFERENCE.md) 开始 →
