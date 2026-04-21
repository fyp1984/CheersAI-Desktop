# API 脚本索引

本索引只保留当前仍有维护价值的辅助脚本。历史性的批量检查、一次性调试和过程性排障脚本已在清理中移除。

## 保留脚本

### 文档处理
- `queue_document.py` - 将文档加入处理队列
- `trigger_index.py` - 触发索引流程
- `trigger_indexing.py` - 触发索引任务
- `trigger_one_doc.py` - 触发单个文档索引
- `trigger_simple.py` - 简化触发入口
- `retry_failed_docs.py` - 重试失败文档
- `reset_all_errors.py` - 重置文档错误状态

### 管理与配置
- `create_admin.py` - 创建管理员账号
- `fix_admin_role.py` - 修复管理员角色
- `restore_admin.py` - 恢复管理员账号状态
- `save_filebay_token.py` - 保存 FileBay 令牌配置

## 相关文档

- `docs/README.md` - API 文档入口
- `START_SERVICES.md` - API 启动说明
- `QUICK_REFERENCE.md` - 常用命令速查

## 维护规则

- 只保留可重复使用、无敏感硬编码的脚本
- 不再把临时调试脚本或一次性修复脚本放在仓库根目录
