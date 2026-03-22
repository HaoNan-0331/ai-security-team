# 修改记录

## 2026-03-04

### 新增
- [tools/inspection.py] - Windows服务器巡检主脚本，通过分布式命令执行系统API连接服务端，对Windows服务器执行巡检任务并生成Markdown报告
- [tools/reports/] - 巡检报告输出目录

### 修改
- [tools/inspection.py:36-43] - 添加自定义SSLAdapter支持旧版TLS协议
- [tools/inspection.py:50-55] - 修改登录API路径为/api/login
- [tools/inspection.py:159-177] - 优化命令执行结果获取逻辑，增加超时时间至120秒
- [tools/inspection.py:540-558] - 使用Base64编码PowerShell命令避免引号转义问题
- [tools/inspection.py:355-367] - 添加URL中文字符自动修正功能

### 功能说明
- 支持登录认证获取Token
- 支持查询在线设备列表
- 支持多选/全选设备
- 支持解析config.xml巡检模板配置
- 支持按分类选择巡检项（8个分类，共42个巡检项）
- 优先执行PowerShell命令（使用Base64编码避免引号问题）
- 支持轮询获取命令执行结果（最长等待120秒）
- 生成Markdown格式的巡检报告
- 自动修正URL中的中文标点符号
- 支持旧版TLS协议的SSL连接
