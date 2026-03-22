# 客户端打包说明

本文档说明如何将客户端打包为独立的 Windows 可执行文件。

## 打包环境要求

- **Python 版本**: 3.12+
- **操作系统**: Windows 10/11
- **PyInstaller 版本**: 6.16.0+

## 安装依赖

### 1. 安装 PyInstaller

```bash
pip install pyinstaller
```

### 2. 安装客户端依赖

```bash
cd client
pip install -r requirements.txt
```

**关键依赖**：
- `websockets` - WebSocket 客户端库
- `requests` - HTTP 请求库
- `paramiko` - SSH 执行库
- `cryptography` - 加密库

## 打包配置

打包配置文件：`build_client.spec`

**关键配置项**：

```python
# 打包入口
[client_exe_entry.py]

# 隐藏导入（必须包含）
hiddenimports=[
    'websockets',
    'websockets.client',
    'websockets.asyncio',
    'ssl',
    'requests',
    'paramiko',
    # ... 更多依赖
]
```

## 打包步骤

### 1. 清理旧文件

```bash
# 删除旧的打包文件
rmdir /s /q dist build
```

### 2. 执行打包

```bash
# 使用 spec 文件打包
pyinstaller build_client.spec --clean --noconfirm

# 或使用命令行参数（不推荐）
pyinstaller --onefile --name CommandExecutorClient client_exe_entry.py
```

### 3. 验证打包结果

打包完成后，`dist/CommandExecutorClient.exe` 应该约为 15-16 MB。

## 常见问题

### 1. ModuleNotFoundError: No module named 'websockets'

**原因**：打包使用的 Python 环境中没有安装 websockets

**解决**：
```bash
# 检查 Python 环境
python --version

# 安装 websockets
python -m pip install websockets

# 重新打包
pyinstaller build_client.spec --clean
```

### 2. SSL 连接错误

**原因**：Python 3.12+ 的 OpenSSL 3.0 与旧版本服务器不兼容

**解决**：代码已配置 TLS 1.2 兼容性，无需额外处理

### 3. 打包后 exe 无法运行

**排查步骤**：
1. 使用批处理文件运行查看错误：`run_client.bat`
2. 检查是否有依赖缺失
3. 查看日志文件：`client/logs/client_YYYYMMDD.log`

## 分发说明

### 需要分发的文件

```
dist/
├── CommandExecutorClient.exe  # 主程序
└── run_client.bat              # 启动脚本（可选）
```

### 用户首次运行

1. 将 `dist/` 目录复制到目标机器
2. 运行 `CommandExecutorClient.exe`
3. 配置服务端地址
4. 输入用户名和密码登录

### 配置文件位置

- **开发环境**：`client/client_config.json`
- **打包后**：`exe所在目录/client_config.json`

## 更新日志

### v2.0 (2026-01-26)

- ✅ 添加用户认证功能
- ✅ 启用 TLS 加密通信（HTTPS + WSS）
- ✅ 配置 TLS 1.2 兼容性
- ✅ 更新 SSL 适配器
- ✅ 修复数据库架构问题

### v1.0

- 初始版本
- WebSocket 长连接
- SSH/HTTP/本地命令执行
