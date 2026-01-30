"""
@Project ：
@File    ：case_base
@Author  ：zhuangjinpo
@Date    ：2024/10/18 下午4:10
@Description     ：测试用例基类，为所有测试用例提供统一的接口和通用功能

        Revision History
===========================================================================
| Date       |       Author       |  Verion | Change Description
===========================================================================
| 2024/10/18    | zhuangjinpo        |   V1.0  | Create first version
| 2024/09/05    | GitHub Copilot     |   V2.0  | Adapt to test framework
===========================================================================
"""

# -*- coding: utf-8 -*-
import os
import time
import datetime
from typing import Tuple

from config import Config
from PySide6.QtCore import QObject
from tools.load_yaml import load_yaml_config
from tools.log_tool import get_logger
from tools.can_tool.zlgcan import (
    ZCAN,
    ZCAN_USBCANFD_200U,
    ZCAN_LIN_INIT_CONFIG,
    ENHANCE_CHKSUM,
    INVALID_DEVICE_HANDLE,
    ZCAN_STATUS_OK,
)


class CaseBase(QObject):
    """
    测试用例基类

    所有测试用例都应该继承此类，并实现 run 方法。
    基类提供了环境初始化、报告生成、资源清理等通用功能。
    """

    def __init__(self, test_data=None):
        """
        初始化测试用例基类

        Args:
            test_data: 测试数据，从测试框架传入的参数
        """
        super(CaseBase, self).__init__()
        self.test_data = test_data or {}
        self.case_name = self.__class__.__name__
        
        # 初始化日志记录器
        self.logger = get_logger(self.case_name)
        
        self.start_time = time.time()
        self.project_yaml_config = None
        self.test_result = False
        self.test_message = ""
        
        # CAN/LIN 设备相关
        self.zcan = None
        self.device_handle = INVALID_DEVICE_HANDLE
        self.lin_handle = None

        # 从测试数据中提取配置信息
        self.project_name = (
            self.test_data.get(0, "")
            if isinstance(test_data, list) and len(test_data) > 0
            else ""
        )
        self.module_file = (
            self.test_data.get(1, "")
            if isinstance(test_data, list) and len(test_data) > 1
            else ""
        )
        self.class_name = (
            self.test_data.get(2, "")
            if isinstance(test_data, list) and len(test_data) > 2
            else ""
        )

        self.logger.info(f"初始化测试用例: {self.case_name}")

    def env_init(self, config_path=None):
        """
        初始化测试环境
        初始化设备：CAN/LIN

        Args:
            config_path: 配置文件路径（可选）

        Returns:
            bool: 初始化成功返回 True，失败返回 False
        """
        try:
            self.logger.info("开始初始化 CAN/LIN 设备...")
            
            # 创建 ZCAN 实例
            self.zcan = ZCAN()
            
            # 打开设备 (USBCANFD-200U)
            device_type = ZCAN_USBCANFD_200U
            device_index = 0
            self.device_handle = self.zcan.OpenDevice(device_type, device_index, 0)
            
            if self.device_handle == INVALID_DEVICE_HANDLE:
                self.logger.error("打开 CAN 设备失败")
                return False
            
            self.logger.info(f"CAN 设备打开成功，句柄: {self.device_handle}")
            
            # 初始化 LIN 通道 (Master 模式)
            lin_channel = 0
            lin_config = ZCAN_LIN_INIT_CONFIG()
            lin_config.linMode = 1      # 1=Master, 0=Slave
            lin_config.linBaud = 19200  # LIN 波特率
            lin_config.chkSumMode = ENHANCE_CHKSUM  # 增强校验
            lin_config.maxLength = 8    # 最大数据长度
            
            self.lin_handle = self.zcan.InitLIN(self.device_handle, lin_channel, lin_config)
            
            if self.lin_handle == 0:
                self.logger.error("初始化 LIN 通道失败")
                self.zcan.CloseDevice(self.device_handle)
                self.device_handle = INVALID_DEVICE_HANDLE
                return False
            
            # 启动 LIN 通道
            ret = self.zcan.StartLIN(self.lin_handle)
            if ret != ZCAN_STATUS_OK:
                self.logger.error("启动 LIN 通道失败")
                self.zcan.CloseDevice(self.device_handle)
                self.device_handle = INVALID_DEVICE_HANDLE
                self.lin_handle = None
                return False
            
            self.logger.info("LIN 通道启动成功")
            return True

        except Exception as e:
            self.logger.error(f"环境初始化失败: {str(e)}")
            # 清理已分配的资源
            if self.device_handle != INVALID_DEVICE_HANDLE and self.zcan:
                self.zcan.CloseDevice(self.device_handle)
                self.device_handle = INVALID_DEVICE_HANDLE
            return False



    def run(self) -> Tuple[bool, str]:
        """
        测试执行主入口 - 必须被子类重写

        Returns:
            tuple: (result, message)
                - result (bool): 测试是否通过
                - message (str): 测试结果信息

        说明：
            这是测试用例的主要执行方法，所有继承CaseBase的测试用例都必须实现此方法。
            方法应该返回一个元组，包含测试结果（True/False）和相关信息。
        """
        self.logger.warning(f"测试用例 {self.case_name} 未实现 run 方法")
        return False, "测试用例未实现run方法"

    def setUp(self):
        """
        测试前置操作 - 可选重写

        子类可以重写此方法来实现特定的测试前置操作
        """
        self.logger.info(f"执行测试用例前置操作: {self.case_name}")

    def tearDown(self):
        """
        测试后置操作 - 可选重写

        子类可以重写此方法来实现特定的测试后置操作
        """
        self.logger.info(f"执行测试用例后置操作: {self.case_name}")
        self.teardown_test()

    def assert_true(self, condition, message="断言失败"):
        """
        断言为真

        Args:
            condition: 要检查的条件
            message: 失败时的消息

        Returns:
            bool: 断言结果
        """
        if not condition:
            self.logger.error(f"断言失败: {message}")
            return False
        return True

    def assert_equal(self, expected, actual, message=None):
        """
        断言相等

        Args:
            expected: 期望值
            actual: 实际值
            message: 自定义错误消息

        Returns:
            bool: 断言结果
        """
        if expected != actual:
            error_msg = message or f"期望值: {expected}, 实际值: {actual}"
            self.logger.error(f"断言失败: {error_msg}")
            return False
        return True

    def log_info(self, message):
        """记录信息日志"""
        self.logger.info(f"[{self.case_name}] {message}")

    def log_error(self, message):
        """记录错误日志"""
        self.logger.error(f"[{self.case_name}] {message}")

    def log_warning(self, message):
        """记录警告日志"""
        self.logger.warning(f"[{self.case_name}] {message}")

    def set_result(self, result, message=""):
        """
        设置测试结果

        Args:
            result (bool): 测试结果
            message (str): 结果描述
        """
        self.test_result = result
        self.test_message = message

        if result:
            self.log_info(f"测试通过: {message}")
        else:
            self.log_error(f"测试失败: {message}")

    def get_execution_time(self):
        """
        获取执行时间

        Returns:
            float: 执行时间（秒）
        """
        return time.time() - self.start_time



    def teardown_test(self):
        """
        清理测试环境

        说明：
            该函数在测试结束后调用，用于关闭连接和清理资源
        """
        try:
            # 关闭 LIN 通道
            if self.lin_handle is not None and self.zcan:
                try:
                    self.zcan.ResetLIN(self.lin_handle)
                    self.logger.info("LIN 通道已关闭")
                except Exception as e:
                    self.logger.warning(f"关闭 LIN 通道时出错: {str(e)}")
                finally:
                    self.lin_handle = None
            
            # 关闭 CAN 设备
            if self.device_handle != INVALID_DEVICE_HANDLE and self.zcan:
                try:
                    self.zcan.CloseDevice(self.device_handle)
                    self.logger.info("CAN 设备已关闭")
                except Exception as e:
                    self.logger.warning(f"关闭 CAN 设备时出错: {str(e)}")
                finally:
                    self.device_handle = INVALID_DEVICE_HANDLE

            # 其他清理操作可以在这里添加

            self.logger.info(f"测试环境清理完成: {self.case_name}")

        except Exception as e:
            self.logger.error(f"测试环境清理失败: {str(e)}")

    def __call__(self):
        """
        使测试用例实例可调用，兼容不同的调用方式

        Returns:
            tuple: (result, message) 或直接执行测试
        """
        try:
            # 执行前置操作
            self.setUp()

            # 环境初始化
            if not self.env_init():
                return False, "环境初始化失败"

            # 执行测试
            result = self.run()

            # 如果run方法返回元组，则使用返回值
            if isinstance(result, tuple) and len(result) == 2:
                self.set_result(result[0], result[1])
                return result
            else:
                # 如果没有返回值或返回值格式不对，使用内部状态
                return self.test_result, self.test_message

        except Exception as e:
            error_msg = f"测试执行异常: {str(e)}"
            self.set_result(False, error_msg)
            return False, error_msg

        finally:
            # 执行后置操作
            self.tearDown()
