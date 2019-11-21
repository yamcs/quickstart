import io
import socket
import sys
from struct import unpack_from
from time import sleep

if __name__ == '__main__':
    filename = 'testdata.ccsds'
    host = '127.0.0.1'
    port = 10015

    tm_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    with io.open(filename, 'rb') as f:

        # Count packets in this CCSDS dump
        total = 0
        buf = bytearray(6)
        while (f.readinto(buf) == 6):
            (len,) = unpack_from('>H', buf, 4)
            f.seek(len + 1, io.SEEK_CUR)
            total += 1
        f.seek(0)

        progress = 1
        header = bytearray(6)
        while (f.readinto(header) == 6):
            (len,) = unpack_from('>H', header, 4)

            packet = bytearray(len + 7)
            f.seek(-6, io.SEEK_CUR)
            f.readinto(packet)

            sys.stdout.write('\rSending packets to {}:{} ({} of {})'.format(host, port, progress, total))
            sys.stdout.flush()

            tm_socket.sendto(packet, (host, port))
            progress += 1

            sleep(1)
