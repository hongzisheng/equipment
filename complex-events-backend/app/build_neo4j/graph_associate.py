import os
from urllib.parse import urlparse

from app.services.database_service import get_extract_result_collection, get_reports_collection


def build_knowledge_graph_data(ids: list[str] = None):
    """
    从数据库中提取数据并构建成图谱关系数据格式
    """
    if ids:
        result = get_extract_result_collection().find({'id': {'$in': ids}})
    else:
        # 连接数据库并获取所有记录
        result = get_extract_result_collection().find()
    reports_collection = get_reports_collection()
    # 初始化图谱节点和关系集合
    nodes = {}
    relationships = []

    # 用于跟踪已创建的节点，避免重复创建
    node_lookup = {}  # {(type, name): node_id}

    # 节点类型计数器，用于生成唯一ID
    node_counters = {
        'event': 0,
        'resource': 0,
        'person': 0,
        'organization': 0,
        'place': 0,
        'action': 0,
        'time': 0,
        'role': 0,
        'report': 0
    }

    # 用于跟踪已创建的关系，避免重复创建
    relationship_lookup = set()  # {(source_id, target_id, type)}

    def get_or_create_node(node_type, node_name, properties=None):
        """获取已存在的节点或创建新节点"""
        if properties is None:
            properties = {}

        # 检查节点是否已存在
        key = (node_type, node_name)
        if key in node_lookup:
            return node_lookup[key]

        # 创建新节点
        node_id = f"{node_type}_{node_counters[node_type]}"
        nodes[node_id] = {
            'id': node_id,
            'type': node_type,
            'name': node_name,
            'properties': properties
        }
        node_lookup[key] = node_id
        node_counters[node_type] += 1
        return node_id

    def create_relationship(source_id, target_id, rel_type, properties=None):
        """创建关系，避免重复"""
        if properties is None:
            properties = {}

        # 检查关系是否已存在
        rel_key = (source_id, target_id, rel_type)
        if rel_key in relationship_lookup:
            return None

        # 创建新关系
        rel_id = f"rel_{len(relationships)}"
        relationship = {
            'id': rel_id,
            'source': {
                'id': source_id,
                'type': nodes[source_id]['type'],
                'name': nodes[source_id]['name']
            },
            'target': {
                'id': target_id,
                'type': nodes[target_id]['type'],
                'name': nodes[target_id]['name']
            },
            'type': rel_type,
            'properties': properties
        }
        relationships.append(relationship)
        relationship_lookup.add(rel_key)
        return rel_id

    # 处理每条记录
    for record in result:
        # 创建新闻报道节点
        report_node_id = get_or_create_node('report', f"新闻报道「{record.get('id', '')}」",
                                            {'report_id': record.get('id', '')})

        # 创建事件节点
        event_node_id = get_or_create_node('event', record.get('eventName', ''), {'report_id': record.get('id', ''),
                                                                                  'eventType': record.get('eventType',
                                                                                                          '')})

        # 创建新闻报道与事件的关系
        create_relationship(report_node_id, event_node_id, '报道')

        # 创建时间节点
        time_value = record.get('time', '')
        if time_value:
            time_node_id = get_or_create_node('time', time_value)
            # 创建事件与时间的关系
            create_relationship(event_node_id, time_node_id, '发生时间')

        # 处理人物节点和关系
        person_nodes = {}  # 用于存储当前记录中的人物节点，便于后续关联
        for person in record.get('person', []):
            person_name = person.get('personName', '')
            # 创建人物节点
            person_node_id = get_or_create_node('person', person_name)
            person_nodes[person_name] = person_node_id

            # 创建人物与组织的关系
            organization = person.get('organization', '')
            if organization and organization != 'null':
                # 创建组织节点
                org_node_id = get_or_create_node('organization', organization)
                # 创建人物与组织的关系
                create_relationship(person_node_id, org_node_id, '所属')

            # 创建人物与角色的关系
            role = person.get('role', '')
            if role and role != 'null':
                # 创建角色节点
                role_node_id = get_or_create_node('role', role)
                # 创建人物与角色的关系
                create_relationship(person_node_id, role_node_id, '承担')

        # 处理组织节点（独立的组织）
        organizations = record.get('organizations', '')
        if organizations:
            org_list = [org.strip() for org in organizations.split(',')]
            for org in org_list:
                # 创建组织节点
                get_or_create_node('organization', org)

        # 处理地点节点
        places = record.get('places', '')
        place_nodes = {}  # 用于存储当前记录中的地点节点
        if places:
            place_list = [place.strip() for place in places.split(',')]
            for place in place_list:
                # 创建地点节点
                place_node_id = get_or_create_node('place', place)
                place_nodes[place] = place_node_id

        # 处理行动节点和关系
        for action in record.get('actions', []):
            action_name = action.get('actionName', '')
            # 创建行动节点
            action_node_id = get_or_create_node('action', action_name)

            # 创建事件与行动的关系（事件-包括-行动）
            create_relationship(event_node_id, action_node_id, '包括')

            # 处理行动相关的人物关系（人物-主导-行动）
            related_persons = action.get('relatedPerson', '')
            if related_persons and related_persons != 'null':
                person_list = [p.strip() for p in related_persons.split(',')]
                for person_name in person_list:
                    if person_name in person_nodes:
                        # 创建人物与行动的关系
                        create_relationship(person_nodes[person_name], action_node_id, '主导')

            # 处理行动相关的地点关系（行动-发生-地点）
            related_places = action.get('relatedPlace', '')
            if related_places and related_places != 'null':
                place_list = [place.strip() for place in related_places.split(',')]
                for place_name in place_list:
                    if place_name in place_nodes:
                        # 创建行动与地点的关系
                        create_relationship(action_node_id, place_nodes[place_name], '发生地点')

        for url in reports_collection.find_one({'id': record.get('id', '')}).get('resources', []):
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            resource_node = get_or_create_node('resource', filename, {'url': url})
            create_relationship(resource_node, event_node_id, '相关资源')
    # 返回图谱数据
    return {
        'nodes': list(nodes.values()),
        'relationships': relationships
    }


# 执行函数获取图谱数据
if __name__ == "__main__":
    graph_data = build_knowledge_graph_data()
    print("节点数量:", len(graph_data['nodes']))
    print("关系数量:", len(graph_data['relationships']))

    # 打印前几个节点和关系示例
    print("\n前5个节点:")
    for node in graph_data['nodes'][:5]:
        print(f"  {node}")

    print("\n前5个关系:")
    for rel in graph_data['relationships'][:5]:
        print(f"  {rel}")
