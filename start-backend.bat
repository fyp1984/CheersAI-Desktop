@echo off
REM CheersAI 后端启动脚本
REM 使用方法: start-backend.bat

echo 正在启动 CheersAI 后端服务...

cd /d "%~dp0api"

REM 检查 .env 文件
if not exist ".env" (
    echo 警告: .env 文件不存在，请先配置环境变量
    echo 你可以复制 .env.example 并重命名为 .env
)

REM 运行数据库迁移
echo.
echo 正在运行数据库迁移...
python -m uv run flask db upgrade

REM 启动 Flask 开发服务器
echo.
echo 正在启动 Flask 开发服务器...
echo 后端 API 地址: http://localhost:5001
echo 按 Ctrl+C 停止服务器
echo.

python -m uv run flask run --host 0.0.0.0 --port=5001 --debug
