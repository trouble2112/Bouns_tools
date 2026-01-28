@echo off
cd /d "%~dp0"
:restart
echo [%date% %time%] 启动奖金计算器服务...
python server.py 8080
echo [%date% %time%] 服务异常退出，3秒后重启...
timeout /t 3
goto restart