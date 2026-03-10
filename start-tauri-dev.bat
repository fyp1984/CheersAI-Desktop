@echo off
REM CheersAI Tauri 开发模式启动脚本

echo.
echo 启动 CheersAI Tauri 开发环境...
echo.

REM 检查数据库服务
echo 检查数据库服务...
docker ps | findstr "dify-postgres" >nul
if errorlevel 1 (
    echo 数据库服务未运行，正在启动...
    call start-database.bat
    timeout /t 5 /nobreak >nul
)

echo 数据库服务已就绪
echo.

REM 启动后端 API
echo 启动后端 API...
start "Dify Backend API" cmd /c start-backend.bat

REM 等待后端启动
echo 等待后端 API 启动...
timeout /t 10 /nobreak >nul

REM 启动前端开发服务器
echo 启动前端开发服务器...
cd web
start "Dify Frontend" cmd /c pnpm dev

REM 等待前端启动
echo 等待前端服务器启动...
timeout /t 15 /nobreak >nul

REM 启动 Tauri
echo 启动 Tauri 桌面应用...
echo.
pnpm run dev:tauri

cd ..
