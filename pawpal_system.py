from __future__ import annotations

import json
import os
from collections import defaultdict
from copy import copy
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
    recurrence: str = ""   # "daily" | "weekly" | "" (one-off)
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

    def end_time(self) -> time:
        """Return the clock time when this task finishes."""
        return (datetime.combine(self.date, self.time) + timedelta(minutes=self.duration_minutes)).time()

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

    def save_to_json(self, path: str = "data.json") -> None:
        """Serialize the owner, all pets, and all their tasks to a JSON file."""
        data = {
            "name": self.name,
            "available_minutes_per_day": self.available_minutes_per_day,
            "preferences": self.preferences,
            "pets": [
                {
                    "name": p.name,
                    "species": p.species,
                    "age": p.age,
                    "tasks": [
                        {
                            "title": t.title,
                            "task_type": t.task_type,
                            "date": str(t.date),
                            "time": t.time.strftime("%H:%M"),
                            "duration_minutes": t.duration_minutes,
                            "priority": t.priority,
                            "pet_name": t.pet_name,
                            "is_recurring": t.is_recurring,
                            "recurrence": t.recurrence,
                            "status": t.status,
                        }
                        for t in p.tasks
                    ],
                }
                for p in self.pets
            ],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_json(cls, path: str = "data.json") -> Optional["Owner"]:
        """Load an Owner (with pets and tasks) from a JSON file.

        Returns None if the file does not exist.
        """
        if not os.path.exists(path):
            return None
        with open(path) as f:
            data = json.load(f)
        owner = cls(
            name=data["name"],
            available_minutes_per_day=data.get("available_minutes_per_day", 120),
            preferences=data.get("preferences", {}),
        )
        for p_data in data.get("pets", []):
            pet = Pet(name=p_data["name"], species=p_data["species"], age=p_data["age"])
            for t_data in p_data.get("tasks", []):
                task = Task(
                    title=t_data["title"],
                    task_type=t_data["task_type"],
                    date=date.fromisoformat(t_data["date"]),
                    time=time.fromisoformat(t_data["time"]),
                    duration_minutes=t_data["duration_minutes"],
                    priority=t_data["priority"],
                    pet_name=t_data["pet_name"],
                    is_recurring=t_data.get("is_recurring", False),
                    recurrence=t_data.get("recurrence", ""),
                    status=t_data.get("status", "pending"),
                )
                pet.add_task(task)
            owner.add_pet(pet)
        return owner


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

    def complete_task(self, task: Task) -> Optional[Task]:
        """Mark a task done and, if it is recurring, schedule the next occurrence automatically.

        Returns the newly created Task instance for 'daily'/'weekly' tasks, or None for one-offs.
        """
        task.mark_done()

        if not task.is_recurring or task.recurrence not in ("daily", "weekly"):
            return None

        gap = timedelta(days=1) if task.recurrence == "daily" else timedelta(weeks=1)

        next_task = copy(task)
        next_task.date   = task.date + gap
        next_task.status = "pending"
        self.tasks.append(next_task)
        return next_task

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by time using a lambda on 'HH:MM' strings — works correctly for 24-hour format."""
        return sorted(tasks, key=lambda t: t.time.strftime("%H:%M"))

    def sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks using the current strategy: 'priority_then_time', 'time_only', or 'priority_only'.

        Uses pre-computed sort keys so strftime() is called once per task, not once per comparison.
        """
        if self.sort_strategy == "priority_then_time":
            # Build key tuples once, sort against them — O(n) key build + O(n log n) sort
            return sorted(tasks, key=lambda t: (PRIORITY_ORDER.get(t.priority, 99), t.time))
        elif self.sort_strategy == "time_only":
            return self.sort_by_time(tasks)
        elif self.sort_strategy == "priority_only":
            return sorted(tasks, key=lambda t: PRIORITY_ORDER.get(t.priority, 99))
        return tasks

    def filter_by_status(self, status: str) -> List[Task]:
        """Return all tasks whose status matches the given value (e.g. 'pending' or 'done')."""
        return self.filter_tasks(status=status)

    def filter_by_pet(self, pet_name: str) -> List[Task]:
        """Return all tasks belonging to the named pet."""
        return self.filter_tasks(pet_name=pet_name)

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> List[Task]:
        """Return tasks matching all supplied filters in a single pass; omitted filters are ignored."""
        return [
            t for t in self.tasks
            if (pet_name  is None or t.pet_name  == pet_name)
            and (status   is None or t.status    == status)
            and (task_type is None or t.task_type == task_type)
        ]

    def expand_recurring(self, days: int = 7) -> List[Task]:
        """Generate copies of every recurring task for the next *days* days and add them to the scheduler."""
        today = date.today()
        new_tasks: List[Task] = []
        templates = [t for t in self.tasks if t.is_recurring and t.recurrence in ("daily", "weekly")]
        for template in templates:
            step = 1 if template.recurrence == "daily" else 7
            for offset in range(step, days + 1, step):
                instance = copy(template)
                instance.date = today + timedelta(days=offset)  # simpler than fromordinal/toordinal
                instance.status = "pending"
                new_tasks.append(instance)
        self.tasks.extend(new_tasks)
        return new_tasks

    def detect_conflicts(self, tasks: Optional[List[Task]] = None) -> List[Tuple[Task, Task]]:
        """Return all pairs of tasks whose time windows overlap on the same date.

        Groups tasks by date first so only same-date pairs are compared,
        avoiding O(n²) cross-date checks.
        """
        check = tasks if tasks is not None else self.tasks
        by_date = defaultdict(list)
        for t in check:
            by_date[t.date].append(t)

        conflicts = []
        for day_tasks in by_date.values():
            for i in range(len(day_tasks)):
                for j in range(i + 1, len(day_tasks)):
                    if day_tasks[i].conflicts_with(day_tasks[j]):
                        conflicts.append((day_tasks[i], day_tasks[j]))
        return conflicts

    def warn_conflicts(self, tasks: Optional[List[Task]] = None) -> List[str]:
        """Return a warning string for every overlapping task pair — never raises an exception.

        Each message names both tasks, their pets, the shared date, and the overlapping times
        so the owner knows exactly what needs to be rescheduled.
        """
        warnings = []
        for a, b in self.detect_conflicts(tasks):
            msg = (
                f"WARNING: '{a.title}' ({a.pet_name}, "
                f"{a.time.strftime('%H:%M')}–{a.end_time().strftime('%H:%M')}) "
                f"overlaps with '{b.title}' ({b.pet_name}, "
                f"{b.time.strftime('%H:%M')}–{b.end_time().strftime('%H:%M')}) "
                f"on {a.date}."
            )
            warnings.append(msg)
        return warnings

    def next_available_slot(self, target_date: date, duration_minutes: int, start_hour: int = 7, end_hour: int = 21) -> Optional[time]:
        """Return the earliest start time on target_date that fits a task of duration_minutes.

        Scans the day's existing tasks in chronological order and returns the first
        gap that is wide enough.  Returns None if no slot exists before end_hour.
        """
        day_tasks = sorted(self.get_tasks_for_date(target_date), key=lambda t: t.time)
        candidate = datetime.combine(target_date, time(start_hour, 0))
        deadline  = datetime.combine(target_date, time(end_hour,   0))

        for t in day_tasks:
            task_start = datetime.combine(target_date, t.time)
            task_end   = task_start + timedelta(minutes=t.duration_minutes)
            if candidate + timedelta(minutes=duration_minutes) <= task_start:
                return candidate.time()   # gap before this task is wide enough
            candidate = max(candidate, task_end)  # move past the blocking task

        # Check the trailing gap after all tasks
        if candidate + timedelta(minutes=duration_minutes) <= deadline:
            return candidate.time()
        return None

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
