from flask import request

from app.models import Result
from . import graph_bp, execute_option_cypher


@graph_bp.route('/addNode', methods=['POST'])
def add_node():
    """
    在图谱中添加一个节点

    -------
    Params:
        node_name: 新节点的名称
        node_type: 新节点的类型

    """
    node_json = request.get_json()
    node_name = node_json.get('name')
    node_type = node_json.get('type')

    if not node_name or not node_type:
        return Result.fail('参数错误')

    # 添加节点的cypher语句
    cypher = f'CREATE (n:{node_type} {{name: "{node_name}"}}) RETURN n'
    return execute_option_cypher(cypher,'add_node')


@graph_bp.route('/updateNode', methods=['POST'])
def update_node():
    """
    修改节点信息, 有element-id信息

    -------
    Params:
        node_id: 节点id
        node_name: 节点名称
        node_type: 节点类型

    """
    node_json = request.get_json()
    node_id = node_json.get('id')
    node_name = node_json.get('name')
    node_type = node_json.get('type')

    if not node_id or not node_name or not node_type:
        return Result.fail('参数错误')

    cypher = f'MATCH (n) WHERE elementId(n) = "{node_id}" SET n.name = "{node_name}", n.type = "{node_type}" RETURN n'
    return execute_option_cypher(cypher)


@graph_bp.route('/deleteNode', methods=['DELETE'])
def delete_node():
    """
    删除节点

    -------
    Params:
        node_id: 需要删除的节点id
    """
    node_json = request.get_json()
    node_id = node_json.get('id')

    if not node_id:
        return Result.fail('参数错误')

    cypher = f'MATCH (n) WHERE elementId(n) = "{node_id}" DETACH DELETE n'
    return execute_option_cypher(cypher,'delete_node')
