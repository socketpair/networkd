#!/usr/bin/env python2.7
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

from tornado import options
from tornado.ioloop import IOLoop
from tornado.web import Application
from networkd.handlers.connections import ConnectionsHandler
from networkd.handlers.devices import DevicesHandler
from networkd.ethernet.device import PhysicalEthernet
from networkd.ethernet.devices import DeviceManager


def main():
    options.parse_command_line()
    application = Application([
        (r"/connections", ConnectionsHandler),
        (r"/devices", DevicesHandler, dict(ethmanager=DeviceManager())),
    ])
    application.listen(8888)
    IOLoop.instance().start()

    qwe = PhysicalEthernet(2)
    qwe.identify()
    qwe.identify()


if __name__ == '__main__':
    main()
