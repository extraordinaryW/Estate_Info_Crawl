# _._ coding:utf-8 _._
"""
:author: Tang
:time: 2024.07.16
:content: 采集京东法拍网站信息
"""
import logging.config
import os
import re
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import pandas as pd
import logging 
"""
程序功能：采集京东法拍网站信息
地址：https://pmsearch.jd.com/?publishSource=7&childrenCateId=12728
cmd中输入以下内容后（内容中路径部分需换成自己的真实路径），在打开的浏览器中访问上述地址，登陆京东账号：
chrome.exe --remote-debugging-port=9222 --user-data-dir="D:\code_Project\竞拍网站\chromedriver"
"""
logging.basicConfig(
    filename='crawl_log.log',
    level = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s',
    datefmt = '%Y-%m-%d %H:%M:%S'
)
def spider_taxpayer_bankruptcy_info(chrome_driver,url, start_page):
    if chrome_driver is None:
        logging.info("###1.1 接管浏览器失败,结束采集流程,请确认浏览器是否正常打开以及端口是否对应---")
        return None
    
    try:
        chrome_driver.get(url)
    except Exception as e:
        logging.info("无法导航到目标页面，错误信息：" + str(e))
        return None
    logging.info("瀏覽器接管成功---" + chrome_driver.capabilities["browserName"] + "-------" + chrome_driver.capabilities["browserVersion"])
    # 定位到目标城市，此处为“广东-深圳” 
    select_loction(chrome_driver)
    logging.info("# 3.获取列表清单")
    pageNo = 1
    datas = []
    # 第三个参数传入开始爬取时的页数
    pageNo = transfer_page(chrome_driver, pageNo, start_page)
    while True:
        sleep(5)
        list_xpath = "//*[@id='root']/div/div/div[4]/ul/li"
        title_elements = chrome_driver.find_elements(By.XPATH, list_xpath)
        if not title_elements:
            return
        element_index = 0
        for index in range(element_index, len(title_elements)):
            url = title_elements[index]
            try:
                # 抓取拍卖当前进行状态（只抓取已经完成的拍卖）
                item_status = url.find_element(By.XPATH, ".//a/div[3]/div[1]").text
                if 1 == 1:
                # if item_status == '已结束' or item_status == '已暂缓' or item_status == '已中止':
                    link = url.find_element(By.XPATH, ".//a").get_property("href")
                    image = url.find_element(By.XPATH, ".//a/div[1]/div/img").get_attribute('src')
                    current_value = url.find_element(By.XPATH, ".//a/div[2]/div[2]/div[2]/em/b").text
                    esti_value = url.find_element(By.XPATH, ".//a/div[2]/div[3]/div[1]/em").text
                    result = spider_content(chrome_driver, link)
                    data = {"资产名称": result['资产名称'], "竞价状态" : item_status, "结束时间" : result['结束时间'], "是否流拍" : result['是否流拍'], "流拍原因" : result['流拍原因'], "图片": image, "当前价": current_value, "评估价": esti_value, "围观人数" : result['围观人数'], "报名人数" : result['报名人数'], "关注提醒人数" : result['关注提醒人数'], "成交价" : result['成交价格'], "起拍价" : result['起拍价格'], "变卖价格" : result['变卖价格'], "加价幅度" : result['加价幅度'], "保证金" : result['保证金'], "竞价周期" : result['竞价周期'], "变卖周期" : result['变卖周期'], "延时周期" : result['延时周期']}
                    datas.append(data)

                    #回到原窗口
                    chrome_driver.switch_to.window(chrome_driver.window_handles[0])
                    sleep(2)
                    title_elements = chrome_driver.find_elements(By.XPATH, list_xpath)
                else:
                    continue
            except Exception as e:
                logging.info(f'错误信息：{e}')
        save_overall(datas)
        target_page = pageNo + 1
        pageNo = transfer_page(chrome_driver, pageNo, pageNo + 1)
        # 需要获取的页数，可选范围为（1，9999),若页数超过已有页数，则爬取已有全部信息 
        if (pageNo != target_page) | (pageNo >= 2):
            logging.info(f"当前页数为{pageNo}")
            break
    return None
def select_loction(chrome_driver):
    chrome_driver.find_element(By.CLASS_NAME, "province").click()
    chrome_driver.find_element(By.XPATH, "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl/dd/a[20]").click()
    sleep(2)
    chrome_driver.find_element(By.CLASS_NAME, "city").click()
    chrome_driver.find_element(By.XPATH, "//*[@id='root']/div/div/div[2]/div[4]/div/div[2]/div/dl[2]/dd/a[3]").click()

def transfer_page(chrome_driver, pageNo, target_page):
    while(pageNo < target_page):
        next_page = chrome_driver.find_element(By.CLASS_NAME, "ui-pager-next")
        if not next_page:
            logging.info("没有找到下一页按钮，结束采集")
        else:
            try:
                chrome_driver.execute_script("arguments[0].scrollIntoView(true);", next_page)
                sleep(2)
                next_page.click()
                sleep(2)
                logging.info("--------翻页成功------pageNo:" + str(pageNo))
                pageNo += 1
                
            except Exception as e:
                logging.info("翻页失败--------" + str(e.args))
                return pageNo
    return pageNo
def save_overall(datas):
    datas = pd.DataFrame(data=datas)
    datas.to_excel('页面信息获取_test.xlsx',index=False)

def spider_content(chrome_driver, url):
    # 记录主窗口句柄
    main_window = chrome_driver.current_window_handle

    # 打开新窗口
    chrome_driver.execute_script(f"window.open('{url}', '_blank');")

    # 切换到新窗口
    all_windows = chrome_driver.window_handles
    for window in all_windows:
        if window != main_window:
            chrome_driver.switch_to.window(window)
            break
    try:
        WebDriverWait(chrome_driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        try:
            # 自动进行验证
            wait = WebDriverWait(chrome_driver, 10)
            button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "dialog-submit")))
            button.click()
        except Exception as e:
            logging.info("当前页面无需验证")

        try:
            # 获取标题内容作为名称
            name = WebDriverWait(chrome_driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pm-name"))
            ).text
            try:
                # 获取结果信息
                final_price = WebDriverWait(chrome_driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[@id='root']/div/div[2]/div[1]/div[2]/div[3]/div[2]/div[1]/div[2]/em"))
                ).text
            except:
                logging.info("----------------------------当前详情页下无结果信息--------------------------------")
                final_price = ''
            # 是否流拍
            bidding_result = chrome_driver.find_element(By.XPATH, "//*[@id='root']/div/div[2]/div[1]/div[2]/div[3]/div[1]/div[2]/span").text
            if '流拍' in bidding_result:
                if_unsold = '是'
                unsold_reason = chrome_driver.find_element(By.XPATH, "//*[@id='root']/div/div[2]/div[1]/div[2]/div[3]/div[1]/div[2]").text
            else:
                if_unsold = '否'
                unsold_reason = ''

            # 是否变卖
            if_sell_off = 0
            if '变卖' in str(name):
                if_sell_off = 1
                sell_off_price = chrome_driver.find_element(By.XPATH, "//*[@id='root']/div/div[2]/div[1]/div[2]/div[3]/div[3]/div/div[1]/ul/li[1]/em").text
                mark_up = chrome_driver.find_element(By.XPATH, "//*[@id='root']/div/div[2]/div[1]/div[2]/div[3]/div[3]/div/div[1]/ul/li[3]/em").text
                sell_off_cycle = chrome_driver.find_element(By.XPATH, "//*[@id='root']/div/div[2]/div[1]/div[2]/div[3]/div[3]/div/div[1]/ul/li[4]/em").text
                delay_cycle = chrome_driver.find_element(By.XPATH, "//*[@id='root']/div/div[2]/div[1]/div[2]/div[3]/div[3]/div/div[1]/ul/li[5]/em").text
            else:
                start_price = chrome_driver.find_element(By.XPATH, "//*[@id='root']/div/div[2]/div[1]/div[2]/div[3]/div[3]/div/div[1]/ul/li[1]/em").text
                mark_up = chrome_driver.find_element(By.XPATH, "//*[@id='root']/div/div[2]/div[1]/div[2]/div[3]/div[3]/div/div[1]/ul/li[3]/em").text
                margin = chrome_driver.find_element(By.XPATH, "//*[@id='root']/div/div[2]/div[1]/div[2]/div[3]/div[3]/div/div[1]/ul/li[4]/em").text
                bidding_cycle = chrome_driver.find_element(By.XPATH, "//*[@id='root']/div/div[2]/div[1]/div[2]/div[3]/div[3]/div/div[1]/ul/li[5]/em").text
                delay_cycle = chrome_driver.find_element(By.XPATH, "//*[@id='root']/div/div[2]/div[1]/div[2]/div[3]/div[3]/div/div[1]/ul/li[6]/em").text

            watched_times_html = chrome_driver.find_element(By.XPATH, "//*[@id='root']/div/div[2]/div[1]/div[2]/div[3]/div[1]/div[3]").text
            match_endTime = re.search(r'\d{4}年\d{2}月\d{2}日 \d{2}:\d{2}:\d{2}', str(watched_times_html))
            end_time = match_endTime.group(0) if match_endTime else '结束时间抓取有误'
            match_watched = re.search(r'(\d+)人围观', str(watched_times_html))
            watched_times = match_watched.group(0) if match_watched else '围观人数抓取有误'
            match_signIn = re.search(r'(\d+)人报名', str(watched_times_html))
            signIn_times = match_signIn.group(0) if match_signIn else '报名人数抓取有误'
            match_attention = re.search(r'(\d+)人关注提醒', str(watched_times_html))
            attention_times = match_attention.group(0) if match_attention else '关注提醒人数抓取有误'

        except Exception as e:
            logging.info("未能获取全部信息页", str(e))

        new_folder_path = os.path.join("./爬取结果集", name)
        os.makedirs(new_folder_path, exist_ok=True)

        try:
            if_pzfw = None
            if_pzfw = chrome_driver.find_element(By.CLASS_NAME, "pm-pzfw")
        except:
            logging.info("配资服务不存在")

        third_div = '6' if if_pzfw else '5'

        try:
            table_content = WebDriverWait(chrome_driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//*[@id='root']/div/div[2]/div[{third_div}]/div[2]/ul/li[1]/div/div[3]/table"))
            )
            table_html = table_content.get_attribute('outerHTML')
            soup = BeautifulSoup(table_html, 'lxml')
            tables = soup.find_all('table')
            if tables:
                table = tables[0]
                df = pd.read_html(str(table))[0]
                df.to_excel(f'{new_folder_path}\\拍卖标的物调查情况表（房产）.xlsx', index=False)
        except:
            logging.info("未找到表格内容")

        try:
            file_list = chrome_driver.find_elements(By.XPATH, f"//*[@id='root']/div/div[2]/div[{third_div}]/div[2]/ul/li[1]/div/div[1]/ul/li")
            if not file_list:
                logging.info(f"标的资产'{name}'下无可获取的pdf")
            else:
                for file in file_list:
                    file_url = file.find_element(By.XPATH, ".//*[@id='openAttachmentTag']").get_property("href")
                    file_name = file.find_element(By.XPATH, ".//*[@id='openAttachmentTag']").text
                    response = requests.get(file_url)
                    file_path = f'{new_folder_path}\\{file_name}'
                    with open(file_path, "wb") as file:
                        file.write(response.content)
        except:
            logging.info("pdf文件未全部成功下载")

        try:
            img_list = chrome_driver.find_elements(By.XPATH, f"//*[@id='root']/div/div[2]/div[{third_div}]/div[2]/ul/li[1]/div/div[3]/a")
            if not img_list:
                logging.info(f"标的资产'{name}'下无可获取的图片")
            else:
                img_count = 0
                for img in img_list:
                    img_url = img.find_element(By.XPATH, ".//img").get_attribute('src')
                    img_name = str(img_count)
                    response = requests.get(img_url)
                    img_path = f'{new_folder_path}\\{img_name}.jpg'
                    with open(img_path, "wb") as img:
                        img.write(response.content)
                    img_count += 1
        except:
            logging.info("图片未全部成功下载")

        try:
            sleep(2)
            find_floors = WebDriverWait(chrome_driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//*[@id='root']/div/div[2]/div[{third_div}]/div[2]/ul"))
            )

            map_exist = None
            try:
                map_exist = find_floors.find_element(By.CLASS_NAME, "floor-exception")
            except:
                logging.info("页面未调用地图API")

            if not map_exist:
                find_notice = find_floors.find_element(By.XPATH, "./li[2]")
                find_rule = find_floors.find_element(By.XPATH, "./li[3]")
            else:
                find_notice = find_floors.find_element(By.XPATH, "./li[3]")
                find_rule = find_floors.find_element(By.XPATH, "./li[4]")

            notice_content = find_notice.find_element(By.XPATH, ".//div[2]/div")
            html_content = notice_content.get_attribute('outerHTML')
            html_content = BeautifulSoup(html_content, 'lxml')
            note_content = html_content.get_text(separator='\n', strip=True)

            rule_content = find_rule.find_element(By.XPATH, ".//div/div")
            html_content = rule_content.get_attribute('outerHTML')
            html_content = BeautifulSoup(html_content, 'lxml')
            instruction_content = html_content.get_text(separator='\n', strip=True)

            result = {"Bidding Notice": [note_content], "Instructions for Bidding": [instruction_content]}
            pd.DataFrame(result).to_excel(f'{new_folder_path}\\存取竞买公告和竞买须知.xlsx', index=False)
        except Exception as e:
            logging.info("存取公告和竞买须知保存出错", str(e))

        bidding_records = []
        while True:
            bidding_record = chrome_driver.find_element(By.CLASS_NAME, "bidList")
            table_content = bidding_record.get_attribute('outerHTML')
            soup = BeautifulSoup(table_content, 'lxml')
            bidding_list = soup.find('tbody').find_all('tr')

            for row in bidding_list:
                columns = row.find_all('td')
                status = columns[0].get_text(strip=True)
                price = columns[1].get_text(strip=True)
                username = columns[2].get_text(strip=True)
                bid_time = columns[3].get_text(strip=True)
                bidding_records.append({
                    "状态": status,
                    "价格": price,
                    "竞拍人": username,
                    "时间": bid_time
                })

            try:
                if not map_exist:
                    bidding_pager = chrome_driver.find_element(By.XPATH, f"//*[@id='root']/div/div[2]/div[{third_div}]/div[2]/ul/li[5]/div/div")
                else:
                    bidding_pager = chrome_driver.find_element(By.XPATH, f"//*[@id='root']/div/div[2]/div[{third_div}]/div[2]/ul/li[6]/div/div")
                next_button = bidding_pager.find_element(By.CLASS_NAME, "next")
                if not next_button.is_enabled():
                    break
            except:
                logging.info("无下一页信息")
                break

            try:
                chrome_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                WebDriverWait(chrome_driver, 10).until(EC.element_to_be_clickable(next_button)).click()
                sleep(2)
                logging.info("--------查找下一页出价信息------")
            except Exception as e:
                logging.info("翻页失败--------" + str(e.args))
                break

        bidding_note = pd.DataFrame(bidding_records)
        bidding_note.to_excel(f'{new_folder_path}\\出价记录.xlsx', index=False)

        try:
            priority_purchase = chrome_driver.find_element(By.CLASS_NAME, "purchaserList")
            people_content = priority_purchase.get_attribute('outerHTML')
            people_content = BeautifulSoup(people_content, 'lxml')
            purchasers = people_content.find_all('table')

            if purchasers:
                purchaser = purchasers[0]
                df = pd.read_html(str(purchaser))[0]
                df.to_excel(f'{new_folder_path}\\优先购买权人.xlsx', index=False)
        except:
            logging.info("未找到优先购买权人")

    except BaseException as be:
        logging.info("匹配搜索结果异常--------------->" + str(be.args))
        return None
    finally:
        chrome_driver.close()
        chrome_driver.switch_to.window(main_window)

        if if_sell_off == 0:
            bidding_res = {'资产名称': name, '结束时间': end_time, '是否流拍': if_unsold, '流拍原因': unsold_reason, '围观人数': watched_times, '报名人数': signIn_times, '关注提醒人数': attention_times, "成交价格": final_price, '起拍价格': start_price, '变卖价格': '', '加价幅度': mark_up, '保证金': margin, '竞价周期': bidding_cycle, '变卖周期': '', '延时周期': delay_cycle}
            return bidding_res
        else:
            sell_off_res = {'资产名称': name, '结束时间': end_time, '是否流拍': if_unsold, '流拍原因': unsold_reason, '围观人数': watched_times, '报名人数': signIn_times, '关注提醒人数': attention_times, "成交价格": final_price, '起拍价格': '', '变卖价格': sell_off_price, '加价幅度': mark_up, '保证金': '', '竞价周期': '', '变卖周期': sell_off_cycle, '延时周期': delay_cycle}
            return sell_off_res

def get_chrome():
    logging.info("# 1.接管浏览器")
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # 无头模式，开启后如果遇到反爬验证可能会导致出错
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    chrome_options.add_argument("--disable-popup-blocking")
    driver = webdriver.Chrome(options=chrome_options)
    logging.info(driver.title)
    return driver
if __name__ == '__main__':
    try:
        url = "https://pmsearch.jd.com/?publishSource=7&childrenCateId=12728"
        chrome_driver = get_chrome()
        spider_taxpayer_bankruptcy_info(chrome_driver,url, start_page = 1) # start_page为开始爬取时的页数，默认为1
        chrome_driver.quit()
    except Exception as e:
        chrome_driver.quit()
        logging.info("执行失败" + e.args)
