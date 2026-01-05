"""
日志配置模块
提供统一的日志接口，支持文件和控制台输出
"""
import logging
import sys
from pathlib import Path

# 日志目录
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 日志文件路径
LOG_FILE = LOG_DIR / "app.log"


def setup_logger(
    name: str = "gemini_chat",
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = False
) -> logging.Logger:
    """
    配置并返回日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_to_file: 是否记录到文件
        log_to_console: 是否输出到控制台

    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    # 日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 文件处理器
    if log_to_file:
        file_handler = logging.FileHandler(
            LOG_FILE,
            encoding="utf-8",
            mode="a"  # 追加模式
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # 控制台处理器
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


# 预配置的日志记录器
def get_logger(name: str = "gemini_chat") -> logging.Logger:
    """获取日志记录器（单例模式）"""
    return setup_logger(name)


# 模块级便捷函数
def debug(msg: str, *args, **kwargs):
    """记录调试信息"""
    get_logger().debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """记录一般信息"""
    get_logger().info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """记录警告信息"""
    get_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """记录错误信息"""
    get_logger().error(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs):
    """记录异常信息（包含堆栈跟踪）"""
    get_logger().exception(msg, *args, **kwargs)
