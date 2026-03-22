#!/bin/bash
# ========================================
# 分布式命令执行系统 - 客户端打包脚本
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
echo "  分布式命令执行系统 - 客户端打包工具"
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

echo -e "${YELLOW}[1/4]${NC} 正在清理旧的构建文件..."
rm -rf build
rm -rf dist

echo -e "${YELLOW}[2/4]${NC} 正在打包客户端（这可能需要几分钟）..."
python3 -m PyInstaller scripts/build_client_linux.spec --clean

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}[错误]${NC} 打包失败！请检查错误信息。"
    exit 1
fi

echo -e "${YELLOW}[3/4]${NC} 正在整理输出文件..."
# 移动可执行文件到 linux 目录
mv dist/CommandExecutorClient "$DIST_DIR/"

# 复制额外的部署文件
cp dist/run_client.sh "$DIST_DIR/" 2>/dev/null || true
cp dist/command-executor-client.service "$DIST_DIR/" 2>/dev/null || true
cp dist/install.sh "$DIST_DIR/" 2>/dev/null || true
cp dist/uninstall.sh "$DIST_DIR/" 2>/dev/null || true

echo -e "${YELLOW}[4/4]${NC} 正在清理临时文件..."
rm -rf build

# 设置可执行权限
chmod +x "$DIST_DIR/CommandExecutorClient"
chmod +x "$DIST_DIR"/*.sh 2>/dev/null || true

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
echo "  2. 运行安装脚本: sudo ./install.sh"
echo "  3. 或直接运行: ./CommandExecutorClient"
echo ""
echo -e "${BLUE}[卸载方法]${NC}"
echo "  运行: sudo ./uninstall.sh"
echo ""
