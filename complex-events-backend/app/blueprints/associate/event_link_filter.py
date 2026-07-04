import flask
from flask import request

from app.models import Result
from app.blueprints.associate import associate_bp
from app.services import execute_cypher

from app.services.database_service import get_extract_result_collection


def generate_link_cypher(start_report_id: str, end_report_id: str, relationship_name: str):
    """
    生成neo4j的cypher语句
    用于在图谱中创建关系（如果关系不存在则创建）
    """
    return f"""
    MATCH (start_node:Event {{report_id: '{start_report_id}'}})
    MATCH (end_node:Event {{report_id: '{end_report_id}'}})
    MERGE (start_node)-[r:`{relationship_name}`]-(end_node)
    """


def associate_in_graph(id_match_list: list[tuple], type_name: str):
    """
    将匹配好的关系在neo4j的图谱中连起来
    """
    for start_id, end_id in id_match_list:
        link_cypher = generate_link_cypher(start_id, end_id, type_name)
        execute_cypher(flask.current_app, link_cypher)


def build_match_pair(match_dict: dict[str, list[str]], main_id: str = None):
    # 查找共同元素的文档对
    candidate_id_set = set()
    for match_key, doc_ids in match_dict.items():
        if len(doc_ids) > 1:  # 只有当多于一个文档包含相同元素时才考虑
            for i in range(len(doc_ids)):
                for j in range(i + 1, len(doc_ids)):
                    if main_id is None:
                        # 无主ID时创建无序配对元组
                        pair = tuple(sorted([doc_ids[i], doc_ids[j]]))
                        candidate_id_set.add(pair)
                    elif main_id == doc_ids[i] or main_id == doc_ids[j]:
                        # 有主ID时保证主ID在前
                        other_id = doc_ids[j] if main_id == doc_ids[i] else doc_ids[i]
                        pair = (main_id, other_id)
                        candidate_id_set.add(pair)
    return candidate_id_set


@associate_bp.route('/filterCommonPerson', methods=['GET'])
def filter_common_person():
    try:
        # 获取id
        main_report_id = request.args.get('mainReportId')

        extract_result_collection = get_extract_result_collection()
        all_docs = list(extract_result_collection.find())

        # 预处理：建立人名到文档ID的映射
        person_name_to_docs = {}
        for doc in all_docs:
            doc_id = doc.get('id')
            persons = doc.get('person', [])
            for person in persons:
                person_name = person.get('personName')
                if person_name and person_name != 'null':
                    if person_name not in person_name_to_docs:
                        person_name_to_docs[person_name] = []
                    person_name_to_docs[person_name].append(doc_id)

        # 查找共同人物的文档对
        candidate_id_set = build_match_pair(person_name_to_docs, main_report_id)

        return Result.success(data=list(candidate_id_set), message=f"找到{len(candidate_id_set)}条具有相同人物的数据")
    except Exception as e:
        return Result.fail(str(e))


@associate_bp.route('/filterCommonPlace', methods=['GET'])
def filter_common_place():
    try:
        main_report_id = request.args.get('mainReportId')

        extract_result_collection = get_extract_result_collection()
        all_docs = list(extract_result_collection.find())

        # 预处理：建立地点名到文档ID的映射
        place_name_to_docs = {}
        for doc in all_docs:
            doc_id = doc.get('id')
            places = doc.get('places', [])
            for place in places.split(','):
                if place not in place_name_to_docs:
                    place_name_to_docs[place] = []
                place_name_to_docs[place].append(doc_id)

        result_set = build_match_pair(place_name_to_docs, main_report_id)
        return Result.success(data=list(result_set), message=f"找到{len(result_set)}条具有相同地点的数据")
    except Exception as e:
        return Result.fail(str(e))


@associate_bp.route('/filterCommonOrganization', methods=['GET'])
def filter_common_organization():
    try:
        main_report_id = request.args.get('mainReportId')

        extract_result_collection = get_extract_result_collection()
        all_docs = list(extract_result_collection.find())

        # 预处理：建立地点名到文档ID的映射
        organization_name_to_docs = {}
        for doc in all_docs:
            doc_id = doc.get('id')
            organizations = doc.get('organizations', [])
            for org in organizations.split(','):
                if org not in organization_name_to_docs:
                    organization_name_to_docs[org] = []
                organization_name_to_docs[org].append(doc_id)

        result_set = build_match_pair(organization_name_to_docs, main_report_id)
        return Result.success(data=list(result_set), message=f"找到{len(result_set)}条具有相同组织的数据")
    except Exception as e:
        return Result.fail(str(e))
