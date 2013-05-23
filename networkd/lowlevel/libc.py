# coding=utf-8
from ctypes import c_int, c_void_p, c_char, c_uint32, c_uint8, c_byte, Union, Structure, CDLL, get_errno
import os

IFNAMSIZ = 16
ETH_ALEN = 6

SIOCGIFNAME = 0x8910
SIOCETHTOOL = 0x8946


class ifreq_union(Union):
    _fields_ = [
        ("ifr_ifindex", c_int),
        ("ifr_data", c_void_p),
    ]


class ifreq(Structure):
    _fields_ = [("ifr_name", c_char * IFNAMSIZ),
                ("ifr_union", ifreq_union)]
    _anonymous_ = ['ifr_union']


ETHTOOL_GDRVINFO = 0x00000003
ETHTOOL_GPERMADDR = 0x00000020
ETHTOOL_PHYS_ID = 0x0000001c


class ethtool_perm_addr(Structure):
    _fields_ = [
        ('cmd', c_uint32),
        ('size', c_uint32),
        ('data', c_uint8 * ETH_ALEN), # data[0] actually
    ]


class ethtool_value(Structure):
    _fields_ = [
        ('cmd', c_uint32),
        ('data', c_uint32),
    ]


ETHTOOL_FWVERS_LEN = 32
ETHTOOL_BUSINFO_LEN = 32


class ethtool_drvinfo(Structure):
    _fields_ = [
        ('cmd', c_uint32),
        ('driver', c_char * 32),
        ('version', c_char * 32),
        ('fw_version', c_char * ETHTOOL_FWVERS_LEN),
        ('bus_info', c_char * ETHTOOL_BUSINFO_LEN),
        ('reserved1', c_byte * 32),
        ('reserved2', c_byte * 12),
        ('n_priv_flags', c_uint32),
        ('n_stats', c_uint32),
        ('testinfo_len', c_uint32),
        ('eedump_len', c_uint32),
        ('regdump_len', c_uint32),
    ]

# class ethtool_cmd(Structure):
#     _fields_ = [
#         ('cmd', c_uint32),
#         ('supported', c_uint32),
#         ('advertising', c_uint32),
#         ('speed', c_uint16),
#         ('duplex', c_uint8),
#         ('port', c_uint8),
#         ('phy_address', c_uint8),
#         ('transceiver', c_uint8),
#         ('autoneg', c_uint8),
#         ('mdio_support', c_uint8),
#         ('maxtxpkt', c_uint32),
#         ('maxrxpkt', c_uint32),
#         ('speed_hi', c_uint16),
#         ('eth_tp_mdix', c_uint8),
#         ('reserved2', c_uint8),
#         ('lp_advertising', c_uint32),
#         ('reserved', c_uint32 * 2),
#     ]

# 1024 bits
SIGSET = c_byte * (1024 / 8)

if os.uname()[0] == "FreeBSD":
    SIG_BLOCK = 1
    SIG_UNBLOCK = 2
    SIG_SETMASK = 3
else:
    SIG_BLOCK = 0
    SIG_UNBLOCK = 1
    SIG_SETMASK = 2


def pthread_error_checker(result, func, args):
    if not result:
        return
    raise RuntimeError('libc returns error', result, func, args)


def std_errno_check(result, func, args):
    if result != -1:
        return
    raise RuntimeError('libc returns error', get_errno(), func, args)


libc = CDLL(None, use_errno=True)

#pthread_kill
pthread_sigmask = libc.pthread_sigmask
pthread_sigmask.argtypes = [c_int, c_void_p, c_void_p]
pthread_sigmask.restype = c_int
pthread_sigmask.errcheck = pthread_error_checker

sigfillset = libc.sigfillset
sigfillset.argtypes = [c_void_p]
sigfillset.restype = c_int
sigfillset.errcheck = std_errno_check


def block_all_thread_signals():
    # noinspection PyCallingNonCallable
    sigset = SIGSET()
    sigfillset(sigset)
    pthread_sigmask(SIG_SETMASK, sigset, None)
