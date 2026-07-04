from flask import jsonify
from dataclasses import dataclass, asdict

# 定义公共响应类
@dataclass
class Result:
    code: int
    message: str
    data: any = None

    def to_json(self):
        # 直接将Result对象转换为Flask的JSON响应
        return jsonify(asdict(self))

    @staticmethod
    def success(data=None, message="success"):
        return Result(20000, message, data).to_json()

    @staticmethod
    def fail(code=20001, message="fail"):
        return Result(code, message).to_json()
