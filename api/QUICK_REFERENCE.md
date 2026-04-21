# API 快速参考

以下命令均在 `api/` 目录下执行。

## 文档处理

```bash
python queue_document.py
python trigger_index.py
python trigger_indexing.py
python trigger_one_doc.py <document_id>
python trigger_simple.py
python retry_failed_docs.py
python reset_all_errors.py
```

## 管理与配置

```bash
python create_admin.py
python fix_admin_role.py
python restore_admin.py
python save_filebay_token.py <email> <username> <repo> <token>
```

## 相关文档

- `docs/README.md`
- `START_SERVICES.md`
- `SCRIPTS_INDEX.md`

## 说明

- 历史性的 `check_*`、`test_*` 和一次性调试脚本已从仓库清理
- 新增脚本前优先判断是否应并入现有能力，而不是继续扩张脚本集合
