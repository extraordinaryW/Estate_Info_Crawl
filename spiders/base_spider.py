# -*- coding: utf-8 -*-
"""
爬虫基类
"""
from abc import ABC, abstractmethod
from selenium import webdriver
from typing import List, Dict, Any, Optional
import logging
from utils.logger import setup_logger
from utils.browser import BrowserManager
from utils.data_storage import DataStorage

class BaseSpider(ABC):
    """爬虫基类"""
    
    def __init__(self, spider_name: str):
        """
        初始化爬虫
        
        Args:
            spider_name: 爬虫名称
        """
        self.spider_name = spider_name
        self.logger = setup_logger(spider_name)
        self.driver: Optional[webdriver.Chrome] = None
        self.data_storage = DataStorage()
        self.data: List[Dict[str, Any]] = []
    
    def start(self) -> None:
        """
        启动爬虫
        """
        try:
            self.logger.info(f"开始运行 {self.spider_name}")
            self.setup_driver()
            self.run()
            self.save_data()
            self.logger.info(f"{self.spider_name} 运行完成")
        except Exception as e:
            self.logger.error(f"{self.spider_name} 运行失败: {e}")
            # 出错时自动保存当前获取到的数据
            self.save_data_on_error()
            raise
        finally:
            self.cleanup()
    
    def setup_driver(self) -> None:
        """
        设置浏览器驱动
        """
        self.driver = BrowserManager.create_normal_driver()
        self.logger.info("浏览器驱动创建成功")
    
    @abstractmethod
    def run(self) -> None:
        """
        运行爬虫逻辑（子类必须实现）
        """
        pass
    
    def save_data(self) -> None:
        """
        保存数据
        """
        if self.data:
            filename = f"{self.spider_name}_数据.xlsx"
            self.data_storage.save_to_excel(self.data, filename)
            self.logger.info(f"数据已保存，共 {len(self.data)} 条记录")
        else:
            self.logger.warning("没有数据需要保存")
    
    def save_data_on_error(self) -> None:
        """
        出错时保存当前获取到的数据
        """
        if self.data:
            # 使用带时间戳的文件名，避免覆盖正常保存的数据
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.spider_name}_数据_错误保存_{timestamp}.xlsx"
            
            try:
                self.data_storage.save_to_excel(self.data, filename)
                self.logger.info(f"错误发生时已自动保存数据，共 {len(self.data)} 条记录")
                self.logger.info(f"保存文件: {filename}")
            except Exception as save_error:
                self.logger.error(f"保存错误数据时失败: {save_error}")
        else:
            self.logger.info("没有数据需要保存")
    
    def cleanup(self) -> None:
        """
        清理资源
        """
        if self.driver:
            BrowserManager.close_driver(self.driver)
            self.logger.info("浏览器驱动已关闭")
    
    def add_data(self, item: Dict[str, Any]) -> None:
        """
        添加数据项
        
        Args:
            item: 数据项
        """
        self.data.append(item)
    
    def get_data(self) -> List[Dict[str, Any]]:
        """
        获取所有数据
        
        Returns:
            List[Dict[str, Any]]: 数据列表
        """
        return self.data.copy() 