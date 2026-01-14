"""
日志工具模块
使用 loguru 库提供统一的日志管理功能
"""

from .logger import get_logger, setup_logger

# 兼容旧代码，提供默认的 log 对象
log = get_logger("root")

__all__ = ["get_logger", "setup_logger", "log"]
