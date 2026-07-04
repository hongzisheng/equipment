import flask
from flask import request

from app.models import Result
from app.services import execute_cypher
from . import graph_bp


def _process_node_record(node, nodes, keyword_filter=None):
    properties = dict(node)
    node_data = {
        "index": node.element_id,
        "id": node.element_id,
        "name": properties.get('name', ''),
        "label": properties.get('name', ''),
        "group": list(node.labels)[0] if node.labels else ''
    }

    # 如果提供了关键词过滤器，则进行过滤
    if keyword_filter and keyword_filter not in node_data['label']:
        pass  # 不添加到nodes中
    else:
        nodes[node.element_id] = node_data


def _process_edge_record(record, edge_key_name):
    # 处理关系r
    if edge_key_name in record.keys() and record[edge_key_name] is not None:
        start_node_element_id = record[edge_key_name].start_node.element_id
        end_node_element_id = record[edge_key_name].end_node.element_id
        edge_data = {
            "index": record[edge_key_name].id,
            "id": record[edge_key_name].element_id,
            "label": record[edge_key_name].type,
            "name": record[edge_key_name].type,
            "from": start_node_element_id,
            "to": end_node_element_id,
            "properties": dict(record[edge_key_name])
        }
        return edge_data
    else:
        return None


def __format_node_edges_response(nodes: dict, edges: list):
    """
    格式化nodes和edges为vis.js兼容的格式

    Args:
        nodes (dict): 包含节点信息的字典，key为节点ID，value为节点数据
        edges (list): 包含边信息的列表，每个元素为一个边的字典数据

    Returns:
        dict: 包含nodes和edges的字典，格式化为vis.js兼容的格式
              - nodes: 包含所有节点信息的列表
              - edges: 包含所有边信息的列表，仅包含两端节点都存在的边
    """
    # 转换nodes字典为列表
    nodes_list = list(nodes.values())
    node_ids_list = list(nodes.keys())
    # 边的两个节点同时存在才添加
    edges = [edge for edge in edges if edge['from'] in node_ids_list and edge['to'] in node_ids_list]
    return {
        "nodes": nodes_list,
        "edges": edges
    }


def _process_graph_records(records, keyword_filter=None):
    """
    处理图数据库查询结果，转换为vis.js兼容的格式

    Args:
        records: 图数据库查询结果记录
        keyword_filter: 可选的关键词过滤器

    Returns:
        dict: 包含nodes和edges的字典
    """
    nodes = {}
    edges = []

    # 用于统计每个节点的度数
    edge_node_degree_count = {}
    max_degree = 20  # 最大度数限制

    for record in records:
        # 处理孤立节点
        if 'x' in record.keys() and record['x'] is not None:
            _process_node_record(record['x'], nodes, keyword_filter)
        # 处理节点n
        if 'n' in record.keys() and record['n'] is not None:
            _process_node_record(record['n'], nodes, keyword_filter)

        # 处理节点m
        if 'm' in record.keys() and record['m'] is not None:
            _process_node_record(record['m'], nodes, keyword_filter)

        # 处理关系r
        if 'r' in record.keys() and record['r'] is not None:
            edge_data = _process_edge_record(record, 'r')
            # 避免重复添加关系
            if edge_data is not None and edge_data not in edges:
                # 检查连接的节点度数是否超过限制
                from_node = edge_data['from']
                to_node = edge_data['to']

                # 更新节点度数计数
                edge_node_degree_count[from_node] = edge_node_degree_count.get(from_node, 0) + 1
                edge_node_degree_count[to_node] = edge_node_degree_count.get(to_node, 0) + 1

                # 只有当两个节点的度数都没有超过限制时才添加边
                if edge_node_degree_count[from_node] <= max_degree and edge_node_degree_count[to_node] <= max_degree:
                    edges.append(edge_data)
                else:
                    # 如果超过限制，减少计数（因为边没有被添加）
                    edge_node_degree_count[from_node] -= 1
                    edge_node_degree_count[to_node] -= 1

    # 从edge_node_degree_count 出发，判断所有与边相连过的节点
    # 然后判断和边相连的节点的度是0，则删除该节点（能够避免非度数超过导致的孤立节点，就是原来就有的孤立节点还是会存在）
    for node_key in edge_node_degree_count:
        if edge_node_degree_count[node_key] == 0:
            del nodes[node_key]

    return __format_node_edges_response(nodes, edges)


@graph_bp.route('/latest', methods=['GET'])
def get_latest_node():
    """
    获取最新创建或修改的一批节点
    以及
    和节点相连的边
    """
    try:
        node_limit = int(request.args.get('node_limit', 25))
        cypher = f"""
            MATCH (x)
            WHERE x.updatedAt IS NOT NULL
            WITH x 
            ORDER BY x.updatedAt DESC
            LIMIT {node_limit}
            OPTIONAL MATCH (n)-[r]-(m)
            WHERE n = x OR m = x
            RETURN x,m,n,r
        """
        records = execute_cypher(flask.current_app, cypher)

        graph_data = _process_graph_records(records)
        return Result.success(message="查询成功", data=graph_data)
    except Exception as e:
        return Result.fail(code=500, message=f"查询失败: {str(e)}")


@graph_bp.route('/search', methods=['POST'])
def search_graph_data():
    try:
        # 从请求中获取keyword参数，支持JSON和表单数据
        if request.is_json:
            keyword = request.json.get('keyword', '')
            node_limit = request.json.get('node_limit', 50)
        else:
            # 处理表单数据或查询参数
            keyword = request.form.get('keyword', '') or request.args.get('keyword', '')
            node_limit = request.form.get('node_limit') or request.args.get('node_limit', 50)

        if not keyword:
            return Result.fail(code=20001, message="关键词不能为空")

        # 明确指明无限制
        if node_limit != 'unlimited':
            node_limit = int(node_limit)
            # 根据关键词构建cypher 语句，查找包含关键词的节点及其相关节点和关系
            cypher = f"""
                MATCH (x)
                WHERE x.name CONTAINS '{keyword}'
                WITH x
                LIMIT {node_limit}
                OPTIONAL MATCH (n)-[r]-(m)
                WHERE n = x OR m = x
                RETURN x,m,n,r
                """
        else:
            cypher = f"""
            MATCH (x)
            WHERE x.name CONTAINS '{keyword}'
            WITH x
            OPTIONAL MATCH (n)-[r]-(m)
            WHERE n = x OR m = x
            RETURN x,m,n,r
            """

        records = execute_cypher(flask.current_app, cypher)

        # 使用公共处理函数处理记录
        graph_data = _process_graph_records(records, keyword_filter=keyword)

        return Result.success(message="查询成功", data=graph_data)

    except Exception as e:
        return Result.fail(code=500, message=f"查询失败: {str(e)}")


@graph_bp.route('/expandNode/<string:node_id>', methods=['GET'])
def search_graph_data_by_id(node_id):
    """
    根据节点ID查询与该节点相关的所有节点和关系

    Args:
        node_id (int): 节点ID

    Returns:
        Result: 包含相关节点和关系的数据
    """
    try:
        # 构建Cypher查询语句，查找指定ID的节点及其相关节点和关系
        cypher = f"""
            MATCH (n)-[r]-(m)
            WHERE elementId(n) = '{node_id}'
            RETURN n, r, m
            """

        records = execute_cypher(flask.current_app, cypher)

        # 如果没有找到记录，返回空结果
        if not records:
            return Result.success(message="未找到相关节点和关系", data={"nodes": [], "edges": []})

        # 使用公共处理函数处理记录（不需要关键词过滤）
        graph_data = _process_graph_records(records)

        return Result.success(message="查询成功", data=graph_data)

    except Exception as e:
        return Result.fail(code=500, message=f"查询失败: {str(e)}")


@graph_bp.route('/expandCommonNodes', methods=['POST'])
def expand_common_nodes():
    try:
        request_json = request.get_json()
        center_node_id = request_json.get('centerNodeId')
        common_node_type = request_json.get('commonNodeType')
        if not center_node_id or not common_node_type:
            return Result.fail(code=20001, message="参数错误")

        cypher = f"""
         MATCH (n:Event)
         WHERE elementId(n) = '{center_node_id}'
         MATCH path = (n)-[*1..2]-(cmtp:{common_node_type})-[*1..2]-(s:Event)
         WHERE s <> n
         UNWIND nodes(path) AS intermediate_node
         UNWIND relationships(path) AS intermediate_relationship
         RETURN DISTINCT intermediate_node, intermediate_relationship
    
        """
        records = execute_cypher(flask.current_app, cypher)
        nodes = {}
        edges = []

        for record in records:
            #  处理每一个record的节点
            if 'intermediate_node' in record.keys() and record['intermediate_node'] is not None:
                _process_node_record(record['intermediate_node'], nodes)
            #  处理每一个record的边
            edge_data = _process_edge_record(record, 'intermediate_relationship')
            if edge_data is not None and edge_data not in edges:
                edges.append(edge_data)

        data = __format_node_edges_response(nodes, edges)
        return Result.success(message="查询成功", data=data)
    except Exception as e:
        return Result.fail(code=500, message=f"查询失败: {str(e)}")
