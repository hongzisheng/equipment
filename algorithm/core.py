import sqlite3
import datetime
import math
from models import DatabaseManager, EquipmentType, Worker, Process, Equipment,ProcessTemplate
from pathlib import Path
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from scheduler_interface import IScheduler
import json
from utils import get_db_path
class Task:
    def __init__(self, id, name, duration, start_time, end_time, dependencies=None):
        self.id = id
        self.name = name
        self.duration = duration  # 单位：天
        self.start_time = start_time
        self.end_time = end_time
        self.dependencies = dependencies if dependencies is not None else []
        self.completed = False

class Scheduler(IScheduler):
    def __init__(self,project_start_datetime=None):
        self.workers = []  # 所有工人
        self.equipments = []  # 所有设备实例
        self.equipment_types = {}  # 设备类型字典
        self.worker_pool = {}  # 按工种分类的工人池
        self.schedule_plan = []  # 最终调度计划
        self.certified_workers = set()  # 持证工人集合
        self.total_project_duration = 0  # 项目总用时(天)
        self.worker_utilization = {}  # 人员利用率
        self.algorithm = None  # 当前使用的算法
        if project_start_datetime is None:
            now = datetime.datetime.now()
            self.project_start_datetime = datetime.datetime(now.year, now.month, now.day+1, 0, 0, 0)
        else:
            self.project_start_datetime = project_start_datetime
    def _get_default_db_path(self):
        """获取默认数据库路径"""
        current_dir = Path(__file__).parent
        return current_dir.parent / 'database' / 'db.sqlite3'
    def get_absolute_time(self, relative_days):
        """将相对天数转换为绝对日期时间字符串"""
        start = self.project_start_datetime
        delta = datetime.timedelta(days=relative_days)
        abs_datetime = start + delta
        return abs_datetime.strftime('%Y-%m-%d %H:%M:%S')
    
    def load_equipment_types_from_db(self, db_path=None):
        """从数据库加载设备类型信息"""
        db_path = db_path or self._get_default_db_path()
        equipment_type_dict = DatabaseManager.load_equipment_types_from_db(str(db_path))
        for equipment_type in equipment_type_dict.values():
            self.add_equipment_type(equipment_type)


    def load_workers_from_db(self, db_path=None):
        """从数据库加载工人信息 - 简化版本"""
        db_path = db_path or self._get_default_db_path()
        worker_records = DatabaseManager.load_selected_workers_from_db(str(db_path))
        if not worker_records : 
            worker_records = DatabaseManager.load_workers_from_db(str(db_path))
        for record in worker_records:
            id,worker_type_id,name,is_certified,organization,compose,skill_level = record
            self.add_worker(Worker(id,name, worker_type_id,is_certified,organization,compose,skill_level))
        print(f"从数据库成功加载 {len(worker_records)} 名工人")
        return len(worker_records)
    def check_resource_sufficiency(self):
        """检查工人资源是否足够支撑所有工序的需求"""
        print("正在进行工人资源充足性检查...")
        
        # 获取所有工序
        all_processes = self.get_all_processes()
        
        # 统计每个工种的最大并发需求
        max_requirements = {}
        for process in all_processes:
            for worker_type, count_needed in process.worker_requirements.items():
                if worker_type not in max_requirements or count_needed > max_requirements[worker_type]:
                    max_requirements[worker_type] = count_needed
                # 累加同一时间可能需要的最大数量（保守估计）
        
        # 检查每个工种的需求是否都能满足
        insufficient_resources = []
        
        for worker_type, max_required in max_requirements.items():
            # 获取该工种的总工人数
            total_workers = len(self.worker_pool.get(worker_type, []))
            if total_workers < max_required:
                insufficient_resources.append({
                    'worker_type': worker_type,
                    'required': max_required,
                    'available': total_workers,
                    'total_workers': total_workers,
                    'issue': f"需要 {max_required} 名{worker_type}，但只有 {total_workers} 名工人可用"
                })
            else:
                print(f"✓ {worker_type}: 需要 {max_required} 名工人，有 {total_workers} 名工人可用")
        
        return insufficient_resources
    def set_algorithm(self, algorithm_name, **kwargs):
        """设置调度算法"""
        from scheduler_algorithms import (
            ShortestProcessingTimeScheduler, 
            TopologicalScheduler, 
            GreedyScheduler, 
            GeneticScheduler
        )
        if algorithm_name == "topological":
            self.algorithm = TopologicalScheduler(self)
        elif algorithm_name == "greedy":
            self.algorithm = GreedyScheduler(self)
        elif algorithm_name == "genetic":
            self.algorithm = GeneticScheduler(self, **kwargs)
        elif algorithm_name == "spt":  # 最短处理时间优先
            self.algorithm = ShortestProcessingTimeScheduler(self)
        else:
            raise ValueError(f"不支持的算法: {algorithm_name}")
    def add_equipment_type(self, equipment_type):
        """添加设备类型"""
        self.equipment_types[equipment_type.id] = equipment_type
    
    def add_equipment(self, equipment_id, equipment_name, equipment_type_id,category):
        """添加设备实例"""
        equipment_type_id_str = str(equipment_type_id)
    
        if equipment_type_id_str not in self.equipment_types:
            print(f"错误: 设备类型 {equipment_type_id_str} 未定义")
            print(f"可用的设备类型: {list(self.equipment_types.keys())}")
            return
        
        equipment_type = self.equipment_types[equipment_type_id]
        equipment = Equipment(equipment_id, equipment_name, equipment_type, category)
        equipment.generate_processes()  # 生成该设备的工序实例
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
            # 里程碑工序
            process.actual_start = start_time
            process.actual_end = start_time
            self.schedule_plan.append({
                'process_id': process.id,
                'process_name': process.name,
                'equipment_id': equipment.id,
                'equipment_name': equipment.name,
                'start_time': start_time,
                'end_time': start_time,
                'workers': {},
                'is_milestone': True
            })
            return

        end_time = start_time + process.duration
        process.actual_start = start_time
        process.actual_end = end_time

        # 记录分配的工人
        process.assigned_workers = workers if workers is not None else {}

        # 添加到设备调度
        equipment.schedule.append((start_time, end_time, process.id))

        # 更新工人工作记录
        if workers:
            for worker_type, worker_list in workers.items():
                if worker_list:
                    for worker in worker_list:
                        worker.assigned_tasks.append((start_time, end_time))
                        worker.total_work_days += process.duration

        worker_info = {}
        worker_names_info = {}
        if workers:
            for wt, w_list in workers.items():
                if w_list:
                    worker_info[wt] = [w.id for w in w_list]
                    worker_names_info[wt] = [w.name for w in w_list]
                else:
                    worker_info[wt] = []
                    worker_names_info[wt] = []
        else:
            worker_info = {wt: [] for wt in process.worker_requirements.keys()}
            worker_names_info = {wt: [] for wt in process.worker_requirements.keys()}

        # 添加到调度计划
        self.schedule_plan.append({
            'process_id': process.id,
            'process_name': process.name,
            'equipment_id': equipment.id,
            'equipment_name': equipment.name,
            'start_time': start_time,
            'end_time': end_time,
            'workers': worker_names_info
        })
    def validate_dependencies(self, process):
        """验证工序的所有前置工序是否已完成调度"""
        for pred_id in process.predecessor_ids:
            pred_process = self.get_process_by_id(pred_id)
            if not pred_process:
                print(f"错误: 找不到前置工序 {pred_id}")
                return False
            if not hasattr(pred_process, 'actual_start') or pred_process.actual_start is None:
                return False
            pred_end_time = pred_process.actual_start + pred_process.duration
            if pred_end_time > process.earliest_start:
                process.earliest_start = pred_end_time  # 无需调整工作时间
        return True
    def schedule_cross_day_process(self, process, equipment, start_time, duration_days):
        """不再需要跨天分段，直接返回一个连续时段"""
        # 为了保持接口兼容，返回单个时间段列表
        return [(start_time, start_time + duration_days)]


    def assign_cross_day_resources(self, process, equipment, work_segments, workers):
        if work_segments:
            start_time = work_segments[0][0]
            end_time = work_segments[-1][1]
            process.actual_start = start_time
            process.actual_end = end_time
            equipment.schedule.append((start_time, end_time, process.id))
            if workers:
                for worker_type, worker_list in workers.items():
                    if worker_list:
                        for worker in worker_list:
                            worker.assigned_tasks.append((start_time, end_time))
                            worker.total_work_days += (end_time - start_time)
            worker_names_info = {}
            if workers:
                for wt, w_list in workers.items():
                    worker_names_info[wt] = [w.name for w in w_list] if w_list else []
            else:
                worker_names_info = {wt: [] for wt in process.worker_requirements.keys()}
            self.schedule_plan.append({
                'process_id': process.id,
                'process_name': process.name,
                'equipment_id': equipment.id,
                'equipment_name': equipment.name,
                'start_time': start_time,
                'end_time': end_time,
                'workers': worker_names_info,
                'work_segments': work_segments,
                'is_cross_day': True
            })
    def find_any_available_workers(self, worker_requirements, start_time, end_time, requires_certification=False):
        """查找可用工人（与之前相同，只是时间单位变更为天）"""
        available_workers = {}
        for worker_type, count_needed in worker_requirements.items():
            if worker_type not in self.worker_pool:
                continue
            workers_of_type = self.worker_pool[worker_type]
            available_of_type = []
            for worker in workers_of_type:
                if requires_certification and worker.id not in self.certified_workers:
                    continue
                if self.is_worker_available(worker, start_time, end_time):
                    available_of_type.append(worker)
            if available_of_type:
                available_of_type.sort(key=lambda w: w.skill_level, reverse=True)
                available_workers[worker_type] = available_of_type[:min(count_needed, len(available_of_type))]
        return available_workers if available_workers else None
    def get_worker_pool(self):
        # 1. 构建工人ID到Worker对象的映射
        worker_by_id = {w.id: w for w in self.workers}
        # 同时建立姓名字符串到Worker的映射（因为schedule_plan中只存了姓名）
        worker_by_name = {w.name: w for w in self.workers}
        
        # 2. 初始化每个工人的busy_slots列表
        busy_slots_map = {w.id: [] for w in self.workers}
        
        # 3. 遍历调度计划，收集忙碌时段
        for task in self.schedule_plan:
            if task.get('is_milestone', False):
                continue
            process_id = task['process_id']
            start = task['start_time']
            end = task['end_time']
            workers_dict = task.get('workers', {})
            for trade, name_list in workers_dict.items():
                for name in name_list:
                    worker = worker_by_name.get(name)
                    if worker:
                        busy_slots_map[worker.id].append({
                            "process_id": process_id,
                            "start": start,
                            "end": end
                        })
        
        # 4. 按工种分组构建结果
        result = {}
        for trade, worker_list in self.worker_pool.items():
            workers_info = []
            for worker in worker_list:
                workers_info.append({
                    "id": worker.id,
                    "name": worker.name,
                    "skill_level": worker.skill_level,
                    "busy_slots": busy_slots_map.get(worker.id, [])
                })
            result[trade] = workers_info
        
        return result  
    def find_equipment_available_slot(self, equipment, start_time, duration_days):
        """查找设备的可用时间段 - 基于连续时间"""
        end_time = start_time + duration_days
        if not equipment.schedule:
            return (start_time, end_time)

        # 对设备调度列表按开始时间排序
        equipment.schedule.sort(key=lambda x: x[0])

        # 检查第一个任务之前的时间段
        first_start = equipment.schedule[0][0]
        if first_start - start_time >= duration_days:
            return (start_time, end_time)

        # 检查任务之间的间隙
        for i in range(len(equipment.schedule) - 1):
            current_end = equipment.schedule[i][1]
            next_start = equipment.schedule[i + 1][0]
            if next_start - current_end >= duration_days:
                return (current_end, current_end + duration_days)

        # 使用最后一个任务之后的时间
        last_end = equipment.schedule[-1][1]
        return (last_end, last_end + duration_days)
    
    def find_available_workers(self, worker_requirements, start_time, end_time, requires_certification=False):
        """查找可用的工人"""
        available_workers = {}
        for worker_type, count_needed in worker_requirements.items():
            if worker_type not in self.worker_pool:
                print(f"错误: 没有找到工种 {worker_type} 的工人")
                # 返回None表示无法满足所有工种需求
                return None
            
            # 获取该工种的所有工人
            workers_of_type = self.worker_pool[worker_type]
            
            # 筛选可用工人
            available_of_type = []
            for worker in workers_of_type:
                if self.is_worker_available(worker, start_time, end_time):
                    # 检查证书要求
                    if requires_certification and worker.id not in self.certified_workers:
                        continue
                    available_of_type.append(worker)

            # 检查是否满足所需人数
            if len(available_of_type) < count_needed:
                print(f"错误: 工种 {worker_type} 可用工人不足，需要 {count_needed} 人，仅有 {len(available_of_type)} 人可用")
                return None

            # 按技能等级降序排序，优先选择等级高的工人
            available_of_type.sort(key=lambda w: w.skill_level, reverse=True)

            # 选择前 count_needed 个工人
            available_workers[worker_type] = available_of_type[:count_needed]
        
        return available_workers
    def get_worker_conflict_info(self, worker, start_time, end_time):
        conflicts = []
        for task_start, task_end in worker.assigned_tasks:
            # 检查时间重叠
            if not (end_time <= task_start or start_time >= task_end):
                conflict_start = max(start_time, task_start)
                conflict_end = min(end_time, task_end)
                conflicts.append(f"与任务[{self.format_time(task_start)}-{self.format_time(task_end)}]冲突")
        
        if conflicts:
            return f"({', '.join(conflicts)})"
        return "(无冲突信息)"
    def get_all_processes(self):
        """获取所有设备的工序"""
        all_processes = []
        for equipment in self.equipments:
            all_processes.extend(equipment.processes)
        return all_processes
    def get_process_by_id(self, process_id):
        """根据工序ID获取工序"""
        for equipment in self.equipments:
            for process in equipment.processes:
                if process.id == process_id:
                    return process
        return None
    
    def get_equipment_by_id(self, equipment_id):
        """根据设备ID获取设备"""
        for equipment in self.equipments:
            if equipment.id == equipment_id:
                return equipment
        return None
    def is_worker_available(self, worker, start_time, end_time):
        """检查工人在指定时间段是否可用"""
        for task_start, task_end in worker.assigned_tasks:
            if not (end_time <= task_start or start_time >= task_end):
                return False
        return True
    def calculate_earliest_start_times(self, processes):
        """计算每个工序的最早开始时间（天），不再调整工作时间"""
        process_dict = {p.id: p for p in processes}
        for process in processes:
            process.earliest_start = 0

        queue = [p for p in processes if not p.predecessor_ids]
        for process in queue:
            process.earliest_start = 0  # 从0开始

        processed = set([p.id for p in queue])
        max_iterations = len(processes) * 2
        iteration_count = 0
        while queue and iteration_count < max_iterations:
            iteration_count += 1
            current = queue.pop(0)
            successors = [p for p in processes if current.id in p.predecessor_ids]
            for successor in successors:
                all_predecessors_processed = all(pred_id in processed for pred_id in successor.predecessor_ids)
                if not all_predecessors_processed:
                    continue
                max_finish_time = 0
                for pred_id in successor.predecessor_ids:
                    pred_process = process_dict.get(pred_id)
                    if pred_process:
                        pred_finish_time = pred_process.earliest_start + pred_process.duration
                        if pred_finish_time > max_finish_time:
                            max_finish_time = pred_finish_time
                successor.earliest_start = max_finish_time  # 不再调整到工作时间
                processed.add(successor.id)
                queue.append(successor)

        # 处理未处理的工序
        unprocessed = [p for p in processes if p.id not in processed]
        for process in unprocessed:
            if not process.predecessor_ids:
                process.earliest_start = 0
            else:
                max_finish_time = 0
                valid_predecessors = 0
                for pred_id in process.predecessor_ids:
                    pred_process = process_dict.get(pred_id)
                    if pred_process and hasattr(pred_process, 'earliest_start'):
                        pred_finish_time = pred_process.earliest_start + pred_process.duration
                        max_finish_time = max(max_finish_time, pred_finish_time)
                        valid_predecessors += 1
                if valid_predecessors > 0:
                    process.earliest_start = max_finish_time
                else:
                    process.earliest_start = 0
            
    def schedule(self):
        """执行调度（与之前相同，但内部时间单位为天）"""
        if not self.algorithm:
            self.set_algorithm("topological")
        insufficient_workers = self.check_resource_sufficiency()
        if insufficient_workers:
            print("\n❌ 资源不足，无法开始调度！")
            print("=" * 60)
            if insufficient_workers:
                print("\n工人资源不足详情:")
                for issue in insufficient_workers:
                    print(f"  - {issue['issue']}")
                    print(f"    解决方案: 需要增加 {issue['required'] - issue['available']} 名{issue['worker_type']}工人")
                    if issue['available'] < issue['total_workers']:
                        print(f"    提示: 有 {issue['total_workers']} 名{issue['worker_type']}工人，但只有 {issue['available']} 名持证")
            print("\n建议:")
            print("  1. 增加相应工种的工人数量")
            print("  2. 为现有工人增加必要的证书")
            print("  3. 检查并添加缺失的设备")
            print("  4. 调整工序的工人需求配置")
            return None
        print("\n✅ 所有资源检查通过，开始调度...")
        print("=" * 60)
        self.calculate_project_statistics()
        self.schedule_plan = self.algorithm.schedule()
        self.calculate_project_statistics()
        return self.schedule_plan
    
    def is_worker_available(self, worker, start_time, end_time):
        """检查工人在指定时间段是否可用"""
        for task in worker.assigned_tasks:
            task_start, task_end = task
            # 检查时间是否重叠
            if not (end_time <= task_start or start_time >= task_end):
                return False
        return True
    def calculate_project_statistics(self):
        if not self.schedule_plan:
            self.total_project_duration = 0
            return
        
        min_start_time = min(task['start_time'] for task in self.schedule_plan)
        max_end_time = max(task['end_time'] for task in self.schedule_plan)
        self.total_project_duration = max_end_time - min_start_time
    
    def format_time(self, days):
    # 将相对天数转换为绝对日期
        start_date = self.project_start_datetime
        target_date = start_date + datetime.timedelta(days=days)
        
        # 格式化为字符串
        formatted = target_date.strftime('%Y-%m-%d %H:%M:%S')
        return formatted
    
    def print_schedule(self):
        print("调度结果（按设备排序）:")
        print("=" * 100)
        
        # 按设备ID对调度计划进行分组和排序
        schedule_by_equipment = {}
        for task in self.schedule_plan:
            if task['process_id'].endswith('_MILESTONE'):
                continue
            equipment_id = task['equipment_id']
            if equipment_id not in schedule_by_equipment:
                equipment = self.get_equipment_by_id(equipment_id)
                schedule_by_equipment[equipment_id] = {
                    'equipment': equipment,
                    'tasks': []
                }
            schedule_by_equipment[equipment_id]['tasks'].append(task)
        
        # 对每个设备的工序进行处理
        for equipment_id, data in sorted(schedule_by_equipment.items()):
            equipment = data['equipment']
            tasks = data['tasks']
            
            if not equipment:
                continue
                
            print(f"\n设备 {equipment_id}({equipment.name}):")
            print("-" * 80)
            
            # 获取该设备的所有工序模板
            process_templates = {}
            for template in equipment.type.process_templates:
                process_templates[template.process_code] = template
            
            # 按大工序分组
            major_process_groups = {}
            
            for task in tasks:
                # 获取工序对应的模板
                process_code = task['process_id'].split('_')[-1]  # 从 process_id 中提取工序代码
                template = process_templates.get(process_code)
                
                if template and template.parent_process_code:
                    # 小工序，按父工序分组
                    parent_code = template.parent_process_code
                    if parent_code not in major_process_groups:
                        major_process_groups[parent_code] = {
                            'major_process': process_templates.get(parent_code),
                            'sub_processes': []
                        }
                    major_process_groups[parent_code]['sub_processes'].append(task)
                else:
                    # 大工序
                    if process_code not in major_process_groups:
                        major_process_groups[process_code] = {
                            'major_process': template,
                            'sub_processes': []
                        }
                    # 将大工序也作为子工序之一，确保显示顺序
                    major_process_groups[process_code]['sub_processes'].append(task)
            
            # 按大工序代码排序输出
            for major_code, group_data in sorted(major_process_groups.items()):
                major_process = group_data['major_process']
                sub_processes = group_data['sub_processes']
                
                # 输出大工序信息
                if major_process and major_process.is_major_process:
                    print(f"  【{major_process.description}】")
                    
                    # 输出物料需求
                    if major_process.material_requirements:
                        print(f"    物料需求: {major_process.material_requirements}")
                    if major_process.material_price and major_process.material_price > 0:
                        print(f"    物料费用: {major_process.material_price}元")
                    
                    # 输出工具需求
                    if major_process.tools_requirements:
                        print(f"    工具需求: {major_process.tools_requirements}")
                    if major_process.tools_price and major_process.tools_price > 0:
                        print(f"    工具费用: {major_process.tools_price}元")
                    
                    print()
                
                # 输出该大工序下的所有子工序（包括大工序本身）
                for task in sorted(sub_processes, key=lambda x: x['start_time']):
                    # 获取工序名称
                    process_code = task['process_id'].split('_')[-1]
                    template = process_templates.get(process_code)
                    process_name = template.description if template else task['process_name']
                    
                    start_time_formatted = self.format_time(task['start_time'])
                    end_time_formatted = self.format_time(task['end_time'])
                    duration_minutes = task['end_time'] - task['start_time']
                    is_cross_day = duration_minutes > self.work_duration_minutes
                    # 如果是大工序，在名称前加标识
                    if template and template.is_major_process:
                        display_name = f"主工序: {process_name}"
                    else:
                        display_name = f"  子工序: {process_name}"
                    if is_cross_day:
                        display_name += " [跨天工序]"
                    print(f"  {display_name}: ")
                    print(f"    时间 [{start_time_formatted} - {end_time_formatted}], "
                        f"工人: {task['workers']}")
                    if is_cross_day and 'work_segments' in task:
                        print("    工作分段详情:")
                        for i, (seg_start, seg_end) in enumerate(task['work_segments']):
                            seg_start_fmt = self.format_time(seg_start)
                            seg_end_fmt = self.format_time(seg_end)
                            print(f"      第{i+1}段: {seg_start_fmt} - {seg_end_fmt}")
    
    def print_statistics(self):
        """打印统计信息"""
        print("\n" + "="*80)
        print("项目统计信息")
        print("="*80)
        
        # 项目总用时
        days = int(self.total_project_duration)

        
    def get_schedule_json(self):
        """获取JSON格式的调度结果"""
        if not self.schedule_plan:
            return {}
        schedule_by_equipment = {}
        for task in self.schedule_plan:
            if task.get('is_milestone', False):
                continue
            equipment_id = task['equipment_id']
            if equipment_id not in schedule_by_equipment:
                equipment = self.get_equipment_by_id(equipment_id)
                schedule_by_equipment[equipment_id] = {
                    'equipment_id': equipment_id,
                    'equipment_name': equipment.name if equipment else equipment_id,
                    'equipment_category': equipment.category if equipment and hasattr(equipment, 'category') else '未知种类',
                    'major_processes': [],
                    'tasks': []
                }
                if equipment:
                    for template in equipment.type.process_templates:
                        if template.is_major_process:
                            schedule_by_equipment[equipment_id]['major_processes'].append({
                                'process_code': template.process_code,
                                'description': template.description,
                                'material_requirements': template.material_requirements,
                                'material_price': template.material_price,
                                'tools_requirements': template.tools_requirements,
                                'tools_price': template.tools_price
                            })
            formatted_task = {
                'process_id': task['process_id'],
                'process_name': task['process_name'],
                'start_time': task['start_time'],
                'end_time': task['end_time'],
                'start_time_formatted': self.format_time(task['start_time']),
                'end_time_formatted': self.format_time(task['end_time']),
                'workers': task['workers'],
                'duration_days': task['end_time'] - task['start_time']
            }
            schedule_by_equipment[equipment_id]['tasks'].append(formatted_task)

        for equipment_data in schedule_by_equipment.values():
            equipment_data['tasks'].sort(key=lambda x: x['start_time'])

        return {
            'schedule_by_equipment': list(schedule_by_equipment.values()),
            'statistics': {
                'total_project_duration_days': self.total_project_duration,
                'total_workers': len(self.workers),
                'total_equipments': len(self.equipments)
            }
        }
    def get_statistics_data(self):
        # 计算实际的项目时间范围
        project_start_time = float('inf')
        project_end_time = 0

        for equipment in self.equipments:
            if equipment.schedule:
                for start, end, _ in equipment.schedule:
                    project_start_time = min(project_start_time, start)
                    project_end_time = max(project_end_time, end)

        # 如果没有调度，使用默认值
        if project_start_time == float('inf'):
            project_start_time = 0
            project_end_time = 0

        return {
            'total_project_duration_days': self.total_project_duration,
            'total_workers': len(self.workers),
            'total_equipments': len(self.equipments),
            'total_processes': len(self.get_all_processes()),
            'actual_start_time': self.format_time(project_start_time),
            'actual_end_time': self.format_time(project_end_time)
    }
    # 在 Scheduler 类中添加以下方法

    def schedule_from_work_orders(self, work_order_ids, algorithm_name="topological"):
        """根据工单ID列表执行调度，返回 (formatted_plan, statistics, success, message)"""
        try:
            db_path = get_db_path()
            conn = sqlite3.connect(str(db_path))
            c = conn.cursor()
            # 验证工单是否存在
            placeholders = ','.join(['?' for _ in work_order_ids])
            c.execute(f'SELECT id FROM work_orders WHERE id IN ({placeholders})', work_order_ids)
            found = {row[0] for row in c.fetchall()}
            missing = set(work_order_ids) - found
            if missing:
                conn.close()
                return None, None, False, f'以下工单不存在: {missing}'

            # 查询所有任务
            c.execute(f'''
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
            ''', work_order_ids)
            tasks = c.fetchall()
            if not tasks:
                conn.close()
                return None, None, False, '选中的工单中没有可调度的任务'

            # 清空当前调度器中的设备和工人（重新加载）
            self.equipments = []
            self.workers = []
            self.worker_pool = {}
            self.schedule_plan = []

            # 重新加载必要的设备类型和工人（确保资源池完整）
            self.load_workers_from_db(str(db_path))
            self.load_equipment_types_from_db(str(db_path))
            # 按设备分组任务，构建 Process 对象
            equipment_tasks = {}
            for task in tasks:
                (task_id, work_order_id, process_id, process_name,
                equipment_id, equipment_name, predecessor_ids_json,
                estimated_day, is_milestone, equipment_type_id,required_workers) = task

                if equipment_id not in equipment_tasks:
                    equipment_tasks[equipment_id] = {
                        'equipment_name': equipment_name,
                        'equipment_type_id': equipment_type_id,
                        'tasks': []
                    }
                predecessor_ids = json.loads(predecessor_ids_json) if predecessor_ids_json else []
                equipment_tasks[equipment_id]['tasks'].append({
                    'task_id': task_id,
                    'process_id': f"{equipment_id}_{process_id}",
                    'process_name': process_name,
                    'duration': estimated_day,
                    'worker_requirements': json.loads(required_workers) if required_workers else {} ,  # 可从 process_templates 获取，但这里简化
                    'predecessor_ids': predecessor_ids,
                    'is_milestone': bool(is_milestone)
                })

            # 为每个设备创建 Equipment 和 Process 实例
            from core import Equipment, Process
            for eq_id, data in equipment_tasks.items():
                equipment_type_id = str(data['equipment_type_id'])
                if eq_id not in [e.id for e in self.equipments]:
                    # 如果设备不在当前调度器中，先添加（理论上已加载）
                    self.add_equipment(eq_id, data['equipment_name'], data['equipment_type_id'], 'unknown')
                equipment = self.get_equipment_by_id(eq_id)
                if not equipment:
                    continue
                # 清空原有工序
                equipment.processes = []
                for task_data in data['tasks']:
                    proc = Process(
                        id=task_data['process_id'],
                        name=task_data['process_name'],
                        duration=task_data['duration'],
                        equipment_id=eq_id,
                        worker_requirements=task_data['worker_requirements'],
                        predecessor_ids=task_data['predecessor_ids']
                    )
                    if task_data['is_milestone']:
                        proc.is_milestone = True
                    equipment.processes.append(proc)

            conn.close()

            # 检查资源充足性
            insufficient = self.check_resource_sufficiency()
            if insufficient:
                error_details = [{'worker_type': i['worker_type'], 'required': i['required'],
                                'available': i['available'], 'issue': i['issue']} for i in insufficient]
                return None, None, False, {'error_type': 'insufficient_workers', 'details': error_details}

            # 设置算法并调度
            self.set_algorithm(algorithm_name)
            plan = self.schedule()
            if plan is None:
                return None, None, False, '调度因资源不足而中止'

            # 写入数据库 schedule_tasks
            formatted = self.format_schedule_plan(plan)
            self._save_schedule_tasks_to_db(formatted)
            stats = self.get_statistics_data()
            result_data = {
                'success': True,
                'algorithm': algorithm_name,
                'schedule_plan': formatted,
                'statistics': stats,
                'project_start_datetime': self.project_start_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                'equipment_utilization': ...,
                'worker_utilization': ...
            }
            return result_data
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise 
    def _save_schedule_tasks_to_db(self, formatted_plan):
        """将调度结果写入 schedule_tasks 表"""
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('DELETE FROM schedule_tasks')
        for task in formatted_plan:
            c.execute('''
                INSERT INTO schedule_tasks
                (duration_days, end_time, end_time_formatted, equipment_category,
                equipment_id, equipment_name, equipment_type_id, equipment_type_name,
                predecessors, process_id, process_name, start_time, start_time_formatted, workers)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task['duration_days'], task['end_time'], task['end_time_formatted'],
                task['equipment_category'], task['equipment_id'], task['equipment_name'],
                task['equipment_type_id'], task['equipment_type_name'],
                json.dumps(task['predecessors'], ensure_ascii=False), task['process_id'], task['process_name'],
                task['start_time'], task['start_time_formatted'], json.dumps(task['workers'], ensure_ascii=False)
            ))
            parts = task['process_id'].split('_', 1)
            equipment_id = parts[0]          # 例如 "51"
            raw_process_id = parts[1] if len(parts) > 1 else task['process_id']  # 例如 "P0101"

            c.execute('''
                UPDATE work_order_tasks 
                SET scheduled_start_time = ?, scheduled_end_time = ? ,workers=?
                WHERE equipment_id = ? AND process_id = ?
            ''', (task['start_time_formatted'], task['end_time_formatted'], json.dumps(task['workers'], ensure_ascii=False),equipment_id, raw_process_id))
        conn.commit()
        conn.close()

    def format_schedule_plan(self, schedule_plan):
        """格式化调度计划"""
        formatted = []
        for task in schedule_plan:
            if task.get('is_milestone', False):
                continue
            
            equipment = self.get_equipment_by_id(task['equipment_id'])
            equipment_type = self.equipment_types.get(str(equipment.type.id)) if equipment and equipment.type else None
            
            # 计算持续时间（天）
            duration_days = task['end_time'] - task['start_time']
            
            formatted_task = {
                'process_id': task['process_id'],
                'process_name': task['process_name'],
                'equipment_id': task['equipment_id'],
                'equipment_name': task.get('equipment_name', equipment.name if equipment else task['equipment_id']),
                'equipment_category': equipment.category if equipment and hasattr(equipment, 'category') else '未知种类',
                'equipment_type_id': equipment.type.id if equipment and equipment.type else None,
                'equipment_type_name': equipment_type.name if equipment_type else '未知类型',
                'start_time': task['start_time'],
                'end_time': task['end_time'],
                'start_time_formatted': self.format_time(task['start_time']),
                'end_time_formatted': self.format_time(task['end_time']),
                'duration_days': duration_days,  # 转换为小时
                'workers': task.get('workers', {}),
                'predecessors': []
            }
            
            # 获取前置工序信息
            process = self.get_process_by_id(task['process_id'])
            if process and hasattr(process, 'predecessor_ids'):
                formatted_task['predecessors'] = process.predecessor_ids
            
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

def run_scheduling(work_order_ids, algorithm_name="topological"):
    """供 app.py 调用的顶层调度函数"""
    scheduler = get_scheduler()
    result = scheduler.schedule_from_work_orders(work_order_ids, algorithm_name)

    # 处理不同的返回类型
    if isinstance(result, tuple) and len(result) == 4:
        # 已经是四元组（失败情况）
        return result
    elif isinstance(result, dict):
        # 成功情况（字典格式）
        success = result.get('success', True)
        if success:
            formatted_plan = result.get('schedule_plan', [])
            statistics = result.get('statistics', {})
            return formatted_plan, statistics, True, "调度成功"
        else:
            return None, None, False, result.get('message', '调度失败')
    else:
        return None, None, False, f"未知的调度返回格式: {type(result)}"
def main():
    # 创建调度器
    scheduler = Scheduler()
    scheduler.load_all_from_db()
    scheduler.set_algorithm("spt")
    # 执行调度
    schedule_plan = scheduler.schedule()
    
    if schedule_plan is None:
        print("调度因资源不足而中止")
        return
    # 输出调度结果
if __name__ == "__main__":
    main()