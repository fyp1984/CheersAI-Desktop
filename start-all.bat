@echo off
chcp 65001 >nul
title CheersAI Desktop - 运行中 (关闭此窗口将停止所有服务)

echo ========================================
echo   CheersAI Desktop 启动中...
echo ========================================
echo.

:: 创建日志目录
if not exist "logs" mkdir logs

echo [1/7] 启动 Docker 服务 (PostgreSQL, Redis, Weaviate, Plugin Daemon)...
docker-compose -f docker-compose.dev.yaml up -d
timeout /t 5 /nobreak >nul
echo       ✓ Docker 服务已启动

echo [2/7] 等待数据库就绪...
timeout /t 10 /nobreak >nul
echo       ✓ 数据库已就绪

echo [3/7] 初始化数据库...
cd /d "%~dp0api"
uv run --project . flask db upgrade >nul 2>&1
if %errorlevel% equ 0 (
    echo       ✓ 数据库初始化完成
) else (
    echo       ⚠ 数据库可能已初始化或需要手动检查
)
cd /d "%~dp0"

echo [4/7] 启动 Ollama 服务...
start "Ollama" /MIN ollama serve
timeout /t 2 /nobreak >nul
echo       ✓ Ollama 已启动

echo [5/7] 启动 Celery Worker...
cd /d "%~dp0api"
start "Celery Worker" /MIN cmd /c "uv run --project . celery -A celery_entrypoint worker -P gevent -c 1 --loglevel INFO -Q dataset,generation,mail,ops_trace,app_deletion"
cd /d "%~dp0"
timeout /t 3 /nobreak >nul
echo       ✓ Celery Worker 已启动

echo [6/7] 启动 Celery Beat...
cd /d "%~dp0api"
start "Celery Beat" /MIN cmd /c "uv run --project . celery -A celery_entrypoint beat --loglevel INFO"
cd /d "%~dp0"
timeout /t 2 /nobreak >nul
echo       ✓ Celery Beat 已启动

echo [6/7] 启动后端 API 服务...
cd /d "%~dp0api"
start "Backend API" /MIN cmd /c "uv run flask run --host 0.0.0.0 --port=5001 --debug"
cd /d "%~dp0"
timeout /t 3 /nobreak >nul
echo       ✓ 后端 API 已启动 (http://127.0.0.1:5001)

echo [7/7] 启动前端 Web 服务...
cd /d "%~dp0web"
start "Frontend Web" /MIN cmd /c "pnpm dev"
cd /d "%~dp0"
timeout /t 5 /nobreak >nul
echo       ✓ 前端 Web 已启动 (http://localhost:3000)

echo.
echo ========================================
echo   所有服务启动完成！
echo ========================================
echo.
echo   前端应用:       http://localhost:3000
echo   后端 API:       http://127.0.0.1:5001
echo   Ollama:         http://localhost:11434
echo   PostgreSQL:     localhost:5432
echo   Redis:          localhost:6700
echo   Weaviate:       http://localhost:8080
echo   Plugin Daemon:  http://localhost:5002
echo.
echo   [重要] 关闭此窗口将自动停止所有服务
echo.
echo   按任意键打开浏览器...
pause >nul

start http://localhost:3000

echo.
echo   服务运行中，请保持此窗口打开...
echo   关闭此窗口将停止所有服务
echo.

:: 保持窗口打开，等待用户关闭
:loop
timeout /t 60 /nobreak >nul
goto loop
