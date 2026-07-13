from flask import jsonify
from dataclasses import dataclass, asdict


@dataclass
class Result:
    code: int
    message: str
    data: any = None
    success: bool = None

    def to_json(self):
        result_dict = asdict(self)
        result_dict = {k: v for k, v in result_dict.items() if v is not None}
        return jsonify(result_dict)

    @staticmethod
    def success(data=None, message="success"):
        return Result(20000, message, data, success=True).to_json()

    @staticmethod
    def fail(code=20001, message="fail"):
        return Result(code, message, success=False).to_json()