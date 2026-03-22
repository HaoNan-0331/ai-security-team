@echo off
REM ========================================
REM 分布式命令执行系统 - 客户端打包脚本
REM ========================================

REM 切换到项目根目录
cd /d "%~dp0.."

echo.
echo ========================================
echo   分布式命令执行系统 - 客户端打包工具
echo ========================================
echo.

REM 检查 PyInstaller 是否安装
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 PyInstaller，正在安装...
    pip install pyinstaller
    if errorlevel 1 (
        echo [错误] PyInstaller 安装失败！
        pause
        exit /b 1
    )
)

echo [1/3] 正在清理旧的构建文件...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

echo [2/3] 正在打包客户端（这可能需要几分钟）...
python -m PyInstaller scripts\build_client.spec --clean

if errorlevel 1 (
    echo.
    echo [错误] 打包失败！请检查错误信息。
    pause
    exit /b 1
)

echo [3/3] 正在清理临时文件...
if exist "build" rmdir /s /q build

echo.
echo ========================================
echo   打包完成！
echo ========================================
echo.
echo 生成的文件位置:
echo   dist\CommandExecutorClient.exe
echo.
echo 使用说明:
echo   1. 将 CommandExecutorClient.exe 复制到目标机器
echo   2. 首次运行时会自动配置向导
echo   3. 或者手动创建 client_config.json 配置文件
echo.

REM 询问是否打开输出目录
set /p opendir="是否打开输出目录？(y/n): "
if /i "%opendir%"=="y" (
    explorer dist
)

pause
