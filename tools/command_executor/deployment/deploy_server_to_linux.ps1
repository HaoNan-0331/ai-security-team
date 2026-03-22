# 服务端部署到 Linux 服务器脚本
# 目标服务器: 192.168.181.132
# 用户: root

$SERVER_HOST = "192.168.181.132"
$SERVER_USER = "root"
$SERVER_PASSWORD = "Qch@2025"
$REMOTE_DIR = "/opt/command_executor"
$PROJECT_DIR = "E:\knowlegdge_base\python_project\command_executor"

Write-Host "=== 开始部署服务端到 Linux 服务器 ===" -ForegroundColor Cyan
Write-Host "目标服务器: $SERVER_HOST" -ForegroundColor Yellow
Write-Host ""

# 使用 plink (PuTTY) 进行 SSH 连接和命令执行
# 检查是否有 plink 或 pscp
$PLINK_PATH = "plink.exe"
$PSCP_PATH = "pscp.exe"

# 检查是否安装了 PuTTY 工具
$HAS_PLINK = Get-Command $PLINK_PATH -ErrorAction SilentlyContinue
$HAS_PSCP = Get-Command $PSCP_PATH -ErrorAction SilentlyContinue

if (-not $HAS_PLINK -or -not $HAS_PSCP) {
    Write-Host "错误: 需要安装 PuTTY 工具 (plink.exe 和 pscp.exe)" -ForegroundColor Red
    Write-Host "请从 https://www.putty.org/ 下载并安装" -ForegroundColor Yellow
    exit 1
}

# Step 1: 创建远程目录
Write-Host "[1/6] 创建远程目录..." -ForegroundColor Green
& $PLINK_PATH -pw $SERVER_PASSWORD "$SERVER_USER@$SERVER_HOST" "mkdir -p $REMOTE_DIR/server $REMOTE_DIR/shared $REMOTE_DIR/logs"
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ 目录创建成功" -ForegroundColor Green
} else {
    Write-Host "  ✗ 目录创建失败" -ForegroundColor Red
    exit 1
}

# Step 2: 上传服务端文件
Write-Host "[2/6] 上传服务端文件..." -ForegroundColor Green

$SERVER_FILES = @(
    "server/main.py",
    "server/websocket_server.py",
    "server/api_server.py",
    "server/database.py",
    "server/config.py",
    "server/requirements.txt"
)

foreach ($file in $SERVER_FILES) {
    $localPath = Join-Path $PROJECT_DIR $file
    $remotePath = "$REMOTE_DIR/$file"
    Write-Host "  上传: $file" -NoNewline
    & $PSCP_PATH -pw $SERVER_PASSWORD $localPath "$SERVER_USER@$SERVER_HOST`:$remotePath" | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓" -ForegroundColor Green
    } else {
        Write-Host " ✗" -ForegroundColor Red
    }
}

# Step 3: 上传共享模块
Write-Host "[3/6] 上传共享模块..." -ForegroundColor Green
$SHARED_FILES = @("shared/models.py")

foreach ($file in $SHARED_FILES) {
    $localPath = Join-Path $PROJECT_DIR $file
    $remotePath = "$REMOTE_DIR/$file"
    Write-Host "  上传: $file" -NoNewline
    & $PSCP_PATH -pw $SERVER_PASSWORD $localPath "$SERVER_USER@$SERVER_HOST`:$remotePath" | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓" -ForegroundColor Green
    } else {
        Write-Host " ✗" -ForegroundColor Red
    }
}

# Step 4: 安装 Python 依赖
Write-Host "[4/6] 安装 Python 依赖..." -ForegroundColor Green
$INSTALL_CMD = "cd $REMOTE_DIR && pip3 install -r server/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple"
& $PLINK_PATH -pw $SERVER_PASSWORD "$SERVER_USER@$SERVER_HOST" $INSTALL_CMD
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ 依赖安装成功" -ForegroundColor Green
} else {
    Write-Host "  ✗ 依赖安装失败" -ForegroundColor Red
}

# Step 5: 停止已运行的服务端（如果有）
Write-Host "[5/6] 检查并停止已运行的服务..." -ForegroundColor Green
& $PLINK_PATH -pw $SERVER_PASSWORD "$SERVER_USER@$SERVER_HOST" "pkill -f 'python.*server/main.py' || true"
Start-Sleep -Seconds 2

# Step 6: 启动服务端
Write-Host "[6/6] 启动服务端..." -ForegroundColor Green

# 创建启动脚本
$START_SCRIPT = @"
#!/bin/bash
cd $REMOTE_DIR
nohup python3 server/main.py > logs/server.log 2>&1 &
echo \$! > logs/server.pid
echo "服务端已启动，PID: \`cat logs/server.pid\`"
"@

& $PLINK_PATH -pw $SERVER_PASSWORD "$SERVER_USER@$SERVER_HOST" "echo '$START_SCRIPT' > $REMOTE_DIR/start_server.sh && chmod +x $REMOTE_DIR/start_server.sh"

# 执行启动脚本
& $PLINK_PATH -pw $SERVER_PASSWORD "$SERVER_USER@$SERVER_HOST" "cd $REMOTE_DIR && ./start_server.sh"

Write-Host ""
Write-Host "=== 部署完成 ===" -ForegroundColor Cyan
Write-Host "服务端已在后台启动" -ForegroundColor Green
Write-Host "查看日志: ssh root@$SERVER_HOST 'tail -f $REMOTE_DIR/logs/server.log'" -ForegroundColor Yellow
Write-Host "停止服务: ssh root@$SERVER_HOST 'cd $REMOTE_DIR && cat logs/server.pid | xargs kill'" -ForegroundColor Yellow
