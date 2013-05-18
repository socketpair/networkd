# coding=utf-8
from threading import Thread
import prctl
from networkd.lowlevel.libc import block_all_thread_signals


class NosignalingThread(Thread):
    def run(self):
        block_all_thread_signals()
        prctl.set_name(self.name)
        super(NosignalingThread, self).run()
