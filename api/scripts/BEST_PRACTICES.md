# 脚本使用最佳实践

## 🎯 使用原则

### 1. 先检查，后操作
在执行任何修复或触发操作前，先用检查脚本了解当前状态。

```bash
# ❌ 错误做法：直接修复
python fix_documents_process_rule.py

# ✅ 正确做法：先检查再修复
python check_process_rule.py          # 查看当前规则
python check_error_docs.py            # 查看错误文档
python fix_documents_process_rule.py  # 确认问题后再修复
python check_error_docs.py            # 验证修复结果
```

### 2. 从轻量级脚本开始
优先使用轻量级脚本（不加载完整app），速度更快。

```bash
# ✅ 快速检查（轻量级）
python check_docs_simple.py
python check_waiting_simple.py
python check_status_counts.py

# ⚠️ 详细检查（完整app，较慢）
python check_all_docs_status.py
python check_waiting_docs.py
```

### 3. 逐步深入排查
从整体到局部，从简单到复杂。

```bash
# 第1步：整体概览
python check_status_counts.py

# 第2步：查看问题文档
python check_error_docs.py

# 第3步：深入分析特定文档
python check_specific_doc.py

# 第4步：检查相关配置
python check_process_rule.py
python check_embedding_status.py
```

---

## 📊 常见场景处理流程

### 场景1：文档一直处于等待状态

```bash
# 1. 确认等待文档数量
python check_status_counts.py

# 2. 查看等待文档详情
python check_waiting_simple.py

# 3. 检查处理规则配置
python check_process_rule.py

# 4. 如果规则有问题，修复它
python fix_documents_process_rule.py

# 5. 触发处理
python trigger_waiting_docs.py

# 6. 验证结果
python check_status_counts.py
```

### 场景2：大量文档处理失败

```bash
# 1. 统计错误数量
python check_status_counts.py

# 2. 查看错误详情
python check_error_docs.py

# 3. 分析具体错误原因
python check_specific_doc.py  # 查看某个错误文档

# 4. 检查配置
python check_process_rule.py
python check_plugin_config.py
python check_dify_extractor_config.py

# 5. 修复配置问题后，重置错误状态
python reset_all_errors.py

# 6. 重新触发处理
python trigger_waiting_docs.py

# 7. 监控处理结果
python check_status_counts.py
```

### 场景3：新上传文档验证

```bash
# 1. 查看最新文档
python check_latest_doc.py

# 2. 检查文档详情
python check_specific_doc.py

# 3. 如果需要，手动触发
python trigger_one_doc.py <document_id>

# 4. 验证处理结果
python check_specific_doc.py
```

### 场景4：Embedding问题排查

```bash
# 1. 检查embedding状态
python check_embedding_status.py

# 2. 查看具体文档的segment
python check_specific_doc.py

# 3. 如果需要重新embedding
python reindex_completed_docs.py  # 或
python reindex_all_error_docs.py
```

### 场景5：插件配置问题

```bash
# 1. 检查插件声明
python check_plugin_declaration.py

# 2. 检查插件配置
python check_plugin_config.py

# 3. 检查extractor配置
python check_dify_extractor_config.py

# 4. 检查环境变量
python check_gitea_env.py
```

---

## ⚠️ 注意事项

### 硬编码问题

大部分脚本中硬编码了以下内容，使用前需要修改：

#### 1. Dataset ID
```python
# 当前硬编码
dataset_id='36adfd03-f829-4eb6-a3b5-041064ef714a'

# 建议修改方式
import sys
dataset_id = sys.argv[1] if len(sys.argv) > 1 else '36adfd03-f829-4eb6-a3b5-041064ef714a'
```

#### 2. 数据库连接
```python
# 当前硬编码
conn = psycopg2.connect(
    host="127.0.0.1",
    port=5432,
    database="dify",
    user="postgres",
    password="difyai123456"
)

# 建议使用环境变量
import os
from dotenv import load_dotenv
load_dotenv()

db_url = os.getenv('DB_URI', 'postgresql://postgres:difyai123456@localhost:5432/dify')
```

#### 3. Document ID
```python
# 某些脚本硬编码了document_id
document_id = '8c2eb51f-927c-4ede-8c2c-02613045f904'

# 建议改为参数
import sys
if len(sys.argv) < 2:
    print("Usage: python script.py <document_id>")
    sys.exit(1)
document_id = sys.argv[1]
```

### 数据安全

#### 1. 备份数据
在执行修复类脚本前，建议备份数据：

```bash
# PostgreSQL备份
pg_dump -U postgres -d dify > backup_$(date +%Y%m%d_%H%M%S).sql

# 或者只备份相关表
pg_dump -U postgres -d dify -t documents -t document_segments > backup_docs.sql
```

#### 2. 测试环境验证
先在测试环境验证脚本效果：

```bash
# 修改.env使用测试数据库
DB_URI=postgresql://postgres:password@localhost:5432/dify_test

# 运行脚本
python fix_documents_process_rule.py
```

#### 3. 小批量测试
对于批量操作，先小批量测试：

```python
# 在脚本中添加limit
docs = db.session.query(Document).filter_by(
    indexing_status='error'
).limit(10).all()  # 先处理10个测试
```

### 并发安全

#### 1. 避免并发修改
不要同时运行多个修复脚本：

```bash
# ❌ 错误：同时运行
python fix_documents_process_rule.py &
python reset_all_errors.py &

# ✅ 正确：顺序执行
python fix_documents_process_rule.py
python reset_all_errors.py
```

#### 2. 检查锁状态
某些操作可能被celery任务锁定：

```bash
# 检查celery任务状态
celery -A celery_app inspect active
```

---

## 🔧 脚本改进建议

### 1. 添加命令行参数

使用argparse添加参数支持：

```python
#!/usr/bin/env python
"""Check document status with parameters."""
import argparse
from sqlalchemy import create_engine, text

def main():
    parser = argparse.ArgumentParser(description='Check document status')
    parser.add_argument('--dataset-id', required=True, help='Dataset ID')
    parser.add_argument('--status', help='Filter by status')
    parser.add_argument('--limit', type=int, default=10, help='Limit results')
    
    args = parser.parse_args()
    
    # 使用参数
    query = f"""
        SELECT id, name, indexing_status
        FROM documents
        WHERE dataset_id = '{args.dataset_id}'
    """
    
    if args.status:
        query += f" AND indexing_status = '{args.status}'"
    
    query += f" LIMIT {args.limit}"
    
    # 执行查询...

if __name__ == '__main__':
    main()
```

### 2. 统一配置管理

创建配置文件：

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_URI = os.getenv('DB_URI', 'postgresql://postgres:difyai123456@localhost:5432/dify')
    PLUGIN_DB_URI = os.getenv('PLUGIN_DB_URI', 'postgresql://postgres:difyai123456@localhost:5432/dify_plugin')
    DEFAULT_DATASET_ID = os.getenv('DEFAULT_DATASET_ID', '36adfd03-f829-4eb6-a3b5-041064ef714a')

# 在脚本中使用
from config import Config
dataset_id = Config.DEFAULT_DATASET_ID
```

### 3. 添加日志

使用logging模块：

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Starting document check...")
logger.warning("Found 5 error documents")
logger.error("Failed to connect to database")
```

### 4. 错误处理

添加完善的异常处理：

```python
try:
    # 数据库操作
    result = conn.execute(query)
except psycopg2.Error as e:
    logger.error(f"Database error: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    sys.exit(1)
finally:
    if conn:
        conn.close()
```

---

## 📝 脚本模板

### 检查脚本模板

```python
#!/usr/bin/env python
"""
Script description here.

Usage:
    python script_name.py [options]

Examples:
    python script_name.py --dataset-id xxx
"""
import argparse
import logging
import sys
from sqlalchemy import create_engine, text

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Script description')
    parser.add_argument('--dataset-id', required=True, help='Dataset ID')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        # 主要逻辑
        logger.info("Starting...")
        
        # 数据库操作
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT ..."))
            # 处理结果
        
        logger.info("Completed successfully")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

---

## 🚀 快速参考

### 最常用的5个脚本

1. **check_status_counts.py** - 快速查看整体状态
2. **check_error_docs.py** - 查看错误文档
3. **check_waiting_simple.py** - 查看等待文档
4. **trigger_waiting_docs.py** - 触发等待文档
5. **fix_documents_process_rule.py** - 修复处理规则

### 推荐的检查顺序

```bash
# 日常检查（每天）
python check_status_counts.py

# 发现问题时
python check_error_docs.py
python check_waiting_simple.py
python check_specific_doc.py

# 深入分析
python check_embedding_status.py
python check_process_rule.py
```

---

## 📚 相关文档

- [脚本详细目录](./SCRIPTS_CATALOG.md)
- [脚本整理说明](../SCRIPTS_ORGANIZATION.md)
- [快速参考](../QUICK_REFERENCE.md)
- [文档索引](../docs/README.md)
