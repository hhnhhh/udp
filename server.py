#server
import socket
import struct
import random
import time

server_ip = '0.0.0.0'
server_port = int(input('请输入服务器端口号: '))

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((server_ip, server_port))

print("服务器运行在:", server_ip, ":", server_port)

SEQ_BYTES = 2
VER_BYTES = 1
CONTENT_BYTES = 200
PACKET_FORMAT = f"!{SEQ_BYTES}s{VER_BYTES}s{CONTENT_BYTES}s"

drop_rate = 0.6

print("等待客户端连接...")
while True:
    data, addr = server_socket.recvfrom(2048)
    if len(data) >= SEQ_BYTES + VER_BYTES + len(b"CONNECT"):
        print(f"收到来自 {addr} 的连接请求: {data}")
        if data[SEQ_BYTES:SEQ_BYTES+VER_BYTES] == b"\x02" and data[SEQ_BYTES+VER_BYTES:].strip() == b"CONNECT":
            server_socket.sendto(data, addr)
            print(f"已建立与 {addr} 的连接")
            break

while True:
    data, addr = server_socket.recvfrom(2048)
    if len(data) >= SEQ_BYTES + VER_BYTES + CONTENT_BYTES:
        seq_number = struct.unpack("!H", data[:SEQ_BYTES])[0]

        if random.random() < drop_rate:
            print(f"丢弃包 {seq_number}")
            continue

        print(f"收到来自 {addr} 的包 {seq_number}")
        response_content = time.strftime("%H-%M-%S").encode().ljust(CONTENT_BYTES, b" ")
        response_packet = struct.pack(PACKET_FORMAT, data[:SEQ_BYTES], data[SEQ_BYTES:SEQ_BYTES + VER_BYTES], response_content)
        server_socket.sendto(response_packet, addr)