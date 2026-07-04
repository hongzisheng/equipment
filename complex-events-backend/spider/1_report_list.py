import time

import webdriver_util

driver = webdriver_util.get_driver()
try:
    for page in range(0,2000):
        # 访问页面
        driver.get(f'http://www.scio.gov.cn/was5/web/search?channelid=246104&searchword=%20%E4%B8%80%E5%B8%A6%E4%B8%80%E8%B7%AF&page={page+1}&orderby=-docreltime&searchscope=&timestart=&timeend=&period=&chnls=&andsen=&total=&orsen=&exclude=')

        # 等待页面加载和JavaScript执行
        time.sleep(2)

        # 获取页面源码
        html = driver.page_source
        # 存储为html文件
        with open(f'./scio/scio{page+1}.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'已保存第{page+1}页数据')

finally:
    driver.quit()
