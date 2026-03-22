# -*- mode: python ; coding: utf-8 -*-
"""
分布式命令执行系统 - 客户端打包配置
使用 PyInstaller 将客户端打包为独立的 exe 文件
"""

import sys
from pathlib import Path

# 项目根目录
project_root = Path(SPECPATH).absolute()

block_cipher = None

a = Analysis(
    [str(project_root / 'client_exe_entry.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # 包含共享模块
        (str(project_root / 'shared' / 'models.py'), 'shared'),
    ],
    hiddenimports=[
        # 客户端模块
        'client.main',
        'client.config',
        'client.database',
        'client.websocket_client',
        'client.ssh_executor',
        'client.http_executor',
        'client.telnet_executor',
        'client.local_executor',

        # 共享模块
        'shared.models',

        # Telnet 库
        'telnetlib3',
        'telnetlib3.telnetlib',
        'telnetlib3.server',
        'telnetlib3.client',
        'telnetlib3.base',
        'telnetlib3.transport',
        'telnetlib3.stream',
        'telnetlib3.accumulator',
        'telnetlib3.compat',
        'asyncio',
        'asyncio.streams',

        # WebSocket 相关 - 完整列表
        'websockets',
        'websockets.server',
        'websockets.client',
        'websockets.asyncio',
        'websockets.legacy',
        'websockets.legacy.client',
        'websockets.legacy.auth',
        'websockets.serve',
        'websockets.connection',
        'websockets.http',
        'websockets.uri',
        'websockets.framing',
        'websockets.headers',

        # Paramiko SSH 库
        'paramiko',
        'paramiko.transport',
        'paramiko.client',
        'paramiko.ssh_exception',
        'paramiko.auth_handler',
        'paramiko.message',
        'paramiko.sftp',
        'paramiko.sftp_client',
        'paramiko.sftp_server',
        'paramiko.channel',
        'paramiko.buffered_pipe',
        'paramiko.ssh_gss',
        'paramiko.agent',
        'paramiko.dsskey',
        'paramiko.rsakey',
        'paramiko.ecdsakey',
        'paramiko.ed25519key',
        'paramiko.hostkeys',
        'paramiko.kex_gex',
        'paramiko.kex_group1',
        'paramiko.kex_group14',
        'paramiko.kex_group16',
        'paramiko.kex_curve25519',
        'paramiko.kex_ecdh_nist',
        'paramiko.kex_gss',
        'paramiko.packet',

        # 加密相关
        'cryptography',
        'cryptography.hazmat',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.backends',
        'cryptography.hazmat.backends.openssl',
        'cryptography.hazmat.bindings',
        'cryptography.hazmat.bindings.openssl',
        'cryptography.fernet',
        'cryptography.exceptions',

        # NaCl 加密
        'nacl',
        'nacl.bindings',
        'nacl.public',
        'nacl.signing',
        'nacl.encoding',

        # HTTP 请求
        'requests',
        'requests.adapters',
        'requests.auth',
        'requests.models',
        'requests.sessions',
        'urllib3',
        'urllib3.util',
        'urllib3.util.ssl_',
        'urllib3.contrib',
        'urllib3.contrib.pyopenssl',

        # 异步IO
        'asyncio',
        'asyncio.runners',
        'asyncio.events',
        'asyncio.locks',
        'asyncio.tasks',
        'asyncio.streams',

        # 标准库
        'socket',
        'ssl',
        'json',
        'logging',
        'logging.handlers',
        'pathlib',
        'datetime',
        'uuid',
        'sqlite3',
        'subprocess',
        'threading',
        'queue',
        'time',
        'hashlib',
        'base64',
        'struct',
        'io',
        'os',
        're',
        'ipaddress',
        'dataclasses',
        'typing',
        'copy',
        'secrets',

        # Windows 特定
        'win32timezone',
        'win32crypt',
        'win32security',
        'win32file',
        'win32pipe',
        'win32api',
        'win32con',
        'pywintypes',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的服务端模块
        'fastapi',
        'uvicorn',
        'uvicorn.loops',
        'uvicorn.protocols',
        'sqlalchemy',
        'pydantic',
        'starlette',
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'flask',
        'django',
        'tornado',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CommandExecutorClient',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加自定义图标
    version_file=None,
)
