@echo off
chcp 65001 >nul
echo ========================================
echo    奖金计算器 Web 服务启动
echo ========================================
echo.

set PORT=8080
if not "%1"=="" set PORT=%1

python server.py %PORT%

pause
