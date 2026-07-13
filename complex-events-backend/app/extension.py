from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()


def init_extensions(app):
    bcrypt.init_app(app)


# ---- 智能问答 OpenAI 兼容客户端（懒加载单例）----
_openai_client = None


def get_openai_client():
    """获取 DashScope/OpenAI 兼容客户端。

    使用懒加载，避免在缺少 API Key 时导致整个应用无法启动。
    仅在真正发起问答请求时才创建客户端。
    """
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        from app.config import Config

        if not Config.DASHSCOPE_API_KEY:
            raise RuntimeError(
                "未配置 DASHSCOPE_API_KEY，请在 .env 文件中设置后重启服务"
            )
        _openai_client = OpenAI(
            api_key=Config.DASHSCOPE_API_KEY,
            base_url=Config.DASHSCOPE_API_URL,
        )
    return _openai_client
