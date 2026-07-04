import neo4j
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable, AuthError
from flask import Flask


def check_neo4j_status(current_app: Flask):
    """
    检查 Neo4j 数据库连接状态

    检查任务包括：
    1. 检查Neo4j服务是否启动
    2. 是否能通过用户名密码正确连接Neo4j
    3. Neo4j 数据库是否可访问
    """
    try:
        # 获取应用配置
        config = current_app.config
        uri = config['NEO4J_URI']
        user = config['NEO4J_USER']
        password = config['NEO4J_PASSWORD']

        # 1. 检查Neo4j服务是否启动
        # 2. 是否能通过用户名密码正确连接Neo4j
        # 创建驱动程序并尝试连接
        driver = GraphDatabase.driver(uri, auth=(user, password))

        # 验证连接是否可用
        driver.verify_connectivity()

        # 3. Neo4j 数据库是否可访问
        # 执行简单查询验证数据库可访问性
        with driver.session() as session:
            result = session.run("RETURN 1 AS result")
            result.single()

        # 关闭驱动程序
        driver.close()
        current_app.logger.info("Neo4j Connect Status: SUCCESS")
        return True

    except ServiceUnavailable as e:
        # 处理无法连接到Neo4j服务的错误
        current_app.logger.error("Neo4j Connect Status: FAILED, 无法连接到Neo4j服务，请检查服务是否启动")
        return False
    except AuthError as e:
        # 处理认证错误（用户名或密码错误）
        current_app.logger.error("Neo4j Connect Status: FAILED, 用户名或密码错误")
        return False
    except Exception as e:
        # 处理其他异常
        current_app.logger.error(f"Neo4j Connect Status: FAILED, 错误信息: {str(e)}")
        return False

def get_neo4j_driver(current_app: Flask) -> Driver:
    # 获取应用配置
    config = current_app.config
    uri = config['NEO4J_URI']
    user = config['NEO4J_USER']
    password = config['NEO4J_PASSWORD']
    return GraphDatabase.driver(uri, auth=(user, password))

def execute_cypher(current_app: Flask, cypher: str,**kwargs) -> list:
    driver = get_neo4j_driver(current_app)
    current_app.logger.info(f"Executing Cypher Query: {cypher}")
    with driver.session() as session:
        # 将结果转换为列表以避免消费问题
        return list(session.run(cypher, **kwargs))

def get_all_node_count(current_app: Flask) -> int:
    """
    获取 Neo4j 数据库中所有节点的总数

    返回：
        节点总数 (int)，如果查询失败则返回 0
    """
    try:
        cypher = "MATCH (n) RETURN count(n) AS total_nodes"
        result = execute_cypher(current_app, cypher)
        if result and len(result) > 0:
            total_nodes = result[0]["total_nodes"]
            # print(f"Neo4j 节点总数: {total_nodes}")
            return total_nodes
        else:
            print("Neo4j 查询结果为空")
            return 0
    except Exception as e:
        print(f"获取 Neo4j 节点总数失败: {e}")
        return 0
