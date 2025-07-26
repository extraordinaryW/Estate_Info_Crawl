# -*- coding: utf-8 -*-
"""
主程序入口
"""
import argparse
import sys
from typing import List
from spiders.jd_auction_spider import JDAuctionSpider
from spiders.lianjia_spider import LianjiaSpider
from config import Config

def run_jd_auction_spider(start_page: int = 1, max_pages: int = None, province: str = None, city: str = None, cutoff_time: str = None) -> None:
    """
    运行京东法拍房爬虫
    
    Args:
        start_page: 开始页码
        max_pages: 最大爬取页数
        province: 要爬取的省份
        city: 要爬取的城市
        cutoff_time: 截止时间，格式为"YYYY年MM月DD日 HH:MM:SS"
    """
    print("=" * 50)
    print("京东法拍房爬虫")
    print("=" * 50)
    print("使用说明：")
    print("1. 请先启动Chrome调试模式：")
    print(f"   chrome.exe --remote-debugging-port={Config.JD_AUCTION_CONFIG['debug_port']} --user-data-dir=\"你的用户数据目录\"")
    print("2. 在打开的浏览器中访问京东法拍网站并登录")
    print("3. 然后运行此程序")
    print("=" * 50)
    
    spider = JDAuctionSpider(start_page=start_page, max_pages=max_pages, province=province, city=city, cutoff_time=cutoff_time)
    spider.start()

def run_lianjia_spider(districts: List[str] = None, max_pages: int = None) -> None:
    """
    运行链家二手房爬虫
    
    Args:
        districts: 要爬取的区域列表
        max_pages: 每个区域最大爬取页数
    """
    print("=" * 50)
    print("链家二手房爬虫")
    print("=" * 50)
    print("使用说明：")
    print("1. 程序会自动打开浏览器")
    print("2. 请在浏览器中完成链家网站的登录")
    print("3. 登录完成后按回车键继续")
    print("=" * 50)
    
    spider = LianjiaSpider(districts=districts, max_pages=max_pages)
    spider.start()

def show_available_districts() -> None:
    """
    显示可用的区域
    """
    print("可用的深圳区域：")
    for district, sub_districts in Config.SHENZHEN_DISTRICTS.items():
        print(f"  {district}: {', '.join(sub_districts[:5])}{'...' if len(sub_districts) > 5 else ''}")

def show_available_provinces_cities() -> None:
    """
    显示可用的省份和城市
    """
    print("京东法拍房可用的省份和城市：")
    for province, cities in Config.JD_AUCTION_CONFIG["province_city_mapping"].items():
        if cities:
            print(f"  {province}: {', '.join(cities)}")
        else:
            print(f"  {province}: 仅支持省份级别")

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description="房产信息爬虫")
    parser.add_argument("--spider", choices=["jd", "lianjia", "both"], default=None, # 调试
                       help="选择要运行的爬虫: jd(京东法拍房), lianjia(链家二手房), both(两个都运行)")
    
    # 京东法拍房参数
    parser.add_argument("--jd-start-page", type=int, default=None,
                       help="京东法拍房开始页码 (默认: 1)")
    parser.add_argument("--jd-max-pages", type=int, default=None,
                       help="京东法拍房最大爬取页数")
    parser.add_argument("--jd-province", type=str, default=None, # 调试
                       help="京东法拍房要爬取的省份")
    parser.add_argument("--jd-city", type=str, default=None, # 调试 
                       help="京东法拍房要爬取的城市")
    parser.add_argument("--jd-cutoff-time", type=str, default=None,
                       help="京东法拍房截止时间，格式为'YYYY年MM月DD日 HH:MM:SS'，当拍卖结束时间早于此时间时停止爬取")
    
    # 链家二手房参数
    parser.add_argument("--lianjia-districts", nargs="+", default=None,
                       help="链家二手房要爬取的区域列表")
    parser.add_argument("--lianjia-max-pages", type=int, default=None,
                       help="链家二手房每个区域最大爬取页数")
    
    # 其他参数
    parser.add_argument("--show-districts", action="store_true",
                       help="显示可用的深圳区域")
    parser.add_argument("--show-provinces", action="store_true",
                       help="显示京东法拍房可用的省份和城市")
    
    args = parser.parse_args()
    
    # 显示可用区域
    if args.show_districts:
        show_available_districts()
        return
    
    # 显示可用省份和城市
    if args.show_provinces:
        show_available_provinces_cities()
        return
    
    try:
        if args.spider in ["jd", "both"]:
            run_jd_auction_spider(
                start_page=args.jd_start_page,
                max_pages=args.jd_max_pages,
                province=args.jd_province,
                city=args.jd_city,
                cutoff_time=args.jd_cutoff_time
            )
        
        if args.spider in ["lianjia", "both"]:
            run_lianjia_spider(
                districts=args.lianjia_districts,
                max_pages=args.lianjia_max_pages
            )
            
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"程序运行出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 