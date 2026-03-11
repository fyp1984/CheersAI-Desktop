CheersAI Desktop 启动说明
============================

前置要求：
  - Docker Desktop 已安装并运行
  - Ollama 已安装
  - Python (uv) 已安装
  - Node.js 和 pnpm 已安装

启动项目：
  双击运行 start-all.bat

停止项目：
  双击运行 stop-all.bat 或直接关闭启动窗口

说明：
  - 运行脚本后会启动所有服务：
    * Docker 服务 (PostgreSQL, Redis, Weaviate, Plugin Daemon)
    * Ollama 本地模型服务
    * Celery Worker (异步任务处理)
    * Celery Beat (定时任务调度)
    * 后端 API 服务
    * 前端 Web 服务
  - 保持CMD窗口打开，服务将持续运行
  - 关闭CMD窗口，所有服务将自动停止
  - 启动完成后会自动打开浏览器访问 http://localhost:3000

服务地址：
  前端应用:       http://localhost:3000
  后端API:        http://127.0.0.1:5001
  Ollama:         http://localhost:11434
  PostgreSQL:     localhost:5432 (用户: postgres, 密码: difyai123456)
  Redis:          localhost:6700 (密码: difyai123456)
  Weaviate:       http://localhost:8080
  Plugin Daemon:  http://localhost:5002

注意事项：
  - 首次启动需要下载 Docker 镜像，可能需要较长时间
  - 确保 Docker Desktop 正在运行
  - 确保端口 3000, 5001, 5002, 5432, 6700, 8080, 11434 未被占用
  - 如需停止服务，可以关闭CMD窗口或运行 stop-all.bat

故障排查：
  - 如果服务启动失败，检查 Docker Desktop 是否运行
  - 如果端口冲突，修改 docker-compose.dev.yaml 中的端口映射
  - 查看 logs/ 目录下的日志文件获取详细错误信息
