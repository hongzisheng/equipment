from flask import Blueprint, current_app

from ...models import Result
from ...services import execute_cypher

graph_bp = Blueprint('graph_bp', __name__)


def execute_option_cypher(cypher: str, opt_type: str = 'update'):
    """
    根据不同的增删改查cypher语句，执行语句，并根据返回结果的长度判断是否执行成功
    """
    try:
        current_app.logger.info(f'执行cypher语句:{cypher}')
        result = execute_cypher(current_app, cypher)
        success_data = None
        if opt_type == 'add_node':
            # 添加需要返回节点elementid
            success_data = result[0].get('n').element_id
        if opt_type == 'add_edge':
            success_data = result[0].get('r').element_id
        if len(result) > 0 or opt_type.startswith('delete'):
            # 删除语句不会返回东西
            return Result.success(data=success_data if success_data else 'success')
        else:
            return Result.fail(message='操作失败')
    except Exception as e:
        return Result.fail(message=f'操作失败,{str(e)}')


from . import graph_blueprint, node_options, edge_options,sub_graph_options,build
