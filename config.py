import os
import logging


class Config:
    LOGGER_LEVEL = logging.INFO  # 日志级别
    ROOT_DIR = os.path.abspath(os.path.dirname(__file__))  # 项目根目录
    CASE_SCRIPT_DIR = os.path.join(ROOT_DIR, "case_script/RecordDev/")  # 用例脚本目录
    LOG_DIR = os.path.join(ROOT_DIR, "logs")  # 日志目录
    REPORT_DIR = os.path.join(ROOT_DIR, "reports")  # 测试报告目录
    ALLURE_RESULTS_DIR = os.path.join(REPORT_DIR, "allure_results")  # allure结果目录
    ALLURE_REPORT_DIR = os.path.join(REPORT_DIR, "allure_report")  # allure报告报告

    USER_CONFIG_DIR = os.path.join(ROOT_DIR, "user_config")  # 用户配置目录
    DEV_CONFIG_DIR = os.path.join(USER_CONFIG_DIR, "dev_config")  # 设备配置目录
    TEST_SUITE_DIR = os.path.join(USER_CONFIG_DIR, "test_suite")  # 测试套件目录
    TESTCASE_CONFIG_DIR = os.path.join(
        USER_CONFIG_DIR, "testcase_config"
    )  # 测试用例配置目录,用于用例执行时的参数配置


