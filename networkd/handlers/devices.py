# coding=utf-8
from networkd.handlers.common import CommonHandler


def _render_device(device1):
    """
    :type device1: PhysicalEthernet
    """
    def rrr(device):
        """
        :type device: PhysicalEthernet
        """
        for name in dir(device):
            if name.startswith('_'):
                continue
            attr = getattr(device, name)
            if callable(attr):
                continue
            yield (name, attr)
        yield ('RUNTIME', device1.get_runtime_info())
    return dict(rrr(device1))


class DeviceInfoHandler(CommonHandler):
    # noinspection PyMethodOverriding
    def initialize(self, ethmanager):
        """
        :type ethmanager: DeviceManager
        """
        super(DeviceInfoHandler, self).initialize()
        self.manager = ethmanager

    def get(self, ifindex=None):
        manager = self.manager

        if ifindex:
            device = manager.get_device(int(ifindex))
            items = {
                device.index: _render_device(device)
            }
        else:
            items = dict((device.index, _render_device(device)) for device in manager.get_devices())

        # if self.get_argument('force', False):
        #     manager.rescan_devices()

        self.finish({
            'status': 'ok',
            'items': items,
        })


class DevicesActionHandler(CommonHandler):
    # noinspection PyMethodOverriding
    def initialize(self, ethmanager):
        """
        :type ethmanager: DeviceManager
        """
        super(DevicesActionHandler, self).initialize()
        self.manager = ethmanager

    def get(self, action=None):
        manager = self.manager

        if action == 'rescan':
            manager.rescan_devices()
        else:
            raise ValueError('No such action', action)

        self.finish({
            'status': 'ok',
        })


class DeviceActionHandler(CommonHandler):
    # noinspection PyMethodOverriding
    def initialize(self, ethmanager):
        """
        :type ethmanager: DeviceManager
        """
        super(DeviceActionHandler, self).initialize()
        self.manager = ethmanager

    def get(self, ifindex=None, action=None):
        manager = self.manager

        device = manager.get_device(int(ifindex))

        if action == 'identify':
            # TODO: catch exception (!)
            # And more, check if identification is not supported (probe? flags?)
            # report that in properties of this device
            device.start_identify(3)
        else:
            raise ValueError('No such action', action)

        self.finish({
            'status': 'ok',
        })
