import socket
import time
import struct
from statistics import mean, stdev

server_ip = input('请输入服务器IP地址: ')
server_port = int(input('请输入服务器端口号: '))

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(0.3)

SEQ_BYTES = 2
VER_BYTES = 1
CONTENT_BYTES = 200
PACKET_FORMAT = f"!{SEQ_BYTES}s{VER_BYTES}s{CONTENT_BYTES}s"

print("正在建立连接...")
connect_packet = struct.pack(PACKET_FORMAT, b'\x00\x00', b'\x02', b'CONNECT'.ljust(CONTENT_BYTES, b' '))
client_socket.sendto(connect_packet, (server_ip, server_port))
try:
    print("等待服务器响应...")
    data, _ = client_socket.recvfrom(2048)
    print("收到服务器响应:", data)
    print("连接已建立。")
except socket.timeout:
    print("连接超时。")
    exit()

received_packets = 0
rtts = []
response_times = []
send_time_stamps = []

start_time = None
end_time = None

for seq in range(1, 13):
    sequence_number = struct.pack("!H", seq)
    ver = b"\x02"
    content = b"A" * CONTENT_BYTES

    packet = struct.pack(PACKET_FORMAT, sequence_number, ver, content)
    send_time = time.time()
    send_time_stamps.append(send_time)
    print(f"正在发送包 {seq} 到 {server_ip}:{server_port}")

    client_socket.sendto(packet, (server_ip, server_port))

    for attempt in range(3):
        try:
            data, _ = client_socket.recvfrom(2048)
            receive_time = time.time()
            rtt = (receive_time - send_time) * 1000

            received_sequence_number = struct.unpack("!H", data[:SEQ_BYTES])[0]
            server_ver = data[SEQ_BYTES:SEQ_BYTES + VER_BYTES]
            server_time = data[SEQ_BYTES + VER_BYTES:SEQ_BYTES + VER_BYTES + CONTENT_BYTES].decode().strip()

            # 将服务器时间字符串转换为时间结构，再转换为秒数
            server_time_struct = time.strptime(server_time, "%H-%M-%S")
            server_time_seconds = server_time_struct.tm_hour * 3600 + server_time_struct.tm_min * 60 + server_time_struct.tm_sec
            response_times.append(server_time_seconds)

            if end_time is None:
                end_time = server_time_seconds
            else:
                end_time = max(end_time, server_time_seconds)
            if start_time is None:
                start_time = server_time_seconds
            else:
                start_time = min(start_time, server_time_seconds)

            print(f"收到来自 {server_ip}:{server_port} 的包 {received_sequence_number}，RTT 为 {rtt:.2f} 毫秒，服务器时间为 {server_time}")
            received_packets += 1
            rtts.append(rtt)
            break
        except socket.timeout:
            print(f"包 {seq} 请求超时 (第 {attempt + 1} 次尝试)")
            if attempt == 2:
                break
            print(f"重试发送包 {seq}")
            client_socket.sendto(packet, (server_ip, server_port))

total_sent = 12
total_lost = total_sent - received_packets
loss_rate = total_lost / total_sent * 100
if rtts:
    max_rtt = max(rtts)
    min_rtt = min(rtts)
    avg_rtt = mean(rtts)
    std_rtt = stdev(rtts) if len(rtts) > 1 else 0.0
else:
    max_rtt = min_rtt = avg_rtt = std_rtt = 0.0

total_response_time = end_time - start_time if response_times else 0.0

print(f"""
汇总:
接收到的UDP包数量: {received_packets}
丢包率: {loss_rate:.2f}%
最大RTT: {max_rtt:.2f} 毫秒
最小RTT: {min_rtt:.2f} 毫秒
平均RTT: {avg_rtt:.2f} 毫秒
RTT标准差: {std_rtt:.2f} 毫秒
服务器响应时间差: {total_response_time:.2f} 秒
""")

print("正在终止连接...")
client_socket.close()