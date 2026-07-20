from sqlalchemy import Column, Integer, String, Text, REAL, BOOLEAN, TIMESTAMP, DATETIME, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class WorkerType(Base):
    __tablename__ = 'worker_types'
    id = Column(String(50), primary_key=True)
    name = Column(String(50))
    description = Column(Text)
    requires_certification = Column(BOOLEAN)
    created_at = Column(TIMESTAMP)
    price = Column(Integer)


class Worker(Base):
    __tablename__ = 'workers'
    id = Column(Integer, primary_key=True)
    worker_type_id = Column(String(50))
    name = Column(String(100))
    status = Column(String(20))
    is_certified = Column(Integer)
    organization = Column(String(200))
    emp_id = Column(Integer)
    compose = Column(String(100))
    skill_level = Column(Integer)
    phone = Column(String(50))


class WorkerTeam(Base):
    __tablename__ = 'worker_team'
    workerteam_type = Column(String(100), primary_key=True)
    total = Column(Integer)
    assigned = Column(Integer)


class SelectedWorker(Base):
    __tablename__ = 'selected_workers'
    id = Column(Integer, primary_key=True)
    worker_type_id = Column(String(50))
    name = Column(String(100))
    status = Column(String(20))
    is_certified = Column(Integer)
    organization = Column(String(200))
    emp_id = Column(Integer)
    compose = Column(String(100))
    skill_level = Column(Integer)
    phone = Column(String(50))


class EquipmentCategory(Base):
    __tablename__ = 'equipment_category'
    category_id = Column(Integer, primary_key=True)
    category_name = Column(String(50))
    description = Column(Text)


class EquipmentType(Base):
    __tablename__ = 'equipment_types'
    id = Column(String(50), primary_key=True)
    name = Column(String(100))
    created_at = Column(String(50))
    updated_at = Column(String(50))
    category = Column(String(50))


class EquipmentInstance(Base):
    __tablename__ = 'equipment_instances'
    id = Column(Integer, primary_key=True)
    equipment_type_id = Column(String(50))
    name = Column(String(200))
    status = Column(String(20))
    created_time = Column(String(50))
    category = Column(String(50))
    equipment_type_name = Column(String(100))


class SelectedEquipment(Base):
    __tablename__ = 'selected_equipments'
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    equipment_type_id = Column(String(50))
    equipment_type_name = Column(String(100))
    category = Column(String(50))
    created_time = Column(TIMESTAMP)


class Material(Base):
    __tablename__ = 'materials'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    price = Column(REAL)
    stock_quantity = Column(REAL)
    unit = Column(String(50))
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)


class MaintenanceTool(Base):
    __tablename__ = 'maintenance_tools'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    tool_type = Column(String(50))
    capacity = Column(REAL)
    daily_rental_cost = Column(REAL)
    is_available = Column(BOOLEAN)
    requires_operator = Column(BOOLEAN)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)


class ProcessTemplate(Base):
    __tablename__ = 'process_templates'
    id = Column(Integer, primary_key=True)
    equipment_type_id = Column(String(50))
    process_code = Column(String(50))
    description = Column(String(200))
    estimated_hours = Column(REAL)
    required_workers = Column(String(200))
    predecessor_codes = Column(String(200))
    parent_process_code = Column(String(50))
    is_major_process = Column(Integer)
    material_requirements = Column(String(500))
    tools_requirements = Column(String(500))
    material_price = Column(Integer)
    tools_price = Column(Integer)
    worker_price = Column(Integer)


class WorkOrder(Base):
    __tablename__ = 'work_orders'
    id = Column(Integer, primary_key=True)
    order_number = Column(String(50))
    title = Column(String(200))
    equipment_id = Column(Integer)
    equipment_name = Column(String(100))
    status = Column(String(20))
    created_by = Column(Integer)
    created_at = Column(DATETIME)
    scheduled_start_time = Column(Integer)
    scheduled_end_time = Column(Integer)
    actual_start_time = Column(Integer)
    actual_end_time = Column(Integer)
    priority = Column(String(10))
    remarks = Column(Text)
    plan_id = Column(Integer)


class WorkOrderTask(Base):
    __tablename__ = 'work_order_tasks'
    id = Column(Integer, primary_key=True)
    work_order_id = Column(Integer)
    task_code = Column(String(50))
    process_id = Column(String(100))
    process_name = Column(String(200))
    equipment_id = Column(Integer)
    equipment_name = Column(String(100))
    description = Column(Text)
    estimated_hours = Column(REAL)
    scheduled_start_time = Column(String(50))
    scheduled_end_time = Column(String(50))
    actual_start_time = Column(String(50))
    actual_end_time = Column(String(50))
    status = Column(String(20))
    predecessor_task_ids = Column(String(200))
    is_milestone = Column(BOOLEAN)
    workers = Column(String(500))
    approver_id = Column(Integer)
    approval_comments = Column(Text)
    approved_at = Column(DATETIME)
    created_at = Column(DATETIME)
    updated_at = Column(DATETIME)
    attachment_path = Column(String(255))
    process_code = Column(String(50))


class WorkOrderTaskWorker(Base):
    __tablename__ = 'work_order_task_workers'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer)
    worker_id = Column(Integer)
    worker_name = Column(String(100))
    worker_type = Column(String(50))
    status = Column(String(20))
    completion_note = Column(Text)
    completed_at = Column(DATETIME)
    created_at = Column(DATETIME)


class MaintenancePlan(Base):
    __tablename__ = 'maintenance_plans'
    id = Column(Integer, primary_key=True)
    plan_name = Column(String(200))
    plan_scale = Column(String(50))
    status = Column(String(50))
    initiator = Column(String(100))
    initiated_at = Column(DATETIME)
    planned_start_time = Column(String(50))
    planned_end_time = Column(String(50))
    actual_start_time = Column(String(50))
    actual_end_time = Column(String(50))
    planned_man_hours = Column(REAL)
    actual_man_hours = Column(REAL)
    planned_cost = Column(REAL)
    actual_cost = Column(REAL)
    schedule_plan_id = Column(String(100))
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)


class SchedulePlan(Base):
    __tablename__ = 'schedule_plans'
    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer)
    schedule_name = Column(String(200))
    algorithm = Column(String(50))
    status = Column(String(50))
    work_order_ids = Column(String(500))
    project_start_datetime = Column(String(50))
    statistics = Column(String(500))
    total_tasks = Column(Integer)
    created_by = Column(Integer)
    created_at = Column(TIMESTAMP)


class ScheduleTask(Base):
    __tablename__ = 'schedule_tasks'
    schedule_id = Column(Integer, primary_key=True)
    process_id = Column(String(50))
    process_name = Column(String(200))
    equipment_id = Column(Integer)
    equipment_name = Column(String(100))
    equipment_type_id = Column(String(50))
    equipment_type_name = Column(String(100))
    equipment_category = Column(String(50))
    start_time = Column(Integer)
    end_time = Column(Integer)
    start_time_formatted = Column(String(50))
    end_time_formatted = Column(String(50))
    duration_days = Column(Integer)
    workers = Column(String(500))
    predecessors = Column(String(500))
    schedule_plan_id = Column(Integer)
    worker_price = Column(String(100))


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    password = Column(String(200))
    email = Column(String(20))
    role = Column(String(20))
    company_id = Column(Integer)
    real_name = Column(String(100))
    phone = Column(String(20))
    created_time = Column(String(50))
    emp_id = Column(String(50))


class UserWx(Base):
    __tablename__ = 'user_wx'
    id = Column(Integer, primary_key=True)
    wx_openid = Column(String(100))
    user_id = Column(Integer)
    created_at = Column(TIMESTAMP)


class Document(Base):
    __tablename__ = 'documents'
    id = Column(String(50), primary_key=True)
    collection = Column(String(50))
    doc = Column(Text)
    created_at = Column(String(50))
    updated_at = Column(String(50))


class UploadedFile(Base):
    __tablename__ = 'uploaded_files'
    id = Column(String(50), primary_key=True)
    original_name = Column(String(200))
    saved_path = Column(String(255))
    category = Column(String(50))
    upload_time = Column(String(50))
    md_path = Column(String(255))


class GraphNode(Base):
    __tablename__ = 'graph_nodes'
    entity_type = Column(String(50), primary_key=True)
    entity_id = Column(String(50), primary_key=True)
    attributes = Column(JSON)


class GraphNodeArchive(Base):
    __tablename__ = 'graph_nodes_archive'
    entity_type = Column(String(50), primary_key=True)
    entity_id = Column(String(50), primary_key=True)
    attributes = Column(JSON)


class GraphRelation(Base):
    __tablename__ = 'graph_relations'
    id = Column(Integer, primary_key=True)
    source_type = Column(String(50))
    source_id = Column(String(50))
    relation_type = Column(String(50))
    target_type = Column(String(50))
    target_id = Column(String(50))


class GraphRelationArchive(Base):
    __tablename__ = 'graph_relations_archive'
    id = Column(Integer, primary_key=True)
    source_type = Column(String(50))
    source_id = Column(String(50))
    relation_type = Column(String(50))
    target_type = Column(String(50))
    target_id = Column(String(50))


class TaskOperationLog(Base):
    __tablename__ = 'task_operation_logs'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer)
    user_id = Column(Integer)
    operation_type = Column(String(50))
    description = Column(Text)
    attachment_path = Column(String(255))
    old_status = Column(String(50))
    new_status = Column(String(50))
    approval_comments = Column(Text)
    created_at = Column(TIMESTAMP)