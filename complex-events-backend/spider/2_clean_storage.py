# -*- coding: utf-8 -*-
from tqdm import tqdm
from bs4 import BeautifulSoup, Comment

from Report import Report
from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client.scio
collection = db.reports

for i in tqdm(range(1, 2000), desc='正在导入中'):
    with open(f'scio/scio{i}.html', 'r', encoding='utf-8') as f:
        html = f.read()
        # 使用内置的 html.parser
        soup = BeautifulSoup(html, "html.parser")
        # 移除所有注释
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment.extract()

        report_result = []
        list = soup.find_all("div", class_="result-list-item")

        for div in list:
            title = div.find("div", class_="result-item-title")
            link_div = div.find('div',class_='result-item-link').find_all('span')
            link_url = link_div[0]
            link_date = link_div[1]
            report_result.append(Report(title.text.strip(), link_date.text.strip(), link_url.text.strip()))

        # for report in report_result:
        #     print(report)

        # 将结果插入mongodb数据库中

        # 将 Report 对象转换为字典
        report_dicts = [report.to_dict() for report in report_result]

        # 批量插入字典数据
        collection.insert_many(report_dicts)