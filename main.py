from datetime import date, time

from pawpal_system import Owner, Pet, Scheduler, Task

# --- Setup ---
scheduler = Scheduler()

owner = Owner(name="Alex", available_minutes_per_day=180)

buddy = Pet(name="Buddy", species="Dog", age=3)
whiskers = Pet(name="Whiskers", species="Cat", age=5)

owner.add_pet(buddy)
owner.add_pet(whiskers)

# --- Add tasks ---
today = date.today()

scheduler.schedule_walk(buddy, today, time(7, 0), duration=30, priority="high")

feeding = Task(
    title="Feed Whiskers",
    task_type="feeding",
    date=today,
    time=time(8, 0),
    duration_minutes=10,
    priority="high",
    pet_name="Whiskers",
)
scheduler.add_task(feeding)
whiskers.add_task(feeding)

medication = Task(
    title="Buddy's flea medication",
    task_type="medication",
    date=today,
    time=time(9, 30),
    duration_minutes=5,
    priority="medium",
    pet_name="Buddy",
)
scheduler.add_task(medication)
buddy.add_task(medication)

grooming = Task(
    title="Brush Whiskers",
    task_type="grooming",
    date=today,
    time=time(18, 0),
    duration_minutes=15,
    priority="low",
    pet_name="Whiskers",
)
scheduler.add_task(grooming)
whiskers.add_task(grooming)

enrichment = Task(
    title="Buddy's training session",
    task_type="enrichment",
    date=today,
    time=time(17, 0),
    duration_minutes=20,
    priority="medium",
    pet_name="Buddy",
)
scheduler.add_task(enrichment)
buddy.add_task(enrichment)

# --- Check for conflicts ---
conflicts = scheduler.detect_conflicts(scheduler.get_today_tasks())

# --- Print Today's Schedule ---
tasks = owner.get_today_tasks(scheduler, today)

# ANSI color helpers
RED, YELLOW, GREEN, CYAN, BOLD, RESET = (
    "\033[91m", "\033[93m", "\033[92m", "\033[96m", "\033[1m", "\033[0m"
)

PRIORITY_COLOR = {"high": RED, "medium": YELLOW, "low": GREEN}

def time_of_day(t):
    if t.hour < 12:
        return "Morning"
    elif t.hour < 17:
        return "Afternoon"
    return "Evening"

# Group tasks by time of day (preserving sorted order)
groups = {}
for task in tasks:
    bucket = time_of_day(task.time)
    groups.setdefault(bucket, []).append(task)

WIDTH = 50
print(f"\n{BOLD}{'=' * WIDTH}{RESET}")
print(f"{BOLD}  PawPal+  •  {today.strftime('%A, %B %d %Y')}{RESET}")
print(f"  Owner: {owner.name}  |  Pets: {', '.join(p.name for p in owner.pets)}")
print(f"{'=' * WIDTH}{RESET}")

for bucket in ["Morning", "Afternoon", "Evening"]:
    if bucket not in groups:
        continue
    print(f"\n  {CYAN}{BOLD}{bucket}{RESET}")
    print(f"  {'-' * (WIDTH - 2)}")
    for task in groups[bucket]:
        color = PRIORITY_COLOR.get(task.priority, "")
        time_str = task.time.strftime("%I:%M %p")
        priority_tag = f"{color}[{task.priority.upper():6}]{RESET}"
        print(f"  {time_str}  {priority_tag}  {task.title:<28}  {task.pet_name} · {task.duration_minutes} min")

# Capacity bar
total = sum(t.duration_minutes for t in tasks)
available = owner.available_minutes_per_day
bar_width = 30
filled = round(bar_width * min(total / available, 1))
bar = f"{GREEN}{'█' * filled}{RESET}{'░' * (bar_width - filled)}"
pct = round(total / available * 100)

print(f"\n{'=' * WIDTH}")
print(f"  Time used:  {bar}  {total}/{available} min ({pct}%)")

if conflicts:
    print(f"\n  {RED}⚠  {len(conflicts)} conflict(s) detected:{RESET}")
    for a, b in conflicts:
        print(f"     • '{a.title}' overlaps with '{b.title}'")
else:
    print(f"  {GREEN}✓  No scheduling conflicts{RESET}")

print(f"{'=' * WIDTH}\n")
