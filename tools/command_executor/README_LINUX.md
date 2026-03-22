# 分布式命令执行系统 - Linux 客户端

## 简介

这是分布式命令执行系统的 Linux 版本客户端，支持主流 Linux 发行版（Ubuntu、Debian、CentOS、Rocky Linux 等）。

## 系统要求

- **操作系统**: Linux (内核 3.10+)
- **架构**: x86_64 / amd64
- **依赖**: 无（打包为独立可执行文件）

## 快速开始

### 方法一：使用预编译版本（推荐）

1. **下载并解压**
   ```bash
   tar -xzf command-executor-client-linux.tar.gz
   cd command-executor-client-linux
   ```

2. **安装**
   ```bash
   sudo ./install.sh
   ```

3. **验证安装**
   ```bash
   sudo systemctl status command-executor-client
   ```

### 方法二：手动运行

1. **设置权限**
   ```bash
   chmod +x CommandExecutorClient
   ```

2. **运行**
   ```bash
   ./CommandExecutorClient
   ```

## 配置

### 配置文件位置

```
~/.config/command_executor/client_config.json
```

### 首次运行

首次运行时，程序会自动启动配置向导，引导您完成基本配置。

### 手动配置示例

```json
{
  "server_url": "wss://your-server.com/ws",
  "client_id": "your-client-id",
  "client_name": "My Linux Client",
  "reconnect_interval": 5
}
```

## 服务管理

### systemd 服务命令

```bash
# 启动服务
sudo systemctl start command-executor-client

# 停止服务
sudo systemctl stop command-executor-client

# 重启服务
sudo systemctl restart command-executor-client

# 查看状态
sudo systemctl status command-executor-client

# 查看日志
sudo journalctl -u command-executor-client -f

# 启用开机自启
sudo systemctl enable command-executor-client

# 禁用开机自启
sudo systemctl disable command-executor-client
```

## 卸载

```bash
sudo ./uninstall.sh
```

## 开发环境

### 从源码运行

1. **克隆仓库**
   ```bash
   git clone https://github.com/your-repo/command-executor.git
   cd command-executor
   ```

2. **安装依赖**
   ```bash
   pip3 install -r client/requirements.txt
   ```

3. **启动客户端**
   ```bash
   ./start_client.sh
   ```

### 打包

1. **安装打包工具**
   ```bash
   pip3 install pyinstaller
   ```

2. **执行打包**
   ```bash
   chmod +x build_client_linux.sh
   ./build_client_linux.sh
   ```

3. **获取输出**
   ```bash
   cd dist/linux
   ls -lh
   ```

## 支持的发行版

| 发行版 | 版本 | 状态 |
|--------|------|------|
| Ubuntu | 20.04+ | ✅ 支持 |
| Debian | 10+ | ✅ 支持 |
| CentOS | 7+ | ✅ 支持 |
| Rocky Linux | 8+ | ✅ 支持 |
| AlmaLinux | 8+ | ✅ 支持 |
| Fedora | 35+ | ✅ 支持 |

## 故障排查

### 问题：服务无法启动

**检查日志**
```bash
sudo journalctl -u command-executor-client -n 50
```

### 问题：无法连接服务器

1. 检查网络连接
2. 检查防火墙设置
3. 验证服务器 URL 配置

### 问题：权限错误

确保可执行文件具有执行权限：
```bash
chmod +x CommandExecutorClient
```

## 文件结构

```
command-executor-client/
├── CommandExecutorClient              # 可执行文件
├── run_client.sh                      # 启动脚本
├── command-executor-client.service    # systemd 服务文件
├── install.sh                         # 安装脚本
└── uninstall.sh                       # 卸载脚本
```

## 安全说明

- 客户端默认使用加密连接 (WSS)
- 配置文件包含敏感信息，请妥善保管
- 建议使用专用账户运行客户端
- 定期更新到最新版本

## 许可证

[您的许可证信息]

## 支持

- 问题反馈: [GitHub Issues](https://github.com/your-repo/command-executor/issues)
- 文档: [在线文档](https://docs.example.com)
