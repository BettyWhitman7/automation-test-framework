# -*- coding: utf-8 -*-
"""
@Project ：automation-test-framework
@File    ：chery_lin_tests
@Author  ：zhuangjinpo
@Date    ：2026/01/29
@Description：Chery LIN 测试用例 - 转速递增测试 0-100%

        Revision History
===========================================================================
| Date       |       Author       |  Version | Change Description
===========================================================================
| 2026/01/29 | zhuangjinpo        |   V1.0   | 创建 LIN 转速递增测试
===========================================================================
"""

import time
import sys
import os
from typing import Tuple

# 添加父目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from case_script.case_base import CaseBase
from tools.can_tool.zlgcan import (
    ZCAN_LIN_PUBLISH_CFG,
    ZCAN_LIN_MSG,
    ZCAN_DT_ZCAN_LIN_DATA,
    ENHANCE_CHKSUM,
    ZCAN_STATUS_OK,
)


class CheryLinSpeedTest(CaseBase):
    """
    奇瑞水泵LIN转速递增测试
    
    测试功能：
        从 0% 到 100% 递增发送 LIN 转速指令，步进为 10%
        使用 LIN ID 0x2A 发送转速数据
    """
    
    def __init__(self, test_data=None):
        """初始化测试用例"""
        super().__init__(test_data)
        self.lin_id = 0x2A  # LIN 消息 ID
        self.speed_step = 10  # 转速步进 (%)
        self.delay = 0.2  # 发送间隔 (秒)
    
    def run(self) -> Tuple[bool, str]:
        """
        执行 LIN 转速递增测试
        
        Returns:
            (bool, str): (测试结果, 结果描述)
        """
        try:
            self.log_info("=" * 60)
            self.log_info("开始执行 LIN 转速递增测试 (0-100%)")
            self.log_info("=" * 60)
            
            # 检查 LIN 句柄是否有效
            if self.lin_handle is None:
                return False, "LIN 通道未初始化"
            
            # 准备 Publish 配置结构体
            pub_cfg = ZCAN_LIN_PUBLISH_CFG()
            pub_cfg.ID = self.lin_id
            pub_cfg.dataLen = 8
            pub_cfg.chkSumMode = ENHANCE_CHKSUM
            
            # 初始化数据为 0
            for i in range(8):
                pub_cfg.data[i] = 0x00
            
            # 准备 Transmit 消息结构体
            msg = ZCAN_LIN_MSG()
            msg.chnl = 0  # LIN 通道 0
            msg.dataType = ZCAN_DT_ZCAN_LIN_DATA
            msg.data.zcanLINData.PID = self.lin_id
            msg.data.zcanLINData.RxData.dataLen = 8
            msg.data.zcanLINData.RxData.chkSum = ENHANCE_CHKSUM
            msg.data.zcanLINData.RxData.dir = 1  # 主站发送
            
            success_count = 0
            fail_count = 0
            
            # 从 0% 到 100% 递增发送转速
            for speed_percent in range(0, 101, self.speed_step):
                # 计算原始值: 转速(%) / 0.4 = 原始值
                raw_value = int(speed_percent / 0.4)
                
                # 确保不超过 255 (单字节最大值)
                if raw_value > 255:
                    raw_value = 255
                
                # 清空数据并设置新值
                for i in range(8):
                    pub_cfg.data[i] = 0x00
                pub_cfg.data[1] = raw_value  # Byte1 存放转速值
                
                # 第一步：调用 SetLINPublish 更新数据
                ret_pub = self.zcan.SetLINPublish(self.lin_handle, pub_cfg, 1)
                
                if ret_pub != ZCAN_STATUS_OK:
                    error_msg = f"设置 Publish 失败 - 转速: {speed_percent}%"
                    self.log_error(error_msg)
                    fail_count += 1
                    continue
                
                # 第二步：调用 TransmitLIN 发送头部
                ret_tx = self.zcan.TransmitLIN(self.lin_handle, msg, 1)
                
                if ret_tx > 0:
                    success_count += 1
                    self.log_info(
                        f"✓ 发送成功 - 转速: {speed_percent:3d}% | "
                        f"原始值: 0x{raw_value:02X} ({raw_value})"
                    )
                else:
                    fail_count += 1
                    error_msg = f"✗ 发送失败 - 转速: {speed_percent}% | 返回值: {ret_tx}"
                    self.log_error(error_msg)
                
                # 延时
                time.sleep(self.delay)
            
            # 测试结果统计
            total_count = success_count + fail_count
            self.log_info("=" * 60)
            self.log_info(f"测试完成 - 总计: {total_count}, 成功: {success_count}, 失败: {fail_count}")
            self.log_info("=" * 60)
            
            if fail_count == 0:
                result_msg = f"LIN 转速递增测试通过 (成功发送 {success_count} 条消息)"
                self.set_result(True, result_msg)
                return True, result_msg
            else:
                result_msg = f"LIN 转速递增测试失败 (失败 {fail_count} 条消息)"
                self.set_result(False, result_msg)
                return False, result_msg
        
        except Exception as e:
            error_msg = f"测试执行异常: {str(e)}"
            self.log_error(error_msg)
            self.set_result(False, error_msg)
            return False, error_msg


# 测试用例入口（用于框架调用）
if __name__ == "__main__":
    # 单独运行测试用例
    test = CheryLinSpeedTest()
    result, message = test()
    print(f"\n测试结果: {'通过' if result else '失败'}")
    print(f"结果信息: {message}")
    print(f"执行时间: {test.get_execution_time():.2f} 秒")
