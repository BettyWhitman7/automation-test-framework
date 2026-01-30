# -*- coding: utf-8 -*-
"""
ZLG CAN Bus Wrapper - 提供类似 python-can 的 API

基于 zlgcan.py 封装，支持阻塞接收，适合在独立线程中使用。

使用示例：
    from tools.can_tool.zlg_can_bus import ZLGCANBus, CANMessage
    
    # 创建总线实例
    with ZLGCANBus(device_type="USBCANFD-200U", channel=0, bitrate=500000) as bus:
        # 发送消息
        msg = CANMessage(arbitration_id=0x123, data=[0x01, 0x02, 0x03])
        bus.send(msg)
        
        # 阻塞接收 (适合在线程中使用)
        received = bus.recv(timeout=1.0)  # 等待1秒
        if received:
            print(f"收到: ID=0x{received.arbitration_id:X}, Data={received.data.hex()}")
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Optional, List, Union
from ctypes import c_int

from .zlgcan import (
    ZCAN,
    ZCAN_USBCANFD_200U,
    ZCAN_USBCANFD_100U,
    ZCAN_USBCAN2,
    ZCAN_CHANNEL_INIT_CONFIG,
    ZCAN_Transmit_Data,
    ZCAN_TransmitFD_Data,
    ZCAN_CAN_FRAME,
    ZCAN_CANFD_FRAME,
    ZCAN_TYPE_CAN,
    ZCAN_TYPE_CANFD,
    ZCAN_STATUS_OK,
    INVALID_DEVICE_HANDLE,
    INVALID_CHANNEL_HANDLE,
)


# 设备类型映射
DEVICE_TYPE_MAP = {
    "USBCANFD-200U": ZCAN_USBCANFD_200U,
    "USBCANFD-100U": ZCAN_USBCANFD_100U,
    "USBCAN-II": ZCAN_USBCAN2,
    "USBCAN2": ZCAN_USBCAN2,
}


@dataclass
class CANMessage:
    """CAN 消息数据类"""
    arbitration_id: int                     # CAN ID
    data: bytes = field(default_factory=bytes)  # 数据
    is_extended_id: bool = False            # 是否扩展帧
    is_remote_frame: bool = False           # 是否远程帧
    is_fd: bool = False                     # 是否 CAN FD
    is_brs: bool = False                    # CAN FD 比特率切换
    dlc: int = 0                            # 数据长度
    timestamp: float = 0.0                  # 时间戳 (秒)
    channel: int = 0                        # 通道号
    
    def __post_init__(self):
        if isinstance(self.data, (list, tuple)):
            self.data = bytes(self.data)
        if self.dlc == 0:
            self.dlc = len(self.data)
    
    def __repr__(self):
        id_str = f"0x{self.arbitration_id:08X}" if self.is_extended_id else f"0x{self.arbitration_id:03X}"
        fd_str = " FD" if self.is_fd else ""
        brs_str = " BRS" if self.is_brs else ""
        return f"CANMessage(id={id_str}, dlc={self.dlc}, data={self.data.hex()}{fd_str}{brs_str})"


class ZLGCAN:
    """
    ZLG CAN 总线封装类
    
    提供类似 python-can 的 API，支持阻塞接收。
    
    Args:
        device_type: 设备类型，如 "USBCANFD-200U", "USBCANFD-100U", "USBCAN-II"
        device_index: 设备索引 (多设备时使用)，默认 0
        channel: CAN 通道号，默认 0
        bitrate: CAN 波特率，默认 500000
        data_bitrate: CAN FD 数据域波特率，默认 2000000
        is_canfd: 是否使用 CAN FD 模式，默认 False
    """
    
    def __init__(
        self,
        device_type: Union[str, int] = "USBCANFD-200U",
        device_index: int = 0,
        channel: int = 0,
        bitrate: int = 500000,
        data_bitrate: int = 2000000,
        is_canfd: bool = False,
    ):
        self._zcan = ZCAN()
        self._device_handle = INVALID_DEVICE_HANDLE
        self._channel_handle = INVALID_CHANNEL_HANDLE
        self._channel = channel
        self._is_canfd = is_canfd
        self._is_open = False
        self._lock = threading.Lock()
        
        # 解析设备类型
        if isinstance(device_type, str):
            if device_type.upper() not in DEVICE_TYPE_MAP:
                raise ValueError(f"不支持的设备类型: {device_type}. 支持: {list(DEVICE_TYPE_MAP.keys())}")
            self._device_type = DEVICE_TYPE_MAP[device_type.upper()]
        else:
            self._device_type = device_type
        
        self._device_index = device_index
        self._bitrate = bitrate
        self._data_bitrate = data_bitrate
        
        # 打开设备
        self._open()
    
    def _open(self):
        """打开设备和通道"""
        # 打开设备
        self._device_handle = self._zcan.OpenDevice(self._device_type, self._device_index, 0)
        if self._device_handle == INVALID_DEVICE_HANDLE:
            raise RuntimeError(f"无法打开设备: type={self._device_type}, index={self._device_index}")
        
        # 配置通道 (使用 SetValue 接口)
        ip = self._zcan.GetIProperty(self._device_handle)
        
        # 设置波特率
        self._zcan.SetValue(ip, f"{self._channel}/baud_rate", str(self._bitrate))
        
        if self._is_canfd:
            # CAN FD 模式设置
            self._zcan.SetValue(ip, f"{self._channel}/canfd_abit_baud_rate", str(self._bitrate))
            self._zcan.SetValue(ip, f"{self._channel}/canfd_dbit_baud_rate", str(self._data_bitrate))
        
        self._zcan.ReleaseIProperty(ip)
        
        # 初始化通道
        init_config = ZCAN_CHANNEL_INIT_CONFIG()
        init_config.can_type = 1 if self._is_canfd else 0  # 0=CAN, 1=CANFD
        init_config.config.canfd.mode = 0  # 正常模式
        
        self._channel_handle = self._zcan.InitCAN(self._device_handle, self._channel, init_config)
        if self._channel_handle == INVALID_CHANNEL_HANDLE:
            self._zcan.CloseDevice(self._device_handle)
            raise RuntimeError(f"无法初始化通道: channel={self._channel}")
        
        # 启动通道
        ret = self._zcan.StartCAN(self._channel_handle)
        if ret != ZCAN_STATUS_OK:
            self._zcan.CloseDevice(self._device_handle)
            raise RuntimeError(f"无法启动通道: channel={self._channel}")
        
        self._is_open = True
    
    def send(self, msg: CANMessage, timeout: Optional[float] = None) -> bool:
        """
        发送 CAN 消息
        
        Args:
            msg: CANMessage 对象
            timeout: 超时时间 (秒)，当前未使用
        
        Returns:
            True 表示发送成功
        """
        if not self._is_open:
            raise RuntimeError("总线未打开")
        
        with self._lock:
            if msg.is_fd or self._is_canfd:
                # CAN FD 发送
                fd_msg = ZCAN_TransmitFD_Data()
                fd_msg.frame.can_id = msg.arbitration_id
                if msg.is_extended_id:
                    fd_msg.frame.can_id |= 0x80000000  # EFF flag
                fd_msg.frame.len = len(msg.data)
                fd_msg.frame.flags = 0x01 if msg.is_brs else 0x00  # BRS flag
                for i, b in enumerate(msg.data[:64]):
                    fd_msg.frame.data[i] = b
                fd_msg.transmit_type = 0  # 正常发送
                
                ret = self._zcan.TransmitFD(self._channel_handle, fd_msg, 1)
            else:
                # CAN 2.0 发送
                can_msg = ZCAN_Transmit_Data()
                can_msg.frame.can_id = msg.arbitration_id
                if msg.is_extended_id:
                    can_msg.frame.can_id |= 0x80000000  # EFF flag
                can_msg.frame.can_dlc = min(len(msg.data), 8)
                for i, b in enumerate(msg.data[:8]):
                    can_msg.frame.data[i] = b
                can_msg.transmit_type = 0  # 正常发送
                
                ret = self._zcan.Transmit(self._channel_handle, can_msg, 1)
        
        return ret == 1
    
    def recv(self, timeout: Optional[float] = None) -> Optional[CANMessage]:
        """
        阻塞接收 CAN 消息
        
        此方法会阻塞当前线程直到收到消息或超时。
        适合在独立的接收线程中使用。
        
        Args:
            timeout: 超时时间 (秒)，None 表示无限等待
        
        Returns:
            CANMessage 对象，超时返回 None
        """
        if not self._is_open:
            raise RuntimeError("总线未打开")
        
        # 转换超时时间为毫秒，-1 表示无限等待
        if timeout is None:
            wait_time = c_int(-1)
        else:
            wait_time = c_int(int(timeout * 1000))
        
        with self._lock:
            if self._is_canfd:
                # CAN FD 接收
                msgs, count = self._zcan.ReceiveFD(self._channel_handle, 1, wait_time)
                if count > 0:
                    frame = msgs[0].frame
                    timestamp = msgs[0].timestamp / 1000000.0  # 微秒转秒
                    
                    is_extended = bool(frame.can_id & 0x80000000)
                    can_id = frame.can_id & 0x1FFFFFFF
                    
                    return CANMessage(
                        arbitration_id=can_id,
                        data=bytes(frame.data[:frame.len]),
                        is_extended_id=is_extended,
                        is_fd=True,
                        is_brs=bool(frame.flags & 0x01),
                        dlc=frame.len,
                        timestamp=timestamp,
                        channel=self._channel,
                    )
            else:
                # CAN 2.0 接收
                msgs, count = self._zcan.Receive(self._channel_handle, 1, wait_time)
                if count > 0:
                    frame = msgs[0].frame
                    timestamp = msgs[0].timestamp / 1000000.0  # 微秒转秒
                    
                    is_extended = bool(frame.can_id & 0x80000000)
                    can_id = frame.can_id & 0x1FFFFFFF
                    
                    return CANMessage(
                        arbitration_id=can_id,
                        data=bytes(frame.data[:frame.can_dlc]),
                        is_extended_id=is_extended,
                        is_fd=False,
                        dlc=frame.can_dlc,
                        timestamp=timestamp,
                        channel=self._channel,
                    )
        
        return None
    
    def get_receive_count(self) -> int:
        """获取接收缓冲区中的消息数量"""
        if not self._is_open:
            return 0
        can_type = ZCAN_TYPE_CANFD if self._is_canfd else ZCAN_TYPE_CAN
        return self._zcan.GetReceiveNum(self._channel_handle, can_type)
    
    def clear_buffer(self):
        """清空接收缓冲区"""
        if self._is_open:
            self._zcan.ClearBuffer(self._channel_handle)
    
    def shutdown(self):
        """关闭总线"""
        if self._is_open:
            self._zcan.ResetCAN(self._channel_handle)
            self._zcan.CloseDevice(self._device_handle)
            self._is_open = False
            self._device_handle = INVALID_DEVICE_HANDLE
            self._channel_handle = INVALID_CHANNEL_HANDLE
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.shutdown()
        return False
    
    @property
    def is_open(self) -> bool:
        """总线是否已打开"""
        return self._is_open
    
    @property
    def channel(self) -> int:
        """当前通道号"""
        return self._channel


# ============== 接收线程示例 ==============

class CANReceiveThread(threading.Thread):
    """
    CAN 消息接收线程示例
    
    使用阻塞接收，不占用 CPU。
    
    使用示例:
        bus = ZLGCAN(device_type="USBCANFD-200U")
        
        def on_message(msg):
            print(f"收到消息: {msg}")
        
        recv_thread = CANReceiveThread(bus, callback=on_message)
        recv_thread.start()
        
        # ... 程序运行 ...
        
        recv_thread.stop()
        recv_thread.join()
        bus.shutdown()
    """
    
    def __init__(self, bus: ZLGCAN, callback=None, timeout: float = 0.5):
        super().__init__(daemon=True)
        self._bus = bus
        self._callback = callback
        self._timeout = timeout
        self._running = False
        self._stop_event = threading.Event()
    
    def run(self):
        """线程主循环"""
        self._running = True
        while not self._stop_event.is_set():
            try:
                # 阻塞接收，有超时以便检查停止标志
                msg = self._bus.recv(timeout=self._timeout)
                if msg and self._callback:
                    self._callback(msg)
            except Exception as e:
                print(f"接收错误: {e}")
                break
        self._running = False
    
    def stop(self):
        """停止接收线程"""
        self._stop_event.set()
    
    @property
    def is_running(self) -> bool:
        return self._running
