import socket
import time

def send_tcp_logs():
    # TCP 514 - RFC5424
    print('发送TCP RFC5424消息到514...')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('127.0.0.1', 514))
        message = '<34>1 2026-02-25T15:30:00.000Z localhost daemon - - - TCP RFC5424测试消息\n'
        s.sendall(message.encode())
        time.sleep(0.1)
    
    # TCP 515 - JSON (威胁探针)
    print('发送JSON消息到515...')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('127.0.0.1', 515))
        message = '{level: ERROR, timestamp: 2026-02-25T15:30:01.000Z, message: 威胁探针告警: 检测到异常访问, source: 192.168.1.100, device: probe-01}\n'
        s.sendall(message.encode())
        time.sleep(0.1)
    
    # TCP 516 - CEF (IDS/IPS)
    print('发送CEF消息到516...')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('127.0.0.1', 516))
        message = 'CEF:0|Palo Alto Networks|Threat|1.0|100|Web Attack|9|src=192.168.1.50 dst=10.0.0.10 msg=SQL Injection Attack suser=admin duser=root\n'
        s.sendall(message.encode())
        time.sleep(0.1)
    
    print('所有TCP测试消息发送完成！')

send_tcp_logs()
