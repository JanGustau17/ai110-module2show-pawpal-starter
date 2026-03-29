import streamlit as st
from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

DATA_FILE = "data.json"

# ── Session state initialisation ───────────────────────────────────────────────
# On first load, try to restore a previous session from data.json.
if "owner" not in st.session_state:
    loaded = Owner.load_from_json(DATA_FILE)
    st.session_state.owner = loaded if loaded else Owner(name="")

if "scheduler" not in st.session_state:
    sched = Scheduler()
    # Re-register all persisted pet tasks into the scheduler
    for pet in st.session_state.owner.pets:
        for task in pet.tasks:
            sched.add_task(task)
    st.session_state.scheduler = sched


def _save() -> None:
    """Persist current owner + pets + tasks to data.json."""
    st.session_state.owner.save_to_json(DATA_FILE)

owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

pet_options = [p.name for p in owner.pets]

PRIORITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}


def _show_conflict_cards(tasks: list) -> bool:
    """Show a structured conflict card for each overlapping pair.

    Each card names both tasks, their pets, and the exact overlapping windows
    so the owner knows at a glance what to reschedule.
    Returns True if any conflicts were shown.
    """
    conflicts = scheduler.detect_conflicts(tasks)
    if not conflicts:
        return False

    st.error(f"⚠️ {len(conflicts)} scheduling conflict(s) detected — review before confirming.")
    for a, b in conflicts:
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**{a.title}**")
                st.caption(
                    f"{PRIORITY_EMOJI.get(a.priority, '')} {a.priority.capitalize()} priority · {a.pet_name}\n\n"
                    f"🕐 {a.time.strftime('%I:%M %p')} – {a.end_time().strftime('%I:%M %p')}  ({a.duration_minutes} min)"
                )
            with col2:
                st.markdown(f"**{b.title}**")
                st.caption(
                    f"{PRIORITY_EMOJI.get(b.priority, '')} {b.priority.capitalize()} priority · {b.pet_name}\n\n"
                    f"🕐 {b.time.strftime('%I:%M %p')} – {b.end_time().strftime('%I:%M %p')}  ({b.duration_minutes} min)"
                )
            st.caption(f"📅 Both on {a.date}  ·  Tip: move the lower-priority task to after {a.end_time().strftime('%I:%M %p')}.")
    return True


def _render_schedule_table(tasks: list) -> None:
    """Render tasks as a clean dataframe, hiding internal fields."""
    if not tasks:
        st.info("No tasks to display.")
        return
    rows = []
    for t in tasks:
        rows.append({
            "Priority": f"{PRIORITY_EMOJI.get(t.priority, '')} {t.priority.capitalize()}",
            "Title": t.title,
            "Pet": t.pet_name,
            "Time": t.time.strftime("%I:%M %p"),
            "Duration": f"{t.duration_minutes} min",
            "Type": t.task_type.capitalize(),
            "Status": "✅ Done" if t.status == "done" else "⏳ Pending",
            "Recurring": "🔁 " + t.recurrence if t.is_recurring else "—",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)


# ── 1) Owner setup ─────────────────────────────────────────────────────────────
st.subheader("1) Owner Profile")
st.caption("Tell us who you are.")

owner_name_input = st.text_input("Your name", value=owner.name or "Jordan", key="owner_name_input")

if st.button("Save owner"):
    owner.name = owner_name_input.strip() or "Owner"
    _save()
    st.success(f"Welcome, {owner.name}!")

if owner.name:
    st.caption(f"Logged in as **{owner.name}** · {len(owner.pets)} pet(s) registered")

st.divider()

# ── 2) Add a Pet ───────────────────────────────────────────────────────────────
st.subheader("2) Add a Pet")
st.caption("Create a pet profile and register it under your account.")

pet_name_input = st.text_input("Pet name", value="Mochi", key="pet_name_input")
species_input  = st.selectbox("Species", ["dog", "cat", "other"], key="species_input")
age_input      = st.number_input("Age (years)", min_value=0, max_value=40, value=2, key="age_input")

if st.button("Save pet"):
    if not owner.name:
        st.error("Please save your owner profile first.")
    else:
        name = pet_name_input.strip() or "Unnamed Pet"
        existing = next((p for p in owner.pets if p.name == name), None)
        if existing:
            existing.update_profile(name, species_input, int(age_input))
            _save()
            st.success(f"Updated profile for {name}.")
        else:
            new_pet = Pet(name=name, species=species_input, age=int(age_input))
            owner.add_pet(new_pet)
            _save()
            st.success(f"{name} added to your account.")

if owner.pets:
    st.write("Your pets:")
    st.dataframe(
        [{"Name": p.name, "Species": p.species.capitalize(), "Age": f"{p.age} yr"} for p in owner.pets],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No pets registered yet.")

st.divider()

# ── 3) Schedule a Walk ─────────────────────────────────────────────────────────
st.subheader("3) Schedule a Walk")
st.caption("Pick a pet, date, time, and duration.")

if not pet_options:
    st.warning("Add a pet first before scheduling a walk.")
else:
    selected_pet_name = st.selectbox("Choose a pet", pet_options, key="walk_pet")
    walk_date     = st.date_input("Walk date", value=date.today(), key="walk_date")
    walk_time     = st.time_input("Walk time", key="walk_time")
    walk_duration = st.number_input("Duration (minutes)", min_value=5, max_value=180, value=30, key="walk_duration")
    walk_priority = st.selectbox("Priority", ["low", "medium", "high"], index=2, key="walk_priority")

    if st.button("Schedule walk"):
        pet = next(p for p in owner.pets if p.name == selected_pet_name)
        scheduler.schedule_walk(
            pet=pet,
            walk_date=walk_date,
            walk_time=walk_time,
            duration=int(walk_duration),
            priority=walk_priority,
        )
        _save()
        st.success(f"Walk scheduled for {pet.name} on {walk_date} at {walk_time.strftime('%I:%M %p')}.")
        _show_conflict_cards(scheduler.get_tasks_for_date(walk_date))

st.divider()

# ── 4) Schedule a Task ─────────────────────────────────────────────────────────
st.subheader("4) Schedule a Task")
st.caption("Add any care task — feeding, medication, grooming, enrichment, and more.")

if not pet_options:
    st.warning("Add a pet first before scheduling a task.")
else:
    task_pet_name  = st.selectbox("Pet", pet_options, key="task_pet")
    task_type      = st.selectbox(
        "Task type", ["feeding", "medication", "grooming", "enrichment", "other"],
        key="task_type",
    )
    task_title     = st.text_input("Task title", value="Morning feeding", key="task_title")
    task_date      = st.date_input("Date", value=date.today(), key="task_date")
    task_time      = st.time_input("Time", key="task_time")
    task_duration  = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=15, key="task_duration")
    task_priority  = st.selectbox("Priority", ["low", "medium", "high"], index=1, key="task_priority")
    task_recurring = st.checkbox("Recurring task", key="task_recurring")

    recurrence_type = ""
    if task_recurring:
        recurrence_type = st.selectbox("Repeat every", ["daily", "weekly"], key="task_recurrence")

    if st.button("Add task"):
        pet = next(p for p in owner.pets if p.name == task_pet_name)
        new_task = Task(
            title=task_title.strip() or task_type.capitalize(),
            task_type=task_type,
            date=task_date,
            time=task_time,
            duration_minutes=int(task_duration),
            priority=task_priority,
            pet_name=pet.name,
            is_recurring=task_recurring,
            recurrence=recurrence_type,
        )
        scheduler.add_task(new_task)
        pet.add_task(new_task)
        _save()
        st.success(f"'{new_task.title}' added for {pet.name} on {task_date} at {task_time.strftime('%I:%M %p')}.")
        _show_conflict_cards(scheduler.get_tasks_for_date(task_date))

st.divider()

# ── 5) Today's Schedule ────────────────────────────────────────────────────────
st.subheader("5) Today's Schedule")
st.caption("Sorted and filtered tasks for today.")

col_sort, col_filter_pet, col_filter_status = st.columns(3)

with col_sort:
    sort_choice = st.selectbox(
        "Sort by",
        ["priority_then_time", "time_only", "priority_only"],
        key="sort_strategy",
    )
    scheduler.sort_strategy = sort_choice

with col_filter_pet:
    filter_pet = st.selectbox("Filter by pet", ["All"] + pet_options, key="filter_pet")

with col_filter_status:
    filter_status = st.selectbox("Filter by status", ["All", "pending", "done"], key="filter_status")

today_tasks = owner.get_today_tasks(scheduler, date.today())

# Apply optional filters
if filter_pet != "All":
    today_tasks = [t for t in today_tasks if t.pet_name == filter_pet]
if filter_status != "All":
    today_tasks = [t for t in today_tasks if t.status == filter_status]

if today_tasks:
    has_conflicts = _show_conflict_cards(today_tasks)
    if not has_conflicts:
        st.success("No conflicts — schedule looks good.")
    _render_schedule_table(today_tasks)
else:
    st.info("No tasks scheduled for today.")

st.divider()

# ── 6) Generate Schedule ───────────────────────────────────────────────────────
st.subheader("6) Generate Schedule")
st.caption("Resolve any conflicts and show the final plan for today.")

if st.button("Generate schedule"):
    if not owner.pets:
        st.error("Add a pet and some tasks first.")
    else:
        base_tasks = owner.get_today_tasks(scheduler, date.today())
        if not base_tasks:
            st.info("No tasks for today to schedule.")
        else:
            had_conflicts = _show_conflict_cards(base_tasks)
            resolved = scheduler.resolve_conflicts(base_tasks)

            remaining = scheduler.detect_conflicts(resolved)
            if remaining:
                st.error("Some conflicts could not be resolved automatically.")
            else:
                total_min = sum(t.duration_minutes for t in resolved)
                pct = round(total_min / owner.available_minutes_per_day * 100)
                if had_conflicts:
                    st.success("Conflicts resolved — here's your updated plan.")
                else:
                    st.success(
                        f"Schedule ready — {len(resolved)} task(s), "
                        f"{total_min} min ({pct}% of your {owner.available_minutes_per_day} min/day)."
                    )

            st.markdown("**Final plan:**")
            _render_schedule_table(resolved)
