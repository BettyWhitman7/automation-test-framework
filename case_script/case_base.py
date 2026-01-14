"""
Copyright 1995-2024 Xiamen Yaxun Network Co., Ltd
@Project ：YaxonATS
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
import copy
import os
import time
import datetime
from typing import Tuple

from business.can_module.usbcan import set_usb_can
from business.serial_module.myserial import Serial
from config import Config
from PySide6.QtCore import QObject
from tools.load_yaml import load_yaml_config
from tools.excelReport import ExcelReport
from tools.log_tool import get_logger


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
        self.excel_report = None
        self.serial_connection = None
        self.test_result = False
        self.test_message = ""

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

        Args:
            config_path (str, optional): 配置文件路径。如果不提供，则尝试从test_data中获取

        Returns:
            bool: 初始化是否成功

        说明：
            该方法主要负责测试环境的初始化工作，包括：
            1. 加载项目配置文件
            2. 初始化串口连接（如果需要）
            3. 配置USB CAN（如果需要）
            4. 初始化测试报告
        """
        try:
            # 如果没有提供配置路径，尝试从项目名构建默认路径
            if not config_path and self.project_name:
                config_path = f"{self.project_name}/{self.project_name}_config.yaml"

            if not config_path:
                self.logger.warning("未提供配置文件路径，使用默认配置")
                return True

            # 加载项目配置
            full_config_path = os.path.join(Config.TESTCASE_CONFIG_DIR, config_path)
            if os.path.exists(full_config_path):
                self.project_yaml_config = load_yaml_config(full_config_path)
                self.logger.info(f"成功加载配置文件: {full_config_path}")

                # 获取环境设置
                env_set = self.project_yaml_config.get("env_set", {})

                # 初始化串口连接（继电器等）
                self._init_serial_connection(env_set)

                # 初始化USB CAN
                self._init_usb_can(env_set)

                # 初始化测试报告
                self._init_test_report(env_set)

            else:
                self.logger.warning(f"配置文件不存在: {full_config_path}")

            return True

        except Exception as e:
            self.logger.error(f"环境初始化失败: {str(e)}")
            return False

    def _init_serial_connection(self, env_set):
        """初始化串口连接"""
        try:
            serial_cfg = env_set.get("power_serial_cfg", {})
            if serial_cfg and serial_cfg.get("is_use", False):
                serial_port = serial_cfg.get("port")
                serial_baudrate = serial_cfg.get("baudrate", 9600)
                is_base = serial_cfg.get("is_base", True)

                if serial_port:
                    self.serial_connection = Serial(serial_port, serial_baudrate)
                    self.logger.info(f"串口连接初始化成功: {serial_port}")

        except Exception as e:
            self.logger.error(f"串口初始化失败: {str(e)}")

    def _init_usb_can(self, env_set):
        """初始化USB CAN"""
        try:
            can_cfg = env_set.get("can_cfg", {})
            if can_cfg and can_cfg.get("is_use", False):
                set_usb_can(can_cfg)
                self.logger.info("USB CAN配置成功")

        except Exception as e:
            self.logger.error(f"USB CAN初始化失败: {str(e)}")

    def _init_test_report(self, env_set):
        """初始化测试报告"""
        try:
            report_cfg = env_set.get("report_cfg", {})
            if report_cfg and report_cfg.get("is_use", False):
                excel_path = report_cfg.get("excel_path")
                if excel_path:
                    self.excel_report = ExcelReport(excel_path)
                    self.logger.info(f"测试报告初始化成功: {excel_path}")

        except Exception as e:
            self.logger.error(f"测试报告初始化失败: {str(e)}")

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

    def report_excel(self, report_sheet=None):
        """
        生成测试报告Excel文件

        Args:
            report_sheet (str, optional): 要生成报告的工作表名称

        说明：
            将测试结果写入Excel报告中
        """
        try:
            if not self.excel_report:
                self.logger.warning("Excel报告未初始化，跳过报告生成")
                return

            # 准备报告数据
            report_data = {
                "case_name": self.case_name,
                "result": "通过" if self.test_result else "失败",
                "message": self.test_message,
                "execution_time": round(self.get_execution_time(), 2),
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        except Exception as e:
            self.logger.error(f"生成Excel报告失败: {str(e)}")

    def teardown_test(self):
        """
        清理测试环境

        说明：
            该函数在测试结束后调用，用于关闭连接和清理资源
        """
        try:
            # 关闭串口连接
            if self.serial_connection:
                self.serial_connection.close()
                self.logger.info("串口连接已关闭")

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
