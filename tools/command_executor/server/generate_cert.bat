@echo off
REM 生成自签名TLS证书脚本

echo 正在生成自签名TLS证书...

REM 创建certs目录
if not exist "certs" mkdir certs

REM 生成私钥和证书（有效期10年）
openssl req -x509 -newkey rsa:4096 -keyout certs/server.key -out certs/server.crt -days 3650 -nodes -subj "/C=CN/ST=Beijing/L=Beijing/O=MyCompany/CN=192.168.10.249"

if errorlevel 1 (
    echo.
    echo [错误] 证书生成失败！
    echo 请确保已安装 OpenSSL 并添加到 PATH 环境变量
    echo.
    echo OpenSSL 下载地址: https://slproweb.com/products/Win32OpenSSL.html
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   证书生成成功！
echo ========================================
echo.
echo 证书文件: certs\server.crt
echo 私钥文件: certs\server.key
echo.
echo 请修改 server\config.py 中的以下配置:
echo   USE_TLS = True
echo   TLS_CERT = "./certs/server.crt"
echo   TLS_KEY = "./certs/server.key"
echo.
pause
