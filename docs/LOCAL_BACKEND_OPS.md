# 本地后端服务运维操作手册

## 1. 环境概览

- 项目根目录：
  - `/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/cheersAIdesktop`
- 使用组件：
  - 中间件（通过 `docker-compose.dev.yaml` 在 Docker 中运行）：
    - Postgres：`localhost:5432`
      - 用户：`postgres`
      - 密码：`difyai123456`
      - 数据库：`dify`
    - Redis：`localhost:6379`
      - 密码：`difyai123456`
    - Weaviate：`localhost:8080`
      - API Key：`WVF5YThaHlkYwhGUSmCRgsX3tD5ngdN8pkih`
    - Plugin Daemon：仅在 Docker 内部使用，不暴露宿主端口
  - 后端 API：
    - 代码路径：`api/`
    - 运行方式：`uv run --project api flask run --port=5001`
    - 监听地址：`http://localhost:5001`

## 2. 关键配置

### 2.1 Docker dev 中间件

配置文件：  
`docker-compose.dev.yaml`

- Postgres

  ```yaml
  services:
    postgres:
      image: postgres:15-alpine
      container_name: dify-postgres
      environment:
        POSTGRES_USER: postgres
        POSTGRES_PASSWORD: difyai123456
        POSTGRES_DB: dify
      ports:
        - "5432:5432"
  ```

- Redis

  ```yaml
  services:
    redis:
      image: redis:7-alpine
      container_name: dify-redis
      command: redis-server --requirepass difyai123456
      ports:
        - "6379:6379"
  ```

- Weaviate

  ```yaml
  services:
    weaviate:
      image: semitechnologies/weaviate:1.19.0
      container_name: dify-weaviate
      ports:
        - "8080:8080"
  ```

- Plugin Daemon（已不暴露 5002/5003）

  ```yaml
  services:
    plugin_daemon:
      image: langgenius/dify-plugin-daemon:0.5.3-local
      container_name: dify-plugin-daemon
      environment:
        REDIS_HOST: redis
        REDIS_PORT: 6379
        REDIS_PASSWORD: difyai123456
        SERVER_PORT: 5002
        ...
      #ports:
      #  - "5002:5002"
      #  - "5003:5003"
  ```

### 2.2 后端 API `.env`

配置文件：  
`api/.env`（只列关键字段）

```env
# ===== Database Configuration =====
DATABASE_URL=postgresql://postgres:difyai123456@localhost:5432/dify
DB_USERNAME=postgres
DB_PASSWORD=difyai123456
DB_HOST=localhost
DB_PORT=5432
DB_DATABASE=dify

# ===== Redis Configuration =====
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=difyai123456

# ===== Vector Store Configuration =====
WEAVIATE_ENABLED=true
WEAVIATE_API_KEY=WVF5YThaHlkYwhGUSmCRgsX3tD5ngdN8pkih
WEAVIATE_ENDPOINT=http://localhost:8080

# ===== Celery Configuration =====
CELERY_BROKER_URL=redis://:difyai123456@localhost:6379/1
CELERY_RESULT_BACKEND=redis://:difyai123456@localhost:6379/2
```

## 3. 工具依赖

- Docker Desktop（包含 docker / docker compose）
- Python + uv（项目推荐）
  - 命令：`uv sync` / `uv run --project api ...`

确保 `uv` 和 `docker` 命令在 PATH 中可用。

## 4. 服务启动与停止

### 4.1 启动所有服务（中间件 + API）

推荐使用脚本 `dev/local_backend.sh`：

```bash
cd /Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/cheersAIdesktop
./dev/local_backend.sh start
```

脚本会执行：

- Docker 中间件：`docker compose -f docker-compose.dev.yaml up -d`
- 后端 API：`uv run --project api flask run --host 0.0.0.0 --port=5001 --debug`（后台运行，写日志到 `logs/api-dev.log`）

### 4.2 停止所有服务

```bash
cd /Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/cheersAIdesktop
./dev/local_backend.sh stop
```

脚本会：

- 停止 Flask API 进程（通过 PID 文件）
- 停止 Docker 中间件：`docker compose -f docker-compose.dev.yaml down`（保留数据卷）

### 4.3 一键重启所有服务

```bash
cd /Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/cheersAIdesktop
./dev/local_backend.sh restart
```

等价于先 `stop` 再 `start`。

## 5. 服务状态与日志

### 5.1 查看当前状态

```bash
./dev/local_backend.sh status
```

会显示：

- Docker 中间件状态：`docker compose -f docker-compose.dev.yaml ps`
- Flask API 是否在运行（通过 PID 检查）

### 5.2 查看后端 API 日志

```bash
./dev/local_backend.sh logs
```

等价于：

```bash
tail -n 100 -f logs/api-dev.log
```

## 6. 手动操作命令（备忘）

### 6.1 Docker 中间件

- 启动：

  ```bash
  cd /Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/cheersAIdesktop
  docker compose -f docker-compose.dev.yaml up -d
  ```

- 停止（保留数据）：

  ```bash
  docker compose -f docker-compose.dev.yaml down
  ```

- 停止并清空所有数据（慎用）：

  ```bash
  docker compose -f docker-compose.dev.yaml down -v
  ```

### 6.2 后端 API

- 安装/更新依赖：

  ```bash
  uv sync --project api
  ```

- 执行数据库迁移：

  ```bash
  uv run --project api flask upgrade-db
  ```

- 启动 API（前台运行）：

  ```bash
  uv run --project api flask run --host 0.0.0.0 --port=5001 --debug
  ```

## 7. 验证服务

- 健康检查（控制台 API）：

  ```bash
  curl -i http://localhost:5001/console/api/ping
  ```

  预期返回：

  ```json
  {"result":"pong"}
  ```

- 后端 API 文档（FastOpenAPI）：

  - 浏览器访问：`http://localhost:5001/fastopenapi/docs`
  - OpenAPI JSON：`http://localhost:5001/fastopenapi/openapi.json`

如果上述两个访问正常，说明当前本地后端环境工作正常。
