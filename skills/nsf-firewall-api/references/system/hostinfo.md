# 系统状态信息

## 简要描述
获取防火墙系统的运行状态信息，包括CPU、内存、磁盘、风扇、温度等硬件状态。

## 请求URL
```
GET https://{{host}}/north/nf/system/hostinfo/
```

## 请求方式
```
GET
```

## 请求参数
无需参数

## 请求示例
```bash
curl -X GET "https://{{host}}/north/nf/system/hostinfo/" \
  -H "Authorization: <your-token>" \
  -H "Content-Type: application/json"
```

## 成功返回示例
```json
{
  "status": 2000,
  "module": "NF",
  "message": "success",
  "result": {
    "mode": "单机",
    "cpu_temperature": "41°C",
    "cpu_temperature_max": "70",
    "cpu_utilization": "6.26%",
    "disk_utilization": "7.8%",
    "disk_size": "234.601G",
    "disk_employ": "18.232G",
    "fan_speed": "5535",
    "data_disk_utilization": "0.69%",
    "data_disk_size": "3.937TB",
    "data_disk_employ": "54.451GB",
    "memory_utilization": "53.00%",
    "disk_exists": true,
    "log_utilization": {
      "total": "2.9T",
      "use_size": "26G",
      "use_rate": "1%",
      "storage_rate": 80
    }
  }
}
```

## 返回参数说明
| 参数名 | 类型 | 说明 |
|--------|------|------|
| mode | string | 部署模式（单机/集群） |
| cpu_temperature | string | CPU当前温度 |
| cpu_temperature_max | string | CPU温度上限 |
| cpu_utilization | string | CPU使用率 |
| disk_utilization | string | 系统磁盘使用率 |
| disk_size | string | 系统磁盘容量大小 |
| disk_employ | string | 系统磁盘已使用容量 |
| fan_speed | string | 风扇转速(RPM) |
| data_disk_utilization | string | 数据盘使用率 |
| data_disk_size | string | 数据盘容量大小 |
| data_disk_employ | string | 数据盘已使用容量 |
| memory_utilization | string | 内存使用率 |
| disk_exists | boolean | 是否存在硬盘 |
| log_utilization | object | 日志存储信息 |
| log_utilization.total | string | 日志存储总容量 |
| log_utilization.use_size | string | 日志存储已使用容量 |
| log_utilization.use_rate | string | 日志存储使用率 |
| log_utilization.storage_rate | int | 日志存储告警阈值(百分比) |

## 失败返回示例
```json
{
  "status": 3001,
  "module": "NF",
  "message": "无权限: 无权限访问"
}
```

## 状态码说明
| status | 说明 |
|--------|------|
| 2000 | 获取成功 |
| 3001 | 无权限访问 |

## 使用场景
- 系统健康状态监控
- 资源使用率巡检
- 故障诊断时查看系统状态
- 容量规划参考
