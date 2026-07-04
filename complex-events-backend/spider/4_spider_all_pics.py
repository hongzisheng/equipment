import base64
import os
from urllib.parse import urlparse

import pymongo

# 连接mongodb
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["complex_events"]
collection = db["reports"]
import requests
import webdriver_util

driver = webdriver_util.get_driver()


def download_image(url, save_path):
    """
    从指定URL下载图片并保存到本地

    参数:
    url: 图片的网络地址
    save_path: 保存图片的本地路径（包含文件名和扩展名）
    """

    try:
        # 访问图片URL
        driver.get(url)

        # 或者通过JavaScript获取图片数据
        # 获取图片的base64编码
        img_data = driver.execute_script("""
            var img = new Image();
            img.crossOrigin = 'Anonymous';
            img.src = arguments[0];
            // 等待图片加载完成
            return new Promise((resolve) => {
                img.onload = function() {
                    var canvas = document.createElement('canvas');
                    canvas.width = img.width;
                    canvas.height = img.height;
                    var ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0);
                    resolve(canvas.toDataURL('image/jpeg'));
                };
            });
        """, url)

        # 解码base64数据并保存
        if img_data:
            header, encoded = img_data.split(',', 1)
            with open(save_path, 'wb') as file:
                file.write(base64.b64decode(encoded))
            print(f"图片已成功下载并保存为: {save_path}")

    except Exception as e:
        print(f"使用driver下载失败: {e}")



# 保存位置为当前位置的外面的assert文件夹
save_folder = os.path.join(os.path.dirname(__file__), '..', "assets", "pictures")
save_path_folder = os.path.abspath(save_folder)
os.makedirs(save_path_folder, exist_ok=True)
for doc in collection.find().limit(250):
    resources = doc.get("resources", [])
    for url in resources:
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        path = os.path.join(save_path_folder, filename)
        # 存在的时候跳过下载
        if os.path.exists(path):
             continue
        else:
            download_image(url, path)

driver.quit()