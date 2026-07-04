import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from pymongo import MongoClient

import webdriver_util

client = MongoClient('localhost', 27017)
db = client.scio
collection = db.reports
driver = webdriver_util.get_driver()
def get_special_details(report):
    url = report['link_url']

    driver.get(url)
    # 等待页面加载和JavaScript执行
    time.sleep(2)

    # 判断是否发生重定向
    if driver.current_url != url:
        # 删掉
        collection.delete_one(
            {'_id': report['_id']},  # 查询条件
        )
        print(f"发生重定向: 原始URL: {url}, 重定向后URL: {driver.current_url}")
        return

    # 获取页面源码
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    article = soup.find('div', class_='trs_web')
    paragraphs = article.find_all('p')

    resources = []
    para_str = ''
    for para in paragraphs:
        img_tags = para.find_all('img')
        if len(img_tags) != 0:
            # 带有img标签 - 修改相对地址为绝对地址
            for img_tag in img_tags:
                if img_tag.has_attr('src'):
                    # 将相对路径转换为绝对路径
                    relative_src = img_tag['src']
                    absolute_src = urljoin(url, relative_src)
                    img_tag['src'] = absolute_src
                    resources.append(absolute_src)
        para_str += str(para)
    # print(paragraphs)
    collection.update_one(
        {'_id': report['_id']},  # 查询条件
        {'$set': {'details': para_str, 'resources': resources}}  # 更新内容
    )
result = collection.find({'details':''}).skip(2)
for report in result:
    try:
        get_special_details(report)
    except:
        print(report)