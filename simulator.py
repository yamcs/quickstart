#!/usr/bin/env python3

import binascii
import io
import json
import socket
import sys
import argparse
<<<<<<< HEAD
import urllib.request
import urllib.error
=======
>>>>>>> f331bfa4ac23db188a7358bda224a2a545c1c2ab

from struct import unpack_from
from threading import Event, Thread
from time import sleep

parser = argparse.ArgumentParser(description='Yamcs Simulator')
parser.add_argument('--testdata', type=str, default='testdata.ccsds', help='simulated testdata.ccsds data')

# telemetry
parser.add_argument('--tm_host',    type=str, default='127.0.0.1', help='TM host')
parser.add_argument('--tm_port',    type=int, default=10015,       help='TM port')
parser.add_argument('-r', '--rate', type=int, default=1,           help='TM playback rate. 1 = 1Hz, 10 = 10Hz, etc.')

# telecommand
parser.add_argument('--tc_host', type=str, default='127.0.0.1', help='TC host')
parser.add_argument('--tc_port', type=int, default=10025 ,      help='TC port')

<<<<<<< HEAD
# yamcs readiness
parser.add_argument('--yamcs_host',     type=str, default='127.0.0.1', help='Yamcs HTTP host')
parser.add_argument('--yamcs_port',     type=int, default=8090,        help='Yamcs HTTP port')
parser.add_argument('--yamcs_instance', type=str, default='myproject', help='Yamcs instance name')

=======
>>>>>>> f331bfa4ac23db188a7358bda224a2a545c1c2ab
args = vars(parser.parse_args())

# test data
TEST_DATA = args['testdata']

# telemetry
TM_SEND_ADDRESS = args['tm_host']
TM_SEND_PORT    = args['tm_port']
RATE            = args['rate']

# telecommand
TC_RECEIVE_ADDRESS = args['tc_host']
TC_RECEIVE_PORT    = args['tc_port']
<<<<<<< HEAD

# yamcs readiness
YAMCS_HOST     = args['yamcs_host']
YAMCS_PORT     = args['yamcs_port']
YAMCS_INSTANCE = args['yamcs_instance']


def wait_for_yamcs(ready_event):
    url = 'http://{}:{}/api/instances/{}'.format(YAMCS_HOST, YAMCS_PORT, YAMCS_INSTANCE)
    sys.stdout.write('\033[33mWaiting for Yamcs at {} ...\033[0m\n'.format(url))
    sys.stdout.flush()
    while True:
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                data = json.loads(resp.read())
                if data.get('state') == 'RUNNING':
                    sys.stdout.write('\n\033[32mYamcs is ready.\033[0m\n')
                    sys.stdout.flush()
                    ready_event.set()
                    return
        except Exception:
            pass
        sleep(2)

=======
>>>>>>> f331bfa4ac23db188a7358bda224a2a545c1c2ab

def send_tm(simulator):
    wait_for_yamcs(simulator.ready)
    tm_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    with io.open(TEST_DATA, 'rb') as f:
        simulator.tm_counter = 1
        header = bytearray(6)
        while f.readinto(header) == 6:
            (len,) = unpack_from('>H', header, 4)

            packet = bytearray(len + 7)
            f.seek(-6, io.SEEK_CUR)
            f.readinto(packet)

            tm_socket.sendto(packet, (TM_SEND_ADDRESS, TM_SEND_PORT))
            simulator.tm_counter += 1

            sleep(1 / simulator.rate)


def receive_tc(simulator):
    tc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tc_socket.bind((TC_RECEIVE_ADDRESS, TC_RECEIVE_PORT ))
    while True:
        data, _ = tc_socket.recvfrom(4096)
        simulator.last_tc = data
        simulator.tc_counter += 1


class Simulator():

    def __init__(self, rate):
        self.tm_counter = 0
        self.tc_counter = 0
        self.tm_thread = None
        self.tc_thread = None
        self.last_tc = None
        self.rate = rate
        self.ready = Event()

    def start(self):
        self.tm_thread = Thread(target=send_tm, args=(self,))
        self.tm_thread.daemon = True
        self.tm_thread.start()
        self.tc_thread = Thread(target=receive_tc, args=(self,))
        self.tc_thread.daemon = True
        self.tc_thread.start()

    def print_status(self):
        cmdhex = None
        if self.last_tc:
            cmdhex = binascii.hexlify(self.last_tc).decode('ascii')
        return 'Sent: \033[34m{}\033[0m packets. Received: {} commands. Last command: {}'.format(
                         self.tm_counter, self.tc_counter, cmdhex)


if __name__ == '__main__':
    simulator = Simulator(RATE)
    simulator.start()
    sys.stdout.write('Using playback rate of ' + str(RATE) + 'Hz, ');
    sys.stdout.write('TM host=' + str(TM_SEND_ADDRESS) + ', TM port=' + str(TM_SEND_PORT) + ', ');
    sys.stdout.write('TC host=' + str(TC_RECEIVE_ADDRESS) + ', TC port=' + str(TC_RECEIVE_PORT) + '\r\n');
    try:
        simulator.ready.wait()
        prev_status = None
        while True:
            status = simulator.print_status()
            if status != prev_status:
                sys.stdout.write('\r')
                sys.stdout.write(status)
                sys.stdout.flush()
                prev_status = status
            sleep(0.5)
    except KeyboardInterrupt:
        sys.stdout.write('\n')
        sys.stdout.flush()
