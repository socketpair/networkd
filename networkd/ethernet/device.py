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
from logging import getLogger
import socket
import struct
import subprocess

log = getLogger(__name__)

SIOCGIFNAME = 0x8910
SIOCETHTOOL = 0x8946

# def render_device2(device, parents=True):
#     """
#     :type device: Device
#     """
#     info = {
#         'attrs': dict(((k, repr(device.attributes.get(k))) for k in device.attributes.iterkeys())),
#         'driver': device.driver,
#         'dict': dict(device),
#         # 'sysname': device.sys_name,
#         # 'devtype': device.device_type,  # always None. why?
#         # 'sysnumber': device.sys_number,
#         # 'type': device.device_type,
#         # 'links': list(device.device_links),
#         # 'tags': list(device.tags),
#     }
#     if parents:
#         info['parents'] = dict(enumerate(render_device(qwe, False) for qwe in device.traverse()))
#     return info


# def render_device(device):
#     """
#     :type device: Device
#     """
#
#     info = {
#         'index': device['IFINDEX'],
#         'vendor': device.get('ID_VENDOR_FROM_DATABASE'),
#         'model': device.get('ID_MODEL_FROM_DATABASE'),
#         'bus': device.get('ID_BUS'),
#         'iface': device['INTERFACE'],
#         # 'hwaddr?': device.attributes['address'], # NO! current address (not real hwaddr... )
#         # 'devtype': device.device_type, # wlan, bridge and so on
#     }
#     parent = device.find_parent('pci')
#     if parent is not None:
#         info['card'] = {
#             'direct driver': device.parent.driver,
#             'pci driver': parent.driver,
#             'pci id': parent.get('PCI_ID'),
#             'pci slot name': parent.get('PCI_SLOT_NAME'),
#             'irq': parent.attributes.asint('irq'),
#         }
#         # info['parents'] = dict(enumerate(render_device2(qwe, False) for qwe in device.traverse()))
#     return info


# 16 - IFNAMSIZ
cgifname_struct = struct.Struct('@16si')

def upgrade_subprocess():
    if hasattr(subprocess, 'check_output'):
        return

    def _check_output(*popenargs, **kwargs):
        if 'stdout' in kwargs:
            raise ValueError('stdout argument not allowed, it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd, output=output)
        return output

    subprocess.check_output = _check_output

upgrade_subprocess()


class PhysicalEthernet(object):
    def __init__(self, device):
        """
        :type device: Device
        """
        self.index = device.asint('IFINDEX')
        self.vendor = device.get('ID_VENDOR_FROM_DATABASE')
        self.model = device.get('ID_MODEL_FROM_DATABASE')
        self.bus = device.get('ID_BUS')
        self.driver_direct = device.parent.driver
        pci_device = device.find_parent('pci')
        if pci_device is not None:
            self.pci_driver = pci_device.driver
            self.pci_id = pci_device.get('PCI_ID')
            self.pci_slot = pci_device.get('PCI_SLOT_NAME')
            self.pci_irq = pci_device.attributes.asint('irq')

        # ETHTOOL_GPERMADDR
        address = subprocess.check_output([
            'ethtool', '--show-permaddr', self.ifacename
        ])
        # TODO: regexp validate, and also 00:00:00:00:00:00, FF:FF:FF:FF:FF:FF, and also case-sensitivity
        self.permaddr = address.rsplit(None, 1)[-1].upper()
        self.debug = {
            'attrs': dict(((k, repr(device.attributes.get(k))) for k in device.attributes.iterkeys())),
            'dict': dict(device),
        }

    @property
    def ifacename(self):
        """
        Deprecated. We should use netlink monitoring for name changes...
        """
        req = array('c', cgifname_struct.pack('', self.index))
        with closing(socket.socket()) as sk:
            if fcntl.ioctl(sk.fileno(), SIOCGIFNAME, req, True):
                raise RuntimeError('ioctl failed')
        (name, idx) = cgifname_struct.unpack_from(req)
        return name.rstrip(b'\x00')



    def identify(self, seconds=3):
        """
        Blink led (if supported)
        ethtool ETHTOOL_PHYS_ID
        """
        subprocess.check_call([
            'ethtool', '--identify', self.ifacename, str(seconds)
        ])



    def get_runtime_info(self):
        subprocess.check_call([
            'ethtool', self.ifacename,
        ])
