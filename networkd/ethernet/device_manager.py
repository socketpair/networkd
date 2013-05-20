# coding=utf-8
from functools import partial
from logging import getLogger
import os
import pyudev
from pyudev.device import Device
import fcntl
from tornado.ioloop import IOLoop
from tornado.platform.auto import set_close_exec
from networkd.ethernet.device import PhysicalEthernet
from networkd.ethernet.interrupts import InterruptMonitor

log = getLogger(__name__)


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

    if not hasattr(Device, 'action'):

        from pyudev.core import libudev, ensure_unicode_string

        @property
        def action_copy(self):
            action = libudev.udev_device_get_action(self)
            if action:
                return ensure_unicode_string(action)

        Device.action = action_copy

    if not hasattr(Device, 'ancestors'):
        @property
        def ancestors_copy(self):
            return self.traverse()

        Device.ancestors = ancestors_copy

    if not hasattr(Device, 'sequence_number'):
        @property
        def sequence_number_copy(self):
            return int(self.get('SEQNUM', 0))

        Device.sequence_number = sequence_number_copy


upgrade_libudev()


class DeviceManager(object):
    def __init__(self):
        # log.debug('Creating ULOG context')
        log.debug(log.name)
        self.netdevices = dict()  # ifindex => MyDevice

        self.udev_version = pyudev.udev_version()
        log.info('Working against udev version %d', self.udev_version)

        # TODO: time_since_initialized  > 0?

        self.context = pyudev.Context()
        self._start_background_udev_monitoring()
        self._start_interrupt_monitoring()
        self.rescan_devices()

    def _start_interrupt_monitoring(self):
        self._interruptmonitor = InterruptMonitor()

    def rescan_devices(self):
        olddevices = self.netdevices
        self.netdevices = dict()
        try:
            for device in self.context.list_devices(subsystem='net'):
                self._handle_device_event(device)
        except:
            self.netdevices = olddevices
            raise
        newindexes = set(self.netdevices.iterkeys())
        oldindexes = set(olddevices.iterkeys())
        added = newindexes - oldindexes
        removed = oldindexes - newindexes
        if added:
            log.debug('Scan: found %d new devices', len(added))
        if removed:
            log.debug('Scan: %d devices disappear', len(removed))

    def _start_background_udev_monitoring(self):
        monitor = pyudev.Monitor.from_netlink(self.context, 'udev')
        monitor.filter_by(subsystem='net')
        monitor.start()

        monitor_fileno = monitor.fileno()

        # we do not trust the udev library....
        set_close_exec(monitor_fileno)
        fcntl.fcntl(monitor_fileno, fcntl.F_SETFL, fcntl.fcntl(monitor_fileno, fcntl.F_GETFL, 0) | os.O_NONBLOCK)

        io_loop = IOLoop.instance()

        fd_handler = partial(self._handle_udev_event, partial(monitor.poll, 0))
        io_loop.add_handler(monitor_fileno, fd_handler, IOLoop.READ | IOLoop.ERROR)

    def _handle_udev_event(self, udev_event_reader, fd, events):
        if events & IOLoop.READ:
            log.debug('udev event %r %r', fd, events)
            for device in iter(udev_event_reader, None):
                self._handle_device_event(device)
        if events & IOLoop.ERROR:
            log.error('Error on monitoring socket. Stopping monitoring')
            IOLoop.instance().remove_handler(fd)

    def _handle_device_event(self, device):
        """
        :type device: Device
        """
        # log.debug('Event: %r for %r', device.action, device)

        #TODO: udev_device_get_ifindex
        ifindex = device.get('IFINDEX', None)
        if ifindex is None:
            log.debug('Skipping device without IFINDEX %r', device)
            return
        ifindex = int(ifindex)

        if device.parent is None:
            log.debug('Skipping device without parent (non-hardware), %r', device)
            return

        # devtype = device.device_type
        # if devtype is not None:
        #     log.debug('Device %r have type %r, so skipped', device, devtype)
        #     return

        action = device.action

        # TODO: add may appear AFTER coldplug, this is OK (races)
        if (action is None) or (action == u'add'):

            if self.udev_version >= 165:
                # TODO: handle udev's initializations errors instead of raise
                if not device.is_initialized:
                    device_path = device.device_path
                    log.debug('Device is not initialized. re-reading %s', device_path)
                    device = Device.from_path(self.context, device_path)
                    if not device.is_initialized:
                        raise Exception('Double-getting device still not initializd')
            else:
                device = Device.from_path(self.context, device.device_path)

            #TODO: udev_device_get_ifindex
            self.netdevices[ifindex] = PhysicalEthernet(device, self._interruptmonitor)
            return

        if action == u'remove':
            try:
                old_eth_device = self.netdevices.pop(ifindex)
            except KeyError:
                log.exception('Device removal error (no such device). Scheduling full rescan.', device, ifindex)
                IOLoop.instance().add_callback(self.rescan_devices)
                return
            old_eth_device.close()

            # actions: add, None, move, add, remove, change, online, offline

    def get_devices(self):
        # TODO: it is not safe to return generator
        # if modification event appear during middle of iteration,
        # modify request will fail
        return self.netdevices.itervalues()

    def get_device(self, index):
        """

        :type index: int
        :rtype : PhysicalEthernet
        """
        return self.netdevices[index]
