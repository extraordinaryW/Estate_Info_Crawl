# -*- coding: utf-8 -*-
"""
日志工具模块
"""
import logging
import logging.config
from typing import Dict, Any
from config import Config

def setup_logger(spider_name: str) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        spider_name: 爬虫名称
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    log_config = Config.get_log_config(spider_name)
    
    # 创建日志记录器
    logger = logging.getLogger(spider_name)
    logger.setLevel(getattr(logging, log_config["level"]))
    
    # 清除已有的处理器
    logger.handlers.clear()
    
    # 创建文件处理器
    file_handler = logging.FileHandler(log_config["filename"], encoding='utf-8')
    file_handler.setLevel(getattr(logging, log_config["level"]))
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_config["level"]))
    
    # 创建格式器
    formatter = logging.Formatter(
        log_config["format"],
        datefmt=log_config["datefmt"]
    )
    
    # 设置格式器
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger 