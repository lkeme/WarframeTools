#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import random
import socket
import string
import struct
import threading
import time
import zlib

import select
from icmplib import ping

from lib.python_hosts import is_ipv4, is_ipv6


# 检查校验
def check_sum(data):
    n = len(data)
    m = n % 2
    c_sum = 0
    for i in range(0, n - m, 2):
        c_sum += (data[i]) + ((data[i + 1]) << 8)  # 传入data以每两个字节（十六进制）通过ord转十进制，第一字节在低位，第二个字节在高位
    if m:
        c_sum += (data[-1])
    # 将高于16位与低16位相加
    c_sum = (c_sum >> 16) + (c_sum & 0xffff)
    c_sum += (c_sum >> 16)  # 如果还有高于16位，将继续与低16位相加
    answer = ~c_sum & 0xffff
    # 主机字节序转网络字节序列（参考小端序转大端序）
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


# 连接套接字,并将数据发送到套接字
def raw_socket(dst_addr, icmp_packet):
    rawsocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
    # rawsocket = socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_ICMPV6)
    send_request_ping_time = time.time()
    # send data to the socket
    rawsocket.sendto(icmp_packet, (dst_addr, 80))
    return send_request_ping_time, rawsocket, dst_addr


# 构造ICMP报文 把字节打包成二进制数据
def request_ping(data_type, data_code, data_checksum, data_id, data_sequence, payload_body):
    icmp_packet = struct.pack('>BBHHH32s', data_type, data_code, data_checksum, data_id, data_sequence, payload_body)
    icmp_check_sum = check_sum(icmp_packet)  # 获取校验和
    icmp_packet = struct.pack('>BBHHH32s', data_type, data_code, icmp_check_sum, data_id, data_sequence, payload_body)
    return icmp_packet


# 接收回复数据
def reply_ping(send_request_ping_time, rawsocket, data_sequence, timeout=2):
    while True:
        started_select = time.time()
        what_ready = select.select([rawsocket], [], [], timeout)
        wait_for_time = (time.time() - started_select)
        if not what_ready[0]:  # Timeout
            return -1
        time_received = time.time()
        received_packet, addr = rawsocket.recvfrom(1500)
        icmp_header = received_packet[20:28]
        icmp_type, code, checksum, packet_id, sequence = struct.unpack(">BBHHH", icmp_header)
        if icmp_type == 0 and sequence == data_sequence:
            return time_received - send_request_ping_time
        timeout = timeout - wait_for_time
        if timeout <= 0:
            return -1


# to avoid icmp_id collision.
def icmp_id():
    # threading.get_native_id() is supported >= python3.8.
    thread_id = threading.get_native_id() if hasattr(threading, 'get_native_id') else threading.current_thread().ident
    # If ping() run under different process, thread_id may be identical. os.getpid() & 0xFFFF
    process_id = os.getpid() & 0xffff
    random_id = zlib.adler32(os.urandom(4)) & 0xffff
    # print("{}{}{}".format(process_id, thread_id, random_id).encode())
    # Combine process_id and thread_id to generate a unique id.
    return zlib.crc32('{}{}{}'.format(process_id, thread_id, random_id).encode()) & 0xffff


# 实现 ping 主机/ip
# def ping(domain: str):
#     data_type = 8  # ICMP Echo Request
#     data_code = 0  # must be zero
#     data_checksum = 0  # "...with value 0 substituted for this field..."
#     data_id = 0  # Identifier
#     data_sequence = 1  # Sequence number
#     payload_body = b'abcdefghijklmnopqrstuvwabcdefghi'  # data
#     dst_addr = socket.gethostbyname(domain)  # 将主机名转ipv4地址格式，返回以ipv4地址格式的字符串，如果主机名称是ipv4地址，则它将保持不变
#     printer(f"正在 Ping {domain} [{dst_addr}] 具有 32 字节的数据:")
#     for i in range(0, 4):
#         icmp_packet = request_ping(data_type, data_code, data_checksum, data_id, data_sequence + i, payload_body)
#         send_request_ping_time, rawsocket, addr = raw_socket(dst_addr, icmp_packet)
#         times = reply_ping(send_request_ping_time, rawsocket, data_sequence + i)
#         if times > 0:
#             printer(f"来自 {addr} 的回复: 字节=32 时间={int(times * 1000)}ms")
#             time.sleep(0.7)
#         else:
#             printer("请求超时。")


# 实现 ping 主机/ip
def ping3(addr: str, index: int):
    data_type = 8  # ICMP Echo Request
    data_code = 0  # must be zero
    data_checksum = 0  # "...with value 0 substituted for this field..."
    data_id = icmp_id()  # Identifier 0
    data_sequence = icmp_id()  # Sequence number 1
    # payload_body = b'abcdefghijklmnopqrstuvwabcdefghi'  # data
    payload_body = "".join(random.choices(string.ascii_lowercase, k=32)).encode("ascii")
    if is_ipv4(addr):
        dst_addr = socket.gethostbyname(addr)  # 将主机名转ipv4地址格式，返回以ipv4地址格式的字符串，如果主机名称是ipv4地址，则它将保持不变
        # printer(f"-> 正在 Ping {domain} [{dst_addr}] 具有 32 字节的数据:", 'ping3', 'green')
        icmp_packet = request_ping(data_type, data_code, data_checksum, data_id, data_sequence + index, payload_body)
        send_request_ping_time, rawsocket, addr = raw_socket(dst_addr, icmp_packet)
        return dst_addr, reply_ping(send_request_ping_time, rawsocket, data_sequence + index)
    elif is_ipv6(addr):
        dst_addr = socket.getaddrinfo(addr, None, socket.AF_INET6)[0][4][0]
        host = ping(dst_addr, count=1, interval=0.2)
        if not host.is_alive:
            return dst_addr, -1
        return dst_addr, round(host.avg_rtt / 1000, 3)
    else:
        # raise ValueError("Invalid IP address")
        return addr, -111
