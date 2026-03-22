"""
客户端打包入口点
用于 PyInstaller 打包，处理路径问题
"""
import sys
import os
from pathlib import Path

# 获取打包后的资源目录
if getattr(sys, 'frozen', False):
    # 打包后的 exe 环境
    _ROOT_PATH = Path(sys.executable).parent
else:
    # 开发环境
    _ROOT_PATH = Path(__file__).parent.parent

# 将项目根目录添加到路径
sys.path.insert(0, str(_ROOT_PATH))

# 导入并运行客户端
from client.main import main

if __name__ == '__main__':
    main()
