"""
基于 loguru 的日志工具

提供功能：
1. 统一的日志格式
2. 控制台和文件日志输出
3. 日志轮转和压缩
4. 彩色控制台输出
5. 不同模块的独立日志记录器
"""

import sys
import os
from pathlib import Path
from typing import Optional
from loguru import logger


# 日志配置
class LogConfig:
    """日志配置类"""
    
    # 日志目录
    LOG_DIR = Path("logs")
    
    # 日志格式
    CONSOLE_FORMAT = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    FILE_FORMAT = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
    
    # 日志级别
    CONSOLE_LEVEL = "INFO"
    FILE_LEVEL = "DEBUG"
    
    # 文件轮转配置
    ROTATION = "10 MB"  # 日志文件达到 10MB 时轮转
    RETENTION = "30 days"  # 保留 30 天的日志
    COMPRESSION = "zip"  # 压缩格式
    
    # 编码
    ENCODING = "utf-8"


class Logger:
    """日志管理器"""
    
    _initialized = False
    _logger_cache = {}
    
    @classmethod
    def setup_logger(
        cls,
        log_dir: Optional[str] = None,
        console_level: str = LogConfig.CONSOLE_LEVEL,
        file_level: str = LogConfig.FILE_LEVEL,
        rotation: str = LogConfig.ROTATION,
        retention: str = LogConfig.RETENTION,
        compression: str = LogConfig.COMPRESSION,
    ):
        """
        设置全局日志配置
        
        Args:
            log_dir: 日志文件目录，默认为 'logs'
            console_level: 控制台日志级别
            file_level: 文件日志级别
            rotation: 日志轮转策略
            retention: 日志保留时间
            compression: 日志压缩格式
        """
        if cls._initialized:
            logger.warning("Logger already initialized, skipping setup")
            return
        
        # 移除默认的 handler
        logger.remove()
        
        # 添加控制台输出
        logger.add(
            sys.stderr,
            format=LogConfig.CONSOLE_FORMAT,
            level=console_level,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
        
        # 设置日志目录
        if log_dir is None:
            log_dir = LogConfig.LOG_DIR
        else:
            log_dir = Path(log_dir)
        
        # 确保日志目录存在
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 添加通用日志文件
        logger.add(
            log_dir / "app_{time:YYYY-MM-DD}.log",
            format=LogConfig.FILE_FORMAT,
            level=file_level,
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding=LogConfig.ENCODING,
            backtrace=True,
            diagnose=True,
        )
        
        # 添加错误日志文件（单独记录 ERROR 及以上级别）
        logger.add(
            log_dir / "error_{time:YYYY-MM-DD}.log",
            format=LogConfig.FILE_FORMAT,
            level="ERROR",
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding=LogConfig.ENCODING,
            backtrace=True,
            diagnose=True,
        )
        
        cls._initialized = True
        logger.info("Logger initialized successfully")
    
    @classmethod
    def get_logger(cls, name: Optional[str] = None):
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称，通常使用模块名 __name__
        
        Returns:
            logger: loguru 日志记录器实例
        """
        # 如果还未初始化，先进行初始化
        if not cls._initialized:
            cls.setup_logger()
        
        # 如果没有指定名称，返回默认 logger
        if name is None:
            return logger
        
        # 检查缓存
        if name in cls._logger_cache:
            return cls._logger_cache[name]
        
        # 创建带上下文的 logger
        custom_logger = logger.bind(name=name)
        cls._logger_cache[name] = custom_logger
        
        return custom_logger


# 便捷函数
def setup_logger(
    log_dir: Optional[str] = None,
    console_level: str = LogConfig.CONSOLE_LEVEL,
    file_level: str = LogConfig.FILE_LEVEL,
    rotation: str = LogConfig.ROTATION,
    retention: str = LogConfig.RETENTION,
    compression: str = LogConfig.COMPRESSION,
):
    """
    设置全局日志配置
    
    Args:
        log_dir: 日志文件目录
        console_level: 控制台日志级别
        file_level: 文件日志级别
        rotation: 日志轮转策略
        retention: 日志保留时间
        compression: 日志压缩格式
    
    Example:
        >>> from tools.log_tool import setup_logger
        >>> setup_logger(log_dir="logs", console_level="DEBUG")
    """
    Logger.setup_logger(
        log_dir=log_dir,
        console_level=console_level,
        file_level=file_level,
        rotation=rotation,
        retention=retention,
        compression=compression,
    )


def get_logger(name: Optional[str] = None):
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称，通常使用模块名 __name__
    
    Returns:
        logger: loguru 日志记录器实例
    
    Example:
        >>> from tools.log_tool import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("This is an info message")
        >>> logger.debug("This is a debug message")
        >>> logger.warning("This is a warning message")
        >>> logger.error("This is an error message")
    """
    return Logger.get_logger(name)


# 模块级别的 logger 实例
module_logger = get_logger(__name__)


if __name__ == "__main__":
    # 测试代码
    setup_logger(console_level="DEBUG")
    
    test_logger = get_logger("test_module")
    
    test_logger.debug("这是一条调试信息")
    test_logger.info("这是一条普通信息")
    test_logger.warning("这是一条警告信息")
    test_logger.error("这是一条错误信息")
    test_logger.success("这是一条成功信息")
    
    # 测试异常日志
    try:
        1 / 0
    except Exception as e:
        test_logger.exception("捕获到异常")
    
    print("\n✅ 日志测试完成！请查看 logs 目录")
