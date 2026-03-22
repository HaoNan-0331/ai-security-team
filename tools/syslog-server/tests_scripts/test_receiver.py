#\!/usr/bin/env python3
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('0.0.0.0', 515))
print('515 UDP接收器已启动')

while True:
    data = sock.recv(4096)
    print('收到:', data.decode())
