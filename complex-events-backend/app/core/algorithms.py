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
        """分配工序资源"""
        equipment = self.scheduler.get_equipment_by_id(process.equipment_id)
        if not equipment:
            print(f"错误: 找不到设备 {process.equipment_id}")
            return
        if not self.scheduler.validate_dependencies(process):
            print(f"错误: 工序 {process.id} 的前置工序未完成，无法调度")
            return
        current_start_time = process.earliest_start
        max_attempts = 30
        for attempt in range(max_attempts):
            available_slot = self.scheduler.find_equipment_available_slot(
                equipment, current_start_time, process.duration
            )
            available_workers = self.scheduler.find_available_workers(
                process.worker_requirements,
                available_slot[0],
                available_slot[1],
                getattr(process, "requires_certification", False),
            )
            if available_workers:
                for worker_type, workers in available_workers.items():
                    sorted_workers = sorted(workers, key=lambda x: x.skill_level, reverse=True)
                    available_workers[worker_type] = sorted_workers[: len(workers)]
                self.scheduler.assign_resources(
                    process, equipment, available_slot[0], available_workers
                )
                return
        self.handle_resource_conflict(process, equipment)

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

    def handle_resource_conflict(self, process, equipment):
        """处理资源冲突 - 向后偏移寻找可用工人"""
        duration = process.duration
        base_time = process.earliest_start
        for offset in [0.5 * i for i in range(1, 20)]:
            current_time = base_time + offset
            available_slot = self.scheduler.find_equipment_available_slot(
                equipment, current_time, duration
            )
            available_workers = self.scheduler.find_available_workers(
                process.worker_requirements,
                available_slot[0],
                available_slot[1],
                getattr(process, "requires_certification", False),
            )
            if available_workers:
                self.scheduler.assign_resources(
                    process, equipment, available_slot[0], available_workers
                )
                return
        for day_offset in range(1, 20):
            current_time = base_time + day_offset
            available_slot = self.scheduler.find_equipment_available_slot(
                equipment, current_time, duration
            )
            available_workers = self.scheduler.find_available_workers(
                process.worker_requirements,
                available_slot[0],
                available_slot[1],
                getattr(process, "requires_certification", False),
            )
            if available_workers:
                self.scheduler.assign_resources(
                    process, equipment, available_slot[0], available_workers
                )
                return
        # 最终回退：使用空工人分配
        if equipment.schedule:
            equipment.schedule.sort(key=lambda x: x[0])
            start_time = equipment.schedule[-1][1]
        else:
            start_time = process.earliest_start
        self.scheduler.assign_resources(process, equipment, start_time, {})


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
        for attempt in range(30):
            available_slot = self.scheduler.find_equipment_available_slot(
                equipment, current_start_time, process.duration
            )
            available_workers = self.scheduler.find_available_workers(
                process.worker_requirements,
                available_slot[0],
                available_slot[1],
                getattr(process, "requires_certification", False),
            )
            if available_workers:
                self.scheduler.assign_resources(
                    process, equipment, available_slot[0], available_workers
                )
                return
            current_start_time = available_slot[1]
        self.scheduler.assign_resources(process, equipment, current_start_time, {})


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
        for attempt in range(30):
            available_slot = self.scheduler.find_equipment_available_slot(
                equipment, current_start_time, process.duration
            )
            available_workers = self.scheduler.find_available_workers(
                process.worker_requirements,
                available_slot[0],
                available_slot[1],
                getattr(process, "requires_certification", False),
            )
            if available_workers:
                self.scheduler.assign_resources(
                    process, equipment, available_slot[0], available_workers
                )
                return
            current_start_time = available_slot[1]
        self.scheduler.assign_resources(process, equipment, current_start_time, {})
