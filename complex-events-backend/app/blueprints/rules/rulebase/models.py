# models.py
import sqlite3
import json
from typing import List, Dict, Tuple, Optional

class Worker:
    def __init__(self,id,name, worker_type,is_certified=False, organization=None,compose=None,skill_level=1):
        self.id = id
        self.name = name  # 姓名
        self.type = worker_type  # 工种
        self.assigned_tasks = []  # 分配的任务列表
        self.total_work_minutes = 0  # 总工作时间(分钟)
        self.is_certified = is_certified  # 新增：是否持证
        self.organization = organization
        self.compose = compose
        self.total_work_days = 0 
        self.skill_level = skill_level  # 技能等级，默认为1，数值越大表示技能越高

class ProcessTemplate:
    """工序模板类，定义每种设备类型的标准工序"""
    def __init__(self, id: int,equipment_type_id: str, process_code: str, description: str, 
                 estimated_hours: float, required_workers: Dict, predecessor_codes: List[str],
                 parent_process_code: Optional[str], is_major_process: bool,
                 material_requirements: Optional[str] = None, material_price: Optional[float] = None,
                 tools_requirements: Optional[str] = None, tools_price: Optional[float] = None,worker_price: Optional[float] = None):
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
        
        # 兼容旧接口的属性
        self.id = process_code
        self.name = description
        self.duration = estimated_hours or 0
        self.predecessor_ids = predecessor_codes
        self.worker_price = worker_price or 0
class EquipmentType:
    """设备类型类，定义每种设备类型的属性和标准工序"""
    def __init__(self, id, name, process_templates=None):
        self.id = id
        self.name = name  # 该设备类型的标准工序模板列表
        self.process_templates = process_templates or []

class Process:
    """具体的工序实例"""
    def __init__(self, id, name, duration, equipment_id, predecessor_ids, worker_requirements, 
                 is_critical=False, requires_certification=False):
        self.id = id
        self.name = name
        self.duration = duration or 0  # 工序需要的时间(小时)
        self.equipment_id = equipment_id  # 所需设备ID
        self.predecessor_ids = predecessor_ids or {}  # 前置工序ID列表
        self.worker_requirements = worker_requirements or {}  # 人员需求，如{"钳工": 3, "电工": 1}
        self.earliest_start = 0  # 最早开始时间(分钟)
        self.actual_start = None  # 实际开始时间(分钟)
        self.actual_end = None  # 实际结束时间(分钟)
        self.assigned_workers = {}  # 分配的工人，按工种分组
        self.is_critical = is_critical  # 是否为关键工序
        self.requires_certification = requires_certification  # 是否需要持证人员

class Equipment:
    """具体的设备实例"""
    def __init__(self, id, name, equipment_type, category=''):
        self.id = id
        self.name = name
        self.type = equipment_type  # 设备类型
        self.category = category  # 添加设备种类
        self.schedule = []  # 设备上的工序安排
        self.processes = [] 
        self.milestone_processes = [] # 该设备的工序实例列表
        
    def generate_processes(self):
        # 第一阶段：创建所有实例ID映射
        template_id_to_instance_id = {}
        template_map = {}
        major_process_templates = {}  # 一级工序模板
        sub_process_templates = {}
        for template in self.type.process_templates:
            instance_id = f"{self.id}_{template.process_code}"
            template_id_to_instance_id[template.process_code] = instance_id
            template_map[template.process_code] = template
            if template.is_major_process:
                # 这是一级工序
                major_process_templates[template.process_code] = template
            else:
                # 这是二级工序，按父工序分组
                parent_code = template.parent_process_code
                if parent_code not in sub_process_templates:
                    sub_process_templates[parent_code] = []
                sub_process_templates[parent_code].append(template)
        
        # 第二阶段：创建工序实例并处理依赖关系
        for template in self.type.process_templates:
            # 包含一级工序和二级工序
            instance_id = template_id_to_instance_id[template.process_code]
            
            instance_predecessor_ids = {}
            for pred_code in template.predecessor_codes:
                if pred_code in template_id_to_instance_id:
                    instance_predecessor_ids[template_id_to_instance_id[pred_code]] = "finish_to_start"
                else:
                    print(f"警告: 工序 {template.process_code} 的前置工序 {pred_code} 未找到")
            
            process = Process(
                id=instance_id,
                name=template.description,
                duration=template.estimated_hours,
                equipment_id=self.id,
                predecessor_ids=instance_predecessor_ids,
                worker_requirements=template.required_workers,
                is_critical=False,
                requires_certification=False
            )
            
            self.processes.append(process)
        
        # 第三阶段：为每个一级工序创建里程碑工序
        for major_code, major_template in major_process_templates.items():
            # 找到该一级工序下的所有二级工序
            sub_processes_for_major = sub_process_templates.get(major_code, [])
            
            if not sub_processes_for_major:
                print(f"警告: 一级工序 {major_code} 没有对应的二级工序")
                continue
            
            # 里程碑工序的ID
            milestone_id = f"{self.id}_{major_code}_MILESTONE"
            
            # 里程碑工序的前置工序是该一级工序下的所有二级工序
            milestone_predecessors = {}
            for sub_template in sub_processes_for_major:
                sub_instance_id = f"{self.id}_{sub_template.process_code}"
                milestone_predecessors[sub_instance_id] = "finish_to_start"
            
            # 创建里程碑工序（虚拟工序，持续时间为0）
            milestone_process = Process(
                id=milestone_id,
                name=f"{major_template.description} - 完成里程碑",
                duration=0,  # 里程碑工序不占用时间
                equipment_id=self.id,
                predecessor_ids=milestone_predecessors,
                worker_requirements={},  # 不需要工人
                is_critical=False,
                requires_certification=False
            )
            
            self.milestone_processes.append(milestone_process)
            self.processes.append(milestone_process)  # 也加入到总工序列表中
        
        # 第四阶段：处理一级工序之间的依赖关系
        for major_code, major_template in major_process_templates.items():
            if not major_template.predecessor_codes:
                continue
                
            # 找到该一级工序下的第一个二级工序
            # 我们将一级工序的依赖关系添加到第一个二级工序上
            sub_processes_for_major = sub_process_templates.get(major_code, [])
            if not sub_processes_for_major:
                continue
                
            # 找到第一个没有前置依赖的二级工序，或者第一个二级工序
            first_sub_process = None
            for sub_template in sub_processes_for_major:
                sub_instance_id = f"{self.id}_{sub_template.process_code}"
                for p in self.processes:
                    if p.id == sub_instance_id and not p.predecessor_ids:
                        first_sub_process = p
                        break
                if first_sub_process:
                    break
            
            # 如果没有找到没有前置依赖的二级工序，就使用第一个二级工序
            if not first_sub_process:
                sub_template = sub_processes_for_major[0]
                sub_instance_id = f"{self.id}_{sub_template.process_code}"
                for p in self.processes:
                    if p.id == sub_instance_id:
                        first_sub_process = p
                        break
            
            if not first_sub_process:
                continue
                
            # 为这个二级工序添加一级工序依赖
            for pred_major_code in major_template.predecessor_codes:
                pred_milestone_id = f"{self.id}_{pred_major_code}_MILESTONE"
                
                # 检查这个里程碑工序是否存在
                milestone_exists = any(p.id == pred_milestone_id for p in self.processes)
                if milestone_exists and pred_milestone_id not in first_sub_process.predecessor_ids:
                    first_sub_process.predecessor_ids[pred_milestone_id] = "finish_to_start"
                    print(f"为工序 {first_sub_process.id} 添加一级工序依赖: {pred_milestone_id}")
    def get_all_processes(self):
        """获取所有工序（包括里程碑工序）"""
        return self.processes
class Material:
    """材料类"""
    def __init__(self, id, name, price, stock_quantity, unit):
        self.id = id
        self.name = name
        self.price = price  # 单价
        self.stock_quantity = stock_quantity  # 库存数量
        self.unit = unit  # 计量单位
        self.created_at = None
        self.updated_at = None

class MaintenanceTool:
    """维修器具类"""
    def __init__(self, id, name, tool_type, capacity, daily_rental_cost, is_available, requires_operator):
        self.id = id
        self.name = name
        self.tool_type = tool_type  # 器具类型
        self.capacity = capacity  # 容量/规格
        self.daily_rental_cost = daily_rental_cost  # 日租金
        self.is_available = is_available  # 是否可用
        self.requires_operator = requires_operator  # 是否需要操作员

# ========== 数据库访问层 ==========
class DatabaseManager:
    """数据库管理类，封装所有数据库操作"""
    
    @staticmethod
    def load_process_templates_from_db(db_path: str) -> Dict:
        """从数据库加载所有设备类型的工序模板"""
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # 获取所有设备类型
        c.execute('SELECT DISTINCT equipment_type_id FROM process_templates')
        equipment_types_data = c.fetchall()
        
        equipment_processes = {}
        for (eq_type_id,) in equipment_types_data:
            # 获取该设备类型的所有工序模板
            c.execute('''
                SELECT id,equipment_type_id, process_code, description, estimated_hours, 
                       required_workers, predecessor_codes, parent_process_code, 
                       is_major_process, material_requirements, material_price, 
                       tools_requirements, tools_price
                FROM process_templates 
                WHERE equipment_type_id = ?
                ORDER BY process_code
            ''', (eq_type_id,))
            
            processes = []
            for row in c.fetchall():
                (id,equipment_type_id, process_code, description, estimated_hours, 
                 required_workers_json, predecessor_codes_json, parent_process_code,
                 is_major_process, material_requirements, material_price,
                 tools_requirements, tools_price) = row
                
                # 解析JSON字段
                required_workers = json.loads(required_workers_json) if required_workers_json else {}
                predecessor_codes = json.loads(predecessor_codes_json) if predecessor_codes_json else []
                
                # 转换布尔值
                is_major_process_bool = bool(is_major_process)
                
                # 创建ProcessTemplate对象
                process = ProcessTemplate(
                    id=id,
                    equipment_type_id=equipment_type_id,
                    process_code=process_code,
                    description=description,
                    estimated_hours=estimated_hours,
                    required_workers=required_workers,
                    predecessor_codes=predecessor_codes,
                    parent_process_code=parent_process_code,
                    is_major_process=is_major_process_bool,
                    material_requirements=material_requirements,
                    material_price=material_price,
                    tools_requirements=tools_requirements,
                    tools_price=tools_price
                )
                processes.append(process)
            
            # 使用设备类型ID作为键
            equipment_processes[eq_type_id] = processes
        
        conn.close()
        return equipment_processes
    
    @staticmethod
    def load_equipment_types_from_db(db_path: str) -> Dict:
        """从数据库加载设备类型信息，并关联该类型的工序模板"""
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            
            # 1. 加载设备类型基本信息
            c.execute('SELECT id, name FROM equipment_types')
            equipment_types = {}
            for row in c.fetchall():
                eq_type_id, eq_type_name = row
                equipment_types[eq_type_id] = EquipmentType(eq_type_id, eq_type_name)
            
            # 2. 为每个设备类型加载其工序模板
            for eq_type_id, eq_type_obj in equipment_types.items():
                c.execute('''
                    SELECT id,process_code, description, estimated_hours, 
                        required_workers, worker_price, material_requirements,
                        tools_requirements, is_major_process, parent_process_code,
                        predecessor_codes, equipment_type_id
                    FROM process_templates
                    WHERE equipment_type_id = ?
                ''', (eq_type_id,))
                rows = c.fetchall()
                templates = []
                for row in rows:
                    template = ProcessTemplate(
                        id=row[0],
                        process_code=row[1],
                        description=row[2],
                        estimated_hours=row[3],
                        required_workers=json.loads(row[4]) if row[4] else {},
                        worker_price=row[5],
                        material_requirements=row[6],
                        tools_requirements=row[7],
                        is_major_process=bool(row[8]),
                        parent_process_code=row[9],
                        predecessor_codes=json.loads(row[10]) if row[10] else [],
                        equipment_type_id=row[11]
                    )
                    templates.append(template)
                eq_type_obj.process_templates = templates
            
            conn.close()
            return equipment_types
        except Exception as e:
            print(f"从数据库加载设备类型时出错: {str(e)}")
            return {}
    
    @staticmethod
    def load_equipment_instances_from_db(db_path: str) -> List[Tuple]:
        """从数据库加载设备实例信息"""
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            # 查询设备实例表
            c.execute('''
            SELECT ei.id, ei.name, ei.equipment_type_id, et.name as equipment_type_name,ei.category
            FROM equipment_instances ei
            LEFT JOIN equipment_types et ON ei.equipment_type_id = et.id
            ORDER BY ei.id
        ''')
            equipment_records = c.fetchall()
            conn.close()
            return equipment_records
        except Exception as e:
            print(f"从数据库加载设备时出错: {str(e)}")
            return []
    
    @staticmethod
    def load_selected_equipment_instances_from_db(db_path:str) -> List[Tuple]:
        """从 selected_equipments 表加载选中的设备实例"""
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            
            c.execute('''
                SELECT id, name, equipment_type_id, equipment_type_name, category
                FROM selected_equipments
                ORDER BY id
            ''')
            
            equipment_records = c.fetchall()
            conn.close()
            
            return equipment_records
            
        except sqlite3.Error as e:
            print(f"加载选中设备失败: {e}")
            return []
    @staticmethod
    def load_workers_from_db(db_path: str) -> List[Tuple]:
        """从数据库加载工人信息"""
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            # 查询工人表
            c.execute('SELECT id,worker_type_id,name,is_certified,organization,compose,skill_level FROM workers')
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
            # 联查selected_workers和workers表，获取选中工人的详细信息
            c.execute('''
                SELECT w.id, w.worker_type_id, w.name, w.is_certified, w.organization, w.compose, w.skill_level
                FROM selected_workers sw
                JOIN workers w ON sw.id = w.id
                ORDER BY w.worker_type_id, w.id
            ''')
            worker_records = c.fetchall()
            conn.close()
            return worker_records
        except Exception as e:
            print(f"从数据库加载选中工人时出错: {str(e)}")
            return []

    @staticmethod
    def clear_selected_workers(db_path: str) -> bool:
        """清空选中的工人表"""
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute('DELETE FROM selected_workers')
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"清空选中工人表时出错: {str(e)}")
            return False

    @staticmethod
    def add_selected_workers(db_path: str, worker_ids: List[int]) -> bool:
        """批量添加选中的工人"""
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            
            # 使用事务批量插入
            c.execute('BEGIN TRANSACTION')
            for worker_id in worker_ids:
                c.execute('INSERT INTO selected_workers (worker_id) VALUES (?)', (worker_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"添加选中工人时出错: {str(e)}")
            conn.rollback()
            return False
    @staticmethod
    def load_materials_from_db(db_path: str) -> List[Material]:
        """从数据库加载所有材料信息"""
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            
            c.execute('''
                SELECT id, name, price, stock_quantity, unit
                FROM materials
            ''')
            
            materials = []
            for row in c.fetchall():
                material = Material(
                    id=row[0],
                    name=row[1],
                    price=row[2],
                    stock_quantity=row[3],
                    unit=row[4]
                )
                materials.append(material)
            
            conn.close()
            return materials
        except Exception as e:
            print(f"从数据库加载材料时出错: {str(e)}")
            return []
    @staticmethod
    def get_selected_workers_count(db_path: str) -> int:
        """获取选中的工人数量"""
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM selected_workers')
            count = c.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            print(f"获取选中工人数量时出错: {str(e)}")
            return 0

    @staticmethod
    def load_maintenance_tools_from_db(db_path: str) -> List[MaintenanceTool]:
        """从数据库加载所有维修器具信息"""
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            
            c.execute('''
                SELECT id, name, tool_type, capacity, daily_rental_cost, is_available, requires_operator
                FROM maintenance_tools
            ''')
            
            tools = []
            for row in c.fetchall():
                tool = MaintenanceTool(
                    id=row[0],
                    name=row[1],
                    tool_type=row[2],
                    capacity=row[3],
                    daily_rental_cost=row[4],
                    is_available=bool(row[5]),
                    requires_operator=bool(row[6])
                )
                tools.append(tool)
            
            conn.close()
            return tools
        except Exception as e:
            print(f"从数据库加载维修器具时出错: {str(e)}")
            return []

# ========== 便捷函数 ==========

def load_equipment_types_from_db(db_path: str) -> Dict:
    """加载设备类型（兼容旧接口）"""
    return DatabaseManager.load_equipment_types_from_db(db_path)

def load_equipment_instances(db_path: str) -> List[Tuple]:
    """加载设备实例（便捷函数）"""
    return DatabaseManager.load_equipment_instances_from_db(db_path)

def load_workers(db_path: str) -> List[Tuple]:
    """加载工人信息（便捷函数）"""
    return DatabaseManager.load_workers_from_db(db_path)

def load_materials(db_path: str) -> List[Material]:
    """加载材料信息（便捷函数）"""
    return DatabaseManager.load_materials_from_db(db_path)

def load_maintenance_tools(db_path: str) -> List[MaintenanceTool]:
    """加载维修器具信息（便捷函数）"""
    return DatabaseManager.load_maintenance_tools_from_db(db_path)
def load_selected_workers(db_path: str) -> List[Tuple]:
    """加载选中的工人信息（便捷函数）"""
    return DatabaseManager.load_selected_workers_from_db(db_path)

def load_selected_equipment_instances(db_path: str) -> List[Tuple]:
    return DatabaseManager.load_selected_equipment_instances_from_db(db_path)
def clear_selected_workers(db_path: str) -> bool:
    """清空选中的工人表（便捷函数）"""
    return DatabaseManager.clear_selected_workers(db_path)

def add_selected_workers(db_path: str, worker_ids: List[int]) -> bool:
    """批量添加选中的工人（便捷函数）"""
    return DatabaseManager.add_selected_workers(db_path, worker_ids)
def get_selected_workers_count(db_path: str) -> int:
    """获取选中的工人数量（便捷函数）"""
    return DatabaseManager.get_selected_workers_count(db_path)