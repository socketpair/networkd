# coding=utf-8

from time import sleep
from networkd.lowlevel.thread import NosignalingThread


class RuntimeItems(object):
    def __init__(self):
        self.values = dict()
        self.speeds = dict()

    def first_scan(self):
        self.values = dict(self.read_values())

    def rescan(self):
        new_values = dict(self.read_values())
        # TODO: Use dict comprehension here (!)
        # TODO: cal deltatime (clock_gettime() or python's 3 func) + update speed as appropriate
        new_speeds = dict(self.calculate_speeds(self.values, self.speeds, new_values))
        (self.values, self.speeds) = (new_values, new_speeds)

    def calculate_speeds(self, values, speeds, newvalues):
        for (irq, interrupt_count) in newvalues.iteritems():
            speed = interrupt_count - values.get(irq, interrupt_count)
            meanspeed = speeds.get(irq, speed) * 0.7 + speed * 0.3
            yield (irq, meanspeed)

    def read_values(self):
        return []


class Interrupts(RuntimeItems):
    def __init__(self):
        self.fileobj = open('/proc/interrupts', 'rt')
        super(Interrupts, self).__init__()

    def __del__(self):
        self.fileobj.close()

    def read_values(self):
        fileobj = self.fileobj
        # TODO: SEEK_SET
        # seeking back to start and reading again for that file generate new info every time.
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


class RuntimeMonitor(object):
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.interrupts = Interrupts()
        self.items = [self.interrupts]

        thrd = NosignalingThread(target=self._inthread, name='interrupts_mon')
        thrd.daemon = True
        thrd.start()
        self._thrd = thrd

    def _inthread(self):
        for i in self.items:
            i.first_scan()
        while 1:
            sleep(1)
            for i in self.items:
                i.rescan()
