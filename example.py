# -*- coding: utf-8 -*-
"""
使用示例脚本
演示如何使用房产信息爬虫项目
"""
from spiders.jd_auction_spider import JDAuctionSpider
from spiders.lianjia_spider import LianjiaSpider
from config import Config

def example_jd_auction():
    """
    京东法拍房爬虫使用示例
    """
    print("京东法拍房爬虫示例")
    print("=" * 30)
    
    # 创建爬虫实例
    spider = JDAuctionSpider(
        start_page=1,      # 从第1页开始
        max_pages=2        # 最多爬取2页
    )
    
    # 运行爬虫
    spider.start()
    
    # 获取爬取的数据
    data = spider.get_data()
    print(f"共爬取到 {len(data)} 条数据")

def example_lianjia():
    """
    链家二手房爬虫使用示例
    """
    print("\n链家二手房爬虫示例")
    print("=" * 30)
    
    # 创建爬虫实例，只爬取南山区和福田区
    spider = LianjiaSpider(
        districts=['南山区', '福田区'],
        max_pages=1  # 每个区域最多爬取1页
    )
    
    # 运行爬虫
    spider.start()
    
    # 获取爬取的数据
    data = spider.get_data()
    print(f"共爬取到 {len(data)} 条数据")

def example_custom_config():
    """
    自定义配置示例
    """
    print("\n自定义配置示例")
    print("=" * 30)
    
    # 修改配置（在实际使用中，建议直接修改config.py文件）
    Config.LIANJIA_CONFIG["max_pages"] = 3
    Config.LIANJIA_CONFIG["sleep_range"] = (2, 5)
    
    # 创建爬虫实例
    spider = LianjiaSpider(
        districts=['罗湖区'],  # 只爬取罗湖区
        max_pages=2
    )
    
    # 运行爬虫
    spider.start()

if __name__ == "__main__":
    print("房产信息爬虫项目使用示例")
    print("=" * 50)
    
    # 注意：这些示例需要相应的环境准备
    # 1. 京东法拍房需要先启动Chrome调试模式
    # 2. 链家二手房需要手动登录
    
    choice = input("请选择要运行的示例 (1: 京东法拍房, 2: 链家二手房, 3: 自定义配置, 0: 退出): ")
    
    if choice == "1":
        example_jd_auction()
    elif choice == "2":
        example_lianjia()
    elif choice == "3":
        example_custom_config()
    elif choice == "0":
        print("退出程序")
    else:
        print("无效选择") 