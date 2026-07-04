from flask import current_app

from .neo4j_service import get_neo4j_service

def insert_graph_data_to_neo4j(ids:list = None):
    try:
        neo4j_service = get_neo4j_service()
        try:
            # 插入数据到Neo4j
            neo4j_service.insert_knowledge_graph_data_with_labels(ids)
            current_app.logger.info("图谱已经成功构建到Neo4j")
        finally:
            # 关闭连接
            neo4j_service.close()

    except Exception as e:
        print(f"插入图谱数据到Neo4j时发生错误: {str(e)}")
        raise

# 如果直接运行此脚本，则执行插入操作
if __name__ == "__main__":
    insert_graph_data_to_neo4j()
