import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

with st.expander("About this app", expanded=False):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.
"""
    )

st.divider()

# ── Owner setup ───────────────────────────────────────────────────────────────
st.subheader("Owner")

with st.form("owner_form"):
    owner_name = st.text_input("Owner name", value="Jordan")
    col_wt, col_al = st.columns(2)
    with col_wt:
        wake_time = st.text_input("Wake time (HH:MM)", value="08:00")
    with col_al:
        activity_level = st.selectbox(
            "Activity level", ["high", "medium", "low"], index=1
        )
    owner_submitted = st.form_submit_button("Save owner")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", wake_time="08:00", activity_level="medium")

if owner_submitted:
    st.session_state.owner.update_preference("name", owner_name)
    st.session_state.owner.update_preference("wake_time", wake_time)
    st.session_state.owner.update_preference("activity_level", activity_level)
    st.success(
        f"Owner saved: **{owner_name}** · wake {wake_time} · activity {activity_level}"
    )

owner = st.session_state.owner
st.caption(
    f"Current: **{owner.get_name()}** · wake {owner.wake_time} · activity {owner.activity_level}"
)

st.divider()

# ── Add a pet ─────────────────────────────────────────────────────────────────
st.subheader("Add a Pet")

with st.form("add_pet_form", clear_on_submit=True):
    pet_name = st.text_input("Pet name", value="Mochi")
    breed = st.selectbox("Breed / species", ["dog", "cat", "rabbit", "bird", "other"])
    pet_submitted = st.form_submit_button("Add pet")

if pet_submitted:
    new_pet = Pet(name=pet_name, breed=breed)
    st.session_state.owner.add_pet(new_pet)
    st.success(f"Added **{new_pet.get_name()}** ({new_pet.get_breed()}).")

pets = st.session_state.owner.pets
if pets:
    st.markdown("**Pets in this session:**")
    for pet in pets:
        st.write(f"- {pet.get_name()} ({pet.get_breed()})")
else:
    st.info("No pets added yet. Use the form above.")

st.divider()

# ── Add a task ────────────────────────────────────────────────────────────────
st.subheader("Add a Task")

if not pets:
    st.warning("Add a pet before adding tasks.")
else:
    selected_pet_name = st.selectbox(
        "Select pet", [p.get_name() for p in pets], key="task_pet"
    )
    selected_pet = next(p for p in pets if p.get_name() == selected_pet_name)

    with st.form("add_task_form", clear_on_submit=True):
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            task_type = st.selectbox(
                "Type", ["walk", "feeding", "meds", "enrichment", "grooming"]
            )
        with col3:
            duration = st.number_input(
                "Duration (min)", min_value=1, max_value=240, value=20
            )
        with col4:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        with col5:
            recurring = st.selectbox("Recurs", ["once", "daily", "weekly"])
        task_submitted = st.form_submit_button("Add task")

    if task_submitted:
        task = Task(
            name=task_title,
            task_type=task_type,
            duration=int(duration),
            priority=priority,
            recurring=recurring,
        )
        selected_pet.add_task(task)
        st.success(f"Added **{task.name}** to {selected_pet.get_name()}.")

    # ── Task list with filter and mark-complete ───────────────────────────────
    all_tasks = selected_pet.get_tasks()
    if all_tasks:
        status_filter = st.radio(
            "Show tasks", ["All", "Incomplete", "Complete"], horizontal=True
        )
        if status_filter == "Incomplete":
            shown = [t for t in all_tasks if not t.completed]
        elif status_filter == "Complete":
            shown = [t for t in all_tasks if t.completed]
        else:
            shown = all_tasks

        st.write(f"Tasks for **{selected_pet.get_name()}** ({len(shown)} shown):")
        for i, t in enumerate(shown):
            col_info, col_btn = st.columns([4, 1])
            with col_info:
                status_icon = "✓" if t.completed else "○"
                st.write(
                    f"{status_icon} **{t.name}** — {t.task_type}, "
                    f"{t.duration} min, {t.priority} priority, {t.recurring}"
                )
            with col_btn:
                if not t.completed:
                    if st.button("Done", key=f"done_{selected_pet_name}_{i}"):
                        t.mark_complete()
                        st.rerun()
    else:
        st.info(f"No tasks yet for {selected_pet.get_name()}.")

st.divider()

# ── Build schedule ────────────────────────────────────────────────────────────
st.subheader("Build Schedule")

if not pets:
    st.warning("Add a pet before generating a schedule.")
else:
    sched_pet_name = st.selectbox(
        "Select pet for schedule", [p.get_name() for p in pets], key="sched_pet"
    )
    sched_pet = next(p for p in pets if p.get_name() == sched_pet_name)

    col_ta, col_dow = st.columns(2)
    with col_ta:
        time_available = st.number_input(
            "Time available today (minutes)", min_value=10, max_value=480, value=120
        )
    with col_dow:
        day_of_week = st.selectbox(
            "Day of week (for weekly tasks)",
            ["", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
        )

    if st.button("Generate schedule"):
        scheduler = Scheduler(time_available=int(time_available))
        scheduler.generate(
            pet=sched_pet,
            owner=st.session_state.owner,
            day_of_week=day_of_week,
        )

        conflicts = scheduler.detect_conflicts()
        if conflicts:
            st.error("Conflicts detected:\n" + "\n".join(f"- {c}" for c in conflicts))

        if scheduler.skipped_tasks:
            skipped_names = ", ".join(
                f"{t.name} ({t.priority})" for t in scheduler.skipped_tasks
            )
            st.warning(f"Skipped (didn't fit): {skipped_names}")

        st.success("Schedule generated!")
        st.text(scheduler.display())
