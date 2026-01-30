"""
使用python-can库模拟虚拟CAN总线设备
可以与实际的USBCANFD-200U设备进行通信测试
"""

import can
import threading
import time
from queue import Queue
import sys
import os

# 添加communication目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from zlgcan import *


class VirtualCANDevice:
    """虚拟CAN设备类"""
    
    def __init__(self, channel='vcan0', bustype='virtual', bitrate=500000):
        """
        初始化虚拟CAN设备
        
        Args:
            channel: 通道名称，virtual类型下可以是任意标识符
            bustype: 总线类型，'virtual'表示虚拟总线
            bitrate: 波特率
        """
        self.channel = channel
        self.bustype = bustype
        self.bitrate = bitrate
        self.bus = None
        self.is_running = False
        self.receive_thread = None
        self.tx_queue = Queue()
        self.message_callback = None  # 消息回调函数
        
    def set_message_callback(self, callback):
        """设置消息接收回调函数"""
        self.message_callback = callback
        
    def connect(self):
        """连接到虚拟CAN总线"""
        try:
            # 创建虚拟CAN总线
            self.bus = can.interface.Bus(
                channel=self.channel,
                bustype=self.bustype,
                bitrate=self.bitrate
            )
            print(f"✓ 虚拟CAN设备已连接: {self.channel} ({self.bustype})")
            print(f"  波特率: {self.bitrate} bps")
            return True
        except Exception as e:
            print(f"✗ 连接虚拟CAN设备失败: {e}")
            return False
    
    def disconnect(self):
        """断开CAN总线连接"""
        self.stop_receive()
        if self.bus:
            self.bus.shutdown()
            print("✓ 虚拟CAN设备已断开")
    
    def send_message(self, can_id, data, is_extended=False, is_fd=False):
        """
        发送CAN消息
        
        Args:
            can_id: CAN ID
            data: 数据字节列表
            is_extended: 是否为扩展帧
            is_fd: 是否为CANFD帧
        """
        try:
            msg = can.Message(
                arbitration_id=can_id,
                data=data,
                is_extended_id=is_extended,
                is_fd=is_fd
            )
            self.bus.send(msg)
            print(f"[TX] ID: 0x{can_id:X} ({'扩展帧' if is_extended else '标准帧'}) "
                  f"DLC: {len(data)} DATA: {' '.join([f'{b:02X}' for b in data])}")
            return True
        except Exception as e:
            print(f"✗ 发送消息失败: {e}")
            return False
    
    def _receive_loop(self):
        """接收消息循环（在独立线程中运行）"""
        print("✓ 接收线程已启动")
        while self.is_running:
            try:
                # 设置超时，以便能够检查is_running标志
                msg = self.bus.recv(timeout=0.1)
                if msg:
                    self._process_received_message(msg)
            except Exception as e:
                if self.is_running:  # 只在运行时报告错误
                    print(f"✗ 接收消息错误: {e}")
        print("✓ 接收线程已停止")
    
    def _process_received_message(self, msg):
        """处理接收到的消息"""
        timestamp = time.time()
        frame_type = "扩展帧" if msg.is_extended_id else "标准帧"
        frame_format = "CANFD" if msg.is_fd else "CAN"
        can_id = msg.arbitration_id
        dlc = len(msg.data)
        data_hex = " ".join([f"{b:02X}" for b in msg.data])
        
        print(f"[{timestamp:.6f}] [虚拟RX] {frame_format} ID: 0x{can_id:X} ({frame_type}) "
              f"DLC: {dlc} DATA: {data_hex}")
        
        # 如果设置了回调函数，调用它
        if self.message_callback:
            self.message_callback(can_id, list(msg.data), msg.is_extended_id, msg.is_fd)
    
    def start_receive(self):
        """启动接收线程"""
        if not self.is_running:
            self.is_running = True
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
    
    def stop_receive(self):
        """停止接收线程"""
        if self.is_running:
            self.is_running = False
            if self.receive_thread:
                self.receive_thread.join(timeout=2)
    
    def send_periodic_message(self, can_id, data, period=1.0, is_extended=False):
        """
        发送周期性消息
        
        Args:
            can_id: CAN ID
            data: 数据字节列表
            period: 发送周期（秒）
            is_extended: 是否为扩展帧
        
        Returns:
            PeriodicSendTask对象，可以用来停止周期发送
        """
        msg = can.Message(
            arbitration_id=can_id,
            data=data,
            is_extended_id=is_extended
        )
        task = self.bus.send_periodic(msg, period)
        print(f"✓ 启动周期发送: ID 0x{can_id:X}, 周期 {period}s")
        return task


class RealCANDevice:
    """实际USBCANFD设备类"""
    
    def __init__(self, device_type=ZCAN_USBCANFD_200U, device_index=0, channel=0, 
                 abit_rate=500000, dbit_rate=2000000):
        """
        初始化实际CAN设备
        
        Args:
            device_type: 设备类型
            device_index: 设备索引
            channel: 通道索引
            abit_rate: 仲裁域波特率
            dbit_rate: 数据域波特率
        """
        self.device_type = device_type
        self.device_index = device_index
        self.channel = channel
        self.abit_rate = abit_rate
        self.dbit_rate = dbit_rate
        self.zcanlib = None
        self.device_handle = None
        self.channel_handle = None
        self.is_running = False
        self.receive_thread = None
        self.message_callback = None  # 消息回调函数
        
    def set_message_callback(self, callback):
        """设置消息接收回调函数"""
        self.message_callback = callback
        
    def connect(self):
        """连接实际CAN设备"""
        try:
            # 初始化ZCAN库
            self.zcanlib = ZCAN()
            
            # 打开设备
            self.device_handle = self.zcanlib.OpenDevice(
                self.device_type, self.device_index, 0
            )
            if self.device_handle == INVALID_DEVICE_HANDLE:
                print("✗ 打开USBCANFD设备失败！")
                return False
            
            print(f"✓ 实际CAN设备已打开，设备句柄: {self.device_handle}")
            
            # 获取设备信息
            info = self.zcanlib.GetDeviceInf(self.device_handle)
            print(f"  设备信息: {info.str_Serial_Num}, 固件版本: {info.fw_version}")
            
            # 启动通道
            self.channel_handle = self._init_channel()
            if self.channel_handle is None:
                print(f"✗ 启动通道{self.channel}失败！")
                return False
            
            print(f"✓ 通道{self.channel}已启动，通道句柄: {self.channel_handle}")
            return True
            
        except Exception as e:
            print(f"✗ 连接实际CAN设备失败: {e}")
            return False
    
    def _init_channel(self):
        """初始化CAN通道"""
        print(f"  开始初始化通道{self.channel}...")
        
        # 设置波特率
        ret = self.zcanlib.ZCAN_SetValue(
            self.device_handle, 
            f"{self.channel}/canfd_abit_baud_rate", 
            str(self.abit_rate).encode("utf-8")
        )
        if ret != ZCAN_STATUS_OK:
            print(f"  ✗ 设置仲裁域波特率失败，状态码: {ret}")
            
        ret = self.zcanlib.ZCAN_SetValue(
            self.device_handle, 
            f"{self.channel}/canfd_dbit_baud_rate", 
            str(self.dbit_rate).encode("utf-8")
        )
        if ret != ZCAN_STATUS_OK:
            print(f"  ✗ 设置数据域波特率失败，状态码: {ret}")
        else:
            print(f"  ✓ 波特率设置: 仲裁域={self.abit_rate}, 数据域={self.dbit_rate}")
        
        # 开启终端电阻
        ret = self.zcanlib.ZCAN_SetValue(
            self.device_handle, 
            f"{self.channel}/initenal_resistance", 
            "1".encode("utf-8")
        )
        if ret == ZCAN_STATUS_OK:
            print(f"  ✓ 终端电阻已开启")
        
        # 初始化通道
        chn_init_cfg = ZCAN_CHANNEL_INIT_CONFIG()
        chn_init_cfg.can_type = ZCAN_TYPE_CANFD
        chn_init_cfg.config.canfd.mode = 0  # 正常模式
        
        print(f"  [调试] 调用InitCAN: device_handle={self.device_handle}, channel={self.channel}")
        chn_handle = self.zcanlib.InitCAN(self.device_handle, self.channel, chn_init_cfg)
        print(f"  [调试] InitCAN返回值: {chn_handle}, 类型: {type(chn_handle)}")
        
        # 检查返回值
        if chn_handle is None:
            print(f"  ✗ InitCAN返回None")
            return None
        if chn_handle == INVALID_CHANNEL_HANDLE:
            print(f"  ✗ InitCAN返回INVALID_CHANNEL_HANDLE ({INVALID_CHANNEL_HANDLE})")
            return None
        if chn_handle == 0:
            print(f"  ✗ InitCAN返回0（失败）")
            return None
        
        print(f"  ✓ InitCAN成功，通道句柄: {chn_handle} (设备句柄: {self.device_handle})")
        
        # 设置发送回显（在StartCAN之前）
        ret = self.zcanlib.ZCAN_SetValue(
            self.device_handle,
            f"{self.channel}/set_device_tx_echo",
            "0".encode("utf-8")  # 禁用回显
        )
        
        # 启动通道
        ret = self.zcanlib.StartCAN(chn_handle)
        if ret != ZCAN_STATUS_OK:
            print(f"  ✗ StartCAN失败，状态码: {ret}")
            return None
        else:
            print(f"  ✓ StartCAN成功")
        
        return chn_handle
    
    def disconnect(self):
        """断开CAN设备连接"""
        self.stop_receive()
        
        if self.channel_handle:
            ret = self.zcanlib.ResetCAN(self.channel_handle)
            if ret == 1:
                print(f"✓ 关闭通道{self.channel}成功")
        
        if self.device_handle:
            ret = self.zcanlib.CloseDevice(self.device_handle)
            if ret == 1:
                print("✓ 关闭设备成功")
    
    def send_message(self, can_id, data, is_extended=False, is_fd=False, brs=False):
        """
        发送CAN消息
        
        Args:
            can_id: CAN ID
            data: 数据字节列表
            is_extended: 是否为扩展帧
            is_fd: 是否为CANFD帧
            brs: 是否加速（仅CANFD有效）
        """
        try:
            # 检查通道句柄
            if self.channel_handle is None:
                print(f"✗ 通道句柄无效，无法发送")
                return False
            
            if is_fd:
                # 发送CANFD消息
                msgs = (ZCAN_TransmitFD_Data * 1)()
                msgs[0].transmit_type = 0
                msgs[0].frame.can_id = can_id
                if is_extended:
                    msgs[0].frame.can_id |= 1 << 31
                msgs[0].frame.len = len(data)
                if brs:
                    msgs[0].frame.flags |= 0x1
                # 不设置回显标志，避免干扰
                for i, byte in enumerate(data):
                    msgs[0].frame.data[i] = byte
                
                print(f"  [调试] 准备发送CANFD: 句柄={self.channel_handle}, ID=0x{can_id:X}, 长度={len(data)}")
                ret = self.zcanlib.TransmitFD(self.channel_handle, msgs, 1)
                frame_type = "CANFD"
            else:
                # 发送CAN消息
                msgs = (ZCAN_Transmit_Data * 1)()
                msgs[0].transmit_type = 0
                msgs[0].frame.can_id = can_id
                if is_extended:
                    msgs[0].frame.can_id |= 1 << 31
                msgs[0].frame.can_dlc = len(data)
                # 不设置回显标志
                for i, byte in enumerate(data):
                    msgs[0].frame.data[i] = byte
                
                print(f"  [调试] 准备发送CAN: 句柄={self.channel_handle}, ID=0x{can_id:X}, DLC={len(data)}")
                ret = self.zcanlib.Transmit(self.channel_handle, msgs, 1)
                frame_type = "CAN"
            
            # 判断发送结果
            if ret > 0:
                print(f"[TX] ✓ {frame_type} ID: 0x{can_id:X} ({'扩展帧' if is_extended else '标准帧'}) "
                      f"DLC: {len(data)} DATA: {' '.join([f'{b:02X}' for b in data])} (成功发送{ret}条)")
                return True
            else:
                print(f"[TX] ✗ {frame_type} ID: 0x{can_id:X} 发送失败 (返回值: {ret})")
                # 尝试获取更多错误信息
                print(f"  [调试] 设备句柄={self.device_handle}, 通道句柄={self.channel_handle}")
                return False
            
        except Exception as e:
            print(f"✗ 发送消息异常: {e}")
            import traceback
            traceback.print_exc()
            return False
            import traceback
            traceback.print_exc()
            return False
    
    def _receive_loop(self):
        """接收消息循环"""
        print("✓ 实际设备接收线程已启动")
        
        CANType_width = len("CANFD加速    ")
        id_width = len(hex(0x1FFFFFFF))
        
        while self.is_running:
            time.sleep(0.005)
            
            # 接收CAN消息
            rcv_num = self.zcanlib.GetReceiveNum(self.channel_handle, ZCAN_TYPE_CAN)
            if rcv_num:
                rcv_num = min(rcv_num, 100)
                rcv_msg, rcv_num = self.zcanlib.Receive(self.channel_handle, rcv_num, 100)
                for msg in rcv_msg[:rcv_num]:
                    can_type = "CAN   "
                    frame = msg.frame
                    direction = "TX" if frame._pad & 0x20 else "RX"
                    frame_type = "扩展帧" if frame.can_id & (1 << 31) else "标准帧"
                    can_id_value = frame.can_id & 0x1FFFFFFF
                    is_extended = bool(frame.can_id & (1 << 31))
                    can_id = hex(can_id_value)
                    dlc = frame.can_dlc
                    data_list = list(frame.data[:dlc])
                    data = " ".join([f"{num:02X}" for num in data_list])
                    
                    print(f"[{msg.timestamp}] [实际RX] CAN{self.channel} {can_type:<{CANType_width}}\t"
                          f"{direction} ID: {can_id:<{id_width}}\t{frame_type} "
                          f"DLC: {dlc}\tDATA: {data}")
                    
                    # 如果是接收消息且设置了回调，调用回调函数
                    if direction == "RX" and self.message_callback:
                        self.message_callback(can_id_value, data_list, is_extended, False)
            
            # 接收CANFD消息
            rcv_canfd_num = self.zcanlib.GetReceiveNum(self.channel_handle, ZCAN_TYPE_CANFD)
            if rcv_canfd_num:
                rcv_canfd_num = min(rcv_canfd_num, 100)
                rcv_canfd_msgs, rcv_canfd_num = self.zcanlib.ReceiveFD(
                    self.channel_handle, rcv_canfd_num, 100
                )
                for msg in rcv_canfd_msgs[:rcv_canfd_num]:
                    frame = msg.frame
                    brs = "加速" if frame.flags & 0x1 else "   "
                    can_type = "CANFD" + brs
                    direction = "TX" if frame.flags & 0x20 else "RX"
                    frame_type = "扩展帧" if frame.can_id & (1 << 31) else "标准帧"
                    can_id_value = frame.can_id & 0x1FFFFFFF
                    is_extended = bool(frame.can_id & (1 << 31))
                    can_id = hex(can_id_value)
                    data_list = list(frame.data[:frame.len])
                    data = " ".join([f"{num:02X}" for num in data_list])
                    
                    print(f"[{msg.timestamp}] [实际RX] CAN{self.channel} {can_type:<{CANType_width}}\t"
                          f"{direction} ID: {can_id:<{id_width}}\t{frame_type} "
                          f"DLC: {frame.len}\tDATA: {data}")
                    
                    # 如果是接收消息且设置了回调，调用回调函数
                    if direction == "RX" and self.message_callback:
                        self.message_callback(can_id_value, data_list, is_extended, True)
        
        print("✓ 实际设备接收线程已停止")
    
    def start_receive(self):
        """启动接收线程"""
        if not self.is_running:
            self.is_running = True
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
    
    def stop_receive(self):
        """停止接收线程"""
        if self.is_running:
            self.is_running = False
            if self.receive_thread:
                self.receive_thread.join(timeout=2)


def demo_with_real_device():
    """
    演示虚拟CAN设备 + 实际USBCANFD设备通信
    
    通过桥接机制，虚拟设备和实际设备可以相互通信
    """
    print("=" * 60)
    print("虚拟CAN + 实际USBCANFD设备桥接通信演示")
    print("=" * 60)
    
    # 创建虚拟设备
    print("\n[1] 初始化虚拟CAN设备...")
    vcan = VirtualCANDevice(channel='test_channel', bustype='virtual', bitrate=500000)
    if not vcan.connect():
        print("虚拟设备连接失败，退出")
        return
    
    # 创建实际设备
    print("\n[2] 初始化实际USBCANFD设备...")
    real_can = RealCANDevice(
        device_type=ZCAN_USBCANFD_200U,
        device_index=0,
        channel=0,
        abit_rate=500000,
        dbit_rate=2000000
    )
    if not real_can.connect():
        print("实际设备连接失败，退出")
        vcan.disconnect()
        return
    
    # 设置桥接：虚拟设备收到的消息转发到实际设备
    def virtual_to_real(can_id, data, is_extended, is_fd):
        print(f"  [桥接] 虚拟 -> 实际: ID 0x{can_id:X}")
        real_can.send_message(can_id, data, is_extended, is_fd)
    
    # 设置桥接：实际设备收到的消息转发到虚拟设备
    def real_to_virtual(can_id, data, is_extended, is_fd):
        print(f"  [桥接] 实际 -> 虚拟: ID 0x{can_id:X}")
        vcan.send_message(can_id, data, is_extended, is_fd)
    
    vcan.set_message_callback(virtual_to_real)
    real_can.set_message_callback(real_to_virtual)
    
    # 启动接收
    vcan.start_receive()
    real_can.start_receive()
    
    try:
        print("\n" + "=" * 60)
        print("桥接已建立！虚拟设备和实际设备现在可以互相通信")
        print("=" * 60)
        
        # 测试1：实际设备发送消息
        print("\n[测试1] 实际设备发送CAN消息（会桥接到虚拟设备）")
        real_can.send_message(0x123, [0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88])
        time.sleep(1)
        
        # 测试2：虚拟设备发送消息
        print("\n[测试2] 虚拟设备发送CAN消息（会桥接到实际设备）")
        vcan.send_message(0x456, [0xAA, 0xBB, 0xCC, 0xDD])
        time.sleep(1)
        
        # 测试3：实际设备发送CANFD消息
        print("\n[测试3] 实际设备发送CANFD消息")
        data_fd = list(range(64))
        real_can.send_message(0x200, data_fd, is_fd=True, brs=True, is_extended=True)
        time.sleep(1)
        
        # 测试4：批量测试
        print("\n[测试4] 批量发送测试")
        for i in range(5):
            data = [(i + j) & 0xFF for j in range(8)]
            real_can.send_message(0x300 + i, data)
            time.sleep(0.2)
        
        print("\n" + "=" * 60)
        print("测试完成！设备保持运行，可以继续观察消息")
        print("按回车键停止...")
        print("=" * 60)
        input()
        
    except KeyboardInterrupt:
        print("\n程序被中断")
    finally:
        print("\n正在关闭设备...")
        real_can.disconnect()
        vcan.disconnect()
        print("所有设备已关闭")


def demo_real_device_only():
    """仅使用实际USBCANFD设备进行测试"""
    print("=" * 60)
    print("实际USBCANFD设备通信测试")
    print("=" * 60)
    
    # 创建实际设备
    real_can = RealCANDevice(
        device_type=ZCAN_USBCANFD_200U,
        device_index=0,
        channel=0,
        abit_rate=500000,
        dbit_rate=2000000
    )
    
    if not real_can.connect():
        return
    
    real_can.start_receive()
    
    try:
        print("\n设备已就绪，开始测试...")
        
        # 发送一些测试消息
        print("\n发送CAN标准帧:")
        for i in range(5):
            data = [i, i+1, i+2, i+3, i+4, i+5, i+6, i+7]
            real_can.send_message(0x100 + i, data)
            time.sleep(0.2)
        
        print("\n发送CANFD消息:")
        data_fd = list(range(64))
        real_can.send_message(0x500, data_fd, is_fd=True, brs=True, is_extended=True)
        
        print("\n等待接收消息（按回车键停止）...")
        input()
        
    except KeyboardInterrupt:
        print("\n程序被中断")
    finally:
        real_can.disconnect()


if __name__ == "__main__":
    print("\n请选择运行模式：")
    print("1. 虚拟CAN设备 + 实际USBCANFD设备通信")
    print("2. 仅实际USBCANFD设备测试")
    
    choice = input("\n请输入选择 (1/2): ").strip()
    
    if choice == "1":
        demo_with_real_device()
    elif choice == "2":
        demo_real_device_only()
    else:
        print("无效的选择")
