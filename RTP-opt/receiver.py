import argparse
import socket
import sys

from utils import PacketHeader, compute_checksum


#tao goi ACK
def make_ack(seq):
    header = PacketHeader(type=3, seq_num=seq, length=0)
    header.checksum = compute_checksum(header / b"")
    return bytes(header / b"")


def receiver(receiver_ip, receiver_port, window_size):
    """TODO: Listen on socket and print received message to sys.stdout."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((receiver_ip, receiver_port))


    joined = False
    queue = 1
    box = {}

    while True:
        #dia chi nhan
        pkt, address = s.recvfrom(2048)
#bo goi < 16
        if len(pkt) < 16:
            continue

        # Extract header and payload
        pkt_header = PacketHeader(pkt[:16])
        msg = pkt[16 : 16 + pkt_header.length]
#check length
        if len(msg) != pkt_header.length:
            continue
        # Verity checksum
        pkt_checksum = pkt_header.checksum
        pkt_header.checksum = 0
        computed_checksum = compute_checksum(pkt_header / msg)
        if pkt_checksum != computed_checksum:
            # print("checksums not match")
            continue
        #print(msg)

        kind = pkt_header.type
        seq = pkt_header.seq_num

        #bat dau
        if kind == 0:
            if not joined:
                joined = True
                queue = 1
                box = {}
                s.sendto(make_ack(1), address)
            continue

        if not joined:
            continue

        #data vo
        if kind == 2:
            if seq >= queue + window_size:
                continue
            if seq >= queue:
                box[seq] = msg
                while queue in box:
                    sys.stdout.buffer.write(box.pop(queue))
                    queue += 1
            s.sendto(make_ack(seq), address)

        #sended
        elif kind == 1:
            if seq == queue:
                s.sendto(make_ack(seq), address)
                sys.stdout.buffer.flush()
                break
            s.sendto(make_ack(queue), address)

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

    receiver(args.receiver_ip, args.receiver_port, args.window_size)


if __name__ == "__main__":
    main()
