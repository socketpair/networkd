# coding=utf-8

from time import sleep
from networkd.lowlevel.thread import NosignalingThread


def qwe(values, speeds, newvalues):
    for (irq, interrupt_count) in newvalues.iteritems():
        speed = interrupt_count - values.get(irq, interrupt_count)
        meanspeed = speeds.get(irq, speed) * 0.7 + speed * 0.3
        yield (irq, meanspeed)


def read_interrupts(fileobj):
    """
    :type fileobj: FileIO of str
    """
    # TODO: SEEK_SET
    fileobj.seek(0, 0)
    cpus = fileobj.readline().count('CPU')
    for line in fileobj:
        (irq, descr) = line.split(':', 1)
        irq = irq.lstrip()
        try:
            irq = int(irq)
        except ValueError:
            pass
        icount = sum(int(v) for v in descr.split(None, cpus)[:cpus])
        yield (irq, icount)


class InterruptMonitor(object):
    def __init__(self):
        self.values = dict()
        self.speeds = dict()
        thrd = NosignalingThread(target=self._inthread, name='interrupts_mon')
        thrd.daemon = True
        self._thrd = thrd
        thrd.start()

    def _inthread(self):
        # seeking back to start and reading again for that file generate new info every time.
        with open('/proc/interrupts', 'rt') as fileobj:
            self.values = dict(read_interrupts(fileobj))
            while 1:
                sleep(1)
                new_values = dict(read_interrupts(fileobj))
                # TODO: Use dict comprehension here (!)
                # TODO: cal deltatime (clock_gettime() or python's 3 func) + update speed as appropriate
                new_speeds = dict(qwe(self.values, self.speeds, new_values))
                (self.values, self.speeds) = (new_values, new_speeds)
