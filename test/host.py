import socket
import threading
import time
import struct

import log

data: bytes = (
        b"\x00" * 32
)
# 131072
MAX_LENGTH = 8192
addr = (socket.gethostname(), 9999)
_log = log.create_logger("MC_host", log_file="mc_host.log")


def average_calc():
    total = 0
    count = 0
    average = 0
    while True:
        num = yield average
        count += 1
        total += num
        average = total / count


def check(recv_data: bytes, complete: bytes) -> float:
    return len(recv_data) / len(complete) * 100


def wait(sign: bytes):
    while True:
        recv_data = client.recv(MAX_LENGTH)
        if recv_data != sign:
            continue
        else:
            break


def send():
    for i in range(2000):
        client.sendall(bag + struct.pack('d', time.time()))
        time.sleep(0.05)
    client.send(b"END")


def recv():
    a = average_calc()
    res = next(a)
    try:
        i = 0
        while True:
            recv_data = client.recv(MAX_LENGTH + 8)
            recv_time = time.time()

            if recv_data != b"END":
                offset = check(recv_data[:MAX_LENGTH], bag)
                _log.debug(len(recv_data))
                send_time = struct.unpack('d', recv_data[MAX_LENGTH:])[0]
                delay = round(recv_time - send_time, 3) * 1000
                res = a.send((recv_time - send_time) * 1000)

                _log.info(f"recv data[{i}] | offset: {offset}% | delay: {delay}ms")
                i += 1
            else:
                _log.info(f"offset: {round(res, 3)}ms on average")
                break
    except Exception as e:
        _log.error(len(recv_data))
        _log.error(e)


def init():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(addr)
    server.listen(1)
    _client, __ = server.accept()

    _bag: bytes = data * int(MAX_LENGTH / 32)
    _client.sendall(struct.pack('i', MAX_LENGTH))

    return _client, _bag


def start():
    thds = [threading.Thread(target=send), threading.Thread(target=recv)]

    for thd in thds:
        thd.start()

    for thd in thds:
        thd.join()

    print("Done")


if __name__ == '__main__':
    client, bag = init()
    wait(b'GOT')
    print("start")

    start()
