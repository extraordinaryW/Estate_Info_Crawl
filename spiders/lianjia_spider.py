# -*- coding: utf-8 -*-
"""
链家二手房爬虫
"""
import pandas as pd
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from typing import Dict, Any, List, Optional
from tqdm import tqdm
from spiders.base_spider import BaseSpider
from config import Config

class LianjiaSpider(BaseSpider):
    """链家二手房爬虫"""
    
    def __init__(self, districts: List[str] = None, max_pages: int = None):
        """
        初始化链家二手房爬虫
        
        Args:
            districts: 要爬取的区域列表，如果为None则爬取所有区域
            max_pages: 每个区域最大爬取页数
        """
        super().__init__("链家二手房")
        self.districts = districts or list(Config.SHENZHEN_DISTRICTS.keys())
        self.max_pages = max_pages or Config.LIANJIA_CONFIG["max_pages"]
        self.config = Config.LIANJIA_CONFIG
        self.district_mapping = Config.DISTRICT_EN_MAPPING
    
    def run(self) -> None:
        """
        运行爬虫逻辑
        """
        try:
            # 访问链家首页
            self.driver.get(self.config["base_url"])
            self.logger.info("成功访问链家首页")
            
            # 等待用户登录
            input("请在浏览器中完成登录，然后按回车键继续...")
            
            # 爬取各个区域的数据
            for district in self.districts:
                self.crawl_district(district)
            
        except Exception as e:
            self.logger.error(f"爬取过程中出错: {e}")
            raise
    
    def crawl_district(self, district: str) -> None:
        """
        爬取指定区域的数据
        
        Args:
            district: 区域名称
        """
        self.logger.info(f"开始爬取 {district} 的数据")
        
        district_data = []
        sub_districts = Config.SHENZHEN_DISTRICTS.get(district, [])
        
        for sub_district in sub_districts:
            try:
                sub_data = self.crawl_sub_district(sub_district)
                if sub_data:
                    district_data.extend(sub_data)
            except Exception as e:
                self.logger.error(f"爬取 {sub_district} 时出错: {e}")
                continue
        
        # 保存区域数据
        if district_data:
            filename = f"链家二手房_{district}.xlsx"
            self.data_storage.save_to_excel(district_data, filename)
            self.logger.info(f"{district} 数据保存完成，共 {len(district_data)} 条记录")
        
        # 添加到总数据
        self.data.extend(district_data)
    
    def crawl_sub_district(self, sub_district: str) -> List[Dict[str, Any]]:
        """
        爬取子区域数据
        
        Args:
            sub_district: 子区域名称
            
        Returns:
            List[Dict[str, Any]]: 子区域数据
        """
        # 获取英文区域名
        district_en = self.district_mapping.get(sub_district)
        if not district_en:
            self.logger.warning(f"未找到 {sub_district} 的英文映射")
            return []
        
        # 构建URL
        url = f"{self.config['base_url']}/{district_en}"
        
        try:
            self.driver.get(url)
            self.logger.info(f"访问 {sub_district} 页面: {url}")
            
            # 获取最大页数
            max_page = self.get_max_pages()
            if not max_page:
                return []
            
            # 限制最大页数
            max_page = min(max_page, self.max_pages)
            
            sub_district_data = []
            
            # 爬取每一页
            for page in tqdm(range(1, max_page + 1), desc=f"爬取{sub_district}"):
                try:
                    if page > 1:
                        page_url = f"{url}/pg{page}/"
                        self.driver.get(page_url)
                    
                    # 获取页面数据
                    page_data = self.get_page_data(sub_district)
                    if page_data:
                        sub_district_data.extend(page_data)
                    
                    # 随机延时
                    time.sleep(random.uniform(*self.config["sleep_range"]))
                    
                except Exception as e:
                    self.logger.error(f"爬取 {sub_district} 第 {page} 页时出错: {e}")
                    continue
            
            return sub_district_data
            
        except Exception as e:
            self.logger.error(f"爬取 {sub_district} 时出错: {e}")
            return []
    
    def get_max_pages(self) -> Optional[int]:
        """
        获取最大页数
        
        Returns:
            Optional[int]: 最大页数
        """
        try:
            page_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, ".//*[contains(@class, 'page-box') and contains(@class, 'house-lst-page-box')]"))
            )
            max_page = int(page_box.find_element(By.XPATH, './/a[4]').text)
            self.logger.info(f"最大页数为: {max_page}")
            return max_page
        except NoSuchElementException:
            self.logger.warning("无法获取最大页数，请手动输入:")
            try:
                max_page = int(input("请输入最大页数: "))
                return max_page
            except ValueError:
                self.logger.error("输入的不是有效数字")
                return None
        except Exception as e:
            self.logger.error(f"获取最大页数失败: {e}")
            return None
    
    def get_page_data(self, district: str) -> List[Dict[str, Any]]:
        """
        获取页面数据
        
        Args:
            district: 区域名称
            
        Returns:
            List[Dict[str, Any]]: 页面数据
        """
        page_data = []
        
        try:
            # 等待列表加载
            sell_list = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "listContent"))
            )
            
            # 获取所有房源项
            li_elements = sell_list.find_elements(By.TAG_NAME, "li")
            
            for estate in li_elements:
                try:
                    estate_data = self.extract_estate_data(estate, district)
                    if estate_data:
                        page_data.append(estate_data)
                except Exception as e:
                    self.logger.error(f"提取房源数据时出错: {e}")
                    continue
            
        except NoSuchElementException:
            self.logger.warning(f"当前页面 {self.driver.current_url} 下找不到房源列表")
        except Exception as e:
            self.logger.error(f"获取页面数据时出错: {e}")
        
        return page_data
    
    def extract_estate_data(self, estate_element, district: str) -> Optional[Dict[str, Any]]:
        """
        提取房源数据
        
        Args:
            estate_element: 房源元素
            district: 区域名称
            
        Returns:
            Optional[Dict[str, Any]]: 房源数据
        """
        try:
            # 获取房源信息容器
            estate_info = estate_element.find_element(By.XPATH, ".//*[contains(@class, 'info')]")
            
            # 获取房源名称
            try:
                name = estate_info.find_element(By.CLASS_NAME, "title").text
            except NoSuchElementException:
                self.logger.warning("获取房源名称失败")
                name = ''
            
            # 获取建筑特征
            try:
                estate_attribute = estate_info.find_element(By.CLASS_NAME, "address")
                estate_towards = estate_attribute.find_element(By.CLASS_NAME, "houseInfo").text
                estate_attribute_floor = estate_info.find_element(By.CLASS_NAME, "flood")
                estate_floor = estate_attribute_floor.find_element(By.CLASS_NAME, "positionInfo").text
            except NoSuchElementException:
                self.logger.warning("获取建筑特征失败")
                estate_towards = ''
                estate_floor = ''
            
            # 获取成交时间
            try:
                deal_date = estate_attribute.find_element(By.CLASS_NAME, "dealDate").text
                deal_date = pd.to_datetime(deal_date, format='%Y.%m.%d')
                
                # 检查日期是否在范围内
                min_date = pd.to_datetime(self.config["min_date"])
                if deal_date <= min_date:
                    return None
                    
            except NoSuchElementException:
                self.logger.warning("获取成交时间失败")
                return None
            
            # 获取价格信息
            try:
                unit_price = estate_attribute_floor.find_element(By.CLASS_NAME, "unitPrice").text
                total_price = estate_attribute.find_element(By.CLASS_NAME, "totalPrice").text
            except NoSuchElementException:
                self.logger.warning("获取价格信息失败")
                unit_price = ''
                total_price = ''
            
            # 构建数据项
            data_item = {
                '房源名称': name,
                '所在区域': district,
                '建筑特征': {
                    '装修及朝向': estate_towards,
                    '楼层及建筑类型': estate_floor
                },
                '成交时间': deal_date,
                '价格信息': {
                    '单价': unit_price,
                    '总价': total_price
                }
            }
            
            return data_item
            
        except Exception as e:
            self.logger.error(f"提取房源数据时出错: {e}")
            return None 