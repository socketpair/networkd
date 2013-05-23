# coding=utf-8

"""
perform link detection (ping, TCP)
"""

# файрвол - пускать на вход только пакеты у которых src попадает в забинденную сеть (для локальных)
# RP-filter
# является ли роутером (IP_FORWARD) (т.е. отбрасывать ли пакеты с не нашим DST)
# треугольная маршрутизация - отключать прием и отправку ICMP redirect
# пинговать время от времени - для проверки связи
# оценивать загруженность шейперов
# количество пакетов в секунду

# v = v*0.9 + v1 #
#


class EthernetConnection(object):
    def connect(self, device, config):
        pass

    def status(self):
        """
        return link, statistics
        """
        pass

    def arp_records(self):
        pass

    def discover_peers(self):
        """
        discover peers, detects if it is router
        """

