@echo off
chcp 65001 >nul
title CheersAI Desktop - 停止服务

echo ========================================
echo   CheersAI Desktop 停止中...
echo ========================================
echo.

echo [1/3] 停止 Docker 服务...
docker-compose -f docker-compose.dev.yaml down
echo       ✓ Docker 服务已停止

echo [2/3] 停止 Ollama 服务...
taskkill /F /IM ollama.exe >nul 2>&1
echo       ✓ Ollama 已停止

echo [3/3] 停止其他进程...
taskkill /F /FI "WINDOWTITLE eq Celery Worker*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Celery Beat*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Backend API*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Frontend Web*" >nul 2>&1
echo       ✓ 所有进程已停止

echo.
echo ========================================
echo   所有服务已停止
echo ========================================
echo.
pause
