"""
规程文件知识提取服务（待实现）

功能：解析规程 markdown → 提取检修步骤、技术要求、安全措施、所需工具/人员等结构化数据
TODO: 后续实现具体提取逻辑
"""


def extract_procedure_from_markdown(markdown_text):
    """
    从规程 markdown 中提取结构化数据

    Args:
        markdown_text: 规程文件的 markdown 内容

    Returns:
        dict: 提取的结构化数据，包含 steps, requirements, tools, personnel 等

    Raises:
        NotImplementedError: 此功能暂未实现
    """
    raise NotImplementedError("规程文件提取功能暂未实现")


def query_procedures():
    """
    查询已提取的规程数据

    Returns:
        list: 规程数据列表

    Raises:
        NotImplementedError: 此功能暂未实现
    """
    raise NotImplementedError("规程文件查询功能暂未实现")
