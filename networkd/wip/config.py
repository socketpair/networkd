# coding=utf-8

#TODO: add inbound/ougoing shaping of traffic, basic firewalling?
# shaper of external interfaces: более гладкий выход трафика, разный шейпер для разных подсетей
# Входящий шейпер - для ограничения исходящего от пользователя трафика

config = {
    # TODO: each IP should have corresponding MAC-address
    'Local1': {
        'hwspeed': '1Gbit FD',
        'netdevice': ['netcard', '1c:75:08:f2:aa:3b'],
        'vlan': 1234,
        'macaddress': '11:22:33:44:55:66',
        'mtu': 1500,
        'addresses': [
            '1.2.3.4/24',
        ],
        'peer': '5.6.7.8', # generate automatic route through
        'gateways': {
            '5.5.5.5': ['0.0.0.0/0', '192.168.5.0/24'],
        },
        'onlink': ['9.9.9.9'],
        'dns': {
            '6.6.6.6': ['ideco.', 'test.'], # list of zones where this DNS answers
        },
        'proxyarps': ['aa:bb:cc:dd:ee:ff'],
    },
}


class EthernetConfig(object):
    pass
