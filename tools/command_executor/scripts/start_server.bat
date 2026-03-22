@echo off
chcp 65001 >nul
title 命令执行系统 - 服务端

echo ========================================
echo   命令执行系统 - 服务端启动脚本
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

echo [1/3] 检查依赖...
cd server
pip install -r requirements.txt -q

echo [2/3] 检查PostgreSQL...
echo 请确保PostgreSQL已安装并运行
echo 数据库名称: command_executor
echo.

echo [3/3] 启动服务端...
echo.

python main.py

pause
