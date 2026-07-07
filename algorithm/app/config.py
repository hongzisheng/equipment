"""应用配置中心

集中管理所有路径与运行时配置，基于环境变量。
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# algorithm/app/config.py -> 向上两级到 algorithm/
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent  # equipment/

# 加载 .env（位于 algorithm/）
load_dotenv(BASE_DIR / '.env')


class Config:
    """Flask 配置对象"""

    # ---- Flask ----
    SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-me')

    # ---- JWT ----
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-me')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600'))

    # ---- 数据库路径 ----
    DB_PATH = PROJECT_ROOT / 'database' / 'db.sqlite3'

    # ---- 数据/上传目录 ----
    DATA_DIR = BASE_DIR / 'data'
    UPLOAD_DIR = BASE_DIR / 'uploads'

    # ---- 智能问答 DashScope ----
    DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
    DASHSCOPE_API_URL = os.getenv(
        'DASHSCOPE_API_URL',
        'https://dashscope.aliyuncs.com/compatible-mode/v1',
    )

    # ---- MinerU 解析 ----
    MINERU_API_TOKEN = os.getenv('MINERU_API_TOKEN', '')

    # ---- 微信小程序 ----
    WX_APP_ID = os.getenv('WX_APP_ID')
    WX_APP_SECRET = os.getenv('WX_APP_SECRET')
