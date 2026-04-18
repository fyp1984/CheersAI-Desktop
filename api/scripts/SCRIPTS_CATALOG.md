# API 脚本详细目录

本文档详细列出所有工具脚本的功能、用途和使用方法。

## 📊 脚本统计

- **检查脚本（Check）**: 17个
- **触发脚本（Trigger）**: 6个
- **修复脚本（Fix/Reset/Reindex）**: 7个
- **测试脚本（Test）**: 2个
- **配置脚本（Config/Save）**: 3个
- **管理脚本（Admin）**: 3个

**总计**: 38个工具脚本

---

## 🔍 检查脚本（Check Scripts）

### 文档状态检查

#### 1. `check_all_docs_status.py`
- **功能**: 检查所有文档的状态统计
- **用途**: 获取文档状态的整体概览
- **输出**: 按状态分组的文档数量
- **使用场景**: 日常监控、问题排查的第一步
- **依赖**: SQLAlchemy, app_factory

```bash
python check_all_docs_status.py
```

#### 2. `check_doc_status.py`
- **功能**: 检查单个文档的状态
- **用途**: 查看特定文档的基本信息
- **输出**: 文档ID、名称、状态、错误信息
- **使用场景**: 定位具体文档问题
- **依赖**: psycopg2（直接数据库连接）
- **硬编码**: document_id

```bash
python check_doc_status.py
```

#### 3. `check_doc_details.py`
- **功能**: 查看文档详细信息
- **用途**: 获取文档的完整详情
- **输出**: 文档的所有字段信息
- **使用场景**: 深入分析文档问题
- **依赖**: psycopg2

```bash
python check_doc_details.py
```

#### 4. `check_docs_simple.py`
- **功能**: 简单列出文档
- **用途**: 快速浏览文档列表
- **输出**: 文档ID、名称、状态、字数、tokens
- **使用场景**: 快速查看文档概况
- **依赖**: SQLAlchemy（轻量级，不加载完整app）

```bash
python check_docs_simple.py
```

#### 5. `check_specific_doc.py`
- **功能**: 检查特定文档及其分段
- **用途**: 查看文档和segment的详细信息
- **输出**: 文档信息 + 所有segment的状态
- **使用场景**: 分析文档分段问题
- **依赖**: SQLAlchemy

```bash
python check_specific_doc.py
```

#### 6. `check_latest_doc.py`
- **功能**: 检查最新上传的文档
- **用途**: 查看最近添加的文档状态
- **输出**: 最新文档的详细信息
- **使用场景**: 验证新上传的文档
- **依赖**: ext_database, models

```bash
python check_latest_doc.py
```

#### 7. `check_successful_doc.py`
- **功能**: 检查成功的文档
- **用途**: 查看成功处理的文档示例
- **输出**: 成功文档的详细信息
- **使用场景**: 对比成功和失败的文档
- **依赖**: psycopg2

```bash
python check_successful_doc.py
```

#### 8. `check_successful_docs.py`
- **功能**: 列出所有成功的文档
- **用途**: 查看成功文档列表
- **输出**: 最近5个成功文档的信息
- **使用场景**: 验证处理流程
- **依赖**: ext_database, models

```bash
python check_successful_docs.py
```

#### 9. `check_error_docs.py`
- **功能**: 检查错误文档
- **用途**: 查看所有处理失败的文档
- **输出**: 错误文档列表及错误信息
- **使用场景**: 问题排查、批量修复前的检查
- **依赖**: SQLAlchemy

```bash
python check_error_docs.py
```

#### 10. `check_waiting_docs.py`
- **功能**: 检查等待处理的文档
- **用途**: 查看pending状态的文档
- **输出**: 等待文档列表及相关信息
- **使用场景**: 检查处理队列
- **依赖**: ext_database, models

```bash
python check_waiting_docs.py
```

#### 11. `check_waiting_simple.py`
- **功能**: 简单检查等待文档
- **用途**: 快速查看pending文档
- **输出**: 等待文档的基本信息
- **使用场景**: 快速检查队列状态
- **依赖**: SQLAlchemy（轻量级）

```bash
python check_waiting_simple.py
```

#### 12. `check_status_counts.py`
- **功能**: 统计各状态文档数量
- **用途**: 获取状态分布统计
- **输出**: 每种状态的文档数量
- **使用场景**: 监控整体处理情况
- **依赖**: psycopg2

```bash
python check_status_counts.py
```

#### 13. `check_embedding_status.py`
- **功能**: 检查文档嵌入状态
- **用途**: 查看文档和segment的embedding状态
- **输出**: 文档及其segment的详细状态
- **使用场景**: 排查embedding问题
- **依赖**: SQLAlchemy

```bash
python check_embedding_status.py
```

#### 14. `check_process_rule.py`
- **功能**: 检查数据集处理规则
- **用途**: 查看process rule配置
- **输出**: 处理规则的mode和rules配置
- **使用场景**: 验证处理规则配置
- **依赖**: SQLAlchemy

```bash
python check_process_rule.py
```

### 配置检查

#### 15. `check_plugin_config.py`
- **功能**: 检查插件配置
- **用途**: 查看plugin数据库的配置表
- **输出**: 插件配置表结构
- **使用场景**: 验证插件配置
- **依赖**: psycopg2（连接dify_plugin数据库）

```bash
python check_plugin_config.py
```

#### 16. `check_plugin_declaration.py`
- **功能**: 检查插件声明
- **用途**: 查看dify_extractor插件的声明信息
- **输出**: 插件声明的JSON配置
- **使用场景**: 验证插件注册
- **依赖**: psycopg2

```bash
python check_plugin_declaration.py
```

#### 17. `check_dify_extractor_config.py`
- **功能**: 检查dify_extractor工具配置
- **用途**: 查看extractor工具的配置
- **输出**: 工具配置表结构和数据
- **使用场景**: 排查extractor问题
- **依赖**: psycopg2

```bash
python check_dify_extractor_config.py
```

### 环境检查

#### 18. `check_gitea_env.py`
- **功能**: 检查Gitea环境变量
- **用途**: 验证Gitea配置是否正确
- **输出**: GITEA_URL, GITEA_OWNER, GITEA_REPO, GITEA_TOKEN
- **使用场景**: 配置验证
- **依赖**: dotenv

```bash
python check_gitea_env.py
```

### 应用检查

#### 19. `check_beta_apps.py`
- **功能**: 检查Beta应用
- **用途**: 查看Beta应用申请列表
- **输出**: Beta应用的详细信息
- **使用场景**: 管理Beta测试用户
- **依赖**: app, ext_database, models

```bash
python check_beta_apps.py
```

---

## 🚀 触发脚本（Trigger Scripts）

#### 1. `trigger_index.py`
- **功能**: 触发文档索引
- **用途**: 手动触发文档索引任务
- **使用场景**: 重新索引文档
- **依赖**: app_factory, services

```bash
python trigger_index.py
```

#### 2. `trigger_indexing.py`
- **功能**: 触发索引任务
- **用途**: 批量触发索引
- **使用场景**: 批量处理文档
- **依赖**: app_factory, services

```bash
python trigger_indexing.py
```

#### 3. `trigger_one_doc.py`
- **功能**: 触发单个文档索引
- **用途**: 处理特定文档
- **参数**: document_id
- **使用场景**: 单个文档重新处理
- **依赖**: app_factory, services

```bash
python trigger_one_doc.py <document_id>
```

#### 4. `trigger_simple.py`
- **功能**: 简单触发
- **用途**: 快速触发索引
- **使用场景**: 简单的触发操作
- **依赖**: 轻量级依赖

```bash
python trigger_simple.py
```

#### 5. `trigger_waiting_docs.py`
- **功能**: 触发等待中的文档
- **用途**: 处理所有pending状态的文档
- **使用场景**: 批量处理等待队列
- **依赖**: app_factory, services

```bash
python trigger_waiting_docs.py
```

#### 6. `queue_document.py`
- **功能**: 将文档加入处理队列
- **用途**: 手动将文档加入队列
- **使用场景**: 重新排队处理
- **依赖**: app_factory, services

```bash
python queue_document.py
```

---

## 🔧 修复脚本（Fix/Reset/Reindex Scripts）

#### 1. `fix_documents_process_rule.py`
- **功能**: 修复文档处理规则
- **用途**: 修复process_rule_id为空的文档
- **输出**: 修复的文档数量
- **使用场景**: 批量修复配置问题
- **依赖**: app_factory, ext_database, models

```bash
python fix_documents_process_rule.py
```

#### 2. `reindex_all_error_docs.py`
- **功能**: 重新索引所有错误文档
- **用途**: 批量重试失败的文档
- **使用场景**: 修复后批量重新处理
- **依赖**: app_factory, services

```bash
python reindex_all_error_docs.py
```

#### 3. `reindex_completed_docs.py`
- **功能**: 重新索引已完成的文档
- **用途**: 重新处理成功的文档
- **使用场景**: 更新索引、重新embedding
- **依赖**: app_factory, services

```bash
python reindex_completed_docs.py
```

#### 4. `reset_all_errors.py`
- **功能**: 重置所有错误状态
- **用途**: 将error状态改为pending
- **使用场景**: 批量重置后重新处理
- **依赖**: app_factory, ext_database

```bash
python reset_all_errors.py
```

#### 5. `reset_docs_for_reindex.py`
- **功能**: 重置文档以便重新索引
- **用途**: 准备文档重新处理
- **使用场景**: 清理状态后重新索引
- **依赖**: app_factory, ext_database

```bash
python reset_docs_for_reindex.py
```

#### 6. `retry_failed_docs.py`
- **功能**: 重试失败的文档
- **用途**: 自动重试error状态的文档
- **使用场景**: 定期重试失败任务
- **依赖**: app_factory, services

```bash
python retry_failed_docs.py
```

#### 7. `fix_admin_role.py`
- **功能**: 修复管理员角色
- **用途**: 修复管理员权限问题
- **使用场景**: 权限修复
- **依赖**: app_factory, ext_database, models

```bash
python fix_admin_role.py
```

---

## 🧪 测试脚本（Test Scripts）

#### 1. `test_document_indexing.py`
- **功能**: 测试文档索引功能
- **用途**: 测试单个文档的索引流程
- **使用场景**: 功能测试、问题复现
- **依赖**: app_factory, services

```bash
python test_document_indexing.py
```

#### 2. `test_gitea_config.py`
- **功能**: 测试Gitea配置API
- **用途**: 验证Gitea配置接口
- **使用场景**: 配置测试
- **依赖**: app_factory

```bash
python test_gitea_config.py
```

---

## ⚙️ 配置脚本（Config Scripts）

#### 1. `save_gitea_config.py`
- **功能**: 保存Gitea配置
- **用途**: 持久化Gitea配置
- **使用场景**: 配置管理
- **依赖**: app_factory, services

```bash
python save_gitea_config.py
```

---

## 👤 管理脚本（Admin Scripts）

#### 1. `create_admin.py`
- **功能**: 创建管理员用户
- **用途**: 初始化管理员账户
- **使用场景**: 系统初始化
- **依赖**: app_factory, ext_database, models

```bash
python create_admin.py
```

#### 2. `restore_admin.py`
- **功能**: 恢复管理员账户
- **用途**: 恢复被删除的管理员
- **使用场景**: 账户恢复
- **依赖**: app_factory, ext_database, models

```bash
python restore_admin.py
```

---

## 📋 脚本依赖分析

### 按依赖类型分类

#### 完整App依赖（需要加载整个应用）
- check_all_docs_status.py
- check_latest_doc.py
- check_successful_docs.py
- check_waiting_docs.py
- check_beta_apps.py
- 所有trigger_*.py
- 所有fix_*.py
- 所有test_*.py
- create_admin.py
- restore_admin.py

#### 轻量级依赖（仅SQLAlchemy）
- check_docs_simple.py
- check_specific_doc.py
- check_error_docs.py
- check_waiting_simple.py
- check_embedding_status.py
- check_process_rule.py

#### 直接数据库连接（psycopg2）
- check_doc_status.py
- check_doc_details.py
- check_status_counts.py
- check_successful_doc.py
- check_plugin_config.py
- check_plugin_declaration.py
- check_dify_extractor_config.py

#### 环境变量依赖
- check_gitea_env.py

---

## 🎯 使用建议

### 日常监控流程
```bash
# 1. 查看整体状态
python check_status_counts.py

# 2. 检查错误文档
python check_error_docs.py

# 3. 检查等待文档
python check_waiting_simple.py
```

### 问题排查流程
```bash
# 1. 查看具体文档
python check_specific_doc.py

# 2. 检查处理规则
python check_process_rule.py

# 3. 检查embedding状态
python check_embedding_status.py
```

### 批量修复流程
```bash
# 1. 修复处理规则
python fix_documents_process_rule.py

# 2. 重置错误状态
python reset_all_errors.py

# 3. 触发重新处理
python trigger_waiting_docs.py
```

---

## 📝 注意事项

1. **硬编码的dataset_id**: 大部分脚本中硬编码了 `dataset_id='36adfd03-f829-4eb6-a3b5-041064ef714a'`，使用前需要修改
2. **数据库连接**: 部分脚本直接使用psycopg2连接，密码硬编码为 `difyai123456`
3. **依赖加载**: 完整app依赖的脚本启动较慢，轻量级脚本更适合快速检查
4. **并发安全**: 修复类脚本可能涉及数据修改，注意并发执行的安全性

---

## 🔄 建议的重构方向

1. **参数化**: 将硬编码的dataset_id改为命令行参数
2. **统一配置**: 使用.env文件统一管理数据库连接
3. **工具类封装**: 将常用功能封装为工具类
4. **日志规范**: 统一日志格式和输出
5. **错误处理**: 添加完善的异常处理
6. **文档完善**: 为每个脚本添加详细的docstring
