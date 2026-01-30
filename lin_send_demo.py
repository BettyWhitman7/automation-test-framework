import time
import ctypes
from tools.can_tool.zlgcan import *

def main():
    zcan = ZCAN()
    
    # 1. 打开设备
    device_type = ZCAN_USBCANFD_200U 
    device_index = 0
    device_handle = zcan.OpenDevice(device_type, device_index, 0)
    if device_handle == INVALID_DEVICE_HANDLE:
        print("打开设备失败!")
        return

    # 2. 初始化 LIN 通道 (Master)
    lin_channel = 0
    lin_config = ZCAN_LIN_INIT_CONFIG()
    lin_config.linMode = 1      # Master
    lin_config.linBaud = 19200
    lin_config.chkSumMode = ENHANCE_CHKSUM
    
    chn_handle = zcan.InitLIN(device_handle, lin_channel, lin_config)
    if chn_handle == 0:
        print("初始化 LIN 失败!")
        zcan.CloseDevice(device_handle)
        return
        
    zcan.StartLIN(chn_handle)
    print("LIN 通道已启动，准备发送转速指令...")

    # ==========================================
    # 严格遵循官方逻辑：步骤 2 (发送头部和响应)
    # ==========================================
    
    # A. 准备 Publish 配置结构体 (用于 SetLINPublish)
    pub_cfg = ZCAN_LIN_PUBLISH_CFG()
    pub_cfg.ID = 0x2A
    pub_cfg.dataLen = 8
    pub_cfg.chkSumMode = ENHANCE_CHKSUM
    # 初始化数据为0，避免脏数据
    for i in range(8):
        pub_cfg.data[i] = 0x00
    
    # B. 准备 Transmit 消息结构体 (用于触发头部)
    msg = ZCAN_LIN_MSG()
    msg.chnl = lin_channel
    msg.dataType = ZCAN_DT_ZCAN_LIN_DATA
    msg.data.zcanLINData.PID = 0x2A
    msg.data.zcanLINData.RxData.dataLen = 8
    msg.data.zcanLINData.RxData.chkSum = ENHANCE_CHKSUM
    # 主站发送时，dir应该设为1
    # TransmitLIN作为触发器，实际数据由SetLINPublish配置
    msg.data.zcanLINData.RxData.dir = 1

    print("开始运行 - 官方查表模式...")

    try:
        target_speed = 0
        while True:
            # 模拟转速变化
            target_speed += 10
            if target_speed > 100: target_speed = 0
            raw_val = int(target_speed / 0.4)

            # --- 第一步：先调用 SetLINPublish 更新数据 ---
            # 这相当于把数据写入设备的“待发送寄存器”
            # 清空并设置新数据
            for i in range(8):
                pub_cfg.data[i] = 0x00
            pub_cfg.data[1] = raw_val  # Byte1存放转速值
            
            ret = zcan.SetLINPublish(chn_handle, pub_cfg, 1)
            
            if ret != ZCAN_STATUS_OK:
                print("设置 Publish 失败")
                continue

            # --- 第二步：调用 TransmitLIN 发送头部 ---
            # 设备发出头后，会发现 0x2A 在 Publish 表里，于是自动把上面的数据发出去
            ret_tx = zcan.TransmitLIN(chn_handle, msg, 1)
            
            if ret_tx > 0:
                print(f"✓ 已触发 ID 0x{pub_cfg.ID:02X}，设定转速: {target_speed}% | 原始值: 0x{raw_val:02X}")
            else:
                print(f"✗ TransmitLIN 失败 (返回: {ret_tx})")
            
            time.sleep(0.2)

    except KeyboardInterrupt:
        # ==========================================
        # 严格遵循官方逻辑：步骤 3 (取消响应)
        # ==========================================
        print("\n\n切换模式：取消发布，改为订阅(Subscribe)模式...")
        
        # 调用 SetLINSubscribe 取消此ID的发布
        sub_cfg = ZCAN_LIN_SUBSCIBE_CFG()
        sub_cfg.ID = 0x2A
        sub_cfg.dataLen = 8
        sub_cfg.chkSumMode = ENHANCE_CHKSUM
        ret_sub = zcan.SetLINSubscribe(chn_handle, sub_cfg, 1)
        
        if ret_sub == ZCAN_STATUS_OK:
            print(f"✓ 已取消 ID 0x{sub_cfg.ID:02X} 的发布，切换为订阅模式")
        else:
            print(f"✗ SetLINSubscribe 失败 (返回: {ret_sub})")
        
        # 此时再调用 TransmitLIN，设备只会发送头部，不附加数据
        # 适用于主站询问从机的场景
        print("\n演示：发送仅头部模式(等待从机响应)...")
        for i in range(3):
            ret_tx = zcan.TransmitLIN(chn_handle, msg, 1)
            if ret_tx > 0:
                print(f"  第{i+1}次: ✓ 仅发送头部 ID 0x{msg.data.zcanLINData.PID:02X} (无数据段)")
            time.sleep(0.3)
        
        print("\n说明: 当前无从机响应，实际应用中从机会回复数据")

    zcan.CloseDevice(device_handle)

if __name__ == "__main__":
    main()