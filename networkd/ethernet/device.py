# coding=utf-8

"""
event of changes
bind connection of appropriate type to given devices
"""
from ctypes import c_void_p, cast, byref
from logging import getLogger
import socket
import fcntl
import prctl
import subprocess
from threading import Thread

from networkd.lowlevel.libc import ifreq, SIOCGIFNAME, SIOCETHTOOL, ETHTOOL_GPERMADDR, ETH_ALEN, ethtool_perm_addr, \
    ETHTOOL_GDRVINFO, ethtool_drvinfo, ethtool_value, ETHTOOL_PHYS_ID, block_all_thread_signals
log = getLogger(__name__)

# 'sysname': device.sys_name,
# 'devtype': device.device_type,  # always None. why?
# 'sysnumber': device.sys_number,
# 'type': device.device_type,
# 'links': list(device.device_links),
# 'tags': list(device.tags),
# 'hwaddr?': device.attributes['address'], # NO! current address (not real hwaddr... )


class SocketForIoctl(socket.SocketType):
    _instance = None

    def __new__(cls, *args):
        if cls._instance is None:
            log.debug('Creating %s instance', cls)
            cls._instance = super(SocketForIoctl, cls).__new__(cls, *args)
        return cls._instance

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


def generate_debuginfo(device, show_parents=True):
    retval = {
        'attrs': dict(((k, repr(device.attributes.get(k))) for k in device.attributes.iterkeys())),
        'dict': dict(device),
    }
    if show_parents:
        retval['parents'] = dict(enumerate(generate_debuginfo(parent, False) for parent in device.ancestors))
    return retval

class PhysicalEthernet(object):
    def __init__(self, device):
        """
        :type device: Device
        """
        self._sk_fileno = SocketForIoctl().fileno()
        self.index = device.asint('IFINDEX')

        #TODO: what if not exists in BD (!)
        self.model1 = device.get('ID_MODEL_FROM_DATABASE')
        self.vendor1 = device.get('ID_VENDOR_FROM_DATABASE')

        self.model2 = device.get('ID_MODEL_ENC')
        self.vendor2 = device.get('ID_VENDOR_ENC')

        if self.model2:
            self.model2 = self.model2.decode('string_escape')
        if self.vendor2:
            self.vendor2 = self.vendor2.decode('string_escape')

        self.driver_of_parent = device.parent.driver
        #self.driver = device.driver # always NULL
        self.bus = device.get('ID_BUS')
        if self.bus == 'pci':
            pci_device = device.find_parent('pci')
            self.pci_driver = pci_device.driver
            self.pci_id = pci_device.get('PCI_ID')
            self.pci_slot = pci_device.get('PCI_SLOT_NAME')
            self.pci_irq = pci_device.attributes.asint('irq')
        elif self.bus == 'usb':
            self.driver_of_self = device.get('ID_USB_DRIVER')
            usb_device = device.find_parent('usb', 'usb_device')
            self.usb_bMaxPower = usb_device.attributes['bMaxPower']
            self.usb_speed = float(usb_device.attributes['speed'].strip("'"))
            self.usb_version = float(usb_device.attributes['version'].strip("'").strip(' '))


        self._fill_permaddr()
        self._fill_drvinfo()
        #self.start_identify()

    # def get_runtime_info(self):
    #     subprocess.check_call([
    #         'ethtool', self._get_iface_name(),
    #     ])

    def _get_iface_name(self):
        """
        :rtype : str
        """
        # TODO: Should never be used. Also, re-create via netlink, and monitor that...
        # generates race-condition, as interface name may be changed after calling this
        # function and before using returned name
        req = ifreq(ifr_ifindex=self.index)
        if fcntl.ioctl(self._sk_fileno, SIOCGIFNAME, req, True):
            raise RuntimeError('SIOCGIFNAME ioctl failed')
        return req.ifr_name

    def _do_ethtool(self, cmd):
        iface = self._get_iface_name()
        data = cast(byref(cmd), c_void_p)

        req = ifreq(ifr_name=iface, ifr_data=data)

        if fcntl.ioctl(self._sk_fileno, SIOCETHTOOL, req, True):
            raise RuntimeError('SIOCETHTOOL ioctl failed', cmd.cmd)

    def _fill_permaddr(self):
        """
        :rtype : str
        """
        perm_addr = ethtool_perm_addr(cmd=ETHTOOL_GPERMADDR, size=ETH_ALEN)
        self._do_ethtool(perm_addr)
        if perm_addr.size != ETH_ALEN:
            raise RuntimeError('Returned mac address is not %d bytes length', ETH_ALEN)
        self.permaddr = ':'.join('{0:02X}'.format(bbb) for bbb in perm_addr.data[:perm_addr.size])

    def _fill_drvinfo(self):
        drv_info = ethtool_drvinfo(cmd=ETHTOOL_GDRVINFO)
        self._do_ethtool(drv_info)

        self.ethtool_driver = drv_info.driver
        self.ethtool_driver_version = drv_info.version
        self.ethtool_fw_version = drv_info.fw_version if drv_info.fw_version != 'N/A' else None
        self.ethtool_bus_info = drv_info.bus_info

    def start_identify(self, seconds=3):
        """
        :type seconds: int

        NOTE: this ioctl is blocking(!). Thanks to ethtool API.
        So, will run in thread...
        """
        cmd = ethtool_value(cmd=ETHTOOL_PHYS_ID, data=seconds)

        thread_name = 'if_{0}_wait'.format(self.index)

        def async_identify():
            block_all_thread_signals()
            prctl.set_name(thread_name)
            self._do_ethtool(cmd)

        thr = Thread(target=async_identify, name=thread_name)
        thr.daemon = True
        thr.start()
