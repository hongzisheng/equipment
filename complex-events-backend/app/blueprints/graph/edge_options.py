from flask import request

from app.blueprints.graph import graph_bp, execute_option_cypher
from app.models import Result


@graph_bp.route('/addEdge', methods=['POST'])
def add_edge():
    """
    在图谱中添加一个关系

    Params:
        startNodeId: 起始节点的元素id
        endNodeId: 结束节点的元素id
        type: 关系类型
    """
    edge_json = request.get_json()
    start_node_id = edge_json.get('startNodeId')
    end_node_id = edge_json.get('endNodeId')
    edge_type = edge_json.get('type')

    if not start_node_id or not end_node_id or not edge_type:
        return Result.fail('参数错误')
    cypher = f'MATCH (a),(b) WHERE elementId(a) = "{start_node_id}" AND elementId(b) = "{end_node_id}" CREATE (a)-[r:{edge_type}]->(b) RETURN r'
    return execute_option_cypher(cypher,'add_edge')

@graph_bp.route('/updateEdge', methods=['POST'])
def update_edge():
    """
    修改关系信息, 关系类型的定义在本体定义阶段完成

    修改连接的前后连接的节点

    Params:
        edgeId: 关系元素id
        type: 关系类型
        startNodeId: 新的起始节点ID（可选）
        endNodeId: 新的结束节点ID（可选）
    """
    edge_json = request.get_json()
    edge_id = edge_json.get('id')
    edge_type = edge_json.get('type')
    start_node_id = edge_json.get('startNodeId')
    end_node_id = edge_json.get('endNodeId')

    if not edge_id or not (edge_type or start_node_id or end_node_id):
        return Result.fail('参数错误')

    # 删除原关系
    cypher_delete = f'MATCH ()-[r]->() WHERE elementId(r) = "{edge_id}" DELETE r'
    execute_option_cypher(cypher_delete,'delete_edge')

    # 创建新关系
    cypher = f"""
    MATCH (a),(b) 
    WHERE elementId(a) = "{start_node_id}" 
    AND elementId(b) = "{end_node_id}"
    CREATE (a)-[r:{edge_type}]->(b) 
    RETURN r"""
    return execute_option_cypher(cypher,'add_edge')


@graph_bp.route('/deleteEdge', methods=['DELETE'])
def delete_edge():
    """
    删除关系

    Params:
        edgeId: 关系元素id
    """
    edge_json = request.get_json()
    edge_id = edge_json.get('id')

    if not edge_id:
        return Result.fail('参数错误')

    cypher = f'MATCH ()-[r]-() WHERE elementId(r) = "{edge_id}" DELETE r'
    return execute_option_cypher(cypher,'delete_edge')
