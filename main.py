#!/usr/bin/env python2
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
import prctl

from tornado import options
from tornado.ioloop import IOLoop
from tornado.web import Application
from networkd.handlers.devices import DeviceInfoHandler, DeviceActionHandler, DevicesActionHandler
from networkd.ethernet.devices import DeviceManager


def main():
    prctl.set_name('networkd_main')
    prctl.set_proctitle('networkd')
    options.parse_command_line()
    dm = DeviceManager()
    application = Application([
        (r"/devices", DeviceInfoHandler, dict(ethmanager=dm)),
        (r"/devices/([0-9]+)", DeviceInfoHandler, dict(ethmanager=dm)),

        (r"/devices/actions/(.+)", DevicesActionHandler, dict(ethmanager=dm)),
        (r"/devices/([0-9]+)/actions/(.+)", DeviceActionHandler, dict(ethmanager=dm)),
    ])
    application.listen(8888)
    IOLoop.instance().start()


if __name__ == '__main__':
    main()
