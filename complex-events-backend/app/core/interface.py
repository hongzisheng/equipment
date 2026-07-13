# scheduler_interface.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class IScheduler(ABC):
    """调度器接口，定义算法需要的方法"""

    @abstractmethod
    def get_equipment_by_id(self, equipment_id):
        pass

    @abstractmethod
    def get_process_by_id(self, process_id):
        pass

    @abstractmethod
    def assign_resources(self, process, equipment, start_time, workers):
        pass

    @abstractmethod
    def find_equipment_available_slot(self, equipment, start_time, duration_minutes):
        pass

    @abstractmethod
    def find_available_workers(
        self, worker_requirements, start_time, end_time, requires_certification=False
    ):
        pass

    @abstractmethod
    def calculate_earliest_start_times(self, processes):
        pass
