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

    def _render_device(self, device):
        dev_descr = {
            'index': device.index,
            'vendor': device.vendor,
            'model': device.model,
            'bus': device.bus,
            'driver_direct': device.driver_direct,
            'ifacename': device.ifacename,
            'permaddr': device.permaddr,
        }
        if device.bus == 'pci':
            dev_descr['pci_info'] = {
                'driver': device.pci_driver,
                'id': device.pci_id,
                'slot': device.pci_slot,
                'irq': device.pci_irq,
            }

        debug = getattr(device, 'debug', None)
        if debug is not None:
            dev_descr['debug'] = debug

        return dev_descr

    def get(self, ifindex=None, action=None):
        manager = self.manager

        if ifindex:
            device = manager.get_device(int(ifindex))
            items = {
                device.index: self._render_device(device)
            }
        else:
            items = dict((device.index, self._render_device(device)) for device in manager.get_devices())

        # if self.get_argument('force', False):
        #     manager.rescan_devices()

        self.finish({
            'status': 'ok',
            'items': items,
        })
