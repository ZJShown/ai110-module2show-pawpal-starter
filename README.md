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

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
=== Today's Schedule for Alex ===

  Biscuit (Golden Retriever)
  07:30 — Morning Walk (30 min) [priority: high]
  08:00 — Breakfast (10 min) [priority: high]
  08:10 — Flea Medicine (5 min) [priority: medium]

  Mochi (Shih Tzu)
  07:30 — Breakfast (10 min) [priority: high]
  07:40 — Brushing (15 min) [priority: medium]
  07:55 — Indoor Playtime (20 min) [priority: low]
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest
python -m pytest tests/test_pawpal.py -v

# Run with coverage:
python -m pytest --cov
```

### What the tests cover

| Type | Tests | Description |
|---|---|---|
| **Sorting** | 3 | Verifies `sort_by_time()` produces strict HH:MM chronological order; confirms `generate()` re-sorts by priority regardless of insertion order |
| **Recurrence** | 4 | Confirms `complete_task()` creates a next-occurrence copy with `due_date + 1 day` (daily) or `+ 7 days` (weekly); confirms `once` tasks produce no new copy; confirms completed tasks are excluded from the next schedule |
| **Conflict detection** | 5 | Checks that same-start and partial-overlap times are flagged; verifies back-to-back tasks produce no false positives; tests cross-pet conflict detection and confirms non-overlapping pets are clean |
| **Baseline** | 2 | `mark_complete()` sets `completed=True`; `add_task()` increments the pet's task count |

### Test run output

```
============================= test session starts ==============================
platform darwin -- Python 3.13.5, pytest-9.0.3, pluggy-1.5.0
rootdir: /ai110-module2show-pawpal-starter
collected 14 items

tests/test_pawpal.py::test_mark_complete_changes_status PASSED           [  7%]
tests/test_pawpal.py::test_add_task_increases_pet_task_count PASSED      [ 14%]
tests/test_pawpal.py::test_sort_by_time_orders_slots_chronologically PASSED [ 21%]
tests/test_pawpal.py::test_sort_by_time_on_manually_reversed_slots PASSED [ 28%]
tests/test_pawpal.py::test_generate_priority_sort_high_before_low PASSED [ 35%]
tests/test_pawpal.py::test_complete_daily_task_creates_next_occurrence PASSED [ 42%]
tests/test_pawpal.py::test_complete_weekly_task_creates_next_occurrence PASSED [ 50%]
tests/test_pawpal.py::test_complete_once_task_does_not_create_new_task PASSED [ 57%]
tests/test_pawpal.py::test_completed_daily_task_excluded_from_next_schedule PASSED [ 64%]
tests/test_pawpal.py::test_detect_conflicts_flags_exact_same_start PASSED [ 71%]
tests/test_pawpal.py::test_detect_conflicts_flags_partial_overlap PASSED [ 78%]
tests/test_pawpal.py::test_detect_conflicts_no_false_positives PASSED    [ 85%]
tests/test_pawpal.py::test_detect_cross_pet_conflicts_flags_overlapping_pets PASSED [ 92%]
tests/test_pawpal.py::test_detect_cross_pet_no_conflict_when_sequential PASSED [100%]

============================== 14 passed in 0.04s ==============================
```

### Confidence level: (4/5)

The core scheduling behaviours are fully covered and all 14 tests pass. The rating stops short of 5 stars because:

- The `weekly` recurrence logic (`task.task_type == day_of_week`) is a rough proxy and has no test for mismatched values
- The activity level multiplier and the 5-minute buffer are exercised indirectly through `generate()` but have no dedicated boundary tests

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| **Sort by priority** | `Scheduler.generate()` | Pending tasks are sorted by `(priority, duration)` before time slots are assigned. High-priority tasks always schedule first; within the same priority, shorter tasks win the tiebreak to maximise the number that fit. |
| **Sort by time** | `Scheduler.sort_by_time()` | Sorts `scheduled_tasks` in place by `"HH:MM"` string using `sorted()` with a lambda key. Zero-padded fixed-width strings compare correctly as plain strings — no `datetime` parsing needed. |
| **Filter scheduled tasks by status** | `Scheduler.filter_tasks(completed=)` | Returns a filtered copy of `scheduled_tasks`. `completed=False` shows only pending tasks; `completed=True` shows only finished ones; `completed=None` returns all. |
| **Filter tasks by pet or status** | `Owner.filter_tasks(pet_name=, completed=)` | Cross-pet filter on raw task objects. Both parameters are optional and combinable — e.g. `owner.filter_tasks(pet_name="Biscuit", completed=False)` returns only Biscuit's incomplete tasks. |
| **Same-pet conflict detection** | `Scheduler.detect_conflicts()` | Checks every pair of scheduled windows using the full interval overlap test (`A.start < B.end AND B.start < A.end`). Returns a list of `WARNING` strings; never raises. |
| **Cross-pet conflict detection** | `Scheduler.detect_cross_pet_conflicts(schedulers)` | Static method that merges all pets' scheduled slots with pet labels, then flags time-window overlaps between different pets — surfacing cases where the owner is double-booked across pets. |
| **Recurring task filtering** | `_should_include(task, day_of_week)` | `daily` tasks always included; `weekly` tasks only included when `task.task_type == day_of_week`; `once` tasks included until `mark_complete()` is called. Completed tasks are always excluded. |
| **Recurring task auto-creation** | `Pet.complete_task(task, reference_date=)` | When a `daily` or `weekly` task is marked complete, automatically creates a next-occurrence copy with `due_date = reference_date + timedelta(days=1)` or `timedelta(weeks=1)`. Returns the new `Task`; returns `None` for `once` tasks. |
| **Activity level scaling** | `Scheduler.generate()` | Multiplies `time_available` by `ACTIVITY_MULTIPLIERS` (`high=1.0`, `medium=0.75`, `low=0.5`) to get `effective_time`. A low-activity owner with 120 min available is treated as having 60 min. |
| **Skipped task tracking** | `Scheduler.generate()` / `Scheduler.display()` | Tasks that don't fit go to `self.skipped_tasks` instead of being silently dropped. `display()` appends a footer listing them; the Streamlit UI surfaces them in a `st.warning()` block. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
