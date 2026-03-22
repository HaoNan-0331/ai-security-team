# 升级与重启

## 概述

升级与重启模块提供固件升级、特征库升级、系统备份和重启功能的配置管理。

## API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| **软件镜像** | 升级版本 | POST | `/api/manual-update` |
| **系统备份** | 当前固件版本显示 | GET | `/api/backup-version` |
| **系统备份** | 备份当前系统 | POST | `/api/backup-version` |
| **系统备份** | 删除备份系统 | DELETE | `/api/backup-version` |
| **启动选项** | 下次启动版本显示 | GET | `/api/backup-version` |
| **启动选项** | 立刻重启，使新版本生效 | PUT | `/api/backup-version` |
| **升级历史** | 查询升级历史 | GET | `/api/update-log` |
| **特征库升级** | 手动升级 | POST | `/api/manual-update` |
| **特征库升级** | 查询自动升级配置 | GET | `/api/auto-update` |
| **特征库升级** | 应用自动升级配置 | PUT | `/api/auto-update` |
| **特征库升级** | 立刻升级 | POST | `/api/auto-update` |
| **重启** | 重启 | PUT | `/api/reboot` |

---

# 软件镜像

## 升级版本

**端点**: `POST /api/manual-update`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| filename | Array | 是 | 上传文件的信息 |
| filetype | String | 是 | 文件类型（MAIN：软件镜像） |

**请求示例**:

```json
{
    "data": [
        {
            "filename": "二进制文件信息",
            "filetype": "MAIN"
        }
    ]
}
```

**响应示例**:

下发正确返回ok，下发错误返回code和str：

```json
{
    "code": "-137",
    "str": "无效的系统升级文件"
}
```

---

# 系统备份

## 当前固件版本显示

**端点**: `GET /api/backup-version`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| primary | String | 下次启动版本（主系统） |
| primary_timestamp | String | 主系统时间戳 |
| secondary | String | 下次启动版本（备份系统） |
| secondary_timestamp | String | 备份系统时间戳 |
| fireware_version | String | 当前固件版本 |
| reboot | Number | 立刻重启（0：否，1：是） |

**响应示例**:

```json
{
    "data": [
        {
            "primary": "ASG-V4.2_REL-arm64-ngfw-marvell-mt-20221031.bin",
            "primary_timestamp": "2022-10-31_16:07:24",
            "secondary": "ASG-V4.2_REL-arm64-ngfw-marvell-mt-20221031.bin",
            "secondary_timestamp": "2022-10-31_16:07:24",
            "firmware_version": "ASG-V4.2_REL-arm64-ngfw-marvell-mt-20221031.bin",
            "reboot": "0"
        }
    ],
    "total": 1
}
```

---

## 备份当前系统

**端点**: `POST /api/backup-version`

**请求参数**: 无

**响应示例**: 下发正确返回空

---

## 删除备份系统

**端点**: `DELETE /api/backup-version`

**请求参数**: 无

**响应示例**: 下发正确返回空

---

# 启动选项

## 下次启动版本显示

**端点**: `GET /api/backup-version`

**响应参数**: 同当前固件版本显示

**响应示例**: 同当前固件版本显示

---

## 立刻重启，使新版本生效

**端点**: `PUT /api/backup-version`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| reboot | Number | 是 | 立刻重启使新版生效（0：否，1：是） |
| primary | String | 是 | 下次启动版本（主系统） |
| primary_timestamp | String | 是 | 主系统时间戳 |
| secondary | String | 是 | 下次启动版本（备份系统） |
| secondary_timestamp | String | 是 | 备份系统时间戳 |

**请求示例**:

```json
{
    "data": [
        {
            "primary": "ASG-V4.2_REL-arm64-ngfw-marvell-mt-20221031.bin",
            "primary_timestamp": "2022-10-31_16:07:24",
            "reboot": "1"
        }
    ]
}
```

**响应示例**: 下发正确返回空

**说明**: 页面下发此配置，会再调用重启/api/reboot接口实现设备重启；postman中下发此配置，可以下发成功，由于无法调用重启接口，页面不能实现重启。

---

# 升级历史

## 查询升级历史

**端点**: `GET /api/update-log`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| version | String | 固件版本版本名称 |
| up_time | Number | 固件版本升级时间 |
| flag | Number | 升级类型：固定为4，代表"软件升级" |
| result | Number | 升级结果（成功或者失败） |
| manual | Number | 固件升级方式（1：手动升级，0：自动升级） |

**响应示例**:

```json
{
    "data": [
        {
            "version": "ASG-V4.2_REL-x86_64-ngfw-20221026.bin",
            "up_time": "Oct 26 11:39:00",
            "flag": "4",
            "result": "成功",
            "manual": "1"
        },
        {
            "version": "ASG-V4.2_REL-x86_64-ngfw-20221025.bin",
            "up_time": "Oct 25 15:31:58",
            "flag": "4",
            "result": "成功",
            "manual": "1"
        }
    ],
    "total": 10
}
```

---

# 特征库版本升级

## 手动升级

**端点**: `POST /api/manual-update`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| filename | Array | 是 | 上传文件的信息 |
| filetype | String | 是 | 文件类型（APPLIB：应用对象特征库，IPSLIB：入侵防护特征库，AVLIB：病毒防护特征库，URLLIB：URL分类特征库，MALURLLIB：威胁情报特征库） |

**请求示例**:

```json
{
    "filename": "二进制文件信息",
    "filetype": "APPLIB"
}
```

**响应示例**:

下发正确返回ok，下发错误返回code和str：

```json
{
    "code": "-221",
    "str": "非法的特征库文件"
}
```

---

## 查询自动升级配置

**端点**: `GET /api/auto-update`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| server_style | Number | 自定义升级服务器开关（0：使用默认升级服务器，1：自定义升级服务器） |
| server_addr | String | 服务器URL，server_style为1时需要配置此项 |
| flag | Number | 定期升级（1：定期升级，0：不定期升级） |
| updata_flag | Number | 升级时间类型（0：每周，1：每月） |
| sun | Number | 星期日（1：选中，0：没有选中） |
| mon | Number | 星期一（1：选中，0：没有选中） |
| tue | Number | 星期二（1：选中，0：没有选中） |
| wed | Number | 星期三（1：选中，0：没有选中） |
| thu | Number | 星期四（1：选中，0：没有选中） |
| fri | Number | 星期五（1：选中，0：没有选中） |
| sat | Number | 星期六（1：选中，0：没有选中） |
| time_hour | Number | 升级时间时钟(0~23) |
| time_min | Number | 升级时间分钟(0~59) |
| is_updating | Number | 正在升级（0：否，1：是） |
| update_time | String | 上次升级时间 |
| update_error | String | 升级失败原因 |
| app_status | String | 应用对象特征库 |
| ips_status | String | 入侵防护特征库 |
| av_status | String | 病毒防护特征库 |
| url_status | String | URL分类特征库 |
| malurl_status | String | 威胁情报特征库 |

**响应示例**:

```json
{
    "data": [
        {
            "server_style": "0",
            "server_addr": "http://www.sec-inside.com/update/update.asp",
            "flag": "1",
            "updata_flag": "0",
            "sun": "1",
            "mon": "1",
            "tue": "1",
            "wed": "1",
            "thu": "1",
            "fri": "1",
            "sat": "1",
            "time_hour": "3",
            "time_min": "55"
        },
        {
            "is_updating": 0,
            "update_time": "2022-10-28 03:55:21",
            "update_error": "DNS查询失败",
            "app_status": "已经是最新版本",
            "ips_status": "已经是最新版本",
            "av_status": "已经是最新版本",
            "url_status": "已经是最新版本",
            "malurl_status": "已经是最新版本"
        }
    ]
}
```

---

## 应用自动升级配置

**端点**: `PUT /api/auto-update`

**请求参数**: 同查询自动升级配置

**请求示例**:

```json
{
    "server_style": "0",
    "server_addr": "http://www.sec-inside.com/update/update.asp",
    "flag": "1",
    "updata_flag": "0",
    "sun": "1",
    "mon": "1",
    "tue": "1",
    "wed": "1",
    "thu": "1",
    "fri": "1",
    "sat": "1",
    "time_hour": "3"
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "248",
    "str": "没有配置DNS服务器"
}
```

---

## 立刻升级

**端点**: `POST /api/auto-update`

**请求参数**: 同查询自动升级配置

**请求示例**:

```json
{
    "server_style": "1",
    "server_addr": "http://www.sec-inside.com/update/update.asp",
    "flag": "1",
    "updata_flag": "0",
    "sun": "1",
    "mon": "1",
    "tue": "1",
    "wed": "1",
    "thu": "1",
    "fri": "1",
    "sat": "1",
    "time_hour": "0",
    "time_min": "0"
}
```

**响应示例**: 同应用自动升级配置

---

# 重启

## 重启

**端点**: `PUT /api/reboot`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| operation | Number | 是 | 重启选项（0：重启，1：恢复出厂设置，并重启设备） |

**请求示例**:

```json
{
    "operation": "0"
}
```

**响应示例**: 下发正确返回空

---

## 参数说明

### reboot 参数说明

| 值 | 说明 |
|----|------|
| 0 | 否 |
| 1 | 是 |

### flag 参数说明

| 值 | 说明 |
|----|------|
| 0 | 不定期升级 |
| 1 | 定期升级 |

### updata_flag 参数说明

| 值 | 说明 |
|----|------|
| 0 | 每周 |
| 1 | 每月 |

### server_style 参数说明

| 值 | 说明 |
|----|------|
| 0 | 使用默认升级服务器 |
| 1 | 自定义升级服务器 |

### filetype 参数说明

| 值 | 说明 |
|----|------|
| MAIN | 软件镜像 |
| APPLIB | 应用对象特征库 |
| IPSLIB | 入侵防护特征库 |
| AVLIB | 病毒防护特征库 |
| URLLIB | URL分类特征库 |
| MALURLLIB | 威胁情报特征库 |

### operation 参数说明

| 值 | 说明 |
|----|------|
| 0 | 重启 |
| 1 | 恢复出厂设置，并重启设备 |
