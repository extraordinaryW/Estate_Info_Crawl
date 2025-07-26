# -*- coding: utf-8 -*-
"""
浏览器工具模块
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional
from config import Config

class BrowserManager:
    """浏览器管理器"""
    
    @staticmethod
    def create_normal_driver() -> webdriver.Chrome:
        """
        创建普通Chrome浏览器驱动
        
        Returns:
            webdriver.Chrome: Chrome浏览器驱动
        """
        options = Options()
        config = Config.BROWSER_CONFIG
        
        # 设置用户代理
        options.add_argument(f"user-agent={config['user_agent']}")
        
        # 设置窗口大小
        options.add_argument(f"--window-size={config['window_size'][0]},{config['window_size'][1]}")
        
        # 其他设置
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 无头模式
        if config["headless"]:
            options.add_argument("--headless")
        
        # 创建驱动
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # 设置超时时间
        driver.implicitly_wait(config["implicit_wait"])
        driver.set_page_load_timeout(config["page_load_timeout"])
        driver.set_script_timeout(config["script_timeout"])
        
        return driver
    
    @staticmethod
    def create_debug_driver(debug_address: str = None) -> Optional[webdriver.Chrome]:
        """
        创建调试模式Chrome浏览器驱动
        
        Args:
            debug_address: 调试地址，格式为 "127.0.0.1:9222"
            
        Returns:
            Optional[webdriver.Chrome]: Chrome浏览器驱动，失败返回None
        """
        if debug_address is None:
            debug_address = Config.JD_AUCTION_CONFIG["debug_address"]
        
        try:
            options = Options()
            options.add_experimental_option("debuggerAddress", debug_address)
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-extensions")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-automation")
            options.add_argument("--disable-infobars")
            
            # 添加反反爬虫脚本
            driver = webdriver.Chrome(options=options)
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
            })
            return driver
        except Exception as e:
            print(f"连接调试浏览器失败: {e}")
            print("请确保已启动Chrome调试模式:")
            print(f"chrome.exe --remote-debugging-port=9222 --user-data-dir=\"你的用户数据目录\"")
            return None
    
    @staticmethod
    def create_user_data_driver(user_data_dir: str = None, profile_name: str = None) -> webdriver.Chrome:
        """
        创建带用户数据目录的Chrome浏览器驱动（用于记住登录信息）
        
        Args:
            user_data_dir: 用户数据目录路径
            profile_name: 配置文件名称
            
        Returns:
            webdriver.Chrome: Chrome浏览器驱动
        """
        if user_data_dir is None:
            user_data_dir = Config.JD_AUCTION_CONFIG["user_data_dir"]
        if profile_name is None:
            profile_name = Config.JD_AUCTION_CONFIG["profile_name"]
        
        # 确保用户数据目录存在
        import os
        os.makedirs(user_data_dir, exist_ok=True)
        
        options = Options()
        config = Config.BROWSER_CONFIG
        
        # 设置用户数据目录
        options.add_argument(f"--user-data-dir={user_data_dir}")
        if profile_name:
            options.add_argument(f"--profile-directory={profile_name}")
        
        # 设置用户代理
        options.add_argument(f"user-agent={config['user_agent']}")
        
        # 设置窗口大小
        options.add_argument(f"--window-size={config['window_size'][0]},{config['window_size'][1]}")
        
        # 其他设置
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 无头模式
        if config["headless"]:
            options.add_argument("--headless")
        
        # 创建驱动
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # 设置超时时间
        driver.implicitly_wait(config["implicit_wait"])
        driver.set_page_load_timeout(config["page_load_timeout"])
        driver.set_script_timeout(config["script_timeout"])
        
        # 添加反反爬虫脚本
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })
        
        return driver
    
    @staticmethod
    def close_driver(driver: webdriver.Chrome) -> None:
        """
        关闭浏览器驱动
        
        Args:
            driver: 浏览器驱动
        """
        try:
            if driver:
                driver.quit()
        except Exception as e:
            print(f"关闭浏览器时出错: {e}") 