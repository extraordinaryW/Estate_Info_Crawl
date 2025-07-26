import pandas as pd
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import logging 
from tqdm import tqdm
import time
import random
logging.basicConfig(
    filename='lj_crawl_cj.log',
    level=logging.INFO,
    format='%(asctime)s-%(levelname)s-%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
'''
页面URL：https://sz.lianjia.com/chengjiao/
'''
def get_info(driver:WebDriver, district):
    time.sleep(random.uniform(1,3))
    res = {
                '房源名称' : [],
                '所在区域' : [],
                '建筑特征' : [],
                '成交时间' : [],
                '价格信息' : []
            }
    try: 
        sell_list = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "listContent"))
        )
        li_elements = sell_list.find_elements(By.TAG_NAME, "li")
        for estate in li_elements:
            try:
                try:
                    estate_info = estate.find_element(By.XPATH, ".//*[contains(@class, 'info')]")
                    name = estate_info.find_element(By.CLASS_NAME, "title").text
                    logging.info(f"获取资产名称：{name}")
                except NoSuchElementException:
                    logging.info("获取资产名称失败")
                    name = ''
                area = district
                try:
                    estate_attribute = estate_info.find_element(By.CLASS_NAME, "address")
                    estate_towards = estate_attribute.find_element(By.CLASS_NAME, "houseInfo").text
                    estate_attribute_floor = estate_info.find_element(By.CLASS_NAME, "flood")
                    estate_floor = estate_attribute_floor.find_element(By.CLASS_NAME, "positionInfo").text
                    logging.info(f"获取资产特征：",{'装修及朝向' : estate_towards, '楼层及建筑类型' : estate_floor})
                except NoSuchElementException:
                    logging.info("获取资产特征失败")
                    estate_towards = ''
                    estate_floor = ''
                try:
                    deal_date = estate_attribute.find_element(By.CLASS_NAME, "dealDate").text
                    deal_date = pd.to_datetime(deal_date, format='%Y.%m.%d')
                    if deal_date <= pd.to_datetime('2017-01-01'):
                        return None
                except NoSuchElementException:
                    logging.info("获取成交时间失败")
                try:
                    unit_price = estate_attribute_floor.find_element(By.CLASS_NAME, "unitPrice").text
                    total_price = estate_attribute.find_element(By.CLASS_NAME, "totalPrice").text
                    logging.info(f"获取资产单价{unit_price}, 总价{total_price}")
                except NoSuchElementException:
                    logging.info("获取资产价格失败")
                    unit_price = ''
                    total_price = ''
                res['房源名称'].append(name)
                res['所在区域'].append(area)
                res['建筑特征'].append({'装修及朝向' : estate_towards, '楼层及建筑类型' : estate_floor})
                res['成交时间'].append(deal_date)
                res['价格信息'].append({'单价' : f'{unit_price}', '总价' : f'{total_price}'})
            except NoSuchElementException:
                logging.info(f"未能获取资产信息")
    except NoSuchElementException:
        logging.info(f"当前页面{driver.current_url}下找不到资源列表")
    res = pd.DataFrame(data=res)
    return res
def create_driver():
    options = Options()
    # option.add_argument('--headless')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver = webdriver.Chrome(options = options, service=Service())
    return driver
def main(driver:WebDriver, url, district):
    driver.get(url)
    result = pd.DataFrame(
        data = {
            '房源名称' : [],
            '所在区域' : [],
            '建筑特征' : [],
            '成交时间' : [],
            '价格信息' : []
        }
    )
    try:
        page_box = WebDriverWait(driver,10).until(
            EC.presence_of_element_located((By.XPATH, ".//*[contains(@class, 'page-box') and contains(@class, 'house-lst-page-box')]"))
        )
        max_page = int(page_box.find_element(By.XPATH, './/a[4]').text)
        logging.info(f"{district}下最大页数为：{max_page}")
    except NoSuchElementException:
        logging.info(f"获取{district}最大页数失败，请查看最大页数后手动输入：")
        max_page = input(f"{district}最大页数为:")
    for page in tqdm(range(1,int(max_page) + 1)):
        if page == 1:
            new_res = get_info(driver,district)
        else:
            driver.get(url + f"/pg{page}/")
            new_res = get_info(driver,district)
        if new_res is not None:
            result = pd.concat([result, new_res], ignore_index=True)
        else:
            return result
    return result
if __name__ == '__main__':
    districts = {
        '罗湖区' : ['百仕达','布心','春风路','翠竹','地王','东门','洪湖','黄贝岭','黄木岗','莲塘','罗湖口岸','螺岭','清水河','笋岗','万象城','新秀','银湖'],
        '福田区' : ['八卦岭','百花','车公庙','赤尾','福田保税区','福田中心','皇岗','黄木岗','华强北','华强南','景田','莲花','梅林','上步','上下沙','沙尾','石厦','香梅北','香蜜湖','新洲','银湖','园岭','竹子林'],
        '南山区' : ['白石洲','大学城','红树湾','后海','华侨城','科技园','南山中心','南头','前海','蛇口','深圳湾','西丽'],
        '盐田区' : ['梅沙','沙头角','盐田港'],
        '宝安区' : ['宝安中心','碧海','翻身','福永','航城','沙井','石岩','松岗','桃源居','曦城','新安','西乡'],
        '龙岗区' : ['布吉大芬','布吉关','布吉街','布吉南岭','布吉石芽岭','布吉水径','丹竹头','大运新城','横岗','龙岗宝荷','龙岗双龙','龙岗中心城','坪地','平湖'],
        '龙华区' : ['坂田','观澜','红山','龙华新区','龙华中心','梅林关','民治','上塘'],
        '光明区' : ['公明','光明'],
        '坪山区' : ['坪山'],
        '大鹏新区' : ['大鹏半岛']
    }
    districts_en = {
        "百仕达": "baishida",
        "布心": "buxin",
        "春风路": "chunfenglu",
        "翠竹": "cuizhu",
        "地王": "diwang",
        "东门": "dongmen",
        "洪湖": "honghu",
        "黄贝岭": "huangbeiling",
        "黄木岗": "huangmugang",
        "莲塘": "liantang",
        "罗湖口岸": "luohukouan",
        "螺岭": "luoling",
        "清水河": "qingshuihe",
        "笋岗": "sungang",
        "万象城": "wanxiangcheng",
        "新秀": "xinxiu",
        "银湖": "yinhu",
        "八卦岭": "bagualing",
        "百花": "baihua",
        "车公庙": "chegongmiao",
        "赤尾": "chiwei",
        "福田保税区": "futianbaoshuiqu",
        "福田中心": "futianzhongxin",
        "皇岗": "huanggang",
        "华强北": "huaqiangbei",
        "华强南": "huaqiangnan",
        "景田": "jingtian",
        "莲花": "lianhua",
        "梅林": "meilin",
        "上步": "shangbu",
        "上下沙": "shangxiasha",
        "沙尾": "shawei",
        "石厦": "shixia",
        "香梅北": "xiangmeibei",
        "香蜜湖": "xiangmihua",
        "新洲": "xinzhou1",
        "银湖": "yinhu",
        "园岭": "yuanling",
        "竹子林": "zhuzilin",
        "白石洲": "baishizhou",
        "大学城": "daxuecheng3",
        "红树湾": "hongshuwan",
        "后海": "houhai",
        "华侨城": "huaqiaocheng1",
        "科技园": "kejiyuan",
        "南山中心": "nanshanzhongxin",
        "南头": "nantou",
        "前海": "qianhai",
        "蛇口": "shekou",
        "深圳湾": "shenzhenwan",
        "西丽": "xili1",
        "梅沙": "meisha",
        "沙头角": "shatoujiao",
        "盐田港": "yantiangang",
        "宝安中心": "baoanzhongxin",
        "碧海": "bihai1",
        "翻身": "fanshen",
        "福永": "fuyong",
        "航城": "hangcheng",
        "沙井": "shajing",
        "石岩": "shiyan",
        "松岗": "songgang",
        "桃源居": "taoyuanju",
        "曦城": "xicheng1",
        "新安": "xinan",
        "西乡": "xixiang",
        "坂田": "bantian",
        "布吉大芬": "bujidafen",
        "布吉关": "bujiguan",
        "布吉街": "bujijie",
        "布吉南岭": "bujinanling",
        "布吉石芽岭": "bujishiyaling",
        "布吉水径": "bujishuijing",
        "丹竹头": "danzhutou",
        "大运新城": "dayunxincheng",
        "横岗": "henggang",
        "龙岗宝荷": "longgangbaohe",
        "龙岗双龙": "longgangshuanglong",
        "龙岗中心城": "longgangzhongxincheng",
        "民治": "minzhi",
        "坪地": "pingdi",
        "平湖": "pinghu",
        "坂田": "bantian",
        "观澜": "guanlan",
        "红山": "hongshan6",
        "龙华新区": "longhuaxinqu",
        "龙华中心": "longhuazhongxin",
        "梅林关": "meilinguan",
        "上塘": "shangtang",
        "石岩": "shiyan",
        "公明": "gongming",
        "光明": "guangming1",
        "坪山": "pingshan",
        "大鹏半岛": "dapengbandao"
    }
    districts_ch = ['龙华区', '光明区', '坪山区', '大鹏新区']
    driver = create_driver()
    driver.get('https://sz.lianjia.com/chengjiao')
    input("完成登陆后输入任意字符")
    for item in districts_ch:
        result = pd.DataFrame(
            data = {
                '房源名称' : [],
                '所在区域' : [],
                '建筑特征' : [],
                '成交时间' : [],
                '价格信息' : []
            }
        )
        districts_list_ch = districts[item]
        for district_ch in districts_list_ch:
            district_en = districts_en[district_ch]
            url = 'https://sz.lianjia.com/chengjiao/' + district_en
            new_info = main(driver, url, district_ch)
            result = pd.concat([result, new_info], ignore_index=True)
        with pd.ExcelWriter('链家信息爬取_cj.xlsx', mode='a', engine='openpyxl') as writer:
            result.to_excel(writer, sheet_name=item, index=False)
        logging.info(f"{item}内容获取完毕")
    driver.quit()