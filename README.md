# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

The scheduling layer (`pawpal_system.py`) goes beyond a simple task list:

- **Sorting** — tasks are ordered by priority (high → medium → low), with time as a tiebreaker. A dedicated `sort_by_time()` method uses a `"%H:%M"` lambda key for pure chronological views.
- **Filtering** — `filter_by_pet()`, `filter_by_status()`, and `filter_tasks()` (combined) let the owner slice the task list in a single pass without multiple scans.
- **Conflict detection** — `detect_conflicts()` groups tasks by date before comparing pairs, so cross-date comparisons are skipped entirely. `warn_conflicts()` returns human-readable warning strings rather than raising exceptions.
- **Conflict resolution** — `resolve_conflicts()` uses a greedy priority-first strategy: lower-priority tasks are shifted to start immediately after the blocking task ends.
- **Recurring tasks** — marking a `daily` or `weekly` task complete via `complete_task()` automatically schedules the next occurrence using `timedelta`. `expand_recurring()` pre-populates a full week of instances in one call.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
