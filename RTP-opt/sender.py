import argparse
import socket
import sys
import time

from utils import PacketHeader, compute_checksum

def make_packet(kind, seq, data = b""):
    header = PacketHeader(type = kind, seq_num = seq, length = len(data))
    header.checksum = compute_checksum(header / data)
    return bytes(header / data)

def read_ack(raw):
    if len(raw) < 16:
        return None
    header = PacketHeader(raw[:16])
    if header.length != 0 or len(raw) != 16:
        return None
    got = header.checksum
    header.checksum = 0
    if compute_checksum(header / b"") != got:
        return None
    if header.type != 3:
        return None
    return header.seq_num

def sender(receiver_ip, receiver_port, window_size):
    """TODO: Open socket and send message from sys.stdin."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#doc mes
    message = sys.stdin.buffer.read()
    size = 1456

    pieces = []
    start = 0
    while start < len(message):
        pieces.append(message[start : start + size])
        start = start + size

    total = len(pieces)
#tao packet
    packets = {}

    for n in range(total):
        packets[n + 1] = make_packet(2, n + 1, pieces[n])
#gui start -> cho ack
    dest = (receiver_ip, receiver_port)
    s.sendto(make_packet(0, 0), dest)

    while True:
        raw, _ = s.recvfrom(2048)
        if read_ack(raw) == 1:
            break


    # pkt_header = PacketHeader(type=2, seq_num=10, length=14)
    # pkt_header.checksum = compute_checksum(pkt_header / "Hello, world!\n")
    # pkt = pkt_header / "Hello, world!\n"
    # s.sendto(bytes(pkt), (receiver_ip, receiver_port))


#tao 1 danh sach cho moi: acked (de miss cac goi da duoc nhan)
    base = 1
    next_seq = 1
    acked = set()
    timer_start = time.time()

    while base <= total:
        #goi con cho trong khung thi gui
        while next_seq < base + window_size and next_seq <= total:
            s.sendto(packets[next_seq], dest)
            next_seq = next_seq + 1

        #end time -> gui ack chua dc
        left = 0.5 - (time.time() - timer_start)
        if left <= 0:
            for seq in range(base, next_seq):
                if seq not in acked:
                    s.sendto(packets[seq], dest)
            timer_start = time.time()
            continue

        #wait ack
        s.settimeout(left)
        try:
            raw, _ = s.recvfrom(2048)
        except socket.timeout:
            continue

        ack = read_ack(raw)
        if ack is None:
            continue

        #only ack trong khung
        if base <= ack < next_seq:
            acked.add(ack)
            if ack == base:
                while base in acked:
                    acked.remove(base)
                    base = base + 1
                timer_start = time.time()

    #send end, cho ack
    end_seq = total + 1
    s.sendto(make_packet(1, end_seq), dest)

    deadline = time.time() + 0.5
    while True:
        left = deadline - time.time()
        if left <= 0:
            break
        s.settimeout(left)
        try:
            raw, _ = s.recvfrom(2048)
        except socket.timeout:
            break
        if read_ack(raw) == end_seq:
            break


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "receiver_ip", help="The IP address of the host that receiver is running on"
    )
    parser.add_argument(
        "receiver_port", type=int, help="The port number on which receiver is listening"
    )
    parser.add_argument(
        "window_size", type=int, help="Maximum number of outstanding packets"
    )
    args = parser.parse_args()

    sender(args.receiver_ip, args.receiver_port, args.window_size)


if __name__ == "__main__":
    main()
