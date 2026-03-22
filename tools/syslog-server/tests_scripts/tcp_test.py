import socket
import time

def send_tcp_log(port, message):
    try:
        # 创建TCP套接字
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(('127.0.0.1', port))
        s.sendall(message.encode('utf-8'))
        time.sleep(0.1)  # 短暂留
        s.close()
        return True
    except Exception as e:
        print(f'Port {port} error: {e}')
        return False

print('发送TCP测试日志到端口514...')
send_tcp_log(514, '<34>1 2026-02-25T15:25:00.000Z testhost app - - - TCP测试消息1\n')

print('发送TCP测试日志到端口515...')
send_tcp_log(515, '{timestamp:2026-02-25T15:25:01.000Z,level:INFO,message:TCP威胁探针测试消息}')

print('发送TCP测试日志到端口516...')
send_tcp_log(516, 'CEF:0|Test|Threat|1.0|100|TCP测试威胁检测|0|src=192.168.10.200')

print('TCP测试完成！')
