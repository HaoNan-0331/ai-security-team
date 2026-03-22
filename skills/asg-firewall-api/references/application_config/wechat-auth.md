# 微信认证

## 概述

微信认证模块提供微信认证功能的配置管理，包括修改和显示微信认证配置。

## API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| **微信认证** | 修改微信认证配置 | POST | `/api/wechat-cnf` |
| **微信认证** | 显示微信认证配置 | GET | `/api/wechat-cnf` |

---

# 微信认证配置

## 修改微信认证配置

**端点**: `POST /api/wechat-cnf`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| force_interval | Number | 是 | 超时时间（10-144000分钟） |
| user_type | Number | 是 | 用户名（1：IP地址，2：应用ID，3：昵称） |
| appid | String | 是 | 自定义应用ID |
| appsecret | String | 是 | 自定义应用密钥 |
| hello_url | String | 是 | 自定义回调地址 |
| cfg_enable | Number | 是 | 微信自定义服务器开关（1：打开，0：关闭） |

**请求示例**:

```json
{
    "force_interval": "10",
    "user_type": "1",
    "cfg_enable": "0"
}
```

**响应示例**:

下发正确无返回值，下发错误会提示：

```json
{
    "code": "250",
    "str": "参数错误"
}
```

---

## 显示微信认证配置

**端点**: `GET /api/wechat-cnf`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| force_interval | Number | 超时时间（10-144000分钟） |
| kick_interval | Number | 超时时间（10-144000分钟） |
| user_type | Number | 用户名（1：IP地址，2：应用ID，3：昵称） |
| appid | String | 自定义应用ID |
| appsecret | String | 自定义应用密钥 |
| hello_url | String | 自定义回调地址 |
| cfg_enable | Number | 微信自定义服务器开关（1：打开，0：关闭） |

**响应示例**:

```json
{
    "data": {
        "force_interval": "0",
        "kick_interval": "10",
        "user_type": "1",
        "cfg_enable": "0"
    }
}
```

---

## 参数说明

### user_type 参数说明

| 值 | 说明 |
|----|------|
| 1 | IP地址 |
| 2 | 应用ID |
| 3 | 昵称 |

### cfg_enable 参数说明

| 值 | 说明 |
|----|------|
| 0 | 关闭 |
| 1 | 打开 |
