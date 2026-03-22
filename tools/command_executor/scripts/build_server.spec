# -*- mode: python ; coding: utf-8 -*-
"""
分布式命令执行系统 - 服务端打包配置 (Windows)
使用 PyInstaller 将服务端打包为独立的 exe 文件
"""

import sys
from pathlib import Path

# 项目根目录 (spec文件在scripts目录，所以需要回到上级目录)
project_root = Path(SPECPATH).parent.absolute()

block_cipher = None

a = Analysis(
    [str(project_root / 'server_exe_entry.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # 包含共享模块
        (str(project_root / 'shared' / 'models.py'), 'shared'),
    ],
    hiddenimports=[
        # 服务端模块
        'server.main',
        'server.config',
        'server.database',
        'server.api_server',
        'server.websocket_server',
        'server.auth',
        'server.manage_users',

        # 共享模块
        'shared.models',

        # FastAPI 和 Uvicorn
        'fastapi',
        'fastapi.routing',
        'fastapi.params',
        'fastapi.middleware',
        'fastapi.middleware.cors',
        'fastapi.responses',
        'fastapi.dependencies',
        'fastapi.security',
        'fastapi.openapi',
        'fastapi.openapi.utils',
        'uvicorn',
        'uvicorn.main',
        'uvicorn.server',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.logging',

        # Starlette (FastAPI 依赖)
        'starlette',
        'starlette.applications',
        'starlette.routing',
        'starlette.responses',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.middleware.gzip',
        'starlette.requests',
        'starlette.datastructures',
        'starlette.exceptions',
        'starlette.types',
        'starlette.concurrency',
        'starlette.background',

        # WebSocket 相关
        'websockets',
        'websockets.server',
        'websockets.client',
        'websockets.asyncio',
        'websockets.legacy',
        'websockets.legacy.server',
        'websockets.http',
        'websockets.uri',
        'websockets.headers',

        # SQLAlchemy ORM
        'sqlalchemy',
        'sqlalchemy.ext',
        'sqlalchemy.ext.declarative',
        'sqlalchemy.ext.asyncio',
        'sqlalchemy.orm',
        'sqlalchemy.orm.decl_api',
        'sqlalchemy.engine',
        'sqlalchemy.pool',
        'sqlalchemy.dialects',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.sql',
        'sqlalchemy.event',
        'sqlalchemy.inspection',
        'sqlalchemy.log',

        # Pydantic 数据验证
        'pydantic',
        'pydantic.main',
        'pydantic.fields',
        'pydantic.types',
        'pydantic.json',
        'pydantic.networks',

        # HTTP 相关
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
        'anyio',
        'anyio.abc',
        'anyio.streams',

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
        'contextlib',
        'collections',
        'inspect',
        'warnings',
        'traceback',
        'string',
        'textwrap',
        'tempfile',
        'shutil',

        # 加密
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
        # 排除不需要的客户端模块
        'paramiko',
        'telnetlib3',
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
    name='CommandExecutorServer',
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
