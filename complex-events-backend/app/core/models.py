# models.py
"""数据模型类和数据库访问层

从 algorithm 分支移植，供调度引擎使用。
"""
import sqlite3
import json
from typing import List, Dict, Tuple, Optional


class Worker:
    def __init__(self, id, name, worker_type, is_certified=False, organization=None, compose=None, skill_level=1):
        self.id = id
        self.name = name
        self.type = worker_type
        self.assigned_tasks = []
        self.total_work_minutes = 0
        self.is_certified = is_certified
        self.organization = organization
        self.compose = compose
        self.total_work_days = 0
        self.skill_level = skill_level


class ProcessTemplate:
    """工序模板类，定义每种设备类型的标准工序"""

    def __init__(
        self,
        id: int,
        equipment_type_id: str,
        process_code: str,
        description: str,
        estimated_hours: float,
        required_workers: Dict,
        predecessor_codes: List[str],
        parent_process_code: Optional[str],
        is_major_process: bool,
        material_requirements: Optional[str] = None,
        material_price: Optional[float] = None,
        tools_requirements: Optional[str] = None,
        tools_price: Optional[float] = None,
        worker_price: Optional[float] = None,
    ):
        self.id = id
        self.equipment_type_id = equipment_type_id
        self.process_code = process_code
        self.description = description
        self.estimated_hours = estimated_hours or 0
        self.required_workers = required_workers or {}
        self.predecessor_codes = predecessor_codes or []
        self.parent_process_code = parent_process_code
        self.is_major_process = is_major_process
        self.material_requirements = material_requirements
        self.material_price = material_price or 0
        self.tools_requirements = tools_requirements
        self.tools_price = tools_price or 0
        # 兼容旧接口
        self.name = description
        self.duration = estimated_hours or 0
        self.predecessor_ids = predecessor_codes
        self.worker_price = worker_price or 0


class EquipmentType:
    """设备类型类"""

    def __init__(self, id, name, process_templates=None):
        self.id = id
        self.name = name
        self.process_templates = process_templates or []


class Process:
    """具体的工序实例"""

    def __init__(
        self,
        id,
        name,
        duration,
        equipment_id,
        predecessor_ids,
        worker_requirements,
        is_critical=False,
        requires_certification=False,
    ):
        self.id = id
        self.name = name
        self.duration = duration or 0
        self.equipment_id = equipment_id
        self.predecessor_ids = predecessor_ids or []
        self.worker_requirements = worker_requirements or {}
        self.earliest_start = 0
        self.actual_start = None
        self.actual_end = None
        self.assigned_workers = {}
        self.is_critical = is_critical
        self.requires_certification = requires_certification


class Equipment:
    """具体的设备实例"""

    def __init__(self, id, name, equipment_type, category=""):
        self.id = id
        self.name = name
        self.type = equipment_type
        self.category = category
        self.schedule = []
        self.processes = []
        self.milestone_processes = []

    def generate_processes(self):
        """根据设备类型的工序模板生成工序实例"""
        template_id_to_instance_id = {}
        template_map = {}
        major_process_templates = {}
        sub_process_templates = {}
        for template in self.type.process_templates:
            instance_id = f"{self.id}_{template.process_code}"
            template_id_to_instance_id[template.process_code] = instance_id
            template_map[template.process_code] = template
            if template.is_major_process:
                major_process_templates[template.process_code] = template
            else:
                parent_code = template.parent_process_code
                if parent_code not in sub_process_templates:
                    sub_process_templates[parent_code] = []
                sub_process_templates[parent_code].append(template)

        for template in self.type.process_templates:
            instance_id = template_id_to_instance_id[template.process_code]
            instance_predecessor_ids = []
            for pred_code in template.predecessor_codes:
                if pred_code in template_id_to_instance_id:
                    instance_predecessor_ids.append(
                        template_id_to_instance_id[pred_code]
                    )

            process = Process(
                id=instance_id,
                name=template.description,
                duration=template.estimated_hours,
                equipment_id=self.id,
                predecessor_ids=instance_predecessor_ids,
                worker_requirements=template.required_workers,
                is_critical=False,
                requires_certification=False,
            )
            self.processes.append(process)

        # 为每个一级工序创建里程碑工序
        for major_code, major_template in major_process_templates.items():
            sub_processes_for_major = sub_process_templates.get(major_code, [])
            if not sub_processes_for_major:
                continue
            milestone_id = f"{self.id}_{major_code}_MILESTONE"
            milestone_predecessors = [
                f"{self.id}_{sub_template.process_code}"
                for sub_template in sub_processes_for_major
            ]
            milestone_process = Process(
                id=milestone_id,
                name=f"{major_template.description} - 完成里程碑",
                duration=0,
                equipment_id=self.id,
                predecessor_ids=milestone_predecessors,
                worker_requirements={},
                is_critical=False,
                requires_certification=False,
            )
            self.milestone_processes.append(milestone_process)
            self.processes.append(milestone_process)

    def get_all_processes(self):
        return self.processes


class Material:
    def __init__(self, id, name, price, stock_quantity, unit):
        self.id = id
        self.name = name
        self.price = price
        self.stock_quantity = stock_quantity
        self.unit = unit
        self.created_at = None
        self.updated_at = None


class MaintenanceTool:
    def __init__(self, id, name, tool_type, capacity, daily_rental_cost, is_available, requires_operator):
        self.id = id
        self.name = name
        self.tool_type = tool_type
        self.capacity = capacity
        self.daily_rental_cost = daily_rental_cost
        self.is_available = is_available
        self.requires_operator = requires_operator


# ========== 数据库访问层 ==========
class DatabaseManager:
    """数据库管理类，封装所有数据库操作"""

    @staticmethod
    def load_equipment_types_from_db(db_path: str) -> Dict:
        """从数据库加载设备类型信息，并关联该类型的工序模板"""
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT id, name FROM equipment_types")
            equipment_types = {}
            for row in c.fetchall():
                eq_type_id, eq_type_name = row
                equipment_types[eq_type_id] = EquipmentType(eq_type_id, eq_type_name)

            for eq_type_id, eq_type_obj in equipment_types.items():
                c.execute(
                    """
                    SELECT id, process_code, description, estimated_hours,
                           required_workers, predecessor_codes, parent_process_code,
                           is_major_process, material_requirements, material_price,
                           tools_requirements, tools_price, equipment_type_id
                    FROM process_templates
                    WHERE equipment_type_id = ?
                """,
                    (eq_type_id,),
                )
                rows = c.fetchall()
                templates = []
                for row in rows:
                    template = ProcessTemplate(
                        id=row[0],
                        process_code=row[1],
                        description=row[2],
                        estimated_hours=row[3],
                        required_workers=json.loads(row[4]) if row[4] else {},
                        predecessor_codes=json.loads(row[5]) if row[5] else [],
                        parent_process_code=row[6],
                        is_major_process=bool(row[7]),
                        material_requirements=row[8],
                        material_price=row[9],
                        tools_requirements=row[10],
                        tools_price=row[11],
                        equipment_type_id=row[12],
                    )
                    templates.append(template)
                eq_type_obj.process_templates = templates

            conn.close()
            return equipment_types
        except Exception as e:
            print(f"从数据库加载设备类型时出错: {str(e)}")
            return {}

    @staticmethod
    def load_workers_from_db(db_path: str) -> List[Tuple]:
        """从数据库加载工人信息"""
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute(
                "SELECT id, worker_type_id, name, is_certified, organization, compose, skill_level FROM workers"
            )
            worker_records = c.fetchall()
            conn.close()
            return worker_records
        except Exception as e:
            print(f"从数据库加载工人时出错: {str(e)}")
            return []

    @staticmethod
    def load_selected_workers_from_db(db_path: str) -> List[Tuple]:
        """从数据库加载选中的工人信息"""
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute(
                """
                SELECT w.id, w.worker_type_id, w.name, w.is_certified, w.organization, w.compose, w.skill_level
                FROM selected_workers sw
                JOIN workers w ON sw.id = w.id
                ORDER BY w.worker_type_id, w.id
            """
            )
            worker_records = c.fetchall()
            conn.close()
            return worker_records
        except Exception as e:
            print(f"从数据库加载选中工人时出错: {str(e)}")
            return []
