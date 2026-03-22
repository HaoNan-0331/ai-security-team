#!/bin/bash
# 测试发送syslog消息

echo "测试1: 发送UDP RFC5424格式消息到端口514"
echo "<34>1 2026-02-25T15:30:00.000Z testhost app - - - 测试UDP日志消息" | nc -u 127.0.0.1 514

echo "测试2: 发送TCP RFC5424格式消息到端口514"
echo "<34>1 2026-02-25T15:30:01.000Z testhost app - - - 测试TCP日志消息" | nc 127.0.0.1 514

echo "测试3: 发送TCP JSON格式消息到端口515"
echo '{"timestamp": "2026-02-25T15:30:02.000Z", "level": "INFO", "message": "测试威胁探针JSON消息", "source": "192.168.10.100"}' | nc 127.0.0.1 515

echo "测试4: 发送TCP CEF格式消息到端口516"
echo "CEF:0|Test|Threat|1.0|100|Test threat detected|0|src=192.168.10.200 dst=192.168.10.10" | nc 127.0.0.1 516

echo "完成所有测试！"
