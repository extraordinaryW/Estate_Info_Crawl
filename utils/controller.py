import pyautogui
import time
from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException

def move_cursor_and_click(driver: webdriver.Chrome, element: WebElement, retry_count=3):
    """
    模拟真实鼠标移动和点击，防止页面滚动干扰
    
    Args:
        driver: Chrome WebDriver实例
        element: 要点击的WebElement
        retry_count: 重试次数，默认3次
    
    Returns:
        bool: 点击是否成功
    """
    
    for attempt in range(retry_count):
        try:
            # 1. 禁用页面滚动
            driver.execute_script("""
                // 保存原始滚动行为
                window.originalScrollBehavior = document.documentElement.style.scrollBehavior;
                window.originalOverflow = document.body.style.overflow;
                
                // 禁用滚动
                document.documentElement.style.scrollBehavior = 'auto';
                document.body.style.overflow = 'hidden';
                
                // 禁用鼠标滚轮事件
                window.addEventListener('wheel', function(e) {
                    e.preventDefault();
                }, { passive: false });
                
                // 禁用键盘滚动事件
                window.addEventListener('keydown', function(e) {
                    if([32, 33, 34, 35, 36, 37, 38, 39, 40].indexOf(e.keyCode) > -1) {
                        e.preventDefault();
                    }
                }, false);
            """)
            
            # 2. 确保元素在视口中且稳定
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element)
            time.sleep(0.1)  # 等待滚动完成
            
            # 3. 获取稳定的位置信息
            location = element.location_once_scrolled_into_view
            size = element.size
            
            # 4. 获取浏览器窗口信息
            win_pos = driver.execute_script("return [window.screenX, window.screenY, window.outerHeight - window.innerHeight];")
            browser_x, browser_y, header_height = win_pos
            
            # 5. 计算元素中心在屏幕上的位置
            x = browser_x + location['x'] + size['width'] // 2
            y = browser_y + header_height + location['y'] + size['height'] // 2
            
            # 6. 验证计算的位置是否合理
            screen_width, screen_height = pyautogui.size()
            if not (0 <= x <= screen_width and 0 <= y <= screen_height):
                raise ValueError(f"计算的位置超出屏幕范围: ({x}, {y})")
            
            # 7. 慢速移动鼠标，避免触发意外事件
            current_pos = pyautogui.position()
            pyautogui.moveTo(current_pos.x, current_pos.y, duration=0.1)  # 先确保鼠标在已知位置
            
            # 分段移动，避免快速移动触发滚动
            steps = 5
            for i in range(steps):
                intermediate_x = current_pos.x + (x - current_pos.x) * (i + 1) / steps
                intermediate_y = current_pos.y + (y - current_pos.y) * (i + 1) / steps
                pyautogui.moveTo(intermediate_x, intermediate_y, duration=0.05)
                time.sleep(0.02)
            
            # 8. 最终点击
            pyautogui.click()
            
            # 9. 恢复页面滚动
            driver.execute_script("""
                // 恢复原始滚动行为
                document.documentElement.style.scrollBehavior = window.originalScrollBehavior || '';
                document.body.style.overflow = window.originalOverflow || '';
            """)
            
            return True
            
        except Exception as e:
            print(f"第{attempt + 1}次点击尝试失败: {str(e)}")
            
            # 恢复页面滚动（异常情况下）
            try:
                driver.execute_script("""
                    document.documentElement.style.scrollBehavior = window.originalScrollBehavior || '';
                    document.body.style.overflow = window.originalOverflow || '';
                """)
            except:
                pass
            
            # 最后一次尝试失败，使用Selenium原生点击作为备用方案
            if attempt == retry_count - 1:
                try:
                    print("尝试使用Selenium原生点击作为备用方案...")
                    ActionChains(driver).move_to_element(element).click().perform()
                    return True
                except WebDriverException as selenium_error:
                    print(f"Selenium原生点击也失败: {str(selenium_error)}")
                    return False
            
            time.sleep(0.2)  # 重试前等待
    
    return False

def move_cursor_and_click_enhanced(driver: webdriver.Chrome, element: WebElement, offset_x=0, offset_y=0):
    """
    增强版鼠标移动和点击，支持偏移量
    
    Args:
        driver: Chrome WebDriver实例
        element: 要点击的WebElement
        offset_x: X轴偏移量（相对于元素中心）
        offset_y: Y轴偏移量（相对于元素中心）
    
    Returns:
        bool: 点击是否成功
    """
    try:
        # 1. 禁用页面滚动并记录当前滚动位置
        scroll_info = driver.execute_script("""
            var scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
            var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            // 锁定滚动位置
            document.body.style.overflow = 'hidden';
            document.documentElement.style.overflow = 'hidden';
            
            return {scrollLeft: scrollLeft, scrollTop: scrollTop};
        """)
        
        # 2. 确保元素可见
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element)
        time.sleep(0.1)
        
        # 3. 恢复到锁定前的滚动位置
        driver.execute_script(f"window.scrollTo({scroll_info['scrollLeft']}, {scroll_info['scrollTop']});")
        
        # 4. 获取元素位置
        location = element.location_once_scrolled_into_view
        size = element.size
        
        # 5. 获取浏览器窗口信息
        win_pos = driver.execute_script("return [window.screenX, window.screenY, window.outerHeight - window.innerHeight];")
        browser_x, browser_y, header_height = win_pos
        
        # 6. 计算点击位置（包含偏移量）
        x = browser_x + location['x'] + size['width'] // 2 + offset_x
        y = browser_y + header_height + location['y'] + size['height'] // 2 + offset_y
        
        # 7. 平滑移动并点击
        pyautogui.moveTo(x, y, duration=0.3)
        pyautogui.click()
        
        # 8. 恢复页面滚动
        driver.execute_script("""
            document.body.style.overflow = '';
            document.documentElement.style.overflow = '';
        """)
        
        return True
        
    except Exception as e:
        print(f"增强版点击失败: {str(e)}")
        
        # 恢复页面滚动
        try:
            driver.execute_script("""
                document.body.style.overflow = '';
                document.documentElement.style.overflow = '';
            """)
        except:
            pass
        
        return False