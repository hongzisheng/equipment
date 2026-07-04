import time

from flask import current_app
from neo4j import GraphDatabase

from .graph_associate import build_knowledge_graph_data


class Neo4jService:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def insert_knowledge_graph_data_with_labels(self, ids: list[str] = None):
        """
        将知识图谱数据插入到Neo4j数据库中，使用具体的标签而不是通用标签
        """
        # 获取图谱数据
        graph_data = build_knowledge_graph_data(ids)
        nodes = graph_data['nodes']
        relationships = graph_data['relationships']

        with self.driver.session() as session:
            # 清空现有数据（可选）
            if ids is None:
                session.run("MATCH (n) DETACH DELETE n")

            # 在创建节点的循环中替换原有的 session.run 调用
            for node in nodes:
                # 构建标签（首字母大写）
                label = node['type'].capitalize()
                properties = {
                    'id': node['id'],
                    'name': node['name'],
                    'updatedAt': int(time.time()),
                    **node['properties']
                }

                # 使用 MERGE 语句检查节点是否存在，存在则更新时间戳，不存在则创建
                cypher_query = f"""
                    MERGE (n:{label} {{name: $props.name}})
                    SET n.updatedAt = $props.updatedAt,
                        n.id = $props.id
                    WITH n
                    WHERE $props.properties IS NOT NULL
                    SET n += $props.properties
                """

                session.run(cypher_query, props=properties)

            # 插入所有关系
            for rel in relationships:
                # 使用 f-string 正确传递关系类型，并添加 updatedAt 属性
                source_label = rel['source']['type']
                source_name = rel['source']['name']
                target_label = rel['target']['type']
                target_name = rel['target']['name']
                session.run(
                    f"""
                            MATCH (a:{source_label} {{name: $source_name}})
                            MATCH (b:{target_label} {{name: $target_name}})
                            CREATE (a)-[r:`{rel['type']}` {{id: $rel_id, updatedAt: $updated_at}}]->(b)
                            """,
                    source_name=source_name,
                    target_name=target_name,
                    rel_id=rel['id'],
                    updated_at=int(time.time())
                )


def get_neo4j_service():
    # 从应用配置中获取Neo4j连接信息
    neo4j_uri = current_app.config.get("NEO4J_URI")
    neo4j_user = current_app.config.get("NEO4J_USER")
    neo4j_password = current_app.config.get("NEO4J_PASSWORD")

    # 创建Neo4j服务实例
    neo4j_service = Neo4jService(neo4j_uri, neo4j_user, neo4j_password)
    return neo4j_service
