#!/bin/bash
# ========================================
# 分布式命令执行系统 - 服务端打包脚本
# ========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 切换到项目根目录
cd "$(dirname "$0")/.."

echo ""
echo "========================================"
echo "  分布式命令执行系统 - 服务端打包工具"
echo "========================================"
echo ""

# 检查 PyInstaller 是否安装
if ! python3 -m PyInstaller --version &> /dev/null; then
    echo -e "${YELLOW}[信息]${NC} 未检测到 PyInstaller，正在安装..."
    pip3 install pyinstaller
    if [ $? -ne 0 ]; then
        echo -e "${RED}[错误]${NC} PyInstaller 安装失败！"
        exit 1
    fi
fi

# 显示 PyInstaller 版本
PYINSTALLER_VERSION=$(python3 -m PyInstaller --version)
echo -e "${GREEN}[信息]${NC} 检测到 PyInstaller $PYINSTALLER_VERSION"

# 创建输出目录
DIST_DIR="dist/linux"
mkdir -p "$DIST_DIR"

echo -e "${YELLOW}[1/5]${NC} 正在清理旧的构建文件..."
rm -rf build
rm -rf dist

echo -e "${YELLOW}[2/5]${NC} 正在打包服务端（这可能需要几分钟）..."
python3 -m PyInstaller scripts/build_server_linux.spec --clean

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}[错误]${NC} 打包失败！请检查错误信息。"
    exit 1
fi

echo -e "${YELLOW}[3/5]${NC} 正在整理输出文件..."
# 移动可执行文件到 linux 目录
mv dist/CommandExecutorServer "$DIST_DIR/"

echo -e "${YELLOW}[4/5]${NC} 正在生成 systemd 服务文件..."
# 生成 systemd 服务文件
cat > "$DIST_DIR/command-executor-server.service" << 'EOF'
[Unit]
Description=Command Executor Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/command-executor-server
ExecStart=/opt/command-executor-server/CommandExecutorServer
Restart=on-failure
RestartSec=10
StandardOutput=append:/var/log/command-executor-server/server.log
StandardError=append:/var/log/command-executor-server/server.error.log

[Install]
WantedBy=multi-user.target
EOF

echo -e "${YELLOW}[5/5]${NC} 正在生成安装脚本..."
# 生成安装脚本
cat > "$DIST_DIR/install_server.sh" << 'EOF'
#!/bin/bash
# ========================================
# Command Executor Server 安装脚本
# ========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

INSTALL_DIR="/opt/command-executor-server"
LOG_DIR="/var/log/command-executor-server"
SERVICE_NAME="command-executor-server"

echo ""
echo "========================================"
echo "  Command Executor Server 安装向导"
echo "========================================"
echo ""

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[错误]${NC} 请使用 root 权限运行此脚本"
    exit 1
fi

# 创建安装目录
echo -e "${YELLOW}[1/6]${NC} 创建安装目录..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/data"

# 复制文件
echo -e "${YELLOW}[2/6]${NC} 复制程序文件..."
cp "$(dirname "$0")/CommandExecutorServer" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/CommandExecutorServer"

# 安装 systemd 服务
echo -e "${YELLOW}[3/6]${NC} 安装 systemd 服务..."
cp "$(dirname "$0")/command-executor-server.service" /etc/systemd/system/
systemctl daemon-reload

# 设置日志权限
echo -e "${YELLOW}[4/6]${NC} 设置日志目录权限..."
chown -R root:root "$LOG_DIR"
chmod 755 "$LOG_DIR"

echo ""
echo "========================================"
echo "  安装完成！"
echo "========================================"
echo ""
echo -e "${GREEN}[服务管理]${NC}"
echo "  启动服务: systemctl start $SERVICE_NAME"
echo "  停止服务: systemctl stop $SERVICE_NAME"
echo "  重启服务: systemctl restart $SERVICE_NAME"
echo "  查看状态: systemctl status $SERVICE_NAME"
echo "  开机自启: systemctl enable $SERVICE_NAME"
echo "  查看日志: journalctl -u $SERVICE_NAME -f"
echo ""
echo -e "${GREEN}[手动运行]${NC}"
echo "  运行: $INSTALL_DIR/CommandExecutorServer"
echo ""
echo -e "${GREEN}[配置说明]${NC}"
echo "  程序目录: $INSTALL_DIR"
echo "  日志目录: $LOG_DIR"
echo "  数据目录: $INSTALL_DIR/data"
echo "  默认端口: API 8080, WebSocket 8765"
echo ""
echo -e "${YELLOW}[下一步]${NC}"
echo "  请使用 Python 脚本创建管理员用户："
echo "  python3 deployment/create_root_user.py"
echo ""

read -p "是否立即启动服务？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl start $SERVICE_NAME
    systemctl enable $SERVICE_NAME
    echo ""
    echo -e "${GREEN}[信息]${NC} 服务已启动并设置为开机自启"
    echo -e "运行 'systemctl status $SERVICE_NAME' 查看运行状态"
fi
EOF

chmod +x "$DIST_DIR/install_server.sh"

# 生成卸载脚本
cat > "$DIST_DIR/uninstall_server.sh" << 'EOF'
#!/bin/bash
# ========================================
# Command Executor Server 卸载脚本
# ========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

INSTALL_DIR="/opt/command-executor-server"
SERVICE_NAME="command-executor-server"

echo ""
echo "========================================"
echo "  Command Executor Server 卸载向导"
echo "========================================"
echo ""

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[错误]${NC} 请使用 root 权限运行此脚本"
    exit 1
fi

# 停止服务
echo -e "${YELLOW}[1/4]${NC} 停止服务..."
if systemctl is-active --quiet $SERVICE_NAME; then
    systemctl stop $SERVICE_NAME
fi

# 禁用服务
echo -e "${YELLOW}[2/4]${NC} 禁用开机自启..."
if systemctl is-enabled --quiet $SERVICE_NAME; then
    systemctl disable $SERVICE_NAME
fi

# 删除 systemd 服务文件
echo -e "${YELLOW}[3/4]${NC} 删除 systemd 服务..."
rm -f /etc/systemd/system/$SERVICE_NAME.service
systemctl daemon-reload

# 删除程序文件
echo -e "${YELLOW}[4/4]${NC} 删除程序文件..."
read -p "是否删除数据目录 $INSTALL_DIR？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$INSTALL_DIR"
fi

echo ""
echo "========================================"
echo "  卸载完成！"
echo "========================================"
EOF

chmod +x "$DIST_DIR/uninstall_server.sh"

# 生成启动脚本
cat > "$DIST_DIR/run_server.sh" << 'EOF'
#!/bin/bash
# Command Executor Server 启动脚本

INSTALL_DIR="/opt/command-executor-server"
cd "$INSTALL_DIR" || exit 1

# 确保日志目录存在
mkdir -p logs

# 启动服务
./CommandExecutorServer
EOF

chmod +x "$DIST_DIR/run_server.sh"

# 正在清理临时文件
echo -e "${YELLOW}[清理]${NC} 正在清理临时文件..."
rm -rf build

# 设置可执行权限
chmod +x "$DIST_DIR/CommandExecutorServer"
chmod +x "$DIST_DIR"/*.sh

echo ""
echo "========================================"
echo "  打包完成！"
echo "========================================"
echo ""
echo -e "${BLUE}[生成的文件]${NC}"
echo "  位置: $DIST_DIR/"
echo ""
echo "  文件列表:"
ls -lh "$DIST_DIR/"
echo ""
echo -e "${BLUE}[使用说明]${NC}"
echo "  1. 将整个 $DIST_DIR 目录复制到目标 Linux 机器"
echo "  2. 运行安装脚本: sudo ./install_server.sh"
echo "  3. 或直接运行: ./CommandExecutorServer"
echo ""
echo -e "${BLUE}[卸载方法]${NC}"
echo "  运行: sudo ./uninstall_server.sh"
echo ""
