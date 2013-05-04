# coding=utf-8

"""
list of network devices
identify devices
blink LED, report PCI port, report hardware info to user
event of changes
bind connection of appropriate type to given devices
periodically detect ip conflict, mac conflict
periodically send gratuitous arp
"""

from array import array
from contextlib import closing
import fcntl
import socket
import struct
import subprocess

SIOCGIFNAME = 0x8910


class PhysicalEthernet(object):
    # 16 - IFNAMSIZ
    cgifname_struct = struct.Struct('@16si')

    def __init__(self, index):
        self.index = index
        self.req = array('c', self.cgifname_struct.pack('', self.index))

    @property
    def ifacename(self):
        with closing(socket.socket()) as sk:
            if fcntl.ioctl(sk.fileno(), SIOCGIFNAME, self.req, True):
                raise RuntimeError('ioctl failed')
        (name, idx) = self.cgifname_struct.unpack_from(self.req)
        return name.rstrip(b'\x00')

    def identify(self, seconds=3):
        """
        Blink led (if supported)
        """
        subprocess.check_call([
            'ethtool', '--identify', self.ifacename, str(seconds)
        ])

    def get_runtime_info(self):
        subprocess.check_call([
            'ethtool', self.ifacename,
        ])
