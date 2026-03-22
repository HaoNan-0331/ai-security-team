# Playwright MCP工具

## 基本信息

**工具类型**: MCP (Model Context Protocol)
**功能**: 浏览器自动化
**运行位置**: 本地

---

## 可用工具列表

### 导航操作
| 工具 | 说明 |
|------|------|
| `browser_navigate` | 导航到指定URL |
| `browser_navigate_back` | 返回上一页 |
| `browser_tabs` | 管理浏览器标签页（列表/新建/关闭/选择） |

### 页面交互
| 工具 | 说明 |
|------|------|
| `browser_click` | 点击元素 |
| `browser_type` | 输入文本 |
| `browser_hover` | 悬停在元素上 |
| `browser_select_option` | 选择下拉选项 |
| `browser_fill_form` | 填充多个表单字段 |
| `browser_drag` | 拖拽操作 |
| `browser_press_key` | 按键操作 |
| `browser_file_upload` | 上传文件 |

### 页面信息
| 工具 | 说明 |
|------|------|
| `browser_snapshot` | 获取页面可访问性快照（推荐） |
| `browser_take_screenshot` | 截图 |
| `browser_console_messages` | 获取控制台消息 |
| `browser_network_requests` | 获取网络请求 |
| `browser_evaluate` | 执行JavaScript |

### 其他
| 工具 | 说明 |
|------|------|
| `browser_wait_for` | 等待文本/元素/时间 |
| `browser_handle_dialog` | 处理对话框 |
| `browser_resize` | 调整窗口大小 |
| `browser_close` | 关闭页面 |
| `browser_install` | 安装浏览器 |
| `browser_run_code` | 执行Playwright代码片段 |

---

## 使用场景

### 1. 查询CVE数据库
```
1. browser_navigate -> https://nvd.nist.gov/
2. browser_type -> 搜索框输入CVE编号
3. browser_click -> 搜索按钮
4. browser_snapshot -> 获取搜索结果
```

### 2. 访问厂商安全公告
```
1. browser_navigate -> 厂商安全公告页面
2. browser_snapshot -> 获取页面内容
3. browser_click -> 查看详情（如需要）
```

### 3. Web资产测试
```
1. browser_navigate -> 目标Web应用
2. browser_snapshot -> 分析页面结构
3. browser_type/browser_click -> 进行交互测试
4. browser_take_screenshot -> 记录测试结果
```

### 4. 威胁情报平台查询
```
1. browser_navigate -> VirusTotal/AlienVault等平台
2. browser_type -> 输入IP/域名/哈希
3. browser_click -> 搜索
4. browser_snapshot -> 获取分析结果
```

### 5. Web界面设备配置
```
1. browser_navigate -> 设备管理界面
2. browser_type -> 输入用户名密码
3. browser_click -> 登录
4. browser_snapshot -> 获取配置页面
5. browser_fill_form -> 修改配置
6. browser_click -> 保存
```

---

## 最佳实践

1. **优先使用snapshot而非screenshot**
   - snapshot返回结构化数据，更适合AI分析
   - screenshot仅用于需要视觉记录的场景

2. **处理动态内容**
   - 使用`browser_wait_for`等待元素加载
   - 避免在页面未加载完成时进行操作

3. **错误处理**
   - 检查`browser_console_messages`排查问题
   - 使用`browser_network_requests`分析请求失败

4. **会话管理**
   - 完成操作后使用`browser_close`关闭页面
   - 使用`browser_tabs`管理多个页面

---

## 调用示例

```javascript
// 导航到页面
browser_navigate({ url: "https://nvd.nist.gov/" })

// 获取页面快照
browser_snapshot({})

// 输入搜索内容
browser_type({ ref: "textbox selector", text: "CVE-2024-1234" })

// 点击搜索
browser_click({ ref: "button selector" })

// 等待结果
browser_wait_for({ text: "Results" })

// 获取结果
browser_snapshot({})
```

---

## 注意事项

1. **网络访问**: 需要网络连接访问目标网站
2. **代理配置**: 如需代理，在MCP服务器配置中设置
3. **认证信息**: 敏感信息通过环境变量或安全存储传递
4. **超时处理**: 长时间操作需设置合理超时时间
