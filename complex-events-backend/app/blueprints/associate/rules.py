from flask import request

from app.blueprints.associate import associate_bp
from app.models import Result
from app.services.database_service import get_event_link_rules_collection
from app.utils import format_doc


@associate_bp.route('/allRules', methods=['GET'])
def get_all_rules():
    collection = get_event_link_rules_collection()
    rules = collection.find()
    result = [format_doc(rule) for rule in rules]
    if result:
        return Result.success(data=result)
    else:
        return Result.fail(message="未找到任何规则")


@associate_bp.route('/addOrUpdateRule', methods=['POST'])
def add_or_update_rule():
    rule = request.get_json()
    if not rule:
        return Result.fail(message="参数错误")

    collection = get_event_link_rules_collection()
    result = collection.update_one({"rule_title": rule['rule_title']}, {"$set": rule}, upsert=True)
    if result.modified_count > 0 or result.upserted_id:
        return Result.success(message="规则保存成功")
    else:
        return Result.fail(message="规则保存失败")
