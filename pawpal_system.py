from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time, datetime, timedelta
from typing import Dict, List, Optional, Tuple

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


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
        """Mark this task as completed by setting its status to 'done'."""
        self.status = "done"

    def reschedule(self, new_date: date, new_time: time) -> None:
        """Update the task's scheduled date and time to the given values."""
        self.date = new_date
        self.time = new_time

    def conflicts_with(self, other_task: "Task") -> bool:
        """Return True if this task's time window overlaps with another task's."""
        if self.date != other_task.date:
            return False
        self_start = datetime.combine(self.date, self.time)
        self_end = self_start + timedelta(minutes=self.duration_minutes)
        other_start = datetime.combine(other_task.date, other_task.time)
        other_end = other_start + timedelta(minutes=other_task.duration_minutes)
        return self_start < other_end and other_start < self_end

    def to_dict(self) -> Dict[str, str]:
        """Serialize all task fields to a flat string dictionary."""
        return {
            "title": self.title,
            "task_type": self.task_type,
            "date": str(self.date),
            "time": self.time.strftime("%I:%M %p"),
            "duration_minutes": str(self.duration_minutes),
            "priority": self.priority,
            "pet_name": self.pet_name,
            "is_recurring": str(self.is_recurring),
            "status": self.status,
        }


@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: List[Task] = field(default_factory=list)

    def update_profile(self, name: str, species: str, age: int) -> None:
        """Replace the pet's name, species, and age with the provided values."""
        self.name = name
        self.species = species
        self.age = age

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's personal task list."""
        self.tasks.append(task)

    def get_tasks_for_date(self, target_date: date) -> List[Task]:
        """Return all of this pet's tasks scheduled on the given date."""
        return [t for t in self.tasks if t.date == target_date]


@dataclass
class Owner:
    name: str
    available_minutes_per_day: int = 120
    preferences: Dict[str, str] = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner's care."""
        self.pets.append(pet)

    def set_preferences(self, preferences: Dict[str, str]) -> None:
        """Merge the given key-value pairs into the owner's scheduling preferences."""
        self.preferences.update(preferences)

    def get_today_tasks(self, scheduler: "Scheduler", target_date: date) -> List[Task]:
        """Return all tasks for this owner's pets on the given date, sorted by the scheduler."""
        pet_names = {pet.name for pet in self.pets}
        tasks = [t for t in scheduler.get_tasks_for_date(target_date) if t.pet_name in pet_names]
        return scheduler.sort_tasks(tasks)


@dataclass
class Scheduler:
    tasks: List[Task] = field(default_factory=list)
    sort_strategy: str = "priority_then_time"

    def add_task(self, task: Task) -> None:
        """Add a task to the scheduler's master task list."""
        self.tasks.append(task)

    def schedule_walk(
        self,
        pet: Pet,
        walk_date: date,
        walk_time: time,
        duration: int,
        priority: str = "high",
    ) -> Task:
        """Create a walk task for the given pet, register it with both the pet and scheduler, and return it."""
        task = Task(
            title=f"Walk {pet.name}",
            task_type="walk",
            date=walk_date,
            time=walk_time,
            duration_minutes=duration,
            priority=priority,
            pet_name=pet.name,
        )
        self.add_task(task)
        pet.add_task(task)
        return task

    def get_tasks_for_date(self, target_date: date) -> List[Task]:
        """Return all tasks in the scheduler that fall on the given date."""
        return [t for t in self.tasks if t.date == target_date]

    def get_today_tasks(self) -> List[Task]:
        """Return today's tasks sorted according to the current sort strategy."""
        return self.sort_tasks(self.get_tasks_for_date(date.today()))

    def sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks using the current strategy: 'priority_then_time', 'time_only', or 'priority_only'."""
        if self.sort_strategy == "priority_then_time":
            return sorted(tasks, key=lambda t: (PRIORITY_ORDER.get(t.priority, 99), t.time))
        elif self.sort_strategy == "time_only":
            return sorted(tasks, key=lambda t: t.time)
        elif self.sort_strategy == "priority_only":
            return sorted(tasks, key=lambda t: PRIORITY_ORDER.get(t.priority, 99))
        return tasks

    def detect_conflicts(self, tasks: Optional[List[Task]] = None) -> List[Tuple[Task, Task]]:
        """Return all pairs of tasks whose time windows overlap on the same date."""
        check = tasks if tasks is not None else self.tasks
        conflicts = []
        for i in range(len(check)):
            for j in range(i + 1, len(check)):
                if check[i].conflicts_with(check[j]):
                    conflicts.append((check[i], check[j]))
        return conflicts

    def resolve_conflicts(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        """Resolve overlapping tasks by shifting lower-priority tasks to start after the blocking task ends."""
        check = list(tasks) if tasks is not None else list(self.tasks)
        check = self.sort_tasks(check)  # process in priority order first

        for i in range(len(check)):
            for j in range(i + 1, len(check)):
                if check[i].conflicts_with(check[j]):
                    # Push the lower-priority task to start after the earlier one ends
                    earlier_end = datetime.combine(check[i].date, check[i].time) + timedelta(
                        minutes=check[i].duration_minutes
                    )
                    check[j].reschedule(check[j].date, earlier_end.time())

        return check
