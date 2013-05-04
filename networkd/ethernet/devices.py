# coding=utf-8
from functools import partial
from logging import getLogger
import os
import pyudev
from pyudev.device import Device
import fcntl
from tornado.ioloop import IOLoop
from tornado.platform.auto import set_close_exec

log = getLogger(__name__)


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


def render_device(device):
    """
    :type device: Device
    """

    info = {
        'index': device['IFINDEX'],
        'vendor': device.get('ID_VENDOR_FROM_DATABASE'),
        'model': device.get('ID_MODEL_FROM_DATABASE'),
        'bus': device.get('ID_BUS'),
        'iface': device['INTERFACE'],
        # 'hwaddr?': device.attributes['address'], # NO! current address (not real hwaddr... )
        'devtype': device.device_type, # wlan, bridge and so on
    }
    parent = device.find_parent('pci')
    if parent is not None:
        info['card'] = {
            'direct driver': device.parent.driver,
            'pci driver': parent.driver,
            'pci id': parent.get('PCI_ID'),
            'pci slot name': parent.get('PCI_SLOT_NAME'),
            'irq': parent.attributes.asint('irq'),
        }
        # info['parents'] = dict(enumerate(render_device2(qwe, False) for qwe in device.traverse()))
    return info


# # hack for old udev library that lacks monitor.poll()
# def get_udev_reader(monitor):
#     if hasattr(monitor, 'poll'):
#         # 0 - mean NONBLOCKING
#         return partial(monitor.poll, 0)
#
#     def udev_event_reader():
#         while 1:
#             try:
#                 device = pyudev.libudev.udev_monitor_receive_device(monitor)
#             except EnvironmentError as err:
#                 if err.args[0] in (errno.EAGAIN, errno.EWOULDBLOCK):
#                     return
#                 monitor._reraise_with_socket_path()
#             # unreal case when return NULL, but errno=0
#             if device is None:
#                 log.debug('Device returned is None')
#                 return
#             yield device
#     return udev_event_reader

def upgrade_libudev():
    if not hasattr(pyudev.Monitor, 'poll'):

    # from warnings import warn
    # warn('Using workaround for old pyudev version')

        import select

        from pyudev.core import libudev

        def poll_copy(self, timeout=None):
            rlist, _, _ = select.select([self], [], [], timeout)
            if self not in rlist:
                return None

            device_p = libudev.udev_monitor_receive_device(self)
            if device_p:
                return Device(self.context, device_p)

            raise EnvironmentError('Could not receive device')

        pyudev.Monitor.poll = poll_copy

    if not hasattr('Device', 'action'):

        from pyudev.core import libudev, ensure_unicode_string

        @property
        def action_copy(self):
            action = libudev.udev_device_get_action(self)
            if action:
                return ensure_unicode_string(action)

        Device.action = action_copy  # property(fget=lambda self: self.get('ACTION'))


upgrade_libudev()


class DeviceManager(object):
    def __init__(self):
        log.debug('Creating ULOG context')
        log.debug(log.name)
        self.netdevices = dict()  # ifindex => MyDevice

        self.udev_version = pyudev.udev_version()
        log.debug('Working against udev version %r', self.udev_version)

        context = pyudev.Context()
        self._prepare_background_monitoring(context)
        self.context = context
        self.rescan_devices()

    def rescan_devices(self):
        # do the coldplug...
        # TODO: detect dead devices and remove them
        for device in self.context.list_devices(subsystem='net'):
            self._handle_event(device)

    def _prepare_background_monitoring(self, context):
        monitor = pyudev.Monitor.from_netlink(context, 'udev')
        monitor.filter_by(subsystem='net')
        monitor.start()

        monitor_fileno = monitor.fileno()

        # we do not trust the udev library....
        set_close_exec(monitor_fileno)
        fcntl.fcntl(monitor_fileno, fcntl.F_SETFL, fcntl.fcntl(monitor_fileno, fcntl.F_GETFL, 0) | os.O_NONBLOCK)

        io_loop = IOLoop.instance()
        io_loop.add_handler(monitor_fileno, partial(self._handle_udev_event, partial(monitor.poll, 0)), io_loop.READ)

    def _handle_udev_event(self, udev_event_reader, fd, events):
        log.debug('udev event %r %r', fd, events)
        for device in iter(udev_event_reader, None):
            self._handle_event(device)

    def _handle_event(self, device):
        log.debug('%r %r', device.action, device)

        # we will ignore that. Wi will not use interface name at our job (races?)
        # receiving events say that devices always uninitialized.
        # TODO: think about a way to wait for device initialization
        # if self.udev_version >= 165:
        #     if not device.is_initialized:
        #         log.debug('Skipping uninitialized device %r', device)
        #         return

        ifindex = device.get('IFINDEX', None)
        if ifindex is None:
            log.debug('Skipping device without IFINDEX %r', device)
            return
        ifindex = int(ifindex)

        if device.parent is None:
            log.debug('Skipping device without parent (non-hardware?), %r', device)
            return

        action = device.action
        # TODO: add may appear AFTER coldplug, this is OK (races)
        if (action is None) or (action == u'add'):
            self.netdevices[ifindex] = render_device(device)

        if action == u'remove':
            try:
                del self.netdevices[ifindex]
            except KeyError:
                log.exception('Device removal error', device, ifindex)

                # actions: add, None, move, add, remove, change, online, offline

    def get_dev_list(self):
        return self.netdevices

