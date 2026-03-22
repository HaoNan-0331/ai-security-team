# configs/ - 配置文件目录

> 存放AI Security Team的所有配置文件

---

## 📁 目录结构

```
configs/
├── credentials/        # 凭证配置 (加密存储)
├── devices/           # 设备配置
├── firewalls/         # 防火墙配置
├── routers/           # 路由器配置
└── switches/          # 交换机配置
```

---

## 🔐 credentials/ - 凭证配置

**⚠️ 重要**: 此目录下的文件应使用加密存储

### 支持的凭证类型

```yaml
# SSH凭证
ssh_credential:
  type: ssh
  username: admin
  password: "{{encrypted}}"
  private_key: /path/to/key

# API凭证
api_credential:
  type: api
  base_url: https://api.example.com
  token: "{{encrypted}}"

# SNMP凭证
snmp_credential:
  type: snmp
  community: public
  version: 2c

# 数据库凭证
db_credential:
  type: database
  host: localhost
  port: 5432
  database: asset_db
  username: asset_user
  password: "{{encrypted}}"
```

### 凭证文件示例

```
credentials/
├── network_devices.yaml     # 网络设备凭证
├── servers.yaml            # 服务器凭证
├── firewalls.yaml          # 防火墙凭证
├── apis.yaml               # API服务凭证
└── databases.yaml           # 数据库凭证
```

### 加密方式

推荐使用 **Ansible Vault** 或 **Python cryptography**:

```bash
# 加密凭证文件
ansible-vault encrypt credentials/network_devices.yaml

# 或使用Python脚本
python scripts/encrypt_credentials.py credentials/
```

---

## 📱 devices/ - 设备配置

### 设备配置模板

```
devices/
├── templates/              # 配置模板
│   ├── cisco_template.j2
│   ├── huawei_template.j2
│   └── h3c_template.j2
├── production/             # 生产环境配置
├── staging/                # 测试环境配置
└── development/            # 开发环境配置
```

---

## 🔥 firewalls/ - 防火墙配置

### 支持的防火墙厂商

```
firewalls/
├── asg/                    # 上元信安ASG
│   ├── policies/
│   ├── rules/
│   └── objects/
├── nsf/                    # 绿盟NSF
├── cisco/                  # Cisco ASA/Firepower
├── fortinet/               # Fortinet
├── paloalto/               # Palo Alto
└── checkpoint/             # Checkpoint
```

---

## 🌐 routers/ - 路由器配置

### 支持的路由器厂商

```
routers/
├── huawei/
├── cisco/
├── h3c/
├── juniper/
└── ruijie/
```

---

## 🔀 switches/ - 交换机配置

### 支持的交换机厂商

```
switches/
├── huawei/
├── cisco/
├── h3c/
├── ruijie/
└── fortinet/
```

---

## 📝 配置文件命名规范

```
{vendor}_{device_type}_{environment}_{version}.{ext}

示例:
  - huawei_s5700_production_v20250212.conf
  - cisco_asa_production_backup_20250212.conf
  - h3c_switch_staging_template.j2
```

---

## 🔧 配置管理脚本

```bash
# 备份配置
python scripts/backup_configs.py --source devices --output configs/backups/

# 检查配置漂移
python scripts/check_drift.py --baseline configs/ --current devices/

# 部署配置
python scripts/deploy_config.py --config configs/ --target device_group
```

---

## ⚠️ 安全注意事项

1. **凭证文件必须加密**
2. **配置文件不应包含敏感信息**
3. **定期轮换密钥和密码**
4. **使用版本控制时排除加密文件**

---

*最后更新: 2026-02-12*
