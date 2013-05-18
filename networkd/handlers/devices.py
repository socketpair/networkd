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


class DevicesHandler(CommonHandler):
    # noinspection PyMethodOverriding
    def initialize(self, ethmanager):
        """
        :type ethmanager: DeviceManager
        """
        super(DevicesHandler, self).initialize()
        self.manager = ethmanager


    def get(self, ifindex=None, action=None):
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
