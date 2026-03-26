from dataclasses import dataclass, field
from datetime import date, time
from typing import Dict, List, Optional, Tuple


@dataclass
class Task:
    title: str
    task_type: str
    date: date
    time: time
    duration_minutes: int
    priority: str
    pet_name: str
    is_recurring: bool = False
    status: str = "pending"

    def mark_done(self) -> None:
        pass

    def reschedule(self, new_date: date, new_time: time) -> None:
        pass

    def conflicts_with(self, other_task: "Task") -> bool:
        pass

    def to_dict(self) -> Dict[str, str]:
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int

    def update_profile(self, name: str, species: str, age: int) -> None:
        pass


@dataclass
class Owner:
    name: str
    available_minutes_per_day: int = 120
    preferences: Dict[str, str] = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def set_preferences(self, preferences: Dict[str, str]) -> None:
        pass

    def get_today_tasks(self, scheduler: "Scheduler", target_date: date) -> List[Task]:
        pass


@dataclass
class Scheduler:
    tasks: List[Task] = field(default_factory=list)
    sort_strategy: str = "priority_then_time"

    def add_task(self, task: Task) -> None:
        pass

    def schedule_walk(
        self,
        pet: Pet,
        walk_date: date,
        walk_time: time,
        duration: int,
        priority: str = "high",
    ) -> Task:
        pass

    def get_tasks_for_date(self, target_date: date) -> List[Task]:
        pass

    def get_today_tasks(self) -> List[Task]:
        pass

    def sort_tasks(self, tasks: List[Task]) -> List[Task]:
        pass

    def detect_conflicts(self, tasks: Optional[List[Task]] = None) -> List[Tuple[Task, Task]]:
        pass

    def resolve_conflicts(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        pass
