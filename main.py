from datetime import date, time

from pawpal_system import Owner, Pet, Scheduler, Task

# ── ANSI helpers ───────────────────────────────────────────────────────────────
RED, YELLOW, GREEN, CYAN, BOLD, DIM, RESET = (
    "\033[91m", "\033[93m", "\033[92m", "\033[96m", "\033[1m", "\033[2m", "\033[0m",
)
PRIORITY_COLOR = {"high": RED, "medium": YELLOW, "low": GREEN}
W = 60

def section(title):
    print(f"\n{BOLD}{CYAN}{'─' * W}")
    print(f"  {title}")
    print(f"{'─' * W}{RESET}")

def row(task):
    color = PRIORITY_COLOR.get(task.priority, "")
    end   = f"{task.time.strftime('%H:%M')}+{task.duration_minutes}m"
    print(
        f"  {end:<12}  "
        f"{color}[{task.priority.upper():6}]{RESET}  "
        f"{task.title:<30}  {DIM}{task.pet_name}{RESET}"
    )

# ── Setup ──────────────────────────────────────────────────────────────────────
scheduler = Scheduler()
owner     = Owner(name="Alex")
buddy     = Pet(name="Buddy",    species="Dog", age=3)
whiskers  = Pet(name="Whiskers", species="Cat", age=5)
owner.add_pet(buddy)
owner.add_pet(whiskers)

today = date.today()

# ── Tasks — three deliberate conflicts planted ─────────────────────────────────
#
#  Conflict 1 (exact same time, same pet):
#    Walk Buddy      07:00 – 07:30
#    Vet call        07:00 – 07:20   ← identical start, same pet
#
#  Conflict 2 (partial overlap, different pets):
#    Feed Whiskers   08:00 – 08:10
#    Grooming Buddy  08:05 – 08:25   ← starts 5 min into Whiskers' task
#
#  No conflict:
#    Training        17:00 – 17:20   ← well clear of everything above

tasks = [
    Task("Walk Buddy",       "walk",     today, time(7,  0),  30, "high",   "Buddy"),
    Task("Vet call",         "other",    today, time(7,  0),  20, "medium", "Buddy"),    # conflict 1
    Task("Feed Whiskers",    "feeding",  today, time(8,  0),  10, "high",   "Whiskers"),
    Task("Grooming Buddy",   "grooming", today, time(8,  5),  20, "medium", "Buddy"),    # conflict 2
    Task("Training session", "enrichment", today, time(17, 0), 20, "medium", "Buddy"),   # no conflict
]

for t in tasks:
    scheduler.add_task(t)

# ── Show all tasks ─────────────────────────────────────────────────────────────
section("ALL TASKS (as added)")
for t in scheduler.sort_by_time(scheduler.tasks):
    row(t)

# ── detect_conflicts(): raw pairs ─────────────────────────────────────────────
section("detect_conflicts()  →  raw overlapping pairs")
pairs = scheduler.detect_conflicts()
if pairs:
    print(f"\n  {len(pairs)} conflict(s) found:\n")
    for a, b in pairs:
        print(f"  • '{a.title}'  ↔  '{b.title}'")
else:
    print(f"  {GREEN}No conflicts.{RESET}")

# ── warn_conflicts(): human-readable messages, no crash ───────────────────────
section("warn_conflicts()  →  warning messages (lightweight, never crashes)")
warnings = scheduler.warn_conflicts()
if warnings:
    for msg in warnings:
        print(f"\n  {RED}⚠  {msg}{RESET}")
else:
    print(f"\n  {GREEN}✓  Schedule is clear.{RESET}")

# ── Proof: no conflict → no warning ───────────────────────────────────────────
section("Proof: single task list → no warning printed")
clean_tasks = [tasks[-1]]   # only the 17:00 training session
clean_warnings = scheduler.warn_conflicts(clean_tasks)
if clean_warnings:
    for msg in clean_warnings:
        print(f"  {RED}⚠  {msg}{RESET}")
else:
    print(f"  {GREEN}✓  No conflicts in this subset — warn_conflicts() returned []{RESET}")

print(f"\n{'─' * W}\n")
