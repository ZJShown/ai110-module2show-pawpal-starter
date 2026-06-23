from datetime import date, timedelta
import pytest
from pawpal_system import Task, Pet, Owner, Scheduler


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_task(name, task_type="walk", duration=10, priority="medium", recurring="daily"):
    return Task(name=name, task_type=task_type, duration=duration,
                priority=priority, recurring=recurring)

def make_owner(wake_time="08:00", activity_level="high"):
    return Owner(name="Alex", wake_time=wake_time, activity_level=activity_level)


# ── Existing tests (unchanged) ────────────────────────────────────────────────

def test_mark_complete_changes_status():
    task = Task(name="Morning Walk", task_type="walk", duration=30,
                priority="high", recurring="daily")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Biscuit", breed="Golden Retriever")
    assert len(pet.get_tasks()) == 0
    pet.add_task(Task(name="Breakfast", task_type="feeding", duration=10,
                      priority="high", recurring="daily"))
    assert len(pet.get_tasks()) == 1


# ── Sorting correctness ───────────────────────────────────────────────────────

def test_sort_by_time_orders_slots_chronologically():
    """sort_by_time() must produce strict HH:MM ascending order."""
    owner = make_owner()
    pet = Pet(name="Mochi", breed="Shih Tzu")
    # Add tasks in reverse priority so they get assigned late slots first
    pet.add_task(make_task("Enrichment", duration=20, priority="low"))
    pet.add_task(make_task("Meds",       duration=5,  priority="medium"))
    pet.add_task(make_task("Walk",       duration=15, priority="high"))

    scheduler = Scheduler(time_available=90)
    scheduler.generate(pet, owner)
    scheduler.sort_by_time()

    slots = [slot for slot, _ in scheduler.scheduled_tasks]
    assert slots == sorted(slots), f"Expected chronological order, got {slots}"


def test_sort_by_time_on_manually_reversed_slots():
    """sort_by_time() fixes manually out-of-order scheduled_tasks."""
    owner = make_owner()
    pet = Pet(name="Biscuit", breed="Golden Retriever")
    pet.add_task(make_task("Walk", duration=10, priority="high"))

    scheduler = Scheduler(time_available=60)
    scheduler.generate(pet, owner)

    # Manually inject a later slot before the earlier one to create disorder
    late_task  = make_task("Late Task",  duration=5)
    early_task = make_task("Early Task", duration=5)
    scheduler.scheduled_tasks = [("10:00", late_task), ("08:00", early_task)]

    scheduler.sort_by_time()

    slots = [s for s, _ in scheduler.scheduled_tasks]
    assert slots == ["08:00", "10:00"]


def test_generate_priority_sort_high_before_low():
    """High-priority tasks must receive earlier time slots than low-priority ones."""
    owner = make_owner()
    pet = Pet(name="Biscuit", breed="Golden Retriever")
    # Add low before high to confirm generate() re-sorts, not insertion order
    pet.add_task(make_task("Enrichment", priority="low",  duration=10))
    pet.add_task(make_task("Meds",       priority="high", duration=10))

    scheduler = Scheduler(time_available=60)
    scheduler.generate(pet, owner)

    names = [task.name for _, task in scheduler.scheduled_tasks]
    assert names.index("Meds") < names.index("Enrichment")


# ── Recurrence logic ──────────────────────────────────────────────────────────

def test_complete_daily_task_creates_next_occurrence():
    """Completing a daily task must add a new task with due_date = today + 1."""
    today = date(2026, 6, 23)
    pet = Pet(name="Mochi", breed="Shih Tzu")
    task = make_task("Breakfast", recurring="daily")
    pet.add_task(task)

    next_task = pet.complete_task(task, reference_date=today)

    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.completed is False
    assert next_task.name == "Breakfast"


def test_complete_weekly_task_creates_next_occurrence():
    """Completing a weekly task must add a new task with due_date = today + 7."""
    today = date(2026, 6, 23)
    pet = Pet(name="Biscuit", breed="Golden Retriever")
    task = make_task("Bath", recurring="weekly")
    pet.add_task(task)

    next_task = pet.complete_task(task, reference_date=today)

    assert next_task is not None
    assert next_task.due_date == today + timedelta(weeks=1)


def test_complete_once_task_does_not_create_new_task():
    """Completing a 'once' task must not add a new occurrence."""
    pet = Pet(name="Biscuit", breed="Golden Retriever")
    task = make_task("Vet Visit", recurring="once")
    pet.add_task(task)
    initial_count = len(pet.get_tasks())

    result = pet.complete_task(task)

    assert result is None
    assert len(pet.get_tasks()) == initial_count   # no new task added


def test_completed_daily_task_excluded_from_next_schedule():
    """After Pet.complete_task(), the original (completed) task must not appear
    in the next schedule; the new occurrence must appear instead."""
    today = date(2026, 6, 23)
    owner = make_owner()
    pet = Pet(name="Mochi", breed="Shih Tzu")
    task = make_task("Breakfast", recurring="daily")
    pet.add_task(task)

    pet.complete_task(task, reference_date=today)

    scheduler = Scheduler(time_available=60)
    scheduler.generate(pet, owner)

    scheduled_names = [t.name for _, t in scheduler.scheduled_tasks]
    # new occurrence should be scheduled; completed original should not appear
    assert "Breakfast" in scheduled_names
    completed_tasks = [t for _, t in scheduler.scheduled_tasks if t.completed]
    assert len(completed_tasks) == 0


# ── Conflict detection ────────────────────────────────────────────────────────

def test_detect_conflicts_flags_exact_same_start():
    """Two tasks at the same start time must be reported as a conflict."""
    owner = make_owner()
    pet = Pet(name="Biscuit", breed="Golden Retriever")
    pet.add_task(make_task("Walk", duration=30, priority="high"))

    scheduler = Scheduler(time_available=90)
    scheduler.generate(pet, owner)

    # Force a duplicate start time
    overlap = make_task("Emergency Vet", duration=15)
    scheduler.scheduled_tasks.append(("08:00", overlap))

    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) > 0
    assert any("Emergency Vet" in w for w in conflicts)


def test_detect_conflicts_flags_partial_overlap():
    """A task starting inside another task's window must be flagged."""
    scheduler = Scheduler(time_available=120)
    t1 = make_task("Walk",  duration=30)
    t2 = make_task("Meds",  duration=10)
    # Walk: 08:00–08:30; Meds starts at 08:15 → overlaps by 15 min
    scheduler.scheduled_tasks = [("08:00", t1), ("08:15", t2)]

    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 1
    assert "Walk" in conflicts[0]
    assert "Meds" in conflicts[0]


def test_detect_conflicts_no_false_positives():
    """Back-to-back tasks with no overlap must produce no conflicts."""
    scheduler = Scheduler(time_available=120)
    t1 = make_task("Walk",      duration=30)
    t2 = make_task("Breakfast", duration=10)
    # Walk: 08:00–08:30; Breakfast: 08:30 → adjacent, not overlapping
    scheduler.scheduled_tasks = [("08:00", t1), ("08:30", t2)]

    conflicts = scheduler.detect_conflicts()
    assert conflicts == []


def test_detect_cross_pet_conflicts_flags_overlapping_pets():
    """Two pets scheduled at the same time must appear in cross-pet conflicts."""
    owner = make_owner()

    biscuit = Pet(name="Biscuit", breed="Golden Retriever")
    biscuit.add_task(make_task("Walk", duration=30, priority="high"))

    mochi = Pet(name="Mochi", breed="Shih Tzu")
    mochi.add_task(make_task("Breakfast", duration=10, priority="high"))

    sched_b = Scheduler(time_available=90)
    sched_b.generate(biscuit, owner)

    sched_m = Scheduler(time_available=90)
    sched_m.generate(mochi, owner)

    # Both start at owner.wake_time="08:00" → cross-pet overlap
    conflicts = Scheduler.detect_cross_pet_conflicts(
        {"Biscuit": sched_b, "Mochi": sched_m}
    )
    assert len(conflicts) > 0
    assert all("cross-pet" in w for w in conflicts)


def test_detect_cross_pet_no_conflict_when_sequential():
    """Pets scheduled in non-overlapping windows must produce no cross-pet conflicts."""
    scheduler_a = Scheduler(time_available=60)
    scheduler_b = Scheduler(time_available=60)

    t1 = make_task("Walk",      duration=30)
    t2 = make_task("Breakfast", duration=10)
    scheduler_a.scheduled_tasks = [("08:00", t1)]   # 08:00–08:30
    scheduler_b.scheduled_tasks = [("09:00", t2)]   # 09:00–09:10 — no overlap

    conflicts = Scheduler.detect_cross_pet_conflicts(
        {"Biscuit": scheduler_a, "Mochi": scheduler_b}
    )
    assert conflicts == []
