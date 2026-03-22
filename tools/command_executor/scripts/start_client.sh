#!/bin/bash
# ========================================
# 分布式命令执行系统 - 客户端启动脚本
# ========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 切换到项目根目录
cd "$(dirname "$0")/.."

echo ""
echo "========================================"
echo "  命令执行系统 - 客户端启动脚本"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[错误]${NC} 未检测到 Python3，请先安装 Python 3.10+"
    echo "安装命令: sudo apt install python3 (Ubuntu/Debian)"
    echo "         sudo yum install python3 (CentOS/Rocky)"
    exit 1
fi

# 显示 Python 版本
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}[信息]${NC} 检测到 $PYTHON_VERSION"

# 检查依赖
echo -e "${YELLOW}[1/2]${NC} 检查依赖..."
if [ -f "client/requirements.txt" ]; then
    pip3 install -r client/requirements.txt -q --disable-pip-version-check
    echo -e "${GREEN}[完成]${NC} 依赖检查完成"
else
    echo -e "${RED}[错误]${NC} 未找到 client/requirements.txt"
    exit 1
fi

# 启动客户端
echo ""
echo -e "${YELLOW}[2/2]${NC} 启动客户端..."
echo ""

cd client && python3 main.py
