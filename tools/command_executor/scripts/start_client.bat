@echo off
chcp 65001 >nul
title 命令执行系统 - 客户端

echo ========================================
echo   命令执行系统 - 客户端启动脚本
echo ========================================
echo.

REM 切换到项目根目录
cd /d "%~dp0.."

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.10+
    pause
    exit /b 1
)

echo [1/2] 检查依赖...
cd client
pip install -r requirements.txt -q

echo [2/2] 启动客户端...
echo.

python main.py

pause
