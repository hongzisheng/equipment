# algorithms.py
"""调度算法实现

从 algorithm 分支移植。TopologicalScheduler 为主要使用的算法。
GreedyScheduler、GeneticScheduler、ShortestProcessingTimeScheduler 为备选算法。
"""
from app.core.interface import IScheduler


class TopologicalScheduler:
    """拓扑排序调度算法"""

    def __init__(self, scheduler: IScheduler):
        self.scheduler = scheduler

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
        """分配工序资源 - 持续向后查找直到找到可用工人"""
        equipment = self.scheduler.get_equipment_by_id(process.equipment_id)
        if not equipment:
            print(f"错误: 找不到设备 {process.equipment_id}")
            return
        if not self.scheduler.validate_dependencies(process):
            print(f"错误: 工序 {process.id} 的前置工序未完成，无法调度")
            return
        
        current_start_time = process.earliest_start
        max_days = 100
        
        best_partial_workers = None
        best_partial_slot = None
        
        for day_offset in range(0, max_days):
            for half_day_offset in [0, 0.5]:
                search_time = current_start_time + day_offset + half_day_offset
                
                available_slot = self.scheduler.find_equipment_available_slot(
                    equipment, search_time, process.duration
                )
                available_workers, all_met = self.scheduler.find_available_workers(
                    process.worker_requirements,
                    available_slot[0],
                    available_slot[1],
                    getattr(process, "requires_certification", False),
                )
                
                if available_workers and all_met:
                    self.scheduler.assign_resources(
                        process, equipment, available_slot[0], available_workers
                    )
                    return
                
                if available_workers and not all_met:
                    if not best_partial_workers or len(available_workers) > len(best_partial_workers):
                        best_partial_workers = available_workers
                        best_partial_slot = available_slot
        
        if best_partial_workers and best_partial_slot:
            self.scheduler.assign_resources(process, equipment, best_partial_slot[0], best_partial_workers)
        else:
            last_slot = self.scheduler.find_equipment_available_slot(
                equipment, current_start_time + max_days, process.duration
            )
            partial_workers, _ = self.scheduler.find_available_workers(
                process.worker_requirements,
                last_slot[0],
                last_slot[1],
                getattr(process, "requires_certification", False),
            )
            self.scheduler.assign_resources(process, equipment, last_slot[0], partial_workers or {})

    def topological_sort(self):
        all_processes = self.scheduler.get_all_processes()
        in_degree = {}
        graph = {}
        for process in all_processes:
            in_degree[process.id] = 0
            graph[process.id] = []
        for process in all_processes:
            for pred_id in process.predecessor_ids:
                if pred_id in [p.id for p in all_processes]:
                    graph[pred_id].append(process.id)
                    in_degree[process.id] += 1
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
        if len(sorted_order) != len(all_processes):
            unsorted_ids = set(p.id for p in all_processes) - set(p.id for p in sorted_order)
            for process in all_processes:
                if process.id in unsorted_ids:
                    sorted_order.append(process)
        return sorted_order




class GreedyScheduler:
    """贪心算法调度（简化版，使用拓扑排序作为基础）"""

    def __init__(self, scheduler: IScheduler):
        self.scheduler = scheduler

    def schedule(self):
        """贪心算法实现 - 按持续时间排序"""
        all_processes = self.scheduler.get_all_processes()
        self.scheduler.calculate_earliest_start_times(all_processes)
        sorted_processes = sorted(all_processes, key=lambda x: -x.duration)
        for process in sorted_processes:
            self._allocate(process)
        return self.scheduler.schedule_plan

    def _allocate(self, process):
        equipment = self.scheduler.get_equipment_by_id(process.equipment_id)
        if not equipment:
            return
        
        current_start_time = process.earliest_start
        max_days = 100
        
        best_partial_workers = None
        best_partial_slot = None
        
        for day_offset in range(0, max_days):
            for half_day_offset in [0, 0.5]:
                search_time = current_start_time + day_offset + half_day_offset
                
                available_slot = self.scheduler.find_equipment_available_slot(
                    equipment, search_time, process.duration
                )
                available_workers, all_met = self.scheduler.find_available_workers(
                    process.worker_requirements,
                    available_slot[0],
                    available_slot[1],
                    getattr(process, "requires_certification", False),
                )
                
                if available_workers and all_met:
                    self.scheduler.assign_resources(
                        process, equipment, available_slot[0], available_workers
                    )
                    return
                
                if available_workers and not all_met:
                    if not best_partial_workers or len(available_workers) > len(best_partial_workers):
                        best_partial_workers = available_workers
                        best_partial_slot = available_slot
        
        if best_partial_workers and best_partial_slot:
            self.scheduler.assign_resources(process, equipment, best_partial_slot[0], best_partial_workers)
        else:
            last_slot = self.scheduler.find_equipment_available_slot(
                equipment, current_start_time + max_days, process.duration
            )
            partial_workers, _ = self.scheduler.find_available_workers(
                process.worker_requirements,
                last_slot[0],
                last_slot[1],
                getattr(process, "requires_certification", False),
            )
            self.scheduler.assign_resources(process, equipment, last_slot[0], partial_workers or {})


class GeneticScheduler:
    """遗传算法调度（简化占位）"""

    def __init__(self, scheduler: IScheduler, population_size=50, generations=100):
        self.scheduler = scheduler
        self.population_size = population_size
        self.generations = generations

    def schedule(self):
        """遗传算法实现（简化为拓扑排序）"""
        topo = TopologicalScheduler(self.scheduler)
        return topo.schedule()


class ShortestProcessingTimeScheduler:
    """最短处理时间优先算法调度"""

    def __init__(self, scheduler: IScheduler):
        self.scheduler = scheduler

    def schedule(self):
        """SPT算法实现 - 优先安排处理时间短的工序"""
        all_processes = self.scheduler.get_all_processes()
        self.scheduler.calculate_earliest_start_times(all_processes)
        sorted_processes = sorted(all_processes, key=lambda x: x.duration)
        for process in sorted_processes:
            self._allocate_spt(process)
        return self.scheduler.schedule_plan

    def _allocate_spt(self, process):
        equipment = self.scheduler.get_equipment_by_id(process.equipment_id)
        if not equipment:
            return
        
        current_start_time = process.earliest_start
        max_days = 100
        
        best_partial_workers = None
        best_partial_slot = None
        
        for day_offset in range(0, max_days):
            for half_day_offset in [0, 0.5]:
                search_time = current_start_time + day_offset + half_day_offset
                
                available_slot = self.scheduler.find_equipment_available_slot(
                    equipment, search_time, process.duration
                )
                available_workers, all_met = self.scheduler.find_available_workers(
                    process.worker_requirements,
                    available_slot[0],
                    available_slot[1],
                    getattr(process, "requires_certification", False),
                )
                
                if available_workers and all_met:
                    self.scheduler.assign_resources(
                        process, equipment, available_slot[0], available_workers
                    )
                    return
                
                if available_workers and not all_met:
                    if not best_partial_workers or len(available_workers) > len(best_partial_workers):
                        best_partial_workers = available_workers
                        best_partial_slot = available_slot
        
        if best_partial_workers and best_partial_slot:
            self.scheduler.assign_resources(process, equipment, best_partial_slot[0], best_partial_workers)
        else:
            last_slot = self.scheduler.find_equipment_available_slot(
                equipment, current_start_time + max_days, process.duration
            )
            partial_workers, _ = self.scheduler.find_available_workers(
                process.worker_requirements,
                last_slot[0],
                last_slot[1],
                getattr(process, "requires_certification", False),
            )
            self.scheduler.assign_resources(process, equipment, last_slot[0], partial_workers or {})
