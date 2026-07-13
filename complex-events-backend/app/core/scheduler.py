"""调度引擎核心模块

从 algorithm 分支移植，适配 main 分支的数据库路径配置。
"""
import sqlite3
import datetime
import json
from pathlib import Path
from typing import Optional

from app.core.models import DatabaseManager, EquipmentType, Worker, Process, Equipment, ProcessTemplate
from app.core.interface import IScheduler


class Task:
    def __init__(self, id, name, duration, start_time, end_time, dependencies=None):
        self.id = id
        self.name = name
        self.duration = duration
        self.start_time = start_time
        self.end_time = end_time
        self.dependencies = dependencies if dependencies is not None else []
        self.completed = False


def _get_db_path():
    """获取数据库路径"""
    from app.config import Config
    return Config.SQLITE_DB_PATH


class Scheduler(IScheduler):
    def __init__(self, project_start_datetime=None):
        self.workers = []
        self.equipments = []
        self.equipment_types = {}
        self.worker_pool = {}
        self.schedule_plan = []
        self.certified_workers = set()
        self.total_project_duration = 0
        self.worker_utilization = {}
        self.algorithm = None
        # 兼容旧算法的属性
        self.work_duration_minutes = 480  # 8小时
        self.work_start_minutes = 0
        self.minutes_per_day = 1440  # 24小时
        if project_start_datetime is None:
            now = datetime.datetime.now()
            tomorrow = now.replace(day=now.day + 1, hour=0, minute=0, second=0, microsecond=0) if now.day < 28 else now
            self.project_start_datetime = tomorrow
        else:
            self.project_start_datetime = project_start_datetime

    def get_absolute_time(self, relative_days):
        """将相对天数转换为绝对日期时间字符串"""
        start = self.project_start_datetime
        delta = datetime.timedelta(days=relative_days)
        abs_datetime = start + delta
        return abs_datetime.strftime("%Y-%m-%d %H:%M:%S")

    def adjust_to_work_time(self, time_minutes):
        """调整到工作时间（简化版：直接返回）"""
        return time_minutes

    def load_equipment_types_from_db(self, db_path=None):
        """从数据库加载设备类型信息"""
        db_path = db_path or _get_db_path()
        equipment_type_dict = DatabaseManager.load_equipment_types_from_db(str(db_path))
        for equipment_type in equipment_type_dict.values():
            self.add_equipment_type(equipment_type)

    def load_workers_from_db(self, db_path=None):
        """从数据库加载工人信息"""
        db_path = db_path or _get_db_path()
        worker_records = DatabaseManager.load_selected_workers_from_db(str(db_path))
        if not worker_records:
            worker_records = DatabaseManager.load_workers_from_db(str(db_path))
        for record in worker_records:
            id, worker_type_id, name, is_certified, organization, compose, skill_level = record
            self.add_worker(Worker(id, name, worker_type_id, is_certified, organization, compose, skill_level))
        print(f"从数据库成功加载 {len(worker_records)} 名工人")
        return len(worker_records)

    def check_resource_sufficiency(self):
        """检查工人资源是否足够支撑所有工序的需求"""
        all_processes = self.get_all_processes()
        max_requirements = {}
        for process in all_processes:
            for worker_type, count_needed in process.worker_requirements.items():
                if worker_type not in max_requirements or count_needed > max_requirements[worker_type]:
                    max_requirements[worker_type] = count_needed
        insufficient_resources = []
        for worker_type, max_required in max_requirements.items():
            total_workers = len(self.worker_pool.get(worker_type, []))
            if total_workers < max_required:
                insufficient_resources.append(
                    {
                        "worker_type": worker_type,
                        "required": max_required,
                        "available": total_workers,
                        "total_workers": total_workers,
                        "issue": f"需要 {max_required} 名{worker_type}，但只有 {total_workers} 名工人可用",
                    }
                )
        return insufficient_resources

    def set_algorithm(self, algorithm_name, **kwargs):
        """设置调度算法"""
        from app.core.algorithms import (
            TopologicalScheduler,
            GreedyScheduler,
            GeneticScheduler,
            ShortestProcessingTimeScheduler,
        )
        if algorithm_name == "topological":
            self.algorithm = TopologicalScheduler(self)
        elif algorithm_name == "greedy":
            self.algorithm = GreedyScheduler(self)
        elif algorithm_name == "genetic":
            self.algorithm = GeneticScheduler(self, **kwargs)
        elif algorithm_name == "spt":
            self.algorithm = ShortestProcessingTimeScheduler(self)
        else:
            raise ValueError(f"不支持的算法: {algorithm_name}")

    def add_equipment_type(self, equipment_type):
        self.equipment_types[equipment_type.id] = equipment_type

    def add_equipment(self, equipment_id, equipment_name, equipment_type_id, category):
        """添加设备实例"""
        equipment_type_id_str = str(equipment_type_id)
        if equipment_type_id_str not in self.equipment_types:
            # 尝试加载该设备类型
            print(f"警告: 设备类型 {equipment_type_id_str} 未预加载，跳过工序模板生成")
            equipment_type = EquipmentType(equipment_type_id_str, "未知")
        else:
            equipment_type = self.equipment_types[equipment_type_id]
        equipment = Equipment(equipment_id, equipment_name, equipment_type, category)
        equipment.generate_processes()
        self.equipments.append(equipment)
        return equipment

    def add_worker(self, worker, is_certified=False):
        self.workers.append(worker)
        if worker.type not in self.worker_pool:
            self.worker_pool[worker.type] = []
        self.worker_pool[worker.type].append(worker)
        if is_certified:
            self.certified_workers.add(worker.id)

    def assign_resources(self, process, equipment, start_time, workers):
        """分配资源 - 记录实际时间"""
        if process.duration == 0:
            process.actual_start = start_time
            process.actual_end = start_time
            self.schedule_plan.append(
                {
                    "process_id": process.id,
                    "process_name": process.name,
                    "equipment_id": equipment.id,
                    "equipment_name": equipment.name,
                    "start_time": start_time,
                    "end_time": start_time,
                    "workers": {},
                    "is_milestone": True,
                }
            )
            return

        end_time = start_time + process.duration
        process.actual_start = start_time
        process.actual_end = end_time
        process.assigned_workers = workers if workers is not None else {}
        equipment.schedule.append((start_time, end_time, process.id))

        if workers:
            for worker_type, worker_list in workers.items():
                if worker_list:
                    for worker in worker_list:
                        worker.assigned_tasks.append((start_time, end_time))
                        worker.total_work_days += process.duration

        worker_names_info = {}
        if workers:
            for wt, w_list in workers.items():
                worker_names_info[wt] = [w.name for w in w_list] if w_list else []
        else:
            worker_names_info = {wt: [] for wt in process.worker_requirements.keys()}

        self.schedule_plan.append(
            {
                "process_id": process.id,
                "process_name": process.name,
                "equipment_id": equipment.id,
                "equipment_name": equipment.name,
                "start_time": start_time,
                "end_time": end_time,
                "workers": worker_names_info,
            }
        )

    def validate_dependencies(self, process):
        """验证工序的所有前置工序是否已完成调度"""
        for pred_id in process.predecessor_ids:
            pred_process = self.get_process_by_id(pred_id)
            if not pred_process:
                return False
            if not hasattr(pred_process, "actual_start") or pred_process.actual_start is None:
                return False
            pred_end_time = pred_process.actual_start + pred_process.duration
            if pred_end_time > process.earliest_start:
                process.earliest_start = pred_end_time
        return True

    def find_available_workers(self, worker_requirements, start_time, end_time, requires_certification=False):
        """查找可用的工人"""
        available_workers = {}
        for worker_type, count_needed in worker_requirements.items():
            if worker_type not in self.worker_pool:
                return None
            workers_of_type = self.worker_pool[worker_type]
            available_of_type = []
            for worker in workers_of_type:
                if self.is_worker_available(worker, start_time, end_time):
                    if requires_certification and worker.id not in self.certified_workers:
                        continue
                    available_of_type.append(worker)
            if len(available_of_type) < count_needed:
                return None
            available_of_type.sort(key=lambda w: w.skill_level, reverse=True)
            available_workers[worker_type] = available_of_type[:count_needed]
        return available_workers

    def find_equipment_available_slot(self, equipment, start_time, duration_days):
        """查找设备的可用时间段"""
        end_time = start_time + duration_days
        if not equipment.schedule:
            return (start_time, end_time)
        equipment.schedule.sort(key=lambda x: x[0])
        first_start = equipment.schedule[0][0]
        if first_start - start_time >= duration_days:
            return (start_time, end_time)
        for i in range(len(equipment.schedule) - 1):
            current_end = equipment.schedule[i][1]
            next_start = equipment.schedule[i + 1][0]
            if next_start - current_end >= duration_days:
                return (current_end, current_end + duration_days)
        last_end = equipment.schedule[-1][1]
        return (last_end, last_end + duration_days)

    def get_worker_pool(self):
        """获取工人池信息"""
        worker_by_name = {w.name: w for w in self.workers}
        busy_slots_map = {w.id: [] for w in self.workers}
        for task in self.schedule_plan:
            if task.get("is_milestone", False):
                continue
            start = task["start_time"]
            end = task["end_time"]
            workers_dict = task.get("workers", {})
            for trade, name_list in workers_dict.items():
                for name in name_list:
                    worker = worker_by_name.get(name)
                    if worker:
                        busy_slots_map[worker.id].append(
                            {"process_id": task["process_id"], "start": start, "end": end}
                        )
        result = {}
        for trade, worker_list in self.worker_pool.items():
            workers_info = []
            for worker in worker_list:
                workers_info.append(
                    {
                        "id": worker.id,
                        "name": worker.name,
                        "skill_level": worker.skill_level,
                        "busy_slots": busy_slots_map.get(worker.id, []),
                    }
                )
            result[trade] = workers_info
        return result

    def get_all_processes(self):
        all_processes = []
        for equipment in self.equipments:
            all_processes.extend(equipment.processes)
        return all_processes

    def get_process_by_id(self, process_id):
        for equipment in self.equipments:
            for process in equipment.processes:
                if process.id == process_id:
                    return process
        return None

    def get_equipment_by_id(self, equipment_id):
        for equipment in self.equipments:
            if equipment.id == equipment_id:
                return equipment
        return None

    def is_worker_available(self, worker, start_time, end_time):
        for task_start, task_end in worker.assigned_tasks:
            if not (end_time <= task_start or start_time >= task_end):
                return False
        return True

    def calculate_earliest_start_times(self, processes):
        """计算每个工序的最早开始时间（天）"""
        process_dict = {p.id: p for p in processes}
        for process in processes:
            process.earliest_start = 0
        queue = [p for p in processes if not p.predecessor_ids]
        for process in queue:
            process.earliest_start = 0
        processed = set(p.id for p in queue)
        max_iterations = len(processes) * 2
        iteration_count = 0
        while queue and iteration_count < max_iterations:
            iteration_count += 1
            current = queue.pop(0)
            successors = [p for p in processes if current.id in p.predecessor_ids]
            for successor in successors:
                all_predecessors_processed = all(
                    pred_id in processed for pred_id in successor.predecessor_ids
                )
                if not all_predecessors_processed:
                    continue
                max_finish_time = 0
                for pred_id in successor.predecessor_ids:
                    pred_process = process_dict.get(pred_id)
                    if pred_process:
                        pred_finish_time = pred_process.earliest_start + pred_process.duration
                        if pred_finish_time > max_finish_time:
                            max_finish_time = pred_finish_time
                successor.earliest_start = max_finish_time
                processed.add(successor.id)
                queue.append(successor)
        # 处理未处理的工序
        unprocessed = [p for p in processes if p.id not in processed]
        for process in unprocessed:
            if not process.predecessor_ids:
                process.earliest_start = 0
            else:
                max_finish_time = 0
                for pred_id in process.predecessor_ids:
                    pred_process = process_dict.get(pred_id)
                    if pred_process and hasattr(pred_process, "earliest_start"):
                        pred_finish_time = pred_process.earliest_start + pred_process.duration
                        max_finish_time = max(max_finish_time, pred_finish_time)
                process.earliest_start = max_finish_time

    def schedule(self):
        """执行调度"""
        if not self.algorithm:
            self.set_algorithm("topological")
        insufficient_workers = self.check_resource_sufficiency()
        if insufficient_workers:
            print("\n❌ 资源不足，无法开始调度！")
            return None
        print("\n✅ 所有资源检查通过，开始调度...")
        self.schedule_plan = self.algorithm.schedule()
        self.calculate_project_statistics()
        return self.schedule_plan

    def calculate_project_statistics(self):
        if not self.schedule_plan:
            self.total_project_duration = 0
            return
        min_start_time = min(task["start_time"] for task in self.schedule_plan)
        max_end_time = max(task["end_time"] for task in self.schedule_plan)
        self.total_project_duration = max_end_time - min_start_time

    def format_time(self, days):
        """将相对天数转换为绝对日期"""
        target_date = self.project_start_datetime + datetime.timedelta(days=days)
        return target_date.strftime("%Y-%m-%d %H:%M:%S")

    def get_statistics_data(self):
        project_start_time = float("inf")
        project_end_time = 0
        for equipment in self.equipments:
            if equipment.schedule:
                for start, end, _ in equipment.schedule:
                    project_start_time = min(project_start_time, start)
                    project_end_time = max(project_end_time, end)
        if project_start_time == float("inf"):
            project_start_time = 0
            project_end_time = 0
        return {
            "total_project_duration_days": self.total_project_duration,
            "total_workers": len(self.workers),
            "total_equipments": len(self.equipments),
            "total_processes": len(self.get_all_processes()),
            "actual_start_time": self.format_time(project_start_time),
            "actual_end_time": self.format_time(project_end_time),
        }

    def schedule_from_work_orders(self, work_order_ids, algorithm_name="topological"):
        """根据工单ID列表执行调度"""
        try:
            db_path = _get_db_path()
            conn = sqlite3.connect(str(db_path))
            c = conn.cursor()
            # 验证工单是否存在
            placeholders = ",".join(["?" for _ in work_order_ids])
            c.execute(
                f"SELECT id FROM work_orders WHERE id IN ({placeholders})",
                work_order_ids,
            )
            found = {row[0] for row in c.fetchall()}
            missing = set(work_order_ids) - found
            if missing:
                conn.close()
                return None, None, False, f"以下工单不存在: {missing}"

            # 查询所有任务
            c.execute(
                f"""
                SELECT
                    wot.id as task_id,
                    wot.work_order_id,
                    wot.process_id,
                    wot.process_name,
                    wot.equipment_id,
                    wot.equipment_name,
                    wot.predecessor_task_ids,
                    wot.estimated_hours,
                    wot.is_milestone,
                    ei.equipment_type_id,
                    pt.required_workers
                FROM work_order_tasks wot
                JOIN work_orders wo ON wot.work_order_id = wo.id
                JOIN equipment_instances ei ON wo.equipment_id = ei.id
                LEFT JOIN process_templates pt ON wot.process_code = pt.process_code
                WHERE wot.work_order_id IN ({placeholders})
                AND wot.status != 'cancelled'
            """,
                work_order_ids,
            )
            tasks = c.fetchall()
            if not tasks:
                conn.close()
                return None, None, False, "选中的工单中没有可调度的任务"

            # 清空当前调度器
            self.equipments = []
            self.workers = []
            self.worker_pool = {}
            self.schedule_plan = []

            # 重新加载工人和设备类型
            self.load_workers_from_db(str(db_path))
            self.load_equipment_types_from_db(str(db_path))

            # 按设备分组任务
            equipment_tasks = {}
            for task in tasks:
                (
                    task_id,
                    work_order_id,
                    process_id,
                    process_name,
                    equipment_id,
                    equipment_name,
                    predecessor_ids_json,
                    estimated_day,
                    is_milestone,
                    equipment_type_id,
                    required_workers,
                ) = task

                if equipment_id not in equipment_tasks:
                    equipment_tasks[equipment_id] = {
                        "equipment_name": equipment_name,
                        "equipment_type_id": equipment_type_id,
                        "tasks": [],
                    }
                predecessor_ids = (
                    json.loads(predecessor_ids_json) if predecessor_ids_json else []
                )
                equipment_tasks[equipment_id]["tasks"].append(
                    {
                        "task_id": task_id,
                        "process_id": f"{equipment_id}_{process_id}",
                        "process_name": process_name,
                        "duration": estimated_day,
                        "worker_requirements": json.loads(required_workers)
                        if required_workers
                        else {},
                        "predecessor_ids": predecessor_ids,
                        "is_milestone": bool(is_milestone),
                    }
                )

            # 为每个设备创建 Equipment 和 Process 实例
            for eq_id, data in equipment_tasks.items():
                equipment_type_id = str(data["equipment_type_id"])
                self.add_equipment(
                    eq_id, data["equipment_name"], data["equipment_type_id"], "unknown"
                )
                equipment = self.get_equipment_by_id(eq_id)
                if not equipment:
                    continue
                equipment.processes = []
                for task_data in data["tasks"]:
                    proc = Process(
                        id=task_data["process_id"],
                        name=task_data["process_name"],
                        duration=task_data["duration"],
                        equipment_id=eq_id,
                        worker_requirements=task_data["worker_requirements"],
                        predecessor_ids=task_data["predecessor_ids"],
                    )
                    equipment.processes.append(proc)

            conn.close()

            # 检查资源充足性
            insufficient = self.check_resource_sufficiency()
            if insufficient:
                error_details = [
                    {
                        "worker_type": i["worker_type"],
                        "required": i["required"],
                        "available": i["available"],
                        "issue": i["issue"],
                    }
                    for i in insufficient
                ]
                return None, None, False, {
                    "error_type": "insufficient_workers",
                    "details": error_details,
                }

            # 设置算法并调度
            self.set_algorithm(algorithm_name)
            plan = self.schedule()
            if plan is None:
                return None, None, False, "调度因资源不足而中止"

            # 写入数据库
            formatted = self.format_schedule_plan(plan)
            self._save_schedule_tasks_to_db(formatted)
            stats = self.get_statistics_data()
            result_data = {
                "success": True,
                "algorithm": algorithm_name,
                "schedule_plan": formatted,
                "statistics": stats,
                "project_start_datetime": self.project_start_datetime.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }
            return result_data
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise

    def _save_schedule_tasks_to_db(self, formatted_plan):
        """将调度结果写入 schedule_tasks 表"""
        db_path = _get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute("DELETE FROM schedule_tasks")
        for task in formatted_plan:
            c.execute(
                """
                INSERT INTO schedule_tasks
                (duration_days, end_time, end_time_formatted, equipment_category,
                equipment_id, equipment_name, equipment_type_id, equipment_type_name,
                predecessors, process_id, process_name, start_time, start_time_formatted, workers)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    task["duration_days"],
                    task["end_time"],
                    task["end_time_formatted"],
                    task["equipment_category"],
                    task["equipment_id"],
                    task["equipment_name"],
                    task["equipment_type_id"],
                    task["equipment_type_name"],
                    json.dumps(task["predecessors"], ensure_ascii=False),
                    task["process_id"],
                    task["process_name"],
                    task["start_time"],
                    task["start_time_formatted"],
                    json.dumps(task["workers"], ensure_ascii=False),
                ),
            )
            # 更新 work_order_tasks 的计划时间
            parts = task["process_id"].split("_", 1)
            equipment_id = parts[0]
            raw_process_id = parts[1] if len(parts) > 1 else task["process_id"]
            c.execute(
                """
                UPDATE work_order_tasks
                SET scheduled_start_time = ?, scheduled_end_time = ?, workers = ?
                WHERE equipment_id = ? AND process_id = ?
            """,
                (
                    task["start_time_formatted"],
                    task["end_time_formatted"],
                    json.dumps(task["workers"], ensure_ascii=False),
                    equipment_id,
                    raw_process_id,
                ),
            )
        conn.commit()
        conn.close()

    def format_schedule_plan(self, schedule_plan):
        """格式化调度计划"""
        formatted = []
        for task in schedule_plan:
            if task.get("is_milestone", False):
                continue
            equipment = self.get_equipment_by_id(task["equipment_id"])
            equipment_type = (
                self.equipment_types.get(str(equipment.type.id))
                if equipment and equipment.type
                else None
            )
            duration_days = task["end_time"] - task["start_time"]
            formatted_task = {
                "process_id": task["process_id"],
                "process_name": task["process_name"],
                "equipment_id": task["equipment_id"],
                "equipment_name": task.get(
                    "equipment_name", equipment.name if equipment else task["equipment_id"]
                ),
                "equipment_category": equipment.category
                if equipment and hasattr(equipment, "category")
                else "未知种类",
                "equipment_type_id": equipment.type.id if equipment and equipment.type else None,
                "equipment_type_name": equipment_type.name if equipment_type else "未知类型",
                "start_time": task["start_time"],
                "end_time": task["end_time"],
                "start_time_formatted": self.format_time(task["start_time"]),
                "end_time_formatted": self.format_time(task["end_time"]),
                "duration_days": duration_days,
                "workers": task.get("workers", {}),
                "predecessors": [],
            }
            process = self.get_process_by_id(task["process_id"])
            if process and hasattr(process, "predecessor_ids"):
                formatted_task["predecessors"] = process.predecessor_ids
            formatted.append(formatted_task)
        return formatted


# 全局调度器单例
_scheduler = None


def init_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
        _scheduler.load_workers_from_db()
    return _scheduler


def get_scheduler():
    if _scheduler is None:
        init_scheduler()
    return _scheduler


def reset_scheduler():
    """重置调度器单例"""
    global _scheduler
    _scheduler = None


def run_scheduling(work_order_ids, algorithm_name="topological"):
    """供 API 调用的顶层调度函数"""
    scheduler = get_scheduler()
    result = scheduler.schedule_from_work_orders(work_order_ids, algorithm_name)
    if isinstance(result, tuple) and len(result) == 4:
        return result
    elif isinstance(result, dict):
        success = result.get("success", True)
        if success:
            formatted_plan = result.get("schedule_plan", [])
            statistics = result.get("statistics", {})
            return formatted_plan, statistics, True, "调度成功"
        else:
            return None, None, False, result.get("message", "调度失败")
    else:
        return None, None, False, f"未知的调度返回格式: {type(result)}"
