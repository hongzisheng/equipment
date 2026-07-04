from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import os

def get_html(url):
    try:
        driver = get_driver()
        driver.get(url)
        time.sleep(2)

        retry = 0

        while "captcha" in driver.page_source.lower() or "identity" in driver.current_url:
            time.sleep(0.5)
            retry += 1
            if retry > 60/0.5:
                break

        html = driver.page_source
        driver.quit()
        return html
    except Exception as e:
        print("get_html error:", e)
        return None

def get_driver():
    # 配置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # 创建WebDriver实例
    # 指定ChromeDriver路径
    chromedriver_path=os.path.join(os.getcwd(), 'spider/chromedriver.exe')
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
          'source': '''
              delete navigator.__proto__.webdriver;
          '''
      })
    return driver