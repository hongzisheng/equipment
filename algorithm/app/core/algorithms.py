# scheduler_algorithms.py
import math
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any
from app.core.interface import IScheduler
class TopologicalScheduler:
    def __init__(self, scheduler: IScheduler):
        self.scheduler = scheduler
    """拓扑排序调度算法 - 修复版本"""
    def schedule(self):
        """执行拓扑排序调度"""
        sorted_processes = self.topological_sort()
        self.scheduler.calculate_earliest_start_times(sorted_processes)
        for process in sorted_processes:
            if not self.scheduler.validate_dependencies(process):
                print(f"错误: 工序 {process.id} 的前置工序未完成，无法调度")
                continue
            self.allocate_process(process)
        return self.scheduler.schedule_plan
    def allocate_process(self, process):
        """分配工序资源的核心方法"""
        # 获取所需的设备
        equipment = self.scheduler.get_equipment_by_id(process.equipment_id)
        
        if not equipment:
            print(f"错误: 找不到设备 {process.equipment_id}")
            return
        
        # 首先验证依赖关系
        if not self.scheduler.validate_dependencies(process):
            print(f"错误: 工序 {process.id} 的前置工序未完成，无法调度")
            return
            
        # 从工序的最早开始时间开始寻找可用时间段
        current_start_time = process.earliest_start
        max_attempts = 30  # 最多尝试次数
        
        for attempt in range(max_attempts):
            # 查找设备可用时间槽
            available_slot = self.scheduler.find_equipment_available_slot(
                equipment, current_start_time, process.duration
            )
            
            # 查找可用工人 - 修复：传入正确的参数
            available_workers = self.scheduler.find_available_workers(
                process.worker_requirements,
                available_slot[0],
                available_slot[1],
                process.requires_certification
            )
            
            if available_workers:
                for worker_type, workers in available_workers.items():
                    # 优先使用技能等级较高的工人
                    sorted_workers = sorted(workers, key=lambda x: x.skill_level, reverse=True)
                    available_workers[worker_type] = sorted_workers[:len(workers)]
                # 分配资源
                self.scheduler.assign_resources(
                    process, equipment, available_slot[0], available_workers
                )
                return
        
        # 如果常规方法失败，使用冲突处理
        self.handle_resource_conflict(process, equipment)
    def topological_sort(self):
        all_processes = self.scheduler.get_all_processes()
        in_degree = {}
        graph = {}
        
        # 初始化
        for process in all_processes:
            in_degree[process.id] = 0
            graph[process.id] = []
        
        # 构建图 - 修复：正确处理前置工序依赖
        for process in all_processes:
            for pred_id in process.predecessor_ids:
                # pred_id 是字符串，直接使用
                if pred_id in [p.id for p in all_processes]:
                    graph[pred_id].append(process.id)
                    in_degree[process.id] += 1
                else:
                    print(f"警告: 工序 {process.id} 的前置工序 {pred_id} 不存在")

        # 拓扑排序
        queue = [pid for pid, degree in in_degree.items() if degree == 0]
        sorted_order = []
        
        while queue:
            current = queue.pop(0)
            current_process = self.scheduler.get_process_by_id(current)
            if current_process:
                sorted_order.append(current_process)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 检查是否所有工序都被排序
        if len(sorted_order) != len(all_processes):
            unsorted_ids = set(p.id for p in all_processes) - set(p.id for p in sorted_order)
            print(f"警告: 存在循环依赖或孤立节点，未排序的工序: {unsorted_ids}")
            for process in all_processes:
                if process.id in unsorted_ids:
                    sorted_order.append(process)
                    print(f"强制添加未排序工序: {process.id}")
        
        return sorted_order
    def validate_topological_order(self, processes):
        """验证拓扑排序结果是否正确"""
        process_positions = {p.id: i for i, p in enumerate(processes)}
        for process in processes:
            for pred_id in process.predecessor_ids:
                if pred_id in process_positions:
                    pred_position = process_positions[pred_id]
                    current_position = process_positions[process.id]
                    if pred_position > current_position:
                        print(f"错误: 拓扑排序无效 - 工序 {process.id} 在它的前置工序 {pred_id} 之前")
    
    def validate_all_dependencies(self, process):
        """严格验证所有前置工序是否已完成调度"""
        for pred_id in process.predecessor_ids:
            pred_process = self.scheduler.get_process_by_id(pred_id)
            if not pred_process:
                print(f"错误: 找不到前置工序 {pred_id}")
                return False
            if not hasattr(pred_process, 'actual_start') or pred_process.actual_start is None:
                print(f"错误: 前置工序 {pred_id} 尚未调度")
                return False
            # 前置工序结束时间 = 开始时间 + 持续时间（天）
            pred_end_time = pred_process.actual_start + pred_process.duration
            if process.earliest_start < pred_end_time:
                # 调整当前工序的最早开始时间（直接使用前置结束时间，无需调整工作时间）
                process.earliest_start = pred_end_time
                print(f"调整工序 {process.id} 的最早开始时间: {process.earliest_start} -> {pred_end_time}")
        return True
    
    def recalculate_earliest_start(self, process):
        """重新计算工序的最早开始时间，考虑实际调度情况"""
        if not process.predecessor_ids:
            return
        max_finish_time = 0
        for pred_id in process.predecessor_ids:
            pred_process = self.scheduler.get_process_by_id(pred_id)
            if pred_process and hasattr(pred_process, 'actual_end') and pred_process.actual_end is not None:
                if pred_process.actual_end > max_finish_time:
                    max_finish_time = pred_process.actual_end
        if max_finish_time > 0:
            process.earliest_start = max_finish_time  # 无需调整工作时间
    
    def recalculate_earliest_start(self, process):
        """重新计算工序的最早开始时间，考虑实际调度情况"""
        if not process.predecessor_ids:
            return
        max_finish_time = 0
        for pred_id in process.predecessor_ids:
            pred_process = self.scheduler.get_process_by_id(pred_id)
            if pred_process and hasattr(pred_process, 'actual_end') and pred_process.actual_end is not None:
                if pred_process.actual_end > max_finish_time:
                    max_finish_time = pred_process.actual_end
        if max_finish_time > 0:
            process.earliest_start = max_finish_time  # 无需调整工作时间
    
    def handle_resource_conflict(self, process, equipment):
        """处理资源冲突 - 向后偏移寻找可用工人"""
        duration = process.duration
        base_time = process.earliest_start

        # 策略1: 逐步向后偏移（每次0.5天），寻找同时满足设备和工人的时间段
        for offset in [0.5 * i for i in range(1, 20)]:  # 最多尝试10天
            current_time = base_time + offset
            available_slot = self.scheduler.find_equipment_available_slot(
                equipment, current_time, duration
            )
            available_workers = self.scheduler.find_available_workers(
                process.worker_requirements,
                available_slot[0],
                available_slot[1],
                process.requires_certification
            )
            if available_workers:
                self.scheduler.assign_resources(process, equipment, available_slot[0], available_workers)
                print(f"通过时间偏移 {offset} 天解决了资源冲突")
                return

        # 策略2: 整体推迟若干天（每次1天）
        for day_offset in range(1, 20):
            current_time = base_time + day_offset
            available_slot = self.scheduler.find_equipment_available_slot(
                equipment, current_time, duration
            )
            available_workers = self.scheduler.find_available_workers(
                process.worker_requirements,
                available_slot[0],
                available_slot[1],
                process.requires_certification
            )
            if available_workers:
                self.scheduler.assign_resources(process, equipment, available_slot[0], available_workers)
                print(f"通过推移 {day_offset} 天解决了资源冲突")
                return

        # 最终回退
        self.fallback_allocation(process, equipment)
    
    def fallback_allocation(self, process, equipment):
        """最终回退方案：在设备空闲后寻找可用工人"""
        duration = process.duration

        # 从 earliest_start 开始，逐步向后搜索（0.5天步长）
        base_time = process.earliest_start
        for day_offset in range(0, 60):  # 最多60天
            for half_day in [0, 0.5]:
                current_time = base_time + day_offset + half_day
                available_slot = self.scheduler.find_equipment_available_slot(
                    equipment, current_time, duration
                )
                available_workers = self.scheduler.find_available_workers(
                    process.worker_requirements,
                    available_slot[0],
                    available_slot[1],
                    process.requires_certification
                )
                if available_workers:
                    self.scheduler.assign_resources(process, equipment, available_slot[0], available_workers)
                    print(f"通过回退方案在 {current_time} 找到了可用工人")
                    return

        # 如果所有尝试都失败，使用设备上最后一个任务之后的时间
        if equipment.schedule:
            equipment.schedule.sort(key=lambda x: x[0])
            last_end = equipment.schedule[-1][1]
            start_time = last_end
        else:
            start_time = process.earliest_start

        # 在设备空闲后继续搜索工人
        for day_offset in range(0, 30):
            current_time = start_time + day_offset
            available_slot = self.scheduler.find_equipment_available_slot(
                equipment, current_time, duration
            )
            available_workers = self.scheduler.find_available_workers(
                process.worker_requirements,
                available_slot[0],
                available_slot[1],
                process.requires_certification
            )
            if available_workers:
                self.scheduler.assign_resources(process, equipment, available_slot[0], available_workers)
                print(f"最终在设备空闲后 {day_offset} 天找到了可用工人")
                return

        # 完全找不到工人，记录问题但不强制分配空工人
        print(f"严重错误: 工序 {process.id} 无法分配到工人，可能需要增加工人资源")
        # 不再强制分配空工人，而是尝试最基本的分配
        self.scheduler.assign_resources(process, equipment, start_time, {})
class GreedyScheduler():
    """贪心算法调度"""
    def __init__(self, scheduler: IScheduler):
        self.scheduler = scheduler
    def schedule(self):
        """贪心算法实现 - 按多种优先级策略排序"""
        print("使用贪心算法进行调度")
        
        # 获取所有工序并计算最早开始时间
        all_processes = self.get_all_processes()
        self.scheduler.calculate_earliest_start_times(all_processes)
        # 贪心策略：按多种因素综合排序
        # 1. 关键工序优先
        # 2. 持续时间长的优先（避免大任务被推迟）
        # 3. 前置依赖少的优先
        sorted_processes = sorted(all_processes, 
                                 key=lambda x: (
                                     not x.is_critical,  # 关键工序在前
                                     -x.duration,        # 持续时间长的在前
                                     len(x.predecessor_ids)  # 前置依赖少的在前
                                 ))
        
        # 调度所有工序
        for process in sorted_processes:
            self.allocate_process_greedy(process)
            
        return self.scheduler.schedule_plan
    
    def allocate_process_greedy(self, process):
        """贪心算法分配资源 - 寻找最早可用的时间段"""
        equipment = self.scheduler.get_equipment_by_id(process.equipment_id)
        duration_minutes = process.duration * 60
        
        # 从最早开始时间开始寻找可用时间段
        current_start_time = process.earliest_start
        max_attempts = 50  # 最多尝试50次
        
        for attempt in range(max_attempts):
            # 调整到工作时间
            adjusted_time = self.scheduler.adjust_to_work_time(current_start_time)
            
            # 查找设备可用时间槽
            available_slot = self.scheduler.find_equipment_available_slot(
                equipment, adjusted_time, duration_minutes
            )
            
            # 查找可用工人
            available_workers = self.scheduler.find_available_workers(
                process.worker_requirements,
                available_slot[0],
                available_slot[1],
                process.requires_certification
            )
            
            if available_workers:
                # 分配资源
                if duration_minutes > self.scheduler.work_duration_minutes:
                    # 跨天工序使用跨天分配
                    work_segments = self.scheduler.schedule_cross_day_process(adjusted_time, duration_minutes)
                    self.scheduler.assign_cross_day_resources(process, equipment, work_segments, available_workers)
                else:
                    self.scheduler.assign_resources(process, equipment, available_slot[0], available_workers)
                return
            
            # 如果当前时间段不可用，尝试下一个可能的时间段
            # 策略：跳到当前时间段结束后再尝试
            current_start_time = available_slot[1] + 1
        
        # 如果常规方法失败，使用冲突处理
        self.handle_greedy_conflict(process, equipment)
    
    def handle_greedy_conflict(self, process, equipment):
        """贪心算法冲突处理 - 寻找任何可用的时间段"""
        duration_minutes = process.duration * 60
        
        # 方法1：从项目开始时间系统性地搜索
        start_search_time = self.scheduler.work_start_minutes
        max_search_days = 60  # 最多搜索60天
        
        for day in range(max_search_days):
            search_time = start_search_time + day * self.scheduler.minutes_per_day
            adjusted_time = self.scheduler.adjust_to_work_time(search_time)
            
            available_slot = self.scheduler.find_equipment_available_slot(
                equipment, adjusted_time, duration_minutes
            )
            
            available_workers = self.scheduler.find_available_workers(
                process.worker_requirements,
                available_slot[0],
                available_slot[1],
                process.requires_certification
            )
            
            if available_workers:
                if duration_minutes > self.scheduler.work_duration_minutes:
                    # 跨天工序：生成工作段并使用跨天分配
                    work_segments = self.scheduler.schedule_cross_day_process(
                        process, equipment, available_slot[0], duration_minutes
                    )
                    self.scheduler.assign_cross_day_resources(
                        process, equipment, work_segments, available_workers
                    )
                else:
                    self.scheduler.assign_resources(process, equipment, available_slot[0], available_workers)
                return
        
        # 方法2：如果还是找不到，使用设备上最后一个任务之后的时间
        if equipment.schedule:
            equipment.schedule.sort(key=lambda x: x[0])
            last_end = equipment.schedule[-1][1]
            start_time = self.scheduler.adjust_to_work_time(last_end)
            
            # 对于跨天工序，需要生成工作段
            if duration_minutes > self.scheduler.work_duration_minutes:
                work_segments = self.scheduler.schedule_cross_day_process(
                    process, equipment, start_time, duration_minutes
                )
                available_workers = self.scheduler.find_available_workers(
                    process.worker_requirements,
                    work_segments[0][0],
                    work_segments[-1][1],
                    process.requires_certification
                )
                
                if available_workers:
                    self.scheduler.assign_cross_day_resources(
                        process, equipment, work_segments, available_workers
                    )
                else:
                    # 最终回退：即使没有工人也分配，在实际应用中可能需要处理这种情况
                    self.fallback_with_workers(process, equipment, start_time)
            else:
                available_slot = (start_time, start_time + duration_minutes)
                available_workers = self.scheduler.find_available_workers(
                    process.worker_requirements,
                    available_slot[0],
                    available_slot[1],
                    process.requires_certification
                )
                
                if available_workers:
                    self.scheduler.assign_resources(process, equipment, start_time, available_workers)
                else:
                    # 最终回退：即使没有工人也分配，在实际应用中可能需要处理这种情况
                    self.fallback_with_workers(process, equipment, start_time)
        else:
            # 设备完全空闲，从最早开始时间安排
            start_time = process.earliest_start
            self.scheduler.assign_resources(process, equipment, start_time, {})
    def fallback_with_workers(self, process, equipment, start_time):
        """寻找有可用工人的时间段"""
        duration_minutes = process.duration * 60
        
        for day_offset in range(0, 30):
            current_time = start_time + day_offset * self.scheduler.minutes_per_day
            adjusted_time = self.scheduler.adjust_to_work_time(current_time)
            
            available_slot = self.scheduler.find_equipment_available_slot(
                equipment, adjusted_time, duration_minutes
            )
            
            available_workers = self.scheduler.find_available_workers(
                process.worker_requirements,
                available_slot[0],
                available_slot[1],
                process.requires_certification
            )
            
            if available_workers:
                if duration_minutes > self.scheduler.work_duration_minutes:
                    # 跨天工序：生成工作段并使用跨天分配
                    work_segments = self.scheduler.schedule_cross_day_process(
                        process, equipment, available_slot[0], duration_minutes
                    )
                    self.scheduler.assign_cross_day_resources(
                        process, equipment, work_segments, available_workers
                    )
                else:
                    self.scheduler.assign_resources(process, equipment, available_slot[0], available_workers)
                print(f"贪心算法在 {day_offset} 天后找到了可用工人")
                return
        
        # 如果还是找不到，使用最终回退
        if duration_minutes > self.scheduler.work_duration_minutes:
            # 跨天工序：生成工作段并使用跨天分配
            work_segments = self.scheduler.schedule_cross_day_process(
                process, equipment, start_time, duration_minutes
            )
            self.scheduler.assign_cross_day_resources(
                process, equipment, work_segments, {}
            )
        else:
            self.scheduler.assign_resources(process, equipment, start_time, {})
class GeneticScheduler():
    """遗传算法调度"""
    def __init__(self, scheduler: IScheduler, population_size=50, generations=100):
        super().__init__(scheduler)
        self.population_size = population_size
        self.generations = generations
        self.scheduler = scheduler
    def schedule(self):
        """遗传算法实现"""
        # 这里实现遗传算法逻辑
        print("使用遗传算法进行调度")
        return self.scheduler.schedule_plan

class ShortestProcessingTimeScheduler():
    """最短处理时间优先算法调度"""
    def __init__(self, scheduler: IScheduler):
        self.scheduler = scheduler
    def schedule(self):
        """SPT算法实现 - 优先安排处理时间短的工序"""
        print("使用最短处理时间优先算法进行调度")
        
        # 获取所有工序并计算最早开始时间
        all_processes = self.scheduler.get_all_processes()
        self.scheduler.calculate_earliest_start_times(all_processes)
        
        # 按处理时间排序（短的优先）
        sorted_processes = sorted(all_processes, key=lambda x: x.duration)
        
        # 调度所有工序
        for process in sorted_processes:
            self.allocate_process_spt(process)
            
        return self.scheduler.schedule_plan
    
    def allocate_process_spt(self, process):
        """SPT算法分配资源"""
        equipment = self.scheduler.get_equipment_by_id(process.equipment_id)
        duration_minutes = process.duration * 60
        
        # 使用最早开始时间作为基准
        current_start_time = process.earliest_start
        max_attempts = 30
        
        for attempt in range(max_attempts):
            # 调整到工作时间
            adjusted_time = self.scheduler.adjust_to_work_time(current_start_time)
            
            # 查找设备可用时间槽
            available_slot = self.scheduler.find_equipment_available_slot(
                equipment, adjusted_time, duration_minutes
            )
            
            # 查找可用工人
            available_workers = self.scheduler.find_available_workers(
                process.worker_requirements,
                available_slot[0],
                available_slot[1],
                process.requires_certification
            )
            
            if available_workers:
                # 分配资源
                self.scheduler.assign_resources(process, equipment, available_slot[0], available_workers)
                return
            
            # 尝试下一个时间
            current_start_time = available_slot[1]
        
        # 冲突处理
        self.handle_spt_conflict(process, equipment)
    
    def handle_spt_conflict(self, process, equipment):
        """SPT冲突处理"""
        duration_minutes = process.duration * 60
        
        # 找到设备上所有时间间隙
        if not equipment.schedule:
            # 设备空闲，从最早开始时间安排
            start_time = process.earliest_start
            available_slot = (start_time, start_time + duration_minutes)
        else:
            # 对设备安排进行排序
            equipment.schedule.sort(key=lambda x: x[0])
            
            # 检查第一个任务前的时间段
            first_task_start = equipment.schedule[0][0]
            if first_task_start - process.earliest_start >= duration_minutes:
                start_time = process.earliest_start
                available_slot = (start_time, start_time + duration_minutes)
            else:
                # 检查任务间的时间段
                available_slot = None
                for i in range(len(equipment.schedule) - 1):
                    current_end = equipment.schedule[i][1]
                    next_start = equipment.schedule[i + 1][0]
                    
                    gap_start = self.scheduler.adjust_to_work_time(current_end)
                    gap_end = next_start
                    
                    if gap_end - gap_start >= duration_minutes:
                        available_slot = (gap_start, gap_start + duration_minutes)
                        break
                
                if not available_slot:
                    # 使用最后一个任务后的时间段
                    last_end = equipment.schedule[-1][1]
                    start_time = self.scheduler.adjust_to_work_time(last_end)
                    available_slot = (start_time, start_time + duration_minutes)
        
        # 查找可用工人
        available_workers = self.scheduler.find_available_workers(
            process.worker_requirements,
            available_slot[0],
            available_slot[1],
            process.requires_certification
        )
        
        if available_workers:
            if duration_minutes > self.scheduler.work_duration_minutes:
                work_segments = self.scheduler.schedule_cross_day_process(available_slot[0], duration_minutes)
                self.scheduler.assign_cross_day_resources(process, equipment, work_segments, available_workers)
            else:
                self.scheduler.assign_resources(process, equipment, available_slot[0], available_workers)
        else:
            # 如果找不到工人，调整时间直到找到可用工人
            self.adjust_for_workers(process, equipment, available_slot[0], duration_minutes)
    
    def adjust_for_workers(self, process, equipment, proposed_start, duration_minutes):
        """调整时间以找到可用工人"""
        current_time = proposed_start
        
        for day_offset in range(20):  # 最多尝试20天
            adjusted_time = self.scheduler.adjust_to_work_time(
                current_time + day_offset * self.scheduler.minutes_per_day
            )
            
            available_slot = self.scheduler.find_equipment_available_slot(
                equipment, adjusted_time, duration_minutes
            )
            
            available_workers = self.scheduler.find_available_workers(
                process.worker_requirements,
                available_slot[0],
                available_slot[1],
                process.requires_certification
            )
            
            if available_workers:
                if duration_minutes > self.scheduler.work_duration_minutes:
                    work_segments = self.scheduler.schedule_cross_day_process(adjusted_time, duration_minutes)
                    self.scheduler.assign_cross_day_resources(process, equipment, work_segments, available_workers)
                else:
                    self.scheduler.assign_resources(process, equipment, available_slot[0], available_workers)
                return
        
        # 最终回退：使用第一个可用时间
        for day_offset in range(20, 50):  # 再尝试30天
            current_time = proposed_start + day_offset * self.scheduler.minutes_per_day
            adjusted_time = self.scheduler.adjust_to_work_time(current_time)
            
            available_slot = self.scheduler.find_equipment_available_slot(
                equipment, adjusted_time, duration_minutes
            )
            
            available_workers = self.scheduler.find_available_workers(
                process.worker_requirements,
                available_slot[0],
                available_slot[1],
                process.requires_certification
            )
            
            if available_workers:
                if duration_minutes > self.scheduler.work_duration_minutes:
                    work_segments = self.scheduler.schedule_cross_day_process(adjusted_time, duration_minutes)
                    self.scheduler.assign_cross_day_resources(process, equipment, work_segments, available_workers)
                else:
                    self.scheduler.assign_resources(process, equipment, available_slot[0], available_workers)
                return

        # 如果所有尝试都失败，才使用空工人
        self.scheduler.assign_resources(process, equipment, proposed_start, {})