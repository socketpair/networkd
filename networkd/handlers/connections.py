# coding=utf-8
from networkd.handlers.common import CommonHandler


class ConnectionsHandler(CommonHandler):
    def get(self):
        self.write("Hello, world")

