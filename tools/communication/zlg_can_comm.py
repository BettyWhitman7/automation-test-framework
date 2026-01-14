# coding:utf-8
#  ZLGCAN API
import copy
import os
import sys
import threading
import time
import platform
import datetime

from ctypes import c_uint, Structure, c_ushort, c_ubyte, Union, c_ulonglong, c_void_p
from ctypes import windll, byref, c_int, POINTER, c_char_p, CFUNCTYPE, cast

from tqdm import tqdm


ZCAN_DEVICE_TYPE = c_uint

INVALID_DEVICE_HANDLE = 0
INVALID_CHANNEL_HANDLE = 0


class ZCANDeviceType:
    """
    Device Type
    """

    ZCAN_PCI5121 = ZCAN_DEVICE_TYPE(1)
    ZCAN_PCI9810 = ZCAN_DEVICE_TYPE(2)
    ZCAN_USBCAN1 = ZCAN_DEVICE_TYPE(3)
    ZCAN_USBCAN2 = ZCAN_DEVICE_TYPE(4)
    ZCAN_PCI9820 = ZCAN_DEVICE_TYPE(5)
    ZCAN_CAN232 = ZCAN_DEVICE_TYPE(6)
    ZCAN_PCI5110 = ZCAN_DEVICE_TYPE(7)
    ZCAN_CANLITE = ZCAN_DEVICE_TYPE(8)
    ZCAN_ISA9620 = ZCAN_DEVICE_TYPE(9)
    ZCAN_ISA5420 = ZCAN_DEVICE_TYPE(10)
    ZCAN_PC104CAN = ZCAN_DEVICE_TYPE(11)
    ZCAN_CANETUDP = ZCAN_DEVICE_TYPE(12)
    ZCAN_CANETE = ZCAN_DEVICE_TYPE(12)
    ZCAN_DNP9810 = ZCAN_DEVICE_TYPE(13)
    ZCAN_PCI9840 = ZCAN_DEVICE_TYPE(14)
    ZCAN_PC104CAN2 = ZCAN_DEVICE_TYPE(15)
    ZCAN_PCI9820I = ZCAN_DEVICE_TYPE(16)
    ZCAN_CANETTCP = ZCAN_DEVICE_TYPE(17)
    ZCAN_PCIE_9220 = ZCAN_DEVICE_TYPE(18)
    ZCAN_PCI5010U = ZCAN_DEVICE_TYPE(19)
    ZCAN_USBCAN_E_U = ZCAN_DEVICE_TYPE(20)
    ZCAN_USBCAN_2E_U = ZCAN_DEVICE_TYPE(21)
    ZCAN_PCI5020U = ZCAN_DEVICE_TYPE(22)
    ZCAN_EG20T_CAN = ZCAN_DEVICE_TYPE(23)
    ZCAN_PCIE9221 = ZCAN_DEVICE_TYPE(24)
    ZCAN_WIFICAN_TCP = ZCAN_DEVICE_TYPE(25)
    ZCAN_WIFICAN_UDP = ZCAN_DEVICE_TYPE(26)
    ZCAN_PCIe9120 = ZCAN_DEVICE_TYPE(27)
    ZCAN_PCIe9110 = ZCAN_DEVICE_TYPE(28)
    ZCAN_PCIe9140 = ZCAN_DEVICE_TYPE(29)
    ZCAN_USBCAN_4E_U = ZCAN_DEVICE_TYPE(31)
    ZCAN_CANDTU_200UR = ZCAN_DEVICE_TYPE(32)
    ZCAN_CANDTU_MINI = ZCAN_DEVICE_TYPE(33)
    ZCAN_USBCAN_8E_U = ZCAN_DEVICE_TYPE(34)
    ZCAN_CANREPLAY = ZCAN_DEVICE_TYPE(35)
    ZCAN_CANDTU_NET = ZCAN_DEVICE_TYPE(36)
    ZCAN_CANDTU_100UR = ZCAN_DEVICE_TYPE(37)
    ZCAN_PCIE_CANFD_100U = ZCAN_DEVICE_TYPE(38)
    ZCAN_PCIE_CANFD_200U = ZCAN_DEVICE_TYPE(39)
    ZCAN_PCIE_CANFD_400U = ZCAN_DEVICE_TYPE(40)
    ZCAN_USBCANFD_200U = ZCAN_DEVICE_TYPE(41)
    ZCAN_USBCANFD_100U = ZCAN_DEVICE_TYPE(42)
    ZCAN_USBCANFD_MINI = ZCAN_DEVICE_TYPE(43)
    ZCAN_CANFDCOM_100IE = ZCAN_DEVICE_TYPE(44)
    ZCAN_CANSCOPE = ZCAN_DEVICE_TYPE(45)
    ZCAN_CLOUD = ZCAN_DEVICE_TYPE(46)
    ZCAN_CANDTU_NET_400 = ZCAN_DEVICE_TYPE(47)
    ZCAN_VIRTUAL_DEVICE = ZCAN_DEVICE_TYPE(99)


"""
 Interface return status
"""
ZCAN_STATUS_ERR = 0
ZCAN_STATUS_OK = 1
ZCAN_STATUS_ONLINE = 2
ZCAN_STATUS_OFFLINE = 3
ZCAN_STATUS_UNSUPPORTED = 4

"""
 CAN type
"""
ZCAN_TYPE_CAN = c_uint(0)
ZCAN_TYPE_CANFD = c_uint(1)

"""
 "ENTER" exit cycle
"""


def bytearray2frame(frame_bytearray, dlc=8):
    """
    字节转报文字符串
    :param frame_bytearray:
    :return:
    """
    frame = [format(i, "0>2x") for i in frame_bytearray][0:dlc]
    return " ".join(frame).upper()


class With_wait_tqdm_by_time:
    def __init__(self, secs=10):
        self.secs = secs - 0.5
        self.is_force_stop = set()
        t = threading.Thread(target=wait_tqdm, args=(self.secs, self.is_force_stop))
        t.start()

    def exit(self):
        # 执行后置条件
        self.is_force_stop.add("停止显示进度条...")


def wait_tqdm(secs, is_force_stop=None):
    """
    使用tqdm库添加一个带进度条的等待功能。
    Args:
        secs (float): 需要等待的秒数。
        is_force_stop (Optional[bool]): 是否强制停止等待，默认为None。仅多线程场景下使用,参数为可变对象.
    """
    pbar = tqdm(total=100, desc="等待", bar_format="{l_bar}{bar}")
    p = 1 / 100
    t0 = time.time()
    interval = 1 if secs / 110 > 1 else secs / 110
    while time.time() - t0 < secs:
        time.sleep(interval)
        if time.time() - t0 > p * secs:
            p += 1 / 100
            pbar.update(1)
        if is_force_stop:
            break
    pbar.close()


def input_thread():
    input()


"""
 Device information
"""


class ZCAN_DEVICE_INFO(Structure):
    _fields_ = [
        ("hw_Version", c_ushort),
        ("fw_Version", c_ushort),
        ("dr_Version", c_ushort),
        ("in_Version", c_ushort),
        ("irq_Num", c_ushort),
        ("can_Num", c_ubyte),
        ("str_Serial_Num", c_ubyte * 20),
        ("str_hw_Type", c_ubyte * 40),
        ("reserved", c_ushort * 4),
    ]

    def __str__(self):
        info = (
            f"Hardware Version: {self.hw_version}",
            f"Firmware Version: {self.fw_version}",
            f"Driver Interface: {self.dr_version}",
            f"Interface Interface: {self.in_version}",
            f"Interrupt Number: {self.irq_num}",
            f"CAN Number: {self.can_num}",
            f"Serial: {self.serial}",
            f"Hardware Type: {self.hw_type}",
        )
        return "\n".join(info)

    @staticmethod
    def __version(version):
        return ("V%02x.%02x" if version // 0xFF >= 9 else "V%d.%02x") % (
            version // 0xFF,
            version & 0xFF,
        )

    @property
    def hw_version(self):
        return self.__version(self.hw_Version)

    @property
    def fw_version(self):
        return self.__version(self.fw_Version)

    @property
    def dr_version(self):
        return self.__version(self.dr_Version)

    @property
    def in_version(self):
        return self.__version(self.in_Version)

    @property
    def irq_num(self):
        return self.irq_Num

    @property
    def can_num(self):
        return self.can_Num

    @property
    def serial(self):
        serial = ""
        for c in self.str_Serial_Num:
            if c > 0:
                serial += chr(c)
            else:
                break
        return serial

    @property
    def hw_type(self):
        hw_type = ""
        for c in self.str_hw_Type:
            if c > 0:
                hw_type += chr(c)
            else:
                break
        return hw_type


class _ZCAN_CHANNEL_CAN_INIT_CONFIG(Structure):
    _fields_ = [
        ("acc_code", c_uint),
        ("acc_mask", c_uint),
        ("reserved", c_uint),
        ("filter", c_ubyte),
        ("timing0", c_ubyte),
        ("timing1", c_ubyte),
        ("mode", c_ubyte),
    ]


class _ZCAN_CHANNEL_CANFD_INIT_CONFIG(Structure):
    _fields_ = [
        ("acc_code", c_uint),
        ("acc_mask", c_uint),
        ("abit_timing", c_uint),
        ("dbit_timing", c_uint),
        ("brp", c_uint),
        ("filter", c_ubyte),
        ("mode", c_ubyte),
        ("pad", c_ushort),
        ("reserved", c_uint),
    ]


class _ZCAN_CHANNEL_INIT_CONFIG(Union):
    _fields_ = [
        ("can", _ZCAN_CHANNEL_CAN_INIT_CONFIG),
        ("canfd", _ZCAN_CHANNEL_CANFD_INIT_CONFIG),
    ]


class ZCAN_CHANNEL_INIT_CONFIG(Structure):
    _fields_ = [("can_type", c_uint), ("config", _ZCAN_CHANNEL_INIT_CONFIG)]


class ZCAN_CHANNEL_ERR_INFO(Structure):
    _fields_ = [
        ("error_code", c_uint),
        ("passive_ErrData", c_ubyte * 3),
        ("arLost_ErrData", c_ubyte),
    ]

    def __str__(self):
        res = dict(
            [
                ("error_code", self.error_code),
                ("passive_ErrData", [d for d in self.passive_ErrData]),
                ("arLost_ErrData", self.arLost_ErrData),
            ]
        )

        return str(res)


class ZCAN_CHANNEL_STATUS(Structure):
    _fields_ = [
        ("errInterrupt", c_ubyte),
        ("regMode", c_ubyte),
        ("regStatus", c_ubyte),
        ("regALCapture", c_ubyte),
        ("regECCapture", c_ubyte),
        ("regEWLimit", c_ubyte),
        ("regRECounter", c_ubyte),
        ("regTECounter", c_ubyte),
        ("Reserved", c_ubyte),
    ]


class ZCAN_CAN_FRAME(Structure):
    _fields_ = [
        ("can_id", c_uint, 29),
        ("err", c_uint, 1),
        ("rtr", c_uint, 1),
        ("eff", c_uint, 1),
        ("can_dlc", c_ubyte),
        ("__pad", c_ubyte),
        ("__res0", c_ubyte),
        ("__res1", c_ubyte),
        ("data", c_ubyte * 8),
    ]


class ZCAN_CANFD_FRAME(Structure):
    _fields_ = [
        ("can_id", c_uint, 29),
        ("err", c_uint, 1),
        ("rtr", c_uint, 1),
        ("eff", c_uint, 1),
        ("len", c_ubyte),
        ("brs", c_ubyte, 1),
        ("esi", c_ubyte, 1),
        ("__res", c_ubyte, 6),
        ("__res0", c_ubyte),
        ("__res1", c_ubyte),
        ("data", c_ubyte * 64),
    ]


class ZCAN_Transmit_Data(Structure):
    _fields_ = [("frame", ZCAN_CAN_FRAME), ("transmit_type", c_uint)]


class ZCAN_Receive_Data(Structure):
    _fields_ = [("frame", ZCAN_CAN_FRAME), ("timestamp", c_ulonglong)]


class ZCAN_TransmitFD_Data(Structure):
    _fields_ = [("frame", ZCAN_CANFD_FRAME), ("transmit_type", c_uint)]


class ZCAN_ReceiveFD_Data(Structure):
    _fields_ = [("frame", ZCAN_CANFD_FRAME), ("timestamp", c_ulonglong)]


class ZCAN_AUTO_TRANSMIT_OBJ(Structure):
    _fields_ = [
        ("enable", c_ushort),
        ("index", c_ushort),
        ("interval", c_uint),
        ("obj", ZCAN_Transmit_Data),
    ]


class ZCANFD_AUTO_TRANSMIT_OBJ(Structure):
    _fields_ = [
        ("enable", c_ushort),
        ("index", c_ushort),
        ("interval", c_uint),
        ("obj", ZCAN_TransmitFD_Data),
    ]


class IProperty(Structure):
    _fields_ = [
        ("SetValue", c_void_p),
        ("GetValue", c_void_p),
        ("GetPropertys", c_void_p),
    ]


class ZCAN(object):
    def __init__(self):
        bits, linkage = platform.architecture()
        if platform.system() == "Windows":
            # 根据系统环境自动选择zlgcan.dll
            try:
                self.__dll = windll.LoadLibrary(
                    f'{os.path.dirname(os.path.abspath(__file__))}/candriver/zlg/{"zlgcan_x64" if bits == "64bit" else "zlgcan_x86"}/zlgcan.dll'
                )
            except Exception as e:
                print(f"DLL couldn't be loaded: {e}")
                self.__dll = None
        else:
            print("No support now!")
            self.__dll = None

        if self.__dll is None:
            print("DLL couldn't be loaded!")

    def OpenDevice(self, device_type, device_index, reserved):
        try:
            return self.__dll.ZCAN_OpenDevice(device_type, device_index, reserved)
        except Exception as e:
            raise Exception("Exception on OpenDevice!" + str(e))

    def CloseDevice(self, device_handle):
        try:
            return self.__dll.ZCAN_CloseDevice(device_handle)
        except Exception as e:
            raise Exception("Exception on CloseDevice!" + str(e))

    def GetDeviceInf(self, device_handle):
        try:
            info = ZCAN_DEVICE_INFO()
            ret = self.__dll.ZCAN_GetDeviceInf(device_handle, byref(info))
            return info if ret == ZCAN_STATUS_OK else None
        except Exception as e:
            raise Exception("Exception on ZCAN_GetDeviceInf" + str(e))

    def DeviceOnLine(self, device_handle):
        try:
            return self.__dll.ZCAN_IsDeviceOnLine(device_handle)
        except Exception as e:
            raise Exception("Exception on ZCAN_ZCAN_IsDeviceOnLine!" + str(e))

    def InitCAN(self, device_handle, can_index, init_config):
        try:
            return self.__dll.ZCAN_InitCAN(device_handle, can_index, byref(init_config))
        except Exception as e:
            raise Exception("Exception on ZCAN_InitCAN!" + str(e))

    def StartCAN(self, chn_handle):
        try:
            return self.__dll.ZCAN_StartCAN(chn_handle)
        except Exception as e:
            raise Exception("Exception on ZCAN_StartCAN!" + str(e))

    def ResetCAN(self, chn_handle):
        try:
            return self.__dll.ZCAN_ResetCAN(chn_handle)
        except Exception as e:
            raise Exception("Exception on ZCAN_ResetCAN!" + str(e))

    def ClearBuffer(self, chn_handle):
        try:
            return self.__dll.ZCAN_ClearBuffer(chn_handle)
        except Exception as e:
            raise Exception("Exception on ZCAN_ClearBuffer!" + str(e))

    def ReadChannelErrInfo(self, chn_handle):
        try:
            err_info = ZCAN_CHANNEL_ERR_INFO()
            ret = self.__dll.ZCAN_ReadChannelErrInfo(chn_handle, byref(err_info))
            return err_info if ret == ZCAN_STATUS_OK else None
        except Exception as e:
            raise Exception("Exception on ZCAN_ReadChannelErrInfo!" + str(e))

    def ReadChannelStatus(self, chn_handle):
        try:
            status = ZCAN_CHANNEL_STATUS()
            ret = self.__dll.ZCAN_ReadChannelStatus(chn_handle, byref(status))
            return status if ret == ZCAN_STATUS_OK else None
        except Exception as e:
            raise Exception("Exception on ZCAN_ReadChannelStatus!" + str(e))

    def GetReceiveNum(self, chn_handle, can_type=ZCAN_TYPE_CAN):
        try:
            return self.__dll.ZCAN_GetReceiveNum(chn_handle, can_type)
        except Exception as e:
            raise Exception("Exception on ZCAN_GetReceiveNum!" + str(e))

    def Transmit(self, chn_handle, std_msg, len_):
        try:
            return self.__dll.ZCAN_Transmit(chn_handle, byref(std_msg), len_)
        except Exception as e:
            raise Exception("Exception on ZCAN_Transmit!" + str(e))

    def Receive(self, chn_handle, rcv_num, wait_time=c_int(-1)):
        try:
            rcv_can_msgs = (ZCAN_Receive_Data * rcv_num)()
            ret = self.__dll.ZCAN_Receive(
                chn_handle, byref(rcv_can_msgs), rcv_num, wait_time
            )
            return rcv_can_msgs, ret
        except Exception as e:
            raise Exception("Exception on ZCAN_Receive!" + str(e))

    def TransmitFD(self, chn_handle, fd_msg, len):
        try:
            return self.__dll.ZCAN_TransmitFD(chn_handle, byref(fd_msg), len)
        except Exception as e:
            raise Exception("Exception on ZCAN_TransmitFD!" + str(e))

    def ReceiveFD(self, chn_handle, rcv_num, wait_time=c_int(-1)):
        try:
            rcv_canfd_msgs = (ZCAN_ReceiveFD_Data * rcv_num)()
            ret = self.__dll.ZCAN_ReceiveFD(
                chn_handle, byref(rcv_canfd_msgs), rcv_num, wait_time
            )
            return rcv_canfd_msgs, ret
        except Exception as e:
            raise Exception("Exception on ZCAN_ReceiveFD!" + str(e))

    def GetIProperty(self, device_handle):
        try:
            self.__dll.GetIProperty.restype = POINTER(IProperty)
            return self.__dll.GetIProperty(device_handle)
        except Exception as e:
            raise Exception("Exception on ZCAN_GetIProperty!" + str(e))

    def SetValue(self, iproperty, path, value):
        try:
            func = CFUNCTYPE(c_uint, c_char_p, c_char_p)(iproperty.contents.SetValue)
            return func(c_char_p(path.encode("utf-8")), c_char_p(value.encode("utf-8")))
        except Exception as e:
            raise Exception("Exception on IProperty SetValue:->" + str(e))

    def set_value(self, iproperty, path, value):
        try:
            func = CFUNCTYPE(c_uint, c_char_p, c_char_p)(iproperty.contents.SetValue)
            return func(c_char_p(path.encode("utf-8")), cast(value, c_char_p))
        except Exception as e:
            raise Exception("Exception on IProperty set_value:->" + str(e))

    def GetValue(self, iproperty, path):
        try:
            func = CFUNCTYPE(c_char_p, c_char_p)(iproperty.contents.GetValue)
            return func(c_char_p(path.encode("utf-8")))
        except Exception as e:
            raise Exception("Exception on IProperty GetValue" + str(e))

    def ReleaseIProperty(self, iproperty):
        try:
            return self.__dll.ReleaseIProperty(iproperty)
        except Exception as e:
            raise Exception("Exception on ZCAN_ReleaseIProperty!" + str(e))

    def TransmitData(self, handle, std_msg, len_):
        try:
            return self.__dll.ZCAN_Transmit(handle, byref(std_msg), len_)
        except Exception as e:
            raise Exception("Exception on ZCAN_Transmit!" + str(e))


zcanlib = ZCAN()
###############################################################################

"""
USBCAN-XE-U Start Demo
"""


def can_E_U_start(
    zcanlib,
    device_handle,
    chn,
    kbps,
    acc_code=0,
    acc_mask=0xFFFFFFFF,
    mode=0,
    filter_ack="0",
    **kwargs,
):
    """
    开启设备
    :param zcanlib:
    :param device_handle:
    :param chn: 通道
    :param kbps: 波特率
    :param acc_code:  SJA1000 的帧过滤验收码，对经过屏蔽码过滤为“有关位”进行匹配，全部匹配成功后，此报文可以被接收，否则不接收。推荐设置为 0。
    :param acc_mask: SJA1000 的帧过滤屏蔽码，对接收的 CAN 帧 ID 进行过滤，位为 0 的是“有关位”，位为 1 的是“无关位”。推荐设置为 0xFFFFFFFF，即全部接收。
    :param mode: 工作模式，=0 表示正常模式（相当于正常节点），=1 表示只听模式（只接收，不影响总线）
    :param filter_start: 滤波起始帧 ID
    :param filter_end: 滤波结束帧 ID
    :param filter_ack:  滤波生效（全部滤波 ID 同时生效）
    :param kwargs 相关的设置参数
        > filters 格式:(('帧格式', 'start', 'end'),...)
        eg:屏蔽canid为18FFED4A [('标准帧', '0000', 'FFF'), ('扩展帧', '0000000', '18FFED49'), ('扩展帧', '18FFED4B', 'FFFFFFFF')]

    :return:
    """
    ip = zcanlib.GetIProperty(device_handle)
    ret = zcanlib.SetValue(ip, str(chn) + "/baud_rate", kbps)  # 250Kbps
    assert ret == ZCAN_STATUS_OK, "Set CH%d %s CAN_E_U baud_rate failed!" % (chn, kbps)

    chn_init_cfg = ZCAN_CHANNEL_INIT_CONFIG()
    chn_init_cfg.can_type = ZCAN_TYPE_CAN
    chn_init_cfg.config.can.acc_code = acc_code
    chn_init_cfg.config.can.acc_mask = acc_mask
    chn_init_cfg.config.can.mode = mode

    chn_handle = zcanlib.InitCAN(device_handle, chn, chn_init_cfg)
    if chn_handle is None:
        return None

    # SET filter
    ret = zcanlib.SetValue(ip, str(chn) + "/filter_clear", "0")  # 清除滤波
    assert ret == ZCAN_STATUS_OK, "Set CH%d CAN_E_U filter_clear failed!\n%s" % (
        chn,
        zcanlib.ReadChannelErrInfo(device_handle),
    )

    # 设置接收帧数据的范围
    if "filters" in kwargs:
        filters = kwargs["filters"]
    else:
        filters = [("标准帧", "000", "7FF"), ("扩展帧", "00000000", "FFFFFFFF")]

    for eff_s, start, end in filters:
        if eff_s == "标准帧":
            eff = "0"
        else:
            eff = "1"
        # print('过滤', eff, start, end)
        if not start.lower().startswith("0x"):
            start = "0X" + start
        if not end.lower().startswith("0x"):
            end = "0X" + end
        ret = zcanlib.SetValue(ip, str(chn) + "/filter_mode", eff)  # 扩展帧滤波
        assert ret == ZCAN_STATUS_OK, "Set CH%d CAN_E_U filter_mode failed!" % chn
        ret = zcanlib.SetValue(ip, str(chn) + "/filter_start", start)
        assert ret == ZCAN_STATUS_OK, "Set CH%d CAN_E_U filter_start failed!" % chn
        ret = zcanlib.SetValue(ip, str(chn) + "/filter_end", end)
        assert ret == ZCAN_STATUS_OK, "Set CH%d CAN_E_U filter_end failed!" % chn

    ret = zcanlib.SetValue(
        ip, str(chn) + "/filter_ack", filter_ack
    )  # 滤波生效（全部滤波 ID 同时生效）
    assert ret == ZCAN_STATUS_OK, "Set CH%d CAN_E_U filter_ack failed!" % chn

    zcanlib.ReleaseIProperty(ip)

    zcanlib.StartCAN(chn_handle)
    return chn_handle


class Channel:

    def __init__(self, device_name, handle, index):
        self.device_name = device_name  # 设备类型
        self.parent_handle = handle  # 设备句柄
        self.channel_handle = None  # 通道句柄
        self.index = index
        self.baud_rate = None
        self.default = dict(ttype=0, rtr=0, err=0)

    def open_channel(self, baud_rate, filters, is_high):
        ip = zcanlib.GetIProperty(self.parent_handle)
        ret = zcanlib.SetValue(ip, f"{self.index}/baud_rate", baud_rate)
        self.baud_rate = str(zcanlib.GetValue(ip, f"{self.index}/baud_rate"), "utf-8")

        config = ZCAN_CHANNEL_INIT_CONFIG()
        config.can_type = ZCAN_TYPE_CAN
        config.config.can.acc_code = 0
        config.config.can.acc_mask = 0xFFFFFFFF
        config.config.can.mode = 0

        if is_high:
            self.__set_filter(ip, self.index, filters)
        self.channel_handle = zcanlib.InitCAN(self.parent_handle, self.index, config)
        assert (
            self.channel_handle is not None
        ), f"{self.device_name}初始化通道{self.index}失败"
        if is_high:
            zcanlib.SetValue(ip, f"{self.index}/filter_ack", "0")
        zcanlib.ReleaseIProperty(ip)
        zcanlib.StartCAN(self.channel_handle)

    def set_transmit_attr(self, **kwargs):
        for (
            k,
            v,
        ) in kwargs.items():
            if k in self.default.keys():
                self.default[k] = v

    def get_transmit_attr(self, name=None):
        return self.__dict__.get(name) or tuple(self.default.values())

    @staticmethod
    def __set_filter(p, i, filters):
        if filters is None or len(filters) == 0:
            filters = [("标准帧", "000", "7FF"), ("扩展帧", "00000000", "FFFFFFFF")]
        elif isinstance(filters, str):
            filters = [tuple(f.split(",")) for f in filters]
        for eff, start, end in filters:
            eff = "0" if eff == "标准帧" else "1"
            if not start.lower().startswith("0x"):
                start = "0x" + start
            if not end.lower().startswith("0x"):
                end = "0x" + end
            zcanlib.SetValue(p, f"{i}/filter_mode", eff)
            zcanlib.SetValue(p, f"{i}/filter_start", start)
            zcanlib.SetValue(p, f"{i}/filter_end", end)


class USBCAN:
    UsbCan_Level = {
        "lower_devices": [
            "ZCAN_USBCAN2",
        ],
        "high_devices": [
            "ZCAN_USBCAN_2E_U",
        ],
    }

    def __init__(
        self, device_type: str, device_index: int, default_channel_name: str = "default"
    ):
        self.device_name = device_type
        self.default_channel = default_channel_name
        self.handle = zcanlib.OpenDevice(
            getattr(ZCANDeviceType, device_type), device_index, 0
        )  # can设备句柄
        assert (
            self.handle != INVALID_DEVICE_HANDLE
        ), f"Open {device_type} device failed!"
        info = zcanlib.GetDeviceInf(self.handle)
        # getLogger().info(f"\nOpen USBCAN-XE-U device success!\ndevice handle:{self.handle}\nDevice Information:{info}")
        self.__channels = []  # 保存通道句柄
        self.channelMap = {}  # 保存通道句柄
        self.temp_datas = []
        self.init_timestamp = None

    def open_start_device(
        self,
        device_type=getattr(ZCANDeviceType, "ZCAN_USBCAN_2E_U"),
        device_index=0,
        can_index=0,
        kbps="250000",
        **kwargs,
    ):
        device_type = (
            getattr(ZCANDeviceType, device_type)
            if type(device_type) is str
            else device_type
        )
        self.handle = zcanlib.OpenDevice(device_type, device_index, can_index)
        assert (
            self.handle != INVALID_DEVICE_HANDLE
        ), f"Open {device_type} device failed!"
        print("Open USBCAN-XE-U device success!")
        print("device handle:%d." % self.handle)

        info = zcanlib.GetDeviceInf(self.handle)

        print("Device Information:\n%s" % info)

        # Start CAN
        self.chn_handle = can_E_U_start(
            zcanlib, self.handle, can_index, kbps=kbps, **kwargs
        )
        print("channel handle:%d." % self.chn_handle)

    def get_init_timestamp(
        self, _id="EFF", _data="FF FF FF FF FF FF FF FF", channel=None
    ):
        t1 = 0
        datas_out = []
        for i in range(100):
            self.transmit(_id, _data, transmit_type=2, channel=channel)
            t0 = time.time()
            datas = self.receive(channel=channel)
            datas_out.extend(datas)
            for data in datas:
                if data["ID"] == _id:
                    t1 = t0 - data["TimeStamp"] / 1000000
                    break
            if t1 != 0:
                self.init_timestamp = t1
                break
        return datas_out

    def open_channel(self, baud_rate: str, index=None, filters=None, **kwargs) -> None:
        """初始化并打开一个can通道
        Args:
            baud_rate: 波特率
        return: 通道句柄
        """
        chn_index = len(self.__channels)
        if not index:
            index = chn_index
        chn = Channel(self.device_name, self.handle, chn_index)
        level = (
            True if self.device_name in USBCAN.UsbCan_Level["high_devices"] else False
        )
        chn.open_channel(baud_rate, filters, level)
        while len(self.__channels) <= index:
            self.__channels.append(None)
        self.__channels[index] = chn
        name = kwargs.get("name")
        self.channelMap[name] = chn
        if not self.init_timestamp:
            self.get_init_timestamp(channel=name)

    def reset_channel(self, baud_rate: str, channel, **kwargs):
        """
        重新设置通道波特率，滤波信息。
        """
        channel = USBCAN.get_channel(channel)
        zcanlib.ResetCAN(channel.channel_handle)
        self.open_channel(baud_rate, index=channel.index, **kwargs)

    def close(self):
        for chn in self.__channels:
            zcanlib.ResetCAN(chn.channel_handle)
        zcanlib.CloseDevice(self.handle)

    def transmit(
        self, id_: str, data: str, transmit_type=0, eff=1, rtr=0, err=0, channel=None
    ) -> int:
        """发送报文
        Args:
            channel: 通道, get_channel()获取channel
            id_:
            eff:
            rtr:
            err:
            data:
            transmit_type:发送方式， 0=正常发送， 1=单次发送， 2=自发自收， 3=单次自发自收。
            发送方式说明如下：
             正常发送：在ID仲裁丢失或发送出现错误时， CAN控制器会自动重发，直到发送
            成功，或发送超时，或总线关闭。
             单次发送：在一些应用中，允许部分数据丢失，但不能出现传输延迟时，自动重发
            就没有意义了。在这些应用中，一般会以固定的时间间隔发送数据，自动重发会导
            致后面的数据无法发送，出现传输延迟。使用单次发送，仲裁丢失或发送错误，
            CAN控制器不会重发报文。
             自发自收： 产生一次带自接收特性的正常发送，在发送完成后，可以从接收缓冲区
            中读到已发送的报文。
             单次自发自收： 产生一次带自接收特性的单次发送，在发送出错或仲裁丢失不会执
            行重发。在发送完成后，可以从接收缓冲区中读到已发送的报文。
        return: 实际发送的条数
        """
        chn_handle = self.get_channel(channel).channel_handle
        msg = ZCAN_Transmit_Data()
        msg.transmit_type = transmit_type  # Send Self
        msg.frame.eff = eff  # extern frame
        msg.frame.rtr = rtr  # remote frame
        msg.frame.err = err
        msg.frame.can_id = int(id_, 16)
        data = data.split(" ")
        msg.frame.can_dlc = len(data)
        for i, d in enumerate(data):
            msg.frame.data[i] = int(d, 16)
        return zcanlib.Transmit(chn_handle, msg, 1)

    def receive_all(self):
        """
        获取所有通道的报文
        """
        datas = []
        for index, chn in enumerate(self.__channels):
            try:
                _data = self.receive(channel=index)
                datas += _data
            except Exception as e:
                print(e)
        return datas

    def receive(
        self, timeout: float = None, channel=None, is_add_temp_datas=True
    ) -> list:
        """等待timeout时间后返回缓冲区获得的数据
        Args:
            channel: 接收报文的通道, get_channel()获取
            timeout: 阻塞时长, 单位ms  当值为负数时
        Return: list[dict, ...]
            {
                timestamp: 时间戳, 单位微秒, 基于设备启动时间
                id: 帧ID
                frame: 报文数据信息, 详情查看以下表示
            }
        """
        if timeout:
            time.sleep(timeout)
        if is_add_temp_datas:
            datas = copy.deepcopy(self.temp_datas)
        else:
            datas = []
        chn_handle = self.get_channel(channel).channel_handle
        p_receive = zcanlib.GetReceiveNum(chn_handle, c_uint(0))
        if p_receive == 0:
            return datas
        if p_receive:
            rcv_msgs, rcv_num = zcanlib.Receive(chn_handle, p_receive, c_int(-1))
            for i, rcv_msg in enumerate(rcv_msgs):
                if self.init_timestamp:
                    time_stamp = self.init_timestamp + rcv_msg.timestamp / 1000000
                    dt = datetime.datetime.fromtimestamp(time_stamp).strftime(
                        "%H:%M:%S.%f"
                    )[:-3]
                else:
                    dt = ""
                data = dict(
                    index=i,
                    TimeStamp=rcv_msg.timestamp,
                    DateTime=dt,
                    ID=hex(rcv_msg.frame.can_id)[2:].upper(),
                    DataLen=rcv_msg.frame.can_dlc,
                    Data=bytearray2frame(rcv_msg.frame.data, rcv_msg.frame.can_dlc),
                    ExternFlag=rcv_msg.frame.eff,
                    RemoteFlag=rcv_msg.frame.rtr,
                )
                datas.append(data)
        if is_add_temp_datas:
            self.temp_datas = []
        return datas

    def receive2(self, timeout=None, channel=None):
        """
        从缓冲区拿一段时间内的数据(default Do no wait)

        Args:
            timeout: 阻塞时长
            channel:

        Return: list[dict, ...]
            {
                timestamp: 时间戳, 单位微秒, 基于设备启动时间
                id: 帧ID
                frame: 报文数据信息, 详情查看以下表示
            }

            can_id:
                帧ID，32位，高3位属于标志位，标志位含义如下：
                第31位(最高位)代表扩展帧标志，=0表示标准帧，=1代表扩展帧
                第30位代表远程帧标志，=0表示数据帧，=1表示远程帧
            　　第29位代表错误帧标准，=0表示CAN帧，=1表示错误帧，目前只能设置为0；
            　　其余位代表实际帧ID值，使用宏MAKE_CAN_ID构造ID，使用宏GET_ID获取ID。

            can_dlc:
                数据长度

            data:
                报文数据, 有效长度can_dlc
        """
        if not self.init_timestamp:
            datas = self.get_init_timestamp(channel=channel)
        else:
            datas = self.receive(timeout, channel)
        return [
            {"timestamp": data["DateTime"], "id": data["ID"], "data": data["Data"]}
            for data in datas
        ]

    def get_channel(self, channel=None) -> Channel:
        if isinstance(channel, Channel):
            chn = channel
        elif isinstance(channel, int):
            chn = self.__channels[channel]
        elif channel is None:
            chn = self.channelMap[self.default_channel]
        elif channel.isdigit():
            chn = self.__channels[int(channel)]
        else:
            chn = self.channelMap[channel]
        assert chn, "channel is not exist..."
        return chn

    def get_channels(self) -> list:
        return self.__channels

    def get_baud_rate(self, channel_index: int) -> str:
        ip = zcanlib.GetIProperty(self.handle)
        br = zcanlib.GetValue(ip, f"{channel_index}/baud_rate")
        zcanlib.ReleaseIProperty(ip)
        return str(br, "utf-8")

    def transmits(
        self,
        frames: list,
        interval: int = None,
        count: int = None,
        duration: int = None,
        channel=None,
    ):
        """
        @datetime: 2022/08/09
        @author: 张志远
        添加默认参数的目的是减少多次发送时构建结构体的耗时
        --------------------------------
        发送can数据组,可以一次性发送多条can数据，经测试，一次发送1000条can数据，花费0.6392999999999986s
        :param frames: 要发送的can数据组，相关的参数为  id, data, transmit_type, eff, rtr, err
        :param duration: 发送总时间(s), count和duration只会生效一个
        :param interval: 单位(ms)
        :param count: 发送次数
        :return:
        """
        msgs = (ZCAN_Transmit_Data * len(frames))()
        chn_handle = self.get_channel(channel).channel_handle
        for i in range(len(frames)):
            can_id, frame_data, transmit_type, eff, rtr, err = frames[i]
            msgs[i].transmit_type = transmit_type
            msgs[i].frame.eff = eff
            msgs[i].frame.rtr = rtr
            msgs[i].frame.err = err
            msgs[i].frame.can_id = int(can_id, 16)
            data = frame_data.split(" ")
            msgs[i].frame.can_dlc = len(data)
            for j, d in enumerate(data):
                msgs[i].frame.data[j] = int(d, 16)
        if count:
            if count > 1:
                pbar = tqdm(total=count, desc="等待", bar_format="{l_bar}{bar}")
                for _ in range(count):
                    zcanlib.Transmit(chn_handle, msgs, len(msgs))
                    time.sleep(interval / 1000)
                    pbar.update(1)
                pbar.close()
            else:
                zcanlib.Transmit(chn_handle, msgs, len(msgs))
        elif duration:
            t0 = time.time()
            _t = time.time()
            wait = With_wait_tqdm_by_time(duration)
            try:
                while time.time() - t0 < duration:
                    zcanlib.Transmit(chn_handle, msgs, len(msgs))
                    time.sleep(interval / 1000)
            except Exception as e:
                raise e
            finally:
                wait.exit()
        else:
            zcanlib.Transmit(chn_handle, msgs, len(msgs))

    def clear_buffer(self, channel=None):
        chn_handle = self.get_channel(channel).channel_handle
        return zcanlib.GetReceiveNum(chn_handle, c_uint(0))

    def set_transmit_attr(self, channel=None, **kwargs):
        """
        设置通道属性。
        Args:
            channel: 通道， get_channel()获取
            kwargs: ttype, rtr, err属性。 eff会自动选择
        """
        channel = self.get_channel(channel)
        channel.set_transmit_attr(**kwargs)

    @staticmethod
    def str2hex(s):
        odata = 0
        su = s.upper()
        for c in su:
            tmp = ord(c)
            if tmp <= ord("9"):
                odata = odata << 4
                odata += tmp - ord("0")
            elif ord("A") <= tmp <= ord("F"):
                odata = odata << 4
                odata += tmp - ord("A") + 10
        return odata

    def strs_to_tuple(self, ss):
        ds = ss.replace("  ", " ").split(" ")
        rst = []
        for s in ds:
            rst.append(self.str2hex(s))
        return tuple(rst)

    def u_info(self):
        info = zcanlib.GetDeviceInf(self.handle)
        return info.hw_type


__all__ = ["USBCAN", "zcanlib"]

if __name__ == "__main__":
    device_type = "ZCAN_USBCAN2"
    device_ind = 0
    timing = "250000"
    dev_name = "channel0"
    can = USBCAN(device_type, device_ind)
    filters = [("标准帧", "000", "7EF"), ("扩展帧", "00000000", "FFFFFFFF")]
    can.open_channel(timing, filters=filters, name=dev_name)
    can.channelMap["default"] = can.get_channel(dev_name)
    can.clear_buffer(dev_name)
    for i in range(10):
        print(can.receive(0.1))
