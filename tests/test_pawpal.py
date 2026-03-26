import pytest
from datetime import date, time

from pawpal_system import Owner, Pet, Scheduler, Task


# ── Shared fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def sample_task():
    return Task(
        title="Walk Buddy",
        task_type="walk",
        date=date(2026, 3, 26),
        time=time(8, 0),
        duration_minutes=30,
        priority="high",
        pet_name="Buddy",
    )

@pytest.fixture
def sample_pet():
    return Pet(name="Buddy", species="Dog", age=3)

@pytest.fixture
def sample_scheduler():
    return Scheduler()


# ── Task tests ─────────────────────────────────────────────────────────────────

def test_task_completion_changes_status(sample_task):
    """Calling mark_done() should change status from 'pending' to 'done'."""
    assert sample_task.status == "pending"
    sample_task.mark_done()
    assert sample_task.status == "done"


def test_task_reschedule_updates_date_and_time(sample_task):
    new_date = date(2026, 4, 1)
    new_time = time(10, 30)
    sample_task.reschedule(new_date, new_time)
    assert sample_task.date == new_date
    assert sample_task.time == new_time


def test_task_to_dict_contains_expected_keys(sample_task):
    d = sample_task.to_dict()
    for key in ("title", "task_type", "date", "time", "duration_minutes", "priority", "pet_name", "status"):
        assert key in d


def test_task_conflicts_with_overlapping_task(sample_task):
    overlapping = Task(
        title="Feed Buddy",
        task_type="feeding",
        date=date(2026, 3, 26),
        time=time(8, 15),          # starts 15 min into the 30-min walk
        duration_minutes=10,
        priority="medium",
        pet_name="Buddy",
    )
    assert sample_task.conflicts_with(overlapping) is True


def test_task_no_conflict_with_non_overlapping_task(sample_task):
    later = Task(
        title="Evening walk",
        task_type="walk",
        date=date(2026, 3, 26),
        time=time(18, 0),          # hours after the morning walk ends
        duration_minutes=30,
        priority="medium",
        pet_name="Buddy",
    )
    assert sample_task.conflicts_with(later) is False


def test_task_no_conflict_on_different_dates(sample_task):
    tomorrow = Task(
        title="Walk Buddy",
        task_type="walk",
        date=date(2026, 3, 27),    # different date, same time
        time=time(8, 0),
        duration_minutes=30,
        priority="high",
        pet_name="Buddy",
    )
    assert sample_task.conflicts_with(tomorrow) is False


# ── Pet tests ──────────────────────────────────────────────────────────────────

def test_task_addition_increases_pet_task_count(sample_pet, sample_task):
    """Adding a task to a Pet should increase its task list by one."""
    before = len(sample_pet.tasks)
    sample_pet.add_task(sample_task)
    assert len(sample_pet.tasks) == before + 1


def test_pet_update_profile(sample_pet):
    sample_pet.update_profile(name="Max", species="Cat", age=5)
    assert sample_pet.name == "Max"
    assert sample_pet.species == "Cat"
    assert sample_pet.age == 5


def test_pet_get_tasks_for_date_filters_correctly(sample_pet):
    today = date(2026, 3, 26)
    tomorrow = date(2026, 3, 27)

    task_today = Task("Feed", "feeding", today, time(8, 0), 10, "high", "Buddy")
    task_tomorrow = Task("Walk", "walk", tomorrow, time(9, 0), 30, "high", "Buddy")

    sample_pet.add_task(task_today)
    sample_pet.add_task(task_tomorrow)

    assert sample_pet.get_tasks_for_date(today) == [task_today]


# ── Owner tests ────────────────────────────────────────────────────────────────

def test_owner_add_pet_increases_pet_count():
    owner = Owner(name="Alex")
    pet = Pet(name="Buddy", species="Dog", age=3)
    owner.add_pet(pet)
    assert len(owner.pets) == 1


def test_owner_set_preferences_merges_values():
    owner = Owner(name="Alex")
    owner.set_preferences({"walk_time": "morning", "priority": "health"})
    assert owner.preferences["walk_time"] == "morning"


def test_owner_get_today_tasks_only_returns_owned_pets(sample_scheduler):
    owner = Owner(name="Alex")
    my_pet = Pet(name="Buddy", species="Dog", age=3)
    other_pet = Pet(name="Stranger", species="Cat", age=2)
    owner.add_pet(my_pet)

    target = date(2026, 3, 26)
    my_task = Task("Walk Buddy", "walk", target, time(8, 0), 30, "high", "Buddy")
    other_task = Task("Feed Stranger", "feeding", target, time(9, 0), 10, "medium", "Stranger")

    sample_scheduler.add_task(my_task)
    sample_scheduler.add_task(other_task)

    result = owner.get_today_tasks(sample_scheduler, target)
    assert my_task in result
    assert other_task not in result


# ── Scheduler tests ────────────────────────────────────────────────────────────

def test_scheduler_add_task_stores_task(sample_scheduler, sample_task):
    sample_scheduler.add_task(sample_task)
    assert sample_task in sample_scheduler.tasks


def test_scheduler_schedule_walk_creates_and_registers_task(sample_scheduler, sample_pet):
    walk_date = date(2026, 3, 26)
    task = sample_scheduler.schedule_walk(sample_pet, walk_date, time(7, 0), duration=30)
    assert task in sample_scheduler.tasks
    assert task in sample_pet.tasks
    assert task.task_type == "walk"


def test_scheduler_get_tasks_for_date(sample_scheduler):
    target = date(2026, 3, 26)
    other = date(2026, 3, 27)

    t1 = Task("A", "walk", target, time(8, 0), 30, "high", "Buddy")
    t2 = Task("B", "feeding", other, time(9, 0), 10, "low", "Buddy")
    sample_scheduler.add_task(t1)
    sample_scheduler.add_task(t2)

    result = sample_scheduler.get_tasks_for_date(target)
    assert t1 in result
    assert t2 not in result


def test_scheduler_sort_priority_then_time(sample_scheduler):
    target = date(2026, 3, 26)
    low   = Task("Low",  "walk",    target, time(7, 0), 10, "low",    "Buddy")
    high  = Task("High", "feeding", target, time(9, 0), 10, "high",   "Buddy")
    med   = Task("Med",  "grooming",target, time(8, 0), 10, "medium", "Buddy")

    sorted_tasks = sample_scheduler.sort_tasks([low, high, med])
    assert [t.priority for t in sorted_tasks] == ["high", "medium", "low"]


def test_scheduler_detect_conflicts(sample_scheduler):
    target = date(2026, 3, 26)
    t1 = Task("A", "walk",    target, time(8, 0),  30, "high",   "Buddy")
    t2 = Task("B", "feeding", target, time(8, 15), 10, "medium", "Buddy")  # overlaps t1
    t3 = Task("C", "grooming",target, time(18, 0), 15, "low",    "Buddy")  # no overlap

    conflicts = sample_scheduler.detect_conflicts([t1, t2, t3])
    assert len(conflicts) == 1
    assert (t1, t2) in conflicts


# ── Sorting correctness ────────────────────────────────────────────────────────

def test_sort_time_only_returns_chronological_order(sample_scheduler):
    """'time_only' strategy must order tasks by clock time, earliest first."""
    sample_scheduler.sort_strategy = "time_only"
    target = date(2026, 3, 26)
    t1 = Task("Morning walk",   "walk",    target, time(9, 0),  30, "low",    "Buddy")
    t2 = Task("Early feeding",  "feeding", target, time(7, 30), 10, "medium", "Buddy")
    t3 = Task("Midday grooming","grooming",target, time(12, 0), 20, "high",   "Buddy")

    result = sample_scheduler.sort_tasks([t1, t2, t3])
    assert [t.time for t in result] == [time(7, 30), time(9, 0), time(12, 0)]


# ── Recurrence logic ───────────────────────────────────────────────────────────

def test_complete_daily_task_creates_next_day_occurrence(sample_scheduler):
    """Completing a daily recurring task must add a new pending task one day later."""
    task = Task(
        title="Feed Buddy",
        task_type="feeding",
        date=date(2026, 3, 26),
        time=time(8, 0),
        duration_minutes=10,
        priority="high",
        pet_name="Buddy",
        is_recurring=True,
        recurrence="daily",
    )
    sample_scheduler.add_task(task)

    next_task = sample_scheduler.complete_task(task)

    assert task.status == "done"
    assert next_task is not None
    assert next_task.date == date(2026, 3, 27)   # exactly one day later
    assert next_task.status == "pending"
    assert next_task in sample_scheduler.tasks


# ── Conflict detection ─────────────────────────────────────────────────────────

def test_scheduler_flags_exact_same_start_time(sample_scheduler):
    """Two tasks with identical start time on the same date must be flagged as a conflict."""
    target = date(2026, 3, 26)
    t1 = Task("Walk Buddy",  "walk",    target, time(8, 0), 30, "high",   "Buddy")
    t2 = Task("Feed Buddy",  "feeding", target, time(8, 0), 10, "medium", "Buddy")

    conflicts = sample_scheduler.detect_conflicts([t1, t2])
    assert len(conflicts) == 1
    assert (t1, t2) in conflicts


# ── Gap 1: weekly recurrence offset ───────────────────────────────────────────

def test_complete_weekly_task_creates_occurrence_seven_days_later(sample_scheduler):
    """Completing a weekly recurring task must schedule the next one exactly 7 days out."""
    task = Task(
        title="Grooming",
        task_type="grooming",
        date=date(2026, 3, 26),
        time=time(10, 0),
        duration_minutes=20,
        priority="medium",
        pet_name="Buddy",
        is_recurring=True,
        recurrence="weekly",
    )
    sample_scheduler.add_task(task)

    next_task = sample_scheduler.complete_task(task)

    assert next_task is not None
    assert next_task.date == date(2026, 4, 2)   # +7 days
    assert next_task.status == "pending"
    assert next_task in sample_scheduler.tasks


# ── Gap 2: expand_recurring called twice doubles the list ─────────────────────

def test_expand_recurring_called_twice_doubles_task_list(sample_scheduler):
    """Calling expand_recurring() twice appends duplicates — documents the known non-idempotent behaviour."""
    task = Task(
        title="Daily walk",
        task_type="walk",
        date=date(2026, 3, 26),
        time=time(7, 0),
        duration_minutes=30,
        priority="high",
        pet_name="Buddy",
        is_recurring=True,
        recurrence="daily",
    )
    sample_scheduler.add_task(task)

    first  = sample_scheduler.expand_recurring(days=3)
    second = sample_scheduler.expand_recurring(days=3)

    # First call: 1 template × 3 days = 3 new tasks
    assert len(first) == 3
    # Second call: 4 templates (original + 3 copies) × 3 days = 12 new tasks
    # Documents the compounding non-idempotent behaviour
    assert len(second) == 12
    assert len(sample_scheduler.tasks) == 1 + 3 + 12   # original + first + second


# ── Gap 3: midnight-spanning task is not cross-day detected ───────────────────

def test_midnight_spanning_task_not_detected_against_next_day(sample_scheduler):
    """A task starting at 23:45 for 30 min bleeds into the next day but detect_conflicts
    groups by task.date only, so the overlap with a next-day task is a known blind spot."""
    day1 = date(2026, 3, 26)
    day2 = date(2026, 3, 27)

    late_task = Task("Late meds", "medication", day1, time(23, 45), 30, "high",   "Buddy")
    early_task = Task("Morning walk", "walk",   day2, time(0, 5),   20, "medium", "Buddy")

    # These physically overlap (23:45–00:15 vs 00:05–00:25) but live on different dates
    conflicts = sample_scheduler.detect_conflicts([late_task, early_task])

    # Documents current behaviour: blind spot returns no conflicts
    assert len(conflicts) == 0
