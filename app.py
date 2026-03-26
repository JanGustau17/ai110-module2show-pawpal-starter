import streamlit as st
from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ── Session state initialisation ───────────────────────────────────────────────
# Streamlit reruns this file top-to-bottom on every interaction.
# Storing objects in st.session_state keeps them alive across reruns.
# The "key not in st.session_state" guard means we only create each object ONCE.

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="")

if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()

owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

# Computed once per rerun; reused in sections 3, 4, and wherever pet names are needed
pet_options = [p.name for p in owner.pets]


def _show_warnings(warnings: list, header: str = "") -> bool:
    """Display each warning with st.warning(); return True if any were shown."""
    if not warnings:
        return False
    if header:
        st.markdown(header)
    for msg in warnings:
        st.warning(msg)
    return True


# ── 1) Owner setup ─────────────────────────────────────────────────────────────
st.subheader("1) Owner Profile")
st.caption("Tell us who you are.")

owner_name_input = st.text_input("Your name", value=owner.name or "Jordan", key="owner_name_input")

if st.button("Save owner"):
    owner.name = owner_name_input.strip() or "Owner"
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
            st.success(f"Updated profile for {name}.")
        else:
            new_pet = Pet(name=name, species=species_input, age=int(age_input))
            owner.add_pet(new_pet)
            st.success(f"{name} added to your account.")

if owner.pets:
    st.write("Your pets:")
    st.table([{"name": p.name, "species": p.species, "age": p.age} for p in owner.pets])
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
        st.success(f"Walk scheduled for {pet.name} on {walk_date} at {walk_time.strftime('%I:%M %p')}.")
        _show_warnings(scheduler.warn_conflicts(scheduler.get_tasks_for_date(walk_date)))

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
        )
        scheduler.add_task(new_task)
        pet.add_task(new_task)
        st.success(f"'{new_task.title}' added for {pet.name} on {task_date} at {task_time.strftime('%I:%M %p')}.")
        _show_warnings(scheduler.warn_conflicts(scheduler.get_tasks_for_date(task_date)))

st.divider()

# ── 5) Today's Schedule ────────────────────────────────────────────────────────
st.subheader("5) Today's Schedule")
st.caption("All tasks for today, sorted by priority then time.")

today_tasks = owner.get_today_tasks(scheduler, date.today())

if today_tasks:
    if not _show_warnings(scheduler.warn_conflicts(today_tasks)):
        st.success("No conflicts — schedule looks good.")
    st.table([t.to_dict() for t in today_tasks])
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
        # Reuse today_tasks already computed above rather than calling get_today_tasks again
        if not today_tasks:
            st.info("No tasks for today to schedule.")
        else:
            _show_warnings(scheduler.warn_conflicts(today_tasks), "**Conflicts found — resolving automatically:**")
            resolved = scheduler.resolve_conflicts(today_tasks)
            if _show_warnings(scheduler.warn_conflicts(resolved)):
                st.error("Some conflicts could not be resolved automatically.")
            else:
                total_min = sum(t.duration_minutes for t in resolved)
                st.success(
                    f"Schedule ready — {len(resolved)} task(s), "
                    f"{total_min} min total out of {owner.available_minutes_per_day} min available."
                )
            st.table([t.to_dict() for t in resolved])
