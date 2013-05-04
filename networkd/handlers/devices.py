# coding=utf-8
from networkd.handlers.common import CommonHandler


class DevicesHandler(CommonHandler):
    # noinspection PyMethodOverriding
    def initialize(self, ethmanager):
        """
        :type ethmanager: DeviceManager
        """
        super(DevicesHandler, self).initialize()
        self.manager = ethmanager

    def get(self, ifindex=None):
        if self.get_argument('force', False):
            self.manager.rescan_devices()

        self.finish({
            'status': 'ok',
            'devices': self.manager.get_dev_list()
        })
