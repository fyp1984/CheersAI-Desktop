# 工具脚本使用指南

## 🎯 快速开始

### 第一次使用？

1. **查看总索引** - [../SCRIPTS_INDEX.md](../SCRIPTS_INDEX.md)
2. **学习常用命令** - [../QUICK_REFERENCE.md](../QUICK_REFERENCE.md)
3. **了解最佳实践** - [BEST_PRACTICES.md](./BEST_PRACTICES.md)

### 查找特定脚本？

- **按场景查找** → [../QUICK_REFERENCE.md](../QUICK_REFERENCE.md)
- **按功能查找** → [SCRIPTS_CATALOG.md](./SCRIPTS_CATALOG.md)
- **查看所有脚本** → [../SCRIPTS_INDEX.md](../SCRIPTS_INDEX.md)

---

## 📚 文档列表

| 文档 | 说明 | 适合 |
|------|------|------|
| [SCRIPTS_CATALOG.md](./SCRIPTS_CATALOG.md) | 38个脚本的详细说明 | 查找具体脚本 |
| [BEST_PRACTICES.md](./BEST_PRACTICES.md) | 使用最佳实践 | 学习正确用法 |
| [README.md](./README.md) | 脚本迁移指南 | 了解目录结构 |

---

## 🔍 最常用的脚本

### 检查状态
```bash
python check_status_counts.py      # 统计各状态数量
python check_error_docs.py         # 查看错误文档
python check_waiting_simple.py     # 查看等待文档
```

### 触发处理
```bash
python trigger_waiting_docs.py     # 触发等待文档
python trigger_one_doc.py <id>     # 触发单个文档
```

### 修复问题
```bash
python fix_documents_process_rule.py  # 修复处理规则
python reindex_all_error_docs.py      # 重新索引错误文档
```

---

## ⚠️ 使用前必读

1. **硬编码问题**: 大部分脚本硬编码了 dataset_id，需要修改
2. **备份数据**: 执行修复类脚本前建议备份
3. **测试环境**: 建议先在测试环境验证

详见 [BEST_PRACTICES.md](./BEST_PRACTICES.md)

---

## 📁 目录结构

```
scripts/
├── README_SCRIPTS.md          # 本文件
├── SCRIPTS_CATALOG.md         # 详细目录
├── BEST_PRACTICES.md          # 最佳实践
├── README.md                  # 迁移指南
│
├── knowledge_base/            # 知识库相关（计划）
│   ├── check/                 # 检查工具
│   ├── trigger/               # 触发工具
│   └── fix/                   # 修复工具
│
├── config/                    # 配置管理（计划）
├── admin/                     # 管理工具（计划）
└── test/                      # 测试工具（计划）
```

---

## 🚀 推荐阅读顺序

1. [快速参考](../QUICK_REFERENCE.md) - 5分钟了解常用命令
2. [最佳实践](./BEST_PRACTICES.md) - 10分钟学习正确用法
3. [详细目录](./SCRIPTS_CATALOG.md) - 需要时查阅

---

**返回总索引**: [../SCRIPTS_INDEX.md](../SCRIPTS_INDEX.md)
