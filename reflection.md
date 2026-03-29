# PawPal+ Project Reflection

## 1. System Design

The current system design focuses on three core user actions that match the MVP goals for PawPal+.

1. Add a pet
- The user can create a pet profile by entering the pet's name, species, and age.
- The app stores this profile in session state so it can be used by later actions.
- This action establishes the primary entity in the system, and all care tasks are associated with that pet.

2. Schedule a walk
- The user can schedule a walk task by selecting a date, time, duration, and priority.
- Before creating the task, the app checks whether a pet profile exists.
- If no pet has been added, the app blocks scheduling and shows a clear message.
- If a pet exists, the app creates a structured walk task and saves it in the task list.

3. See today's tasks
- The app filters the stored task list to only show tasks scheduled for the current date.
- This gives the user a focused daily view instead of a full history.
- If no tasks exist for today, the app communicates that state clearly.

Design note: this first implementation uses Streamlit session state as the storage layer and keeps logic close to the UI to deliver a working vertical slice quickly. A next iteration can extract these behaviors into dedicated classes (such as Pet, Task, and Scheduler) for stronger separation of concerns and easier testing.

**1b. Design changes**

After asking Copilot to review the initial skeleton, two issues were flagged and changed:

1. `Pet` had no `tasks` list and no `add_task()` method. The original design assumed the Scheduler would be the only place tasks lived, but that made per-pet queries require a full scan of the scheduler. Adding `tasks: list` to `Pet` allowed `get_tasks_for_date()` to run directly on the pet without touching the scheduler.

2. `Task` had `pet_id` (an integer reference) instead of `pet_name` (a string). Since this app has no database, a foreign key integer added complexity with no benefit. Replacing it with `pet_name` kept lookups simple and human-readable throughout the UI.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints: time (when a task is scheduled and how long it runs), priority (high / medium / low), and the owner's available minutes per day. When sorting, priority is applied first so high-urgency tasks like medication always appear before low-urgency ones like grooming, then time breaks ties within the same priority band. Available minutes was treated as a soft cap — the scheduler surfaces the total against the budget but does not hard-block tasks that exceed it, since pet care tasks often cannot simply be skipped.

**b. Tradeoffs**

The conflict resolver uses a single-pass greedy strategy: it sorts tasks by priority, then shifts each lower-priority task to start exactly when the higher-priority one ends. This is fast and predictable but can create a cascade — pushing task B may cause B to now overlap C, which is not re-checked. The tradeoff is reasonable here because most pet care schedules are sparse (a handful of tasks per day), so multi-level cascades are rare in practice, and the simplicity makes the behavior easy to explain to the owner.

---

## 3. AI Collaboration

**a. Most effective Copilot features**

Inline completions were the most useful — especially when implementing repetitive but logic-heavy methods like `filter_tasks()` and `expand_recurring()`. Copilot would complete the pattern after the first condition, which saved time on boilerplate. The chat panel was helpful for quickly explaining what a `defaultdict` grouping strategy would look like before writing `detect_conflicts()`.

**b. One suggestion I rejected**

Copilot initially suggested `detect_conflicts()` as a flat O(n²) double loop over all tasks. I rejected this because it would compare tasks across different dates unnecessarily. I replaced it with a `defaultdict(list)` grouping by date first, so only same-day pairs are ever compared. The AI gave a working solution — but not an efficient or logically clean one.

**c. How separate chat sessions helped**

Keeping design, implementation, and testing in separate sessions prevented context bleed. When writing tests I didn't want the AI to assume implementation details from earlier chats — a fresh session forced me to describe the interface explicitly, which also helped me catch two method name mismatches (`get_tasks` vs `get_tasks_for_date`).

**d. Being the lead architect**

AI tools are fast at filling in structure but they don't know your constraints. Every time Copilot suggested something that "worked," I still had to ask: does this fit the design? Is it consistent with the other classes? The main skill I built was using AI to accelerate execution while keeping all architectural decisions — naming, relationships, tradeoffs — in my own hands.

---

## 4. Testing and Verification

**a. What you tested**

23 tests covering: all three sort strategies, daily and weekly recurrence chaining, conflict detection (overlap, identical start, different dates), conflict detection blind spots (midnight-spanning tasks, double `expand_recurring`), task lifecycle (`mark_done`, `reschedule`, `to_dict`), and owner/pet/scheduler integration.

**b. Confidence**

4/5. Core daily scheduling is solid. Known gaps: weekly recurrence is tested but `expand_recurring` called twice compounds silently, and tasks spanning midnight are not cross-day detected. Both are documented as known limitations.

---

## 5. Reflection

**a. What went well**

The conflict detection and resolution pipeline. `detect_conflicts` → `warn_conflicts` → `resolve_conflicts` forms a clean three-step chain that the UI can call independently, which made the Streamlit integration straightforward.

**b. What I would improve**

Make `expand_recurring()` idempotent by checking for existing instances before appending, and add a cross-midnight check in `detect_conflicts` for tasks whose `end_time()` crosses into the next date.

**c. Key takeaway**

A powerful AI can write correct code faster than you can — but it cannot decide what correct means for your system. That judgment is the architect's job, and it cannot be delegated.
