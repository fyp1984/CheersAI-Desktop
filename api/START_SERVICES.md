# 服务启动说明

## 必需的服务

### 1. 中间件服务（Docker）
```bash
cd docker
docker-compose -f docker-compose.middleware.yaml up -d
```

### 2. Celery Worker（处理异步任务）
```bash
cd api
python -m uv run celery -A app.celery worker -P gevent -c 1 --loglevel INFO -Q dataset,priority_dataset,pipeline,priority_pipeline,generation,mail,ops_trace,app_deletion
```

**重要**: 必须包含以下队列，否则相关功能无法正常工作：
- `dataset`, `priority_dataset`: 文档索引任务
- `pipeline`, `priority_pipeline`: RAG Pipeline 文档处理任务
- `generation`: 生成任务
- `mail`: 邮件发送任务
- `ops_trace`: 操作追踪任务
- `app_deletion`: 应用删除任务

### 3. Celery Beat（定时任务调度器）
```bash
cd api
python -m uv run celery -A app.celery beat --loglevel INFO
```

包含的定时任务：
- `auto_fix_documents_process_rule`: 每2分钟自动修复缺少处理规则的文档

### 4. Flask API 服务
```bash
cd api
python -m uv run flask run --host 0.0.0.0 --port=5001 --debug
```

### 5. Next.js 前端服务
```bash
cd web
pnpm dev:inspect
```

## 常见问题

### 文档一直显示"排队中"

**原因**: Celery Worker 没有监听必需的队列

**解决方案**: 
1. 停止当前的 Celery Worker
2. 使用上面的完整命令重新启动，确保包含所有队列：
   - `-Q dataset,priority_dataset,pipeline,priority_pipeline,generation,mail,ops_trace,app_deletion`

**特别注意**:
- 直接上传文档需要 `priority_dataset` 队列
- 通过 RAG Pipeline 上传需要 `pipeline` 或 `priority_pipeline` 队列

### 如何检查服务状态

```bash
# 检查 Docker 容器
docker ps

# 检查 Celery Worker 日志
# 查看正在运行的 worker 进程

# 检查 Flask 日志
# 查看 Flask 进程输出

# 检查文档索引状态
cd api
python -m uv run flask shell
>>> from extensions.ext_database import db
>>> from models.dataset import Document
>>> docs = db.session.query(Document).filter_by(indexing_status='waiting').all()
>>> print(f"Waiting documents: {len(docs)}")
```

## 端口使用

- Flask API: 5001
- Next.js: 3000
- PostgreSQL: 5432
- Redis: 6379
- Weaviate: 8080
- Ollama: 11434
