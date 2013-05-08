#!/usr/bin/env python2.6
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
from networkd.handlers.devices import DevicesHandler
from networkd.ethernet.devices import DeviceManager


def main():
    options.parse_command_line()
    dm = DeviceManager()
    application = Application([
        (r"/devices", DevicesHandler, dict(ethmanager=dm)),
        (r"/devices/(.*)", DevicesHandler, dict(ethmanager=dm)),
        (r"/device/([0-9]+)", DevicesHandler, dict(ethmanager=dm)),
        (r"/device/([0-9]+)/(.*)", DevicesHandler, dict(ethmanager=dm)),
    ])
    application.listen(8888)
    IOLoop.instance().start()


if __name__ == '__main__':
    main()
