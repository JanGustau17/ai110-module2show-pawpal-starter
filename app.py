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

# Convenience aliases so the rest of the file stays readable
owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

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
        # If a pet with this name already exists, update it; otherwise add a new one
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

pet_options = [p.name for p in owner.pets]

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
        task = scheduler.schedule_walk(
            pet=pet,
            walk_date=walk_date,
            walk_time=walk_time,
            duration=int(walk_duration),
            priority=walk_priority,
        )
        st.success(f"Walk scheduled for {pet.name} on {walk_date} at {walk_time.strftime('%I:%M %p')}.")
        # Immediately check if the new task conflicts with anything already scheduled
        new_warnings = scheduler.warn_conflicts(scheduler.get_tasks_for_date(walk_date))
        for msg in new_warnings:
            st.warning(msg)

st.divider()

# ── 4) Schedule a Task ─────────────────────────────────────────────────────────
st.subheader("4) Schedule a Task")
st.caption("Add any care task — feeding, medication, grooming, enrichment, and more.")

pet_options_task = [p.name for p in owner.pets]

if not pet_options_task:
    st.warning("Add a pet first before scheduling a task.")
else:
    task_pet_name = st.selectbox("Pet", pet_options_task, key="task_pet")
    task_type     = st.selectbox(
        "Task type", ["feeding", "medication", "grooming", "enrichment", "other"],
        key="task_type",
    )
    task_title    = st.text_input("Task title", value="Morning feeding", key="task_title")
    task_date     = st.date_input("Date", value=date.today(), key="task_date")
    task_time     = st.time_input("Time", key="task_time")
    task_duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=15, key="task_duration")
    task_priority = st.selectbox("Priority", ["low", "medium", "high"], index=1, key="task_priority")
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
        # Immediately check if the new task conflicts with anything already scheduled
        new_warnings = scheduler.warn_conflicts(scheduler.get_tasks_for_date(task_date))
        for msg in new_warnings:
            st.warning(msg)

st.divider()

# ── 5) Today's Schedule ────────────────────────────────────────────────────────
st.subheader("5) Today's Schedule")
st.caption("All tasks for today, sorted by priority then time.")

today_tasks = owner.get_today_tasks(scheduler, date.today())

if today_tasks:
    warnings = scheduler.warn_conflicts(today_tasks)
    if warnings:
        for msg in warnings:
            st.warning(msg)
    else:
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
        raw = owner.get_today_tasks(scheduler, date.today())
        if not raw:
            st.info("No tasks for today to schedule.")
        else:
            before_warnings = scheduler.warn_conflicts(raw)
            if before_warnings:
                st.markdown("**Conflicts found — resolving automatically:**")
                for msg in before_warnings:
                    st.warning(msg)

            resolved = scheduler.resolve_conflicts(raw)

            after_warnings = scheduler.warn_conflicts(resolved)
            if after_warnings:
                st.error("Some conflicts could not be resolved automatically.")
                for msg in after_warnings:
                    st.warning(msg)
            else:
                total_min = sum(t.duration_minutes for t in resolved)
                st.success(
                    f"Schedule ready — {len(resolved)} task(s), "
                    f"{total_min} min total out of {owner.available_minutes_per_day} min available."
                )
            st.table([t.to_dict() for t in resolved])
