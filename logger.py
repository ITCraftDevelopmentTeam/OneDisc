import logging
import inspect

BASIC_CONFIG = {
    "level": 20,
    "datefmt": "%Y-%m-%d %H:%M:%S",
    "format": "[%(asctime)s][%(name)s / %(levelname)s]: %(message)s"
}


def init_logger(logger_config: dict) -> None:
    """
    初始化 Logging 配置

    Args:
        logger_config (dict): 配置（`config.json->system.logger`）
    """
    config = BASIC_CONFIG.copy()
    config.update(logger_config)
    logging.basicConfig(**config)


def get_logger(name: str | None = None) -> logging.Logger:
    """
    获取日志记录器

    Args:
        name (str | None, optional): 名称，为`None`则为模块 `__name__`. Defaults to None.

    Returns:
        logging.Logger: 日志记录器
    """
    return logging.getLogger(name or inspect.getmodule(inspect.stack()[1][0]).__name__)
