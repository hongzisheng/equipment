"""Flask 扩展与共享客户端

将原 app.py 中模块级的 OpenAI 客户端封装为懒加载单例，
避免在缺少环境变量时导致整个应用无法导入。
"""
from openai import OpenAI

from app.config import Config

_openai_client = None


def get_openai_client():
    """获取 DashScope/OpenAI 兼容客户端（懒加载）"""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(
            api_key=Config.DASHSCOPE_API_KEY,
            base_url=Config.DASHSCOPE_API_URL,
        )
    return _openai_client
