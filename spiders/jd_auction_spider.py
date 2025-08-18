# -*- coding: utf-8 -*-
"""
京东法拍房爬虫
"""
import re
import time
import random
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import pandas as pd
from typing import Dict, Any, Optional
import undetected_chromedriver as uc
from spiders.base_spider import BaseSpider
from utils.data_storage import DataStorage
from config import Config
import os
from datetime import datetime

class JDAuctionSpider(BaseSpider):
    """京东法拍房爬虫"""
    
    def __init__(self, start_page: int = 1, max_pages: int = None, province: str = None, city: str = None, cutoff_time: str = None, resume_from_archive: bool = False):
        """
        初始化京东法拍房爬虫
        
        Args:
            start_page: 开始页码
            max_pages: 最大爬取页数
            province: 要爬取的省份
            city: 要爬取的城市
            cutoff_time: 截止时间，格式为"YYYY年MM月DD日 HH:MM:SS"，当拍卖结束时间早于此时间时停止爬取
            resume_from_archive: 是否从存档恢复爬取
        """
        super().__init__("京东法拍房")
        self.start_page = start_page
        self.max_pages = max_pages or Config.JD_AUCTION_CONFIG["max_pages"]
        self.config = Config.JD_AUCTION_CONFIG
        self.cutoff_time = cutoff_time
        self.should_stop = False  # 控制爬取停止的标志
        self.resume_from_archive = resume_from_archive
        self.last_crawled_asset_name = None  # 存档中最后一条记录的资产名称
        self.should_start_crawling = True  # 是否开始正式爬取的标志
        
        # 设置省份和城市
        self.province = province
        self.city = city
        
        # 验证省份和城市是否有效
        self._validate_location()
        
        # 如果设置了截止时间，验证格式并记录
        if self.cutoff_time:
            self._validate_cutoff_time()
            self.logger.info(f"设置截止时间: {self.cutoff_time}")
        
        # 如果启用存档恢复，获取最后一条记录的资产名称
        if self.resume_from_archive:
            self.last_crawled_asset_name = self._get_last_asset_name_from_archive()
            if self.last_crawled_asset_name:
                self.should_start_crawling = False  # 需要先找到对应记录
                self.logger.info(f"启用存档恢复模式，最后爬取的资产名称: {self.last_crawled_asset_name}")
            else:
                self.logger.warning("未找到存档文件或存档文件为空，将从头开始爬取")
    
    def _validate_cutoff_time(self) -> None:
        """
        验证截止时间格式是否正确
        """
        try:
            self._parse_time_string(self.cutoff_time)
            self.logger.info(f"截止时间格式验证通过: {self.cutoff_time}")
        except ValueError as e:
            raise ValueError(f"截止时间格式错误: {e}。正确格式示例: '2024年01月01日 12:00:00'")
    
    def _parse_time_string(self, time_str: str) -> datetime:
        """
        解析时间字符串为datetime对象
        
        Args:
            time_str: 时间字符串，格式为"YYYY年MM月DD日 HH:MM:SS"
            
        Returns:
            datetime: 解析后的datetime对象
        """
        try:
            return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError(f"时间格式错误: {time_str}，正确格式: 'YYYY年MM月DD日 HH:MM:SS'")
    
    def _is_end_time_before_cutoff(self, end_time: str) -> bool:
        """
        检查结束时间是否早于截止时间
        
        Args:
            end_time: 拍卖结束时间字符串
            
        Returns:
            bool: 如果结束时间早于截止时间返回True，否则返回False
        """
        if not self.cutoff_time or not end_time:
            return False
        
        try:
            end_datetime = self._parse_time_string(end_time)
            cutoff_datetime = self._parse_time_string(self.cutoff_time)
            
            is_before = end_datetime < cutoff_datetime
            if is_before:
                self.logger.info(f"拍卖结束时间 {end_time} 早于截止时间 {self.cutoff_time}，准备停止爬取")
            
            return is_before
        except ValueError as e:
            self.logger.warning(f"时间比较失败: {e}")
            return False

    def _get_last_asset_name_from_archive(self) -> Optional[str]:
        """
        从存档文件中获取最后一条记录的资产名称
        
        Returns:
            Optional[str]: 最后一条记录的资产名称，如果没有找到则返回None
        """
        try:
            # 获取output目录下的所有xlsx文件
            output_dir = Config.OUTPUT_DIR
            xlsx_files = os.path.join(output_dir, "京东法拍房_数据_错误保存.xlsx")
            
            if not xlsx_files:
                self.logger.info("未找到任何xlsx存档文件")
                return None
            
            # 读取Excel文件
            df = pd.read_excel(xlsx_files)
            
            if df.empty:
                self.logger.info("存档文件为空")
                return None
            
            # 检查是否包含"资产名称"列
            if "资产名称" not in df.columns:
                self.logger.warning("存档文件中未找到'资产名称'列")
                return None
            
            # 获取最后一条记录的资产名称
            last_asset_name = df["资产名称"].iloc[-1]
            
            if pd.isna(last_asset_name) or str(last_asset_name).strip() == "":
                self.logger.warning("最后一条记录的资产名称为空")
                return None
            
            self.logger.info(f"从存档文件中读取到最后一条记录的资产名称: {last_asset_name}")
            return str(last_asset_name.split("】")[1]).strip()
            
        except Exception as e:
            self.logger.error(f"读取存档文件失败: {e}")
            return None

    def _validate_location(self) -> None:
        """
        验证省份和城市是否有效
        """
        available_provinces = list(self.config["province_xpath_mapping"].keys())
        if self.province not in available_provinces:
            raise ValueError(f"不支持的省份: {self.province}。支持的省份: {', '.join(available_provinces)}")
        
        available_cities = self.config["province_city_mapping"].get(self.province, [])
        if self.city and self.city not in available_cities:
            raise ValueError(f"省份 {self.province} 不支持城市 {self.city}。支持的城市: {', '.join(available_cities)}")
    
    def setup_driver(self) -> None:
        """
        设置浏览器驱动（使用undetected-chromedriver）
        """
        try:
            # 配置 undetected-chromedriver 选项
            options = uc.ChromeOptions()
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-extensions")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            
            # 创建 undetected-chromedriver 实例
            self.driver = uc.Chrome(options=options, version_main=None)
            self.logger.info("成功创建 undetected-chromedriver 浏览器实例")
            
        except Exception as e:
            self.logger.error(f"创建浏览器驱动失败: {e}")
            raise Exception(f"无法创建浏览器驱动: {e}")
    
    def run(self) -> None:
        """
        运行爬虫逻辑
        """
        try:
            # 设置浏览器驱动
            self.setup_driver()
            
            # 自动打开京东法拍页面
            self.wait_for_manual_page_open()
            
            # 等待手动登录
            self.wait_for_manual_login()
            
            # 选择地区
            self.select_location()
            
            # 开始爬取
            self.crawl_auction_data()
            
        except Exception as e:
            self.logger.error(f"爬取过程中出错: {e}")
            raise
        finally:
            # 关闭浏览器
            if hasattr(self, 'driver') and self.driver:
                try:
                    self.driver.quit()
                    self.logger.info("浏览器已关闭")
                except:
                    pass
    
    def wait_for_manual_page_open(self) -> None:
        """
        自动打开京东法拍页面
        """
        self.logger.info("=" * 50)
        self.logger.info("正在自动打开京东法拍页面...")
        self.logger.info(f"目标URL: {self.config['base_url']}")
        self.logger.info("=" * 50)
        
        try:
            # 直接导航到京东法拍页面
            self.driver.get(self.config['base_url'])
            
            # 等待页面加载完成
            self.logger.info("等待页面加载完成...")
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "province"))
            )
            
            # 增加额外等待，确保页面完全加载
            sleep(random.uniform(3, 5))
            
            self.logger.info("京东法拍页面加载完成，开始执行后续逻辑...")
            
        except Exception as e:
            self.logger.error(f"打开京东法拍页面失败: {e}")
            raise Exception(f"无法打开京东法拍页面: {e}")
    

    def wait_for_manual_login(self) -> None:
        """
        等待手动登录网站
        """
        self.logger.info("=" * 50)
        
        # 首先检查是否已经登录
        if self.check_login_status():
            self.logger.info("检测到已登录状态，无需重新登录")
            return
        
        self.logger.info("请手动登录京东法拍网站")
        self.logger.info("登录完成后，请按回车键继续...")
        self.logger.info("=" * 50)
        
        try:
            # 等待用户输入
            input("按回车键继续...")
            
            # 验证是否已登录
            if self.check_login_status():
                self.logger.info("登录验证完成，继续执行后续逻辑...")
            else:
                self.logger.warning("登录状态验证失败，请确认是否已正确登录")
                
        except KeyboardInterrupt:
            self.logger.info("用户中断操作")
            raise Exception("用户中断登录过程")
        except Exception as e:
            self.logger.error(f"等待登录过程中出错: {e}")
            raise
    
    def check_login_status(self) -> bool:
        """
        检查登录状态
        
        Returns:
            bool: 是否已登录
        """
        try:
            # 等待一段时间让页面稳定
            sleep(2)
            
            # 检查URL是否包含登录相关信息
            current_url = self.driver.current_url
            if "login" in current_url.lower() or "signin" in current_url.lower():
                return False
            
            # 检查页面中是否存在登录相关元素
            try:
                # 查找登录按钮或登录链接
                login_elements = self.driver.find_elements(By.XPATH, 
                    "//*[contains(text(), '登录') or contains(text(), '登录') or contains(@class, 'login')]")
                
                # 查找用户相关元素（如用户头像、用户名等）
                user_elements = self.driver.find_elements(By.XPATH, 
                    "//*[contains(@class, 'user') or contains(@class, 'avatar') or contains(@class, 'nickname')]")
                
                # 如果找到用户相关元素且没有登录按钮，认为已登录
                if user_elements and not login_elements:
                    self.logger.info("检测到用户相关元素，判断为已登录状态")
                    return True
                
                # 如果找到登录按钮，认为未登录
                if login_elements:
                    self.logger.info("检测到登录按钮，判断为未登录状态")
                    return False
                
                # 其他情况，尝试访问需要登录的页面来验证
                return self.verify_login_by_access()
                
            except Exception as e:
                self.logger.debug(f"检查登录状态时出错: {e}")
                return self.verify_login_by_access()
                
        except Exception as e:
            self.logger.debug(f"检查登录状态时出错: {e}")
            return False
    

    def verify_login_by_access(self) -> bool:
        """
        通过访问需要登录的页面来验证登录状态
        
        Returns:
            bool: 是否已登录
        """
        try:
            # 记录当前URL
            original_url = self.driver.current_url
            
            # 尝试访问一个需要登录的页面
            test_url = "https://pmsearch.jd.com/user/center"
            self.driver.get(test_url)
            sleep(3)
            
            # 检查是否被重定向到登录页面
            current_url = self.driver.current_url
            if "login" in current_url.lower() or "signin" in current_url.lower():
                self.logger.info("访问用户中心被重定向到登录页面，判断为未登录")
                # 回到原页面
                self.driver.get(original_url)
                return False
            
            # 检查页面内容是否包含用户信息
            page_source = self.driver.page_source
            if "用户中心" in page_source or "个人中心" in page_source:
                self.logger.info("成功访问用户中心，判断为已登录")
                # 回到原页面
                self.driver.get(original_url)
                return True
            
            # 回到原页面
            self.driver.get(original_url)
            return False
            
        except Exception as e:
            self.logger.debug(f"通过访问验证登录状态时出错: {e}")
            return False
    
    def handle_verification_popup(self) -> None:
        """
        处理验证弹窗（支持多种弹窗类型）
        """
        max_retries = 3
        popup_selectors = [
            # 基于类名的选择器（处理空格问题）
            "//div[contains(@class, 'alert-popup-button-confirm')]",
            # 基于文本内容的选择器（忽略前后空格）
            "//div[normalize-space(text())='我已知晓并同意']",
            # 组合选择器
            "//div[@class=' alert-popup-button-confirm']",
            # 更宽泛的选择器
            "//div[contains(@class, 'alert-popup-buttons')]//div[contains(text(), '我已知晓')]",
            # 基于父容器的选择器
            "//div[contains(@class, 'alert-popup-overlay')]//div[contains(text(), '我已知晓并同意')]"
        ]
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"检查验证弹窗 (第{attempt + 1}次)")
                
                # 首先检查弹窗是否存在
                popup_overlay = None
                try:
                    popup_overlay = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "alert-popup-overlay"))
                    )
                    self.logger.info("检测到验证弹窗")
                except:
                    self.logger.info("未检测到验证弹窗")
                    return
                
                # 等待弹窗完全加载
                sleep(random.uniform(1, 2))
                
                # 尝试不同的选择器找到确认按钮
                confirm_button = None
                for i, selector in enumerate(popup_selectors):
                    try:
                        self.logger.debug(f"尝试选择器 {i+1}: {selector}")
                        confirm_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        self.logger.info(f"使用选择器 {i+1} 成功找到确认按钮")
                        break
                    except:
                        continue
                
                if not confirm_button:
                    self.logger.warning("未找到可点击的确认按钮，尝试通过关闭按钮关闭弹窗")
                    try:
                        close_button = self.driver.find_element(By.CLASS_NAME, "alert-popup-close")
                        close_button.click()
                        self.logger.info("通过关闭按钮关闭了验证弹窗")
                        return
                    except:
                        self.logger.warning("也未找到关闭按钮")
                        if attempt < max_retries - 1:
                            continue
                        else:
                            self.logger.error("无法处理验证弹窗，继续执行...")
                            return
                
                # 模拟人类行为：先滚动到按钮位置
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", confirm_button)
                sleep(random.uniform(0.5, 1))
                
                # 模拟鼠标悬停
                ActionChains(self.driver).move_to_element(confirm_button).perform()
                sleep(random.uniform(0.3, 0.8))
                
                # 点击确认按钮
                confirm_button.click()
                self.logger.info("成功点击验证弹窗的确认按钮")
                
                # 等待弹窗消失
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.invisibility_of_element_located((By.CLASS_NAME, "alert-popup-overlay"))
                    )
                    self.logger.info("验证弹窗已消失")
                except:
                    self.logger.warning("验证弹窗可能未完全消失")
                
                # 额外等待，确保页面稳定
                sleep(random.uniform(1, 2))
                return
                
            except Exception as e:
                self.logger.warning(f"处理验证弹窗失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    sleep(random.uniform(2, 4))
        
        self.logger.error(f"处理验证弹窗失败，已重试 {max_retries} 次，继续执行...")
        
        # 尝试最后的兜底方案：按ESC键关闭弹窗
        try:
            from selenium.webdriver.common.keys import Keys
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            self.logger.info("尝试使用ESC键关闭弹窗")
            sleep(1)
        except:
            pass
    
    def verify_login_status(self) -> None:
        """
        验证登录状态（可选）
        """
        try:
            # 等待一段时间让页面稳定
            sleep(2)
        
            try:
                # 如果找到用户相关元素，说明可能已登录
                user_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'user') or contains(@class, 'login') or contains(@class, 'avatar')]")
                if user_elements:
                    self.logger.info("检测到可能的登录状态")
                else:
                    self.logger.warning("未检测到明显的登录状态，请确认是否已正确登录")
            except:
                self.logger.info("无法检测登录状态，请手动确认")
                
        except Exception as e:
            self.logger.debug(f"验证登录状态时出错: {e}")
            # 不抛出异常，因为这只是可选的验证
    
    def select_location(self) -> None:
        """
        选择地区（增加反反爬虫措施）
        """
        try:
            # 等待页面完全加载
            self.wait_for_page_load()
            
            # 选择省份
            self.select_province_with_retry()
            
            # 如果有城市选择，则选择城市
            if self.city:
                self.select_city_with_retry()
                self.logger.info(f"地区选择完成: {self.province}-{self.city}")
            else:
                self.logger.info(f"地区选择完成: {self.province}")
            
        except Exception as e:
            self.logger.error(f"选择地区失败: {e}")
            raise
    
    def wait_for_page_load(self) -> None:
        """
        等待页面完全加载
        """
        self.logger.info("等待页面完全加载...")
        # 随机等待时间，模拟人类行为
        sleep(random.uniform(2, 4))
        
        # 等待关键元素加载
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "province"))
            )
            self.logger.info("页面加载完成")
        except Exception as e:
            self.logger.warning(f"等待页面加载超时: {e}")
    
    def select_province_with_retry(self) -> None:
        """
        选择省份（带重试机制）
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.logger.info(f"尝试选择省份: {self.province} (第{attempt + 1}次)")
                
                # 记录当前页面的一些状态信息
                initial_url = self.driver.current_url
                
                # 模拟人类行为：先移动鼠标到省份元素附近
                province_element = self.driver.find_element(By.CLASS_NAME, "province")
                ActionChains(self.driver).move_to_element(province_element).perform()
                
                # 随机短暂延时
                sleep(random.uniform(0.5, 1.5))
                
                # 点击省份选择
                province_element.click()
                
                # 等待省份列表出现
                self.wait_for_dropdown_appear()
                
                # 选择具体省份
                province_xpath = self.config["province_xpath_mapping"][self.province]
                province_option = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, province_xpath))
                )
                
                # 模拟人类行为：先悬停再点击
                ActionChains(self.driver).move_to_element(province_option).perform()
                sleep(random.uniform(0.3, 0.8))
                province_option.click()
                
                # 验证省份选择是否生效
                if self.verify_province_selection():
                    self.logger.info(f"省份选择成功: {self.province}")
                    return
                else:
                    self.logger.warning(f"省份选择未生效，准备重试 (尝试 {attempt + 1}/{max_retries})")
                    
            except Exception as e:
                self.logger.warning(f"选择省份失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                
            # 重试前等待
            if attempt < max_retries - 1:
                sleep(random.uniform(2, 4))
        
        raise Exception(f"选择省份失败，已重试 {max_retries} 次")
    
    def select_city_with_retry(self) -> None:
        """
        选择城市（带重试机制）
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.logger.info(f"尝试选择城市: {self.city} (第{attempt + 1}次)")
                
                # 模拟人类行为：先移动鼠标到城市元素附近
                city_element = self.driver.find_element(By.CLASS_NAME, "city")
                ActionChains(self.driver).move_to_element(city_element).perform()
                
                # 随机短暂延时
                sleep(random.uniform(0.5, 1.5))
                
                # 点击城市选择
                city_element.click()
                
                # 等待城市列表出现
                self.wait_for_dropdown_appear()
                
                # 选择具体城市
                city_xpath = self.config["city_xpath_mapping"][self.city]
                city_option = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, city_xpath))
                )
                
                # 模拟人类行为：先悬停再点击
                ActionChains(self.driver).move_to_element(city_option).perform()
                sleep(random.uniform(0.3, 0.8))
                city_option.click()
                
                # 验证城市选择是否生效
                if self.verify_city_selection():
                    self.logger.info(f"城市选择成功: {self.city}")
                    return
                else:
                    self.logger.warning(f"城市选择未生效，准备重试 (尝试 {attempt + 1}/{max_retries})")
                    
            except Exception as e:
                self.logger.warning(f"选择城市失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                
            # 重试前等待
            if attempt < max_retries - 1:
                sleep(random.uniform(2, 4))
        
        raise Exception(f"选择城市失败，已重试 {max_retries} 次")
    
    def wait_for_dropdown_appear(self) -> None:
        """
        等待下拉菜单出现
        """
        sleep(random.uniform(1, 2))
        # 可以添加更具体的等待条件
    
    def verify_province_selection(self) -> bool:
        """
        验证省份选择是否生效
        """
        try:
            # 等待页面更新
            sleep(random.uniform(2, 4))
            
            # 检查URL是否发生变化
            current_url = self.driver.current_url
            if self.province.lower() in current_url.lower():
                return True
            
            # 检查页面元素变化
            try:
                province_element = self.driver.find_element(By.CLASS_NAME, "province")
                if self.province in province_element.text:
                    return True
            except:
                pass
            
            # 检查是否有新的列表项加载
            try:
                list_elements = self.driver.find_elements(By.XPATH, self.config["list_xpath"])
                if len(list_elements) > 0:
                    return True
            except:
                pass
            
            return False
            
        except Exception as e:
            self.logger.debug(f"验证省份选择时出错: {e}")
            return False
    
    def verify_city_selection(self) -> bool:
        """
        验证城市选择是否生效
        """
        try:
            # 等待页面更新
            sleep(random.uniform(2, 4))
            
            # 检查URL是否发生变化
            current_url = self.driver.current_url
            if self.city.lower() in current_url.lower():
                return True
            
            # 检查页面元素变化
            try:
                city_element = self.driver.find_element(By.CLASS_NAME, "city")
                if self.city in city_element.text:
                    return True
            except:
                pass
            
            # 检查是否有新的列表项加载
            try:
                list_elements = self.driver.find_elements(By.XPATH, self.config["list_xpath"])
                if len(list_elements) > 0:
                    return True
            except:
                pass
            
            return False
            
        except Exception as e:
            self.logger.debug(f"验证城市选择时出错: {e}")
            return False
    
    def crawl_auction_data(self) -> None:
        """
        爬取拍卖数据
        """
        page_no = int(self.driver.find_element(By.CLASS_NAME, "ui-pager-current").text)
        page_no = self.transfer_to_start_page(page_no, self.start_page)
        
        consecutive_failures = 0  # 连续失败次数
        max_consecutive_failures = 3  # 最大连续失败次数
        
        # 存档恢复模式的日志记录
        if self.resume_from_archive:
            if self.last_crawled_asset_name:
                self.logger.info(f"存档恢复模式启动，正在寻找资产名称: {self.last_crawled_asset_name}")
            else:
                self.logger.info("存档恢复模式启动，但未找到有效的存档数据，将从头开始爬取")
        
        while page_no <= self.max_pages and not self.should_stop:
            try:
                self.logger.info(f"正在爬取第 {page_no} 页")
                
                # 随机等待页面加载，模拟人类行为
                sleep(random.uniform(3, 6))
                
                # 获取列表项
                list_elements = self.driver.find_elements(By.XPATH, self.config["list_xpath"])
                if not list_elements:
                    self.logger.info("没有找到更多数据，爬取结束")
                    break
                
                self.logger.info(f"本页找到 {len(list_elements)} 个拍卖项")
                
                # 处理每个拍卖项
                success_count = 0
                for index, element in enumerate(list_elements):
                    try:
                        # 检查是否需要停止爬取
                        if self.should_stop:
                            self.logger.info("检测到停止信号，结束爬取")
                            break
                        
                        # 添加随机延时，避免操作过快
                        if index > 0:
                            sleep(random.uniform(1, 3))
                        
                        self.logger.info(f"正在处理第 {index + 1} 个拍卖项")
                        self.process_auction_item(element)
                        success_count += 1
                        
                        # 每处理几个项目后稍作休息
                        if (index + 1) % 5 == 0:
                            self.logger.info(f"已处理 {index + 1} 个项目，休息片刻...")
                            sleep(random.uniform(5, 10))
                        
                    except Exception as e:
                        self.logger.error(f"处理拍卖项 {index + 1} 时出错: {e}")
                        continue
                
                self.logger.info(f"第 {page_no} 页处理完成，成功处理 {success_count}/{len(list_elements)} 个拍卖项")
                
                # 如果因为时间截止而停止，退出循环
                if self.should_stop:
                    self.logger.info("达到时间截止条件，停止爬取")
                    break
                
                # 重置连续失败计数
                
                # 翻页
                target_page = page_no + 1
                new_page_no = self.transfer_to_start_page(page_no, target_page)
                
                if new_page_no != target_page:
                    self.logger.warning(f"翻页失败，目标页数: {target_page}，实际页数: {new_page_no}")
                    self.save_data()
                    return
                    
                else:
                    break
                page_no = new_page_no
                
            except Exception as e:
                self.logger.error(f"爬取第 {page_no} 页时出错: {e}")
                self.save_data()
                return
        
        # 爬取结束，保存数据
        self.logger.info("数据爬取完成，正在保存数据...")
        self.save_data()
    
    def process_auction_item(self, element) -> None:
        """
        处理单个拍卖项
        
        Args:
            element: 拍卖项元素
        """
        try:
            # 获取拍卖状态
            status_element = element.find_element(By.XPATH, ".//a/div[3]/div[1]")
            item_status = status_element.text
            
            # 只处理已结束的拍卖
            if item_status not in ['已结束', '已暂缓', '已中止']:
                return
            
            # 获取基本信息
            link = element.find_element(By.XPATH, ".//a").get_property("href")
            item_name = element.find_element(By.XPATH, ".//a/div[2]/div[1]").text
            image = element.find_element(By.XPATH, ".//a/div[1]/div/img").get_attribute('src')
            current_value = element.find_element(By.XPATH, ".//a/div[2]/div[2]/div[2]/em/b").text
            esti_value = element.find_element(By.XPATH, ".//a/div[2]/div[3]/div[1]/em").text

            # 如果启用了存档恢复模式，检查是否应该开始爬取
            if self.resume_from_archive and not self.should_start_crawling:
                if item_name == self.last_crawled_asset_name:
                    self.logger.info(f"找到存档中的最后一条记录: {item_name}，跳过该记录，从下一条开始爬取")
                    self.should_start_crawling = True
                    return  # 跳过这一条记录
                else:
                    self.logger.info(f"跳过记录: {item_name} (正在寻找: {self.last_crawled_asset_name})")
                    return  # 继续跳过，直到找到目标记录
            
            # 获取详细信息
            detail_info = self.get_auction_detail(link)
            if not detail_info:
                return
            current_asset_name = detail_info.get('资产名称', '')
            
            # 检查结束时间是否早于截止时间
            end_time = detail_info.get('结束时间', '')
            if self._is_end_time_before_cutoff(end_time):
                self.logger.info(f"拍卖项 '{current_asset_name}' 的结束时间早于截止时间，设置停止标志")
                self.should_stop = True
                # 仍然保存当前这一条数据，然后停止
            
            # 构建数据项
            data_item = {
                "资产名称": current_asset_name,
                "竞价状态": item_status,
                "结束时间": detail_info.get('结束时间', ''),
                "是否流拍": detail_info.get('是否流拍', ''),
                "流拍原因": detail_info.get('流拍原因', ''),
                "图片": image,
                "当前价": current_value,
                "评估价": esti_value,
                "围观人数": detail_info.get('围观人数', ''),
                "报名人数": detail_info.get('报名人数', ''),
                "关注提醒人数": detail_info.get('关注提醒人数', ''),
                "成交价": detail_info.get('成交价格', ''),
                "起拍价": detail_info.get('起拍价格', ''),
                "变卖价格": detail_info.get('变卖价格', ''),
                "加价幅度": detail_info.get('加价幅度', ''),
                "保证金": detail_info.get('保证金', ''),
                "竞价周期": detail_info.get('竞价周期', ''),
                "变卖周期": detail_info.get('变卖周期', ''),
                "延时周期": detail_info.get('延时周期', '')
            }
            
            self.add_data(data_item)
            self.logger.info(f"成功处理拍卖项: {current_asset_name}")
            
            # 如果设置了停止标志，提前返回
            if self.should_stop:
                return
            
        except Exception as e:
            self.logger.error(f"处理拍卖项时出错: {e}")
    
    def get_auction_detail(self, url: str) -> Optional[Dict[str, Any]]:
        """
        获取拍卖详情
        
        Args:
            url: 拍卖详情页URL
            
        Returns:
            Optional[Dict[str, Any]]: 详情信息
        """
        # 记录主窗口句柄
        main_window = self.driver.current_window_handle
        
        try:
            # 打开新窗口
            self.driver.execute_script(f"window.open('{url}', '_blank');")
            
            # 切换到新窗口
            all_windows = self.driver.window_handles
            for window in all_windows:
                if window != main_window:
                    self.driver.switch_to.window(window)
                    break
            
            # 等待页面加载
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # 处理验证弹窗
            self.handle_verification_popup()
            
            # 获取详细信息
            detail_info = self.extract_detail_info()
            
            # 下载附件和图片
            self.download_attachments(detail_info.get('资产名称', ''))

            # 获取标的物调查表
            self.extract_property_survey_table(detail_info.get('资产名称', ''))

            # 获取竞买公告和竞买须知
            self.extract_notice_info(detail_info.get('资产名称', ''))

            # 获取竞价记录
            self.extract_bidding_info(detail_info.get('资产名称', ''))

            # 获取优先购买权人
            self.extract_priority_purchaser(detail_info.get('资产名称', ''))

            return detail_info
            
        except Exception as e:
            self.logger.error(f"获取拍卖详情失败: {e}")
            return None
        finally:
            # 关闭新窗口，回到主窗口
            self.driver.close()
            self.driver.switch_to.window(main_window)
    
    def extract_detail_info(self) -> Dict[str, Any]:
        """
        提取详情信息
        
        Returns:
            Dict[str, Any]: 详情信息
        """
        try:
            # 获取标题
            name = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pm-name"))
            ).text
            
            # 获取成交价格
            try:
                final_price = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[@id='pageContainer']/div[2]/div[1]/div[2]/div[3]/div[3]/div[1]/div/div[2]"))
                ).text
            except:
                final_price = ''
            
            # 获取流拍信息
            bidding_result = self.driver.find_element(By.XPATH, "//*[@id='pageContainer']/div[2]/div[1]/div[2]/div[3]/div[1]/div[1]/div").text
            if '流拍' in bidding_result:
                if_unsold = '是'
                unsold_reason = '本标的物已流拍'
            else:
                if_unsold = '否'
                unsold_reason = ''
            
            # 获取其他信息
            info_html = self.driver.find_element(By.XPATH, "//*[@id='pageContainer']/div[2]/div[1]/div[2]/div[3]/div[1]/div[2]/div").text
            
            # 使用正则表达式提取信息
            end_time_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', info_html)
            end_time = end_time_match.group(0) if end_time_match else ''
            
            watched_match = re.search(r'(\d+)人围观', info_html)
            watched_times = watched_match.group(1) if watched_match else ''
            
            signin_match = re.search(r'(\d+)人报名', info_html)
            signin_times = signin_match.group(1) if signin_match else ''
            
            attention_match = re.search(r'(\d+)人关注', info_html)
            attention_times = attention_match.group(1) if attention_match else ''
            
            bidding_info = self.driver.find_element(By.XPATH, "//*[@id='pageContainer']/div[2]/div[1]/div[2]/div[4]/div[2]/div/div[1]/div/ul").text #竞价信息
            bidding_info = bidding_info.replace(',', '')
            make_up_match = re.search(r'加价幅度：\n￥\n(\d+)\n', bidding_info)
            make_up = make_up_match.group(1) if make_up_match else ''
            delay_cycle_match = re.search(r'延时周期：\n(\d+)分钟/次\n', bidding_info)
            delay_cycle = delay_cycle_match.group(1) if delay_cycle_match else ''
            # 判断是否为变卖
            if '变卖' in name:
                sell_off_price_match = re.search(r'变卖价：\n￥\n(\d+)\n', bidding_info)
                sell_off_price = sell_off_price_match.group(1) if sell_off_price_match else ''
                sell_off_cycle_match = re.search(r'变卖周期：\n(\d+)天\n', bidding_info)
                sell_off_cycle = sell_off_cycle_match.group(1) if sell_off_cycle_match else ''
                
                return {
                    '资产名称': name, '结束时间': end_time, '是否流拍': if_unsold, '流拍原因': unsold_reason,
                    '围观人数': watched_times, '报名人数': signin_times, '关注提醒人数': attention_times,
                    "成交价格": final_price, '起拍价格': '', '变卖价格': sell_off_price,
                    '加价幅度': make_up, '保证金': '', '竞价周期': '', '变卖周期': sell_off_cycle, '延时周期': delay_cycle
                }
            else:
                start_price_match = re.search(r'起拍价：\n￥\n(\d+)\n', bidding_info)
                start_price = start_price_match.group(1) if start_price_match else ''
                margin_match = re.search(r'保证金：\n￥\n(\d+)\n', bidding_info)
                margin = margin_match.group(1) if margin_match else ''
                bidding_cycle_match = re.search(r'竞价周期：\n(\d+)天\n', bidding_info)
                bidding_cycle = bidding_cycle_match.group(1) if bidding_cycle_match else ''
                
                return {
                    '资产名称': name, '结束时间': end_time, '是否流拍': if_unsold, '流拍原因': unsold_reason,
                    '围观人数': watched_times, '报名人数': signin_times, '关注提醒人数': attention_times,
                    "成交价格": final_price, '起拍价格': start_price, '变卖价格': '',
                    '加价幅度': make_up, '保证金': margin, '竞价周期': bidding_cycle, '变卖周期': '', '延时周期': delay_cycle
                }
                
        except Exception as e:
            self.logger.error(f"提取详情信息失败: {e}")
            return {}
    def extract_property_survey_table(self, asset_name: str) -> None:
        """
        提取标的物调查表
        
        Args:
            asset_name: 资产名称
        """
        if not asset_name:
            return
        
        try:
            # 创建文件夹
            folder_path = self.data_storage.create_folder(f"京东法拍/{asset_name}")
            
            # 提取标的物调查表
            try:
                table_content = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f"//*[@id='pmMainFloor']/ul/li[1]/div[2]/div"))
                )
                table_html = table_content.get_attribute('outerHTML')
                soup = BeautifulSoup(table_html, 'lxml')
                tables = soup.find_all('table')
                if tables:
                    table = tables[0]
                    df = pd.read_html(str(table))[0]
                    file_path = os.path.join(folder_path, "拍卖标的物调查情况表（房产）.xlsx")
                    df.to_excel(file_path, index=False)
                    self.logger.info(f"标的物调查表已保存到: {file_path}")
                else:
                    self.logger.info("未找到表格内容")
            except Exception as e:
                self.logger.info("未找到表格内容")
                
        except Exception as e:
            self.logger.error(f"提取标的物调查表失败: {e}")
    def download_attachments(self, asset_name: str) -> None:
        """
        下载附件和图片
        
        Args:
            asset_name: 资产名称
        """
        if not asset_name:
            return
        
        try:
            # 创建文件夹
            folder_path = self.data_storage.create_folder(f"京东法拍/{asset_name}")
            
            # # 检查是否有配资服务
            # try:
            #     self.driver.find_element(By.CLASS_NAME, "pm-pzfw")
            #     third_div = '6'
            # except:
            #     third_div = '5'
            
            # 下载PDF文件
            try:
                file_list = self.driver.find_elements(By.XPATH, f"//*[@id='pmMainFloor']/ul/li[1]/div[1]/div/div/div[1]/ul/li")
                for file in file_list:
                    file_url = file.find_element(By.XPATH, ".//*[@id='openAttachmentTag']").get_property("href")
                    file_name = file.find_element(By.XPATH, ".//*[@id='openAttachmentTag']").text
                    file_path = os.path.join(folder_path, file_name)
                    self.data_storage.download_file(file_url, file_path)
            except:
                pass
            
            # 下载图片
            try:
                img_list = self.driver.find_elements(By.XPATH, f"//*[@id='pmMainFloor']/ul/li[1]/div[2]/a")
                for i, img in enumerate(img_list):
                    img_url = img.get_attribute('href')
                    img_path = os.path.join(folder_path, f"{i}.jpg")
                    self.data_storage.download_file(img_url, img_path)
            except:
                pass
                
        except Exception as e:
            self.logger.error(f"下载附件失败: {e}")

    def extract_notice_info(self, asset_name: str = None):
        """
        提取竞买公告和竞买须知
        
        Args:
            asset_name: 资产名称，用于创建文件夹
            
        """
        if not asset_name:
            return

        try:
            find_floors = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='pmMainFloor']/ul"))
            )

            find_notice = find_floors.find_element(By.XPATH, "./li[2]")
            find_rule = find_floors.find_element(By.XPATH, "./li[3]")

            notice_content = find_notice.find_element(By.XPATH, "./div[2]")
            html_content = notice_content.get_attribute('outerHTML')
            html_content = BeautifulSoup(html_content, 'lxml')
            note_content = html_content.get_text(separator='\n', strip=True)

            rule_content = find_rule.find_element(By.XPATH, "./div")
            html_content = rule_content.get_attribute('outerHTML')
            html_content = BeautifulSoup(html_content, 'lxml')
            instruction_content = html_content.get_text(separator='\n', strip=True)

            result = {"Bidding Notice": [note_content], "Instructions for Bidding": [instruction_content]}
            
            # 如果有资产名称，保存到Excel文件
            if asset_name:
                folder_path = self.data_storage.create_folder(f"京东法拍/{asset_name}")
                file_path = os.path.join(folder_path, "竞买公告和竞买须知.xlsx")
                pd.DataFrame(result).to_excel(file_path, index=False)
                self.logger.info(f"竞买公告和竞买须知已保存到: {file_path}")                
        except Exception as e:
            self.logger.error(f"提取竞买公告和竞买须知失败: {e}")

    def extract_bidding_info(self, asset_name: str = None):
        """
        提取竞价记录信息
        
        Args:
            asset_name: 资产名称，用于创建文件夹
        """
        if not asset_name:
            return
            
        try:
            # 查找竞价记录区域
            bidding_record = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'floor') and contains(@class, 'floor-bid')]"))
            )
            
            bidding_records = []
            
            while True:
                try:
                    # 获取当前页面的竞价记录
                    table_content = bidding_record.get_attribute('outerHTML')
                    soup = BeautifulSoup(table_content, 'lxml')
                    bidding_list = soup.find('tbody').find_all('tr')

                    for row in bidding_list:
                        columns = row.find_all('td')
                        if len(columns) >= 4:
                            status = columns[0].get_text(strip=True)
                            bidding_code = columns[1].get_text(strip=True)
                            price = columns[2].get_text(strip=True)
                            bidding_time = columns[3].get_text(strip=True)
                            
                            bidding_records.append({
                                "状态": status,
                                "价格": price,
                                "竞拍人": bidding_code,
                                "时间": bidding_time
                            })

                    # 尝试查找下一页按钮
                    try:
                        bidding_pager = self.driver.find_element(By.CLASS_NAME, "index_ui_pager__x0-LU")
                        
                        next_button = bidding_pager.find_element(By.CLASS_NAME, "index_ui_pager_next__Rqo9l ")
                        
                        # 检查下一页按钮是否可用
                        if "index_disabled__bPJgO" in next_button.get_attribute('class'):
                            self.logger.info("已到达竞价记录最后一页")
                            break
                            
                    except Exception as e:
                        self.logger.info("无下一页信息或已到达最后一页")
                        break

                    # 点击下一页
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(next_button)).click()
                        sleep(random.uniform(2, 4))  # 随机等待时间
                        self.logger.info("正在查找下一页出价信息...")
                    except Exception as e:
                        self.logger.warning(f"翻页失败: {e}")
                        break
                        
                except Exception as e:
                    self.logger.error(f"处理竞价记录页面时出错: {e}")
                    break

            # 保存竞价记录到Excel文件
            if bidding_records:
                folder_path = self.data_storage.create_folder(f"京东法拍/{asset_name}")
                file_path = os.path.join(folder_path, "出价记录.xlsx")
                bidding_df = pd.DataFrame(bidding_records)
                bidding_df.to_excel(file_path, index=False)
                self.logger.info(f"竞价记录已保存到: {file_path}，共 {len(bidding_records)} 条记录")
            else:
                self.logger.info("未找到竞价记录")
                
        except Exception as e:
            self.logger.error(f"提取竞价记录失败: {e}")

    def extract_priority_purchaser(self, asset_name: str = None):
        """
        提取优先购买权人
        
        Args:
            asset_name: 资产名称，用于创建文件夹
        """
        if not asset_name:
            return
        
        try:
            # 查找优先购买权人区域
            priority_purchase = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "purchaserList"))
            )
            
            # 获取优先购买权人的HTML内容
            people_content = priority_purchase.get_attribute('outerHTML')
            people_content = BeautifulSoup(people_content, 'lxml')
            purchasers = people_content.find_all('table')

            if purchasers:
                # 获取第一个表格（通常只有一个优先购买权人表格）
                purchaser = purchasers[0]
                
                # 使用pandas读取HTML表格
                df = pd.read_html(str(purchaser))[0]
                
                # 保存到Excel文件
                folder_path = self.data_storage.create_folder(f"京东法拍/{asset_name}")
                file_path = os.path.join(folder_path, "优先购买权人.xlsx")
                df.to_excel(file_path, index=False)
                
                self.logger.info(f"优先购买权人信息已保存到: {file_path}")
                self.logger.info(f"共找到 {len(df)} 条优先购买权人记录")
            else:
                self.logger.info("未找到优先购买权人表格")

        except Exception as e:
            self.logger.info("未找到优先购买权人信息")
            self.logger.debug(f"提取优先购买权人失败: {e}")

    def transfer_to_start_page(self, current_page: int, target_page: int) -> int:
        """
        跳转到指定页面
        
        Args:
            current_page: 当前页码
            target_page: 目标页码
            
        Returns:
            int: 实际到达的页码
        """
        consecutive_failures = 0
        while consecutive_failures < 3 and current_page < target_page:
            try:
                current_page = int(self.driver.find_element(By.CLASS_NAME, "ui-pager-current").text)
                
                # 查找下一页按钮
                next_button = self.driver.find_element(By.CLASS_NAME, "ui-pager-next")
                
                # 模拟人类行为：先滚动到按钮位置
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                sleep(random.uniform(1, 2))
                
                # 模拟鼠标悬停
                ActionChains(self.driver).move_to_element(next_button).perform()
                sleep(random.uniform(0.5, 1))
                
                # 点击下一页
                next_button.click()
                
                transferred_page = int(self.driver.find_element(By.CLASS_NAME, "ui-pager-current").text)

                if transferred_page == current_page + 1:
                    current_page += 1
                    self.logger.info(f"成功跳转到第 {current_page} 页")
                    consecutive_failures = 0
                else:
                    self.logger.warning(f"跳转页面失败，当前页码: {current_page}，目标页码: {target_page}")
                    consecutive_failures += 1
                    
            except Exception as e:
                self.logger.error(f"跳转页面失败: {e}")
                break
        
        return current_page
    
    def get_page_content_signature(self) -> str:
        """
        获取页面内容签名，用于检测页面是否发生变化
        
        Returns:
            str: 页面内容的签名
        """
        try:
            # 获取列表项的数量和部分内容作为签名
            list_elements = self.driver.find_elements(By.XPATH, self.config["list_xpath"])
            if not list_elements:
                return ""
            
            # 取前几个元素的文本作为签名
            signature_parts = []
            for i, element in enumerate(list_elements[:3]):  # 只取前3个元素
                try:
                    text = element.text[:50]  # 只取前50个字符
                    signature_parts.append(text)
                except:
                    signature_parts.append(f"element_{i}")
            
            return "|".join(signature_parts)
            
        except Exception as e:
            self.logger.debug(f"获取页面签名失败: {e}")
            return ""
    
    def wait_for_page_change(self, initial_signature: str, max_wait: int = 15) -> bool:
        """
        等待页面内容发生变化
        
        Args:
            initial_signature: 初始页面签名
            max_wait: 最大等待时间（秒）
            
        Returns:
            bool: 页面是否发生变化
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                # 等待一段时间再检查
                sleep(random.uniform(1, 2))
                
                # 获取当前页面签名
                current_signature = self.get_page_content_signature()
                
                # 检查页面是否发生变化
                if current_signature and current_signature != initial_signature:
                    self.logger.debug("检测到页面内容发生变化")
                    return True
                    
            except Exception as e:
                self.logger.debug(f"等待页面变化时出错: {e}")
                
        self.logger.warning(f"等待页面变化超时 ({max_wait} 秒)")
        return False 