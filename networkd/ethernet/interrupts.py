# coding=utf-8

from threading import Thread
from time import sleep
import prctl
from networkd.lowlevel.libc import block_all_thread_signals


def qwe(values, speeds, newvalues):
    for (irq, interrupt_count) in newvalues.iteritems():
        speed = interrupt_count - values.get(irq, interrupt_count)
        meanspeed = speeds.get(irq, speed) * 0.7 + speed * 0.3
        yield (irq, meanspeed)


class InterruptMonitor(object):
    def __init__(self):
        self.values = dict()
        self.speeds = dict()
        thrd = Thread(target=self._inthread)
        thrd.daemon = True
        self._thrd = thrd
        thrd.start()

    def _inthread(self):
        block_all_thread_signals()
        prctl.set_name('interrupts_mon')
        self.values = dict(self.read_interrupts())
        while 1:
            sleep(1)
            new_values = dict(self.read_interrupts())
            # TODO: Use dict comprehension here (!)
            # TODO: cal deltatime (clock_gettime() or python's 3 func) + update speed as appropriate
            new_speeds = dict(qwe(self.values, self.speeds, new_values))
            (self.values, self.speeds) = (new_values, new_speeds)

    def read_interrupts(self):
        with open('/proc/interrupts', 'rt', 4096) as fileobj:
            cpus = fileobj.readline().count('CPU')
            # print 'CPUS', cpus
            for line in fileobj:
                # print 'LINE', line
                (irq, descr) = line.split(':', 1)
                irq = irq.lstrip()
                try:
                    irq = int(irq)
                except ValueError:
                    pass
                yield irq, sum(int(v) for v in descr.split(None, cpus)[:cpus])
