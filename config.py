# -*- coding: utf-8 -*-
"""
配置文件
统一管理爬虫项目的所有配置参数
"""
import os
from typing import Dict, List, Any

class Config:
    """配置类"""
    
    # 基础配置
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    OUTPUT_DIR = os.path.join(BASE_DIR, "output")
    
    # 确保目录存在
    for dir_path in [DATA_DIR, LOG_DIR, OUTPUT_DIR]:
        os.makedirs(dir_path, exist_ok=True)
    
    # 日志配置
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    # 浏览器配置
    BROWSER_CONFIG = {
        "headless": False,  # 是否无头模式
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "window_size": (1920, 1080),
        "implicit_wait": 10,
        "page_load_timeout": 30,
        "script_timeout": 30
    }
    # 京东法拍房配置
    JD_AUCTION_CONFIG = {
        "base_url": "https://pmsearch.jd.com/?publishSource=7&childrenCateId=12728",
        "debug_port": 9222,
        "debug_address": "127.0.0.1:9222",
        # 省份XPath映射
        "province_xpath_mapping": {
            "gd": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl/dd/a[20]",
            "zj": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl[1]/dd/a[16]",
            "bj": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl[1]/dd/a[2]",
            "sh": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl[1]/dd/a[3]",
            "sc": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl[1]/dd/a[23]",
            "hb": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl[1]/dd/a[18]"
        },
        # 城市XPath映射
        "city_xpath_mapping": {
            "sz": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl[2]/dd/a[3]",
            "hz": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl[2]/dd/a[3]",
            "cd": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl[2]/dd/a[2]",
            "wh": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl[2]/dd/a[2]"
        },
        # 省份对应的城市列表
        "province_city_mapping": {
            "gd": ["sz"],
            "zj": ["hz"],
            "bj": [],
            "sh": [],
            "sc": ["cd"],
            "hb": ["wh"]
        },
        # 默认选择的省份和城市
        "default_province": "gd",
        "default_city": "sz",
        # 保留原有的XPath配置（向后兼容）
        "province_xpath_guangdong": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl/dd/a[20]",  # 广东
        "city_xpath_shenzhen": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl[2]/dd/a[3]",  # 深圳
        "province_xpath_zhejiang": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl[1]/dd/a[16]",  # 浙江
        "city_xpath_hangzhou": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl[2]/dd/a[3]",  # 杭州
        "province_xpath_beijing": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl[1]/dd/a[2]",  # 北京
        "province_xpath_shanghai": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl[1]/dd/a[3]",  # 上海
        "province_xpath_sichuan": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl[1]/dd/a[23]",  # 四川
        "city_xpath_chengdu": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl[2]/dd/a[2]",  # 成都
        "province_xpath_hubei": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl[1]/dd/a[18]",  # 湖北
        "city_xpath_wuhan": "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl[2]/dd/a[2]",  # 武汉
        "list_xpath": "//*[@id='root']/div/div/div[4]/ul/li",
        "max_pages": 9999,
        "sleep_time": 5,
        "output_filename": "京东法拍房数据.xlsx"
    }
    
    # 链家二手房配置
    LIANJIA_CONFIG = {
        "base_url": "https://sz.lianjia.com/chengjiao",
        "max_pages": 100,
        "sleep_range": (1, 3),
        "output_filename": "链家二手房数据.xlsx",
        "min_date": "2017-01-01"  # 最早爬取日期
    }
    
    # 深圳区域配置
    SHENZHEN_DISTRICTS = {
        '罗湖区': ['百仕达', '布心', '春风路', '翠竹', '地王', '东门', '洪湖', '黄贝岭', '黄木岗', '莲塘', '罗湖口岸', '螺岭', '清水河', '笋岗', '万象城', '新秀', '银湖'],
        '福田区': ['八卦岭', '百花', '车公庙', '赤尾', '福田保税区', '福田中心', '皇岗', '黄木岗', '华强北', '华强南', '景田', '莲花', '梅林', '上步', '上下沙', '沙尾', '石厦', '香梅北', '香蜜湖', '新洲', '银湖', '园岭', '竹子林'],
        '南山区': ['白石洲', '大学城', '红树湾', '后海', '华侨城', '科技园', '南山中心', '南头', '前海', '蛇口', '深圳湾', '西丽'],
        '盐田区': ['梅沙', '沙头角', '盐田港'],
        '宝安区': ['宝安中心', '碧海', '翻身', '福永', '航城', '沙井', '石岩', '松岗', '桃源居', '曦城', '新安', '西乡'],
        '龙岗区': ['布吉大芬', '布吉关', '布吉街', '布吉南岭', '布吉石芽岭', '布吉水径', '丹竹头', '大运新城', '横岗', '龙岗宝荷', '龙岗双龙', '龙岗中心城', '坪地', '平湖'],
        '龙华区': ['坂田', '观澜', '红山', '龙华新区', '龙华中心', '梅林关', '民治', '上塘'],
        '光明区': ['公明', '光明'],
        '坪山区': ['坪山'],
        '大鹏新区': ['大鹏半岛']
    }

    # 杭州区域配置
    HANGZHOU_DISTRICTS = {

    }
    
    # 区域英文映射
    DISTRICT_EN_MAPPING = {
        "百仕达": "baishida", "布心": "buxin", "春风路": "chunfenglu", "翠竹": "cuizhu", "地王": "diwang",
        "东门": "dongmen", "洪湖": "honghu", "黄贝岭": "huangbeiling", "黄木岗": "huangmugang", "莲塘": "liantang",
        "罗湖口岸": "luohukouan", "螺岭": "luoling", "清水河": "qingshuihe", "笋岗": "sungang", "万象城": "wanxiangcheng",
        "新秀": "xinxiu", "银湖": "yinhu", "八卦岭": "bagualing", "百花": "baihua", "车公庙": "chegongmiao",
        "赤尾": "chiwei", "福田保税区": "futianbaoshuiqu", "福田中心": "futianzhongxin", "皇岗": "huanggang",
        "华强北": "huaqiangbei", "华强南": "huaqiangnan", "景田": "jingtian", "莲花": "lianhua", "梅林": "meilin",
        "上步": "shangbu", "上下沙": "shangxiasha", "沙尾": "shawei", "石厦": "shixia", "香梅北": "xiangmeibei",
        "香蜜湖": "xiangmihua", "新洲": "xinzhou1", "园岭": "yuanling", "竹子林": "zhuzilin", "白石洲": "baishizhou",
        "大学城": "daxuecheng3", "红树湾": "hongshuwan", "后海": "houhai", "华侨城": "huaqiaocheng1", "科技园": "kejiyuan",
        "南山中心": "nanshanzhongxin", "南头": "nantou", "前海": "qianhai", "蛇口": "shekou", "深圳湾": "shenzhenwan",
        "西丽": "xili1", "梅沙": "meisha", "沙头角": "shatoujiao", "盐田港": "yantiangang", "宝安中心": "baoanzhongxin",
        "碧海": "bihai1", "翻身": "fanshen", "福永": "fuyong", "航城": "hangcheng", "沙井": "shajing", "石岩": "shiyan",
        "松岗": "songgang", "桃源居": "taoyuanju", "曦城": "xicheng1", "新安": "xinan", "西乡": "xixiang", "坂田": "bantian",
        "布吉大芬": "bujidafen", "布吉关": "bujiguan", "布吉街": "bujijie", "布吉南岭": "bujinanling", "布吉石芽岭": "bujishiyaling",
        "布吉水径": "bujishuijing", "丹竹头": "danzhutou", "大运新城": "dayunxincheng", "横岗": "henggang", "龙岗宝荷": "longgangbaohe",
        "龙岗双龙": "longgangshuanglong", "龙岗中心城": "longgangzhongxincheng", "民治": "minzhi", "坪地": "pingdi", "平湖": "pinghu",
        "观澜": "guanlan", "红山": "hongshan6", "龙华新区": "longhuaxinqu", "龙华中心": "longhuazhongxin", "梅林关": "meilinguan",
        "上塘": "shangtang", "公明": "gongming", "光明": "guangming1", "坪山": "pingshan", "大鹏半岛": "dapengbandao"
    }
    
    @classmethod
    def get_log_config(cls, spider_name: str) -> Dict[str, Any]:
        """获取日志配置"""
        return {
            "filename": os.path.join(cls.LOG_DIR, f"{spider_name}.log"),
            "level": cls.LOG_LEVEL,
            "format": cls.LOG_FORMAT,
            "datefmt": cls.LOG_DATE_FORMAT
        } 