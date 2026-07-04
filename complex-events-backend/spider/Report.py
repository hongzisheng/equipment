from urllib.parse import urlparse


def _extract_id_from_url(url):
    """从URL中提取最后一段作为ID，去除文件扩展名"""
    if not url:
        return None

    try:
        # 解析URL获取路径部分
        parsed_url = urlparse(url)
        path = parsed_url.path

        # 获取最后一段路径
        if path:
            # 移除开头和结尾的斜杠
            path = path.strip('/')
            # 获取最后一部分
            last_segment = path.split('/')[-1]
            # 移除文件扩展名（如 .html）
            if '.' in last_segment:
                last_segment = '.'.join(last_segment.split('.')[:-1])
            return last_segment
        return None
    except Exception:
        # 如果解析失败，使用简单方法
        try:
            url = url.rstrip('/')
            last_segment = url.split('/')[-1]
            if '.' in last_segment:
                last_segment = '.'.join(last_segment.split('.')[:-1])
            return last_segment
        except:
            return None


class Report:
    def __init__(self,
                 title: str,
                 date:str,
                 link_url: str,
                 details: str = '',
                 resources=None
                 ):
        if resources is None:
            self.resources = []
        self.id = _extract_id_from_url(link_url)
        self.title = title
        self.date = date
        self.link_url = link_url
        self.details = details

    def __str__(self):
        return f"{self.title}\t{self.date}\t{self.link_url}\t{self.details}"

    def __repr__(self):
        return f"{self.title} {self.date} {self.link_url} {self.details}"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "date": self.date,
            "link_url": self.link_url,
            "details": self.details,
            "resources": self.resources
        }
