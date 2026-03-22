#!/bin/bash
# ========================================
# 分布式命令执行系统 - 客户端启动脚本 (Linux)
# ========================================

set -e

echo ""
echo "========================================"
echo "  分布式命令执行系统 - 客户端启动"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python 3.10+"
    echo ""
    echo "安装命令示例:"
    echo "  Ubuntu/Debian: sudo apt install python3"
    echo "  CentOS/RHEL:   sudo yum install python3"
    echo "  Arch Linux:    sudo pacman -S python"
    exit 1
fi

# 显示 Python 版本
PYTHON_VERSION=$(python3 --version)
echo "[检测] $PYTHON_VERSION"

# 进入 client 目录
cd "$(dirname "$0")/client"

# 检查并安装依赖
echo "[1/2] 检查依赖..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt -q
else
    echo "[警告] requirements.txt 未找到"
fi

# 启动客户端
echo "[2/2] 启动客户端..."
echo ""

python3 main.py

# 捕获退出代码
EXIT_CODE=$?
echo ""
echo "========================================"
echo "[退出] 客户端已退出 (代码: $EXIT_CODE)"
echo "========================================"

exit $EXIT_CODE
