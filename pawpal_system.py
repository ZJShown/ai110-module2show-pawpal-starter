"""Core domain classes and scheduling logic for PawPal+."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
ACTIVITY_MULTIPLIERS = {"high": 1.0, "medium": 0.75, "low": 0.5}
BUFFER_MINUTES = 5


@dataclass
class Task:
    """A single pet care activity with type, duration, priority, and recurrence."""
    name: str
    task_type: str        # "walk", "feeding", "meds", "enrichment", "grooming"
    duration: int         # minutes
    priority: str         # "high", "medium", "low"
    recurring: str        # "daily", "weekly", "once"
    completed: bool = False
    due_date: date = field(default_factory=date.today)

    def update_priority(self, priority: str) -> None:
        """Set a new priority level for this task."""
        self.priority = priority

    def get_duration(self) -> int:
        """Return the task duration in minutes."""
        return self.duration

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True


@dataclass
class Pet:
    """A pet with breed details and a list of assigned care tasks."""

    name: str
    breed: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def get_name(self) -> str:
        """Return the pet's name."""
        return self.name

    def get_breed(self) -> str:
        """Return the pet's breed."""
        return self.breed

    def get_tasks(self) -> list[Task]:
        """Return all tasks assigned to this pet."""
        return self.tasks

    def complete_task(self, task: Task, reference_date: date = None) -> "Task | None":
        """Mark task complete and, if it recurs, auto-create the next occurrence.

        reference_date lets callers fix 'today' for testing without mocking.
        Returns the newly created Task for daily/weekly, or None for 'once'.
        """
        task.mark_complete()

        if task.recurring not in ("daily", "weekly"):
            return None

        ref = reference_date or date.today()
        delta = timedelta(days=1) if task.recurring == "daily" else timedelta(weeks=1)

        next_task = Task(
            name=task.name,
            task_type=task.task_type,
            duration=task.duration,
            priority=task.priority,
            recurring=task.recurring,
            due_date=ref + delta,
        )
        self.add_task(next_task)
        return next_task


class Owner:
    """A pet owner who manages one or more pets and provides scheduling preferences."""

    def __init__(self, name: str, wake_time: str = "08:00", activity_level: str = "medium"):
        """Initialise owner with name, wake time, and activity level."""
        self.name: str = name
        self.wake_time: str = wake_time        # "HH:MM" format
        self.activity_level: str = activity_level  # "high", "medium", "low"
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's pet list."""
        self.pets.append(pet)

    def delete_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner's pet list."""
        self.pets.remove(pet)

    def update_preference(self, key: str, value) -> None:
        """Update an owner preference attribute by name."""
        setattr(self, key, value)

    def get_name(self) -> str:
        """Return the owner's name."""
        return self.name

    def get_all_tasks(self) -> list[Task]:
        """Return a flat list of all tasks across every pet."""
        return [task for pet in self.pets for task in pet.get_tasks()]

    def filter_tasks(
        self, pet_name: str = None, completed: bool = None
    ) -> list[Task]:
        """Return tasks filtered by pet name and/or completion status.

        pet_name=None  → include all pets
        completed=True → only completed tasks
        completed=False → only incomplete tasks
        completed=None → all tasks regardless of status
        """
        results = []
        for pet in self.pets:
            if pet_name is not None and pet.get_name() != pet_name:
                continue
            for task in pet.get_tasks():
                if completed is not None and task.completed != completed:
                    continue
                results.append(task)
        return results


def _should_include(task: Task, day_of_week: str) -> bool:
    """Return True if a task should be considered for today's schedule."""
    if task.completed:
        return False
    if task.recurring == "daily":
        return True
    if task.recurring == "weekly":
        return task.task_type == day_of_week
    return True  # "once"


class Scheduler:
    """Generates a time-slotted daily plan from a pet's tasks and owner preferences."""

    def __init__(self, time_available: int):
        """Initialise the scheduler with total minutes available for the day."""
        self.time_available: int = time_available
        self.scheduled_tasks: list[tuple[str, Task]] = []  # (time_slot, task)
        self.skipped_tasks: list[Task] = []
        self._pet_name: str = ""   # set by generate(); used in conflict messages

    def generate(self, pet: Pet, owner: Owner, day_of_week: str = "") -> None:
        """Build a time-slotted schedule for one pet.

        Algorithm:
        1. Filter via _should_include(): drop completed tasks and weekly tasks
           whose task_type does not match day_of_week.
        2. Scale time_available by owner.activity_level (high=100%, medium=75%,
           low=50%) to get effective_time.
        3. Sort by (priority, duration): high-priority first; within the same
           priority, shorter tasks slot first to maximise the number that fit.
        4. Greedily assign HH:MM slots from owner.wake_time, inserting a
           5-minute buffer between consecutive tasks.
        5. Tasks that exceed remaining time go to self.skipped_tasks.

        Args:
            pet:         The pet whose tasks are being scheduled.
            owner:       Provides wake_time and activity_level preferences.
            day_of_week: Lowercase weekday name (e.g. "monday") used to include
                         weekly-recurring tasks. Pass "" to exclude them.
        """
        self.scheduled_tasks = []
        self.skipped_tasks = []
        self._pet_name = pet.get_name()

        effective_time = int(
            self.time_available * ACTIVITY_MULTIPLIERS.get(owner.activity_level, 1.0)
        )

        pending = [t for t in pet.get_tasks() if _should_include(t, day_of_week)]
        # Primary sort: priority; tiebreak: shorter duration first (fits more tasks)
        pending.sort(key=lambda t: (PRIORITY_ORDER.get(t.priority, 99), t.duration))

        current_time = datetime.strptime(owner.wake_time, "%H:%M")
        remaining = effective_time

        for task in pending:
            buffer = BUFFER_MINUTES if self.scheduled_tasks else 0
            slot_cost = task.duration + buffer
            if slot_cost <= remaining:
                current_time += timedelta(minutes=buffer)
                self.scheduled_tasks.append((current_time.strftime("%H:%M"), task))
                current_time += timedelta(minutes=task.duration)
                remaining -= slot_cost
            else:
                self.skipped_tasks.append(task)

    def get_time_available(self) -> int:
        """Return the total minutes available for scheduling."""
        return self.time_available

    def sort_by_time(self) -> None:
        """Sort scheduled_tasks in place by their HH:MM time slot string."""
        self.scheduled_tasks = sorted(
            self.scheduled_tasks,
            key=lambda slot_task: slot_task[0]  # "HH:MM" strings sort correctly as strings
        )

    def filter_tasks(self, completed: bool = None) -> list[tuple[str, Task]]:
        """Return a filtered copy of scheduled_tasks by task completion status.

        completed=True  → only completed tasks
        completed=False → only incomplete tasks
        completed=None  → all tasks (no filtering)
        """
        if completed is None:
            return list(self.scheduled_tasks)
        return [
            (slot, task)
            for slot, task in self.scheduled_tasks
            if task.completed == completed
        ]

    def detect_conflicts(self) -> list[str]:
        """Return warning strings for any overlapping time windows in this schedule.

        Uses full interval overlap check (A.start < B.end AND B.start < A.end)
        so it catches both partial overlaps and exact-same-start conflicts.
        Never raises — always returns a (possibly empty) list of strings.
        """
        warnings = []
        pet_label = f" [{self._pet_name}]" if self._pet_name else ""
        for i, (s1, t1) in enumerate(self.scheduled_tasks):
            t1_start = datetime.strptime(s1, "%H:%M")
            t1_end = t1_start + timedelta(minutes=t1.duration)
            for s2, t2 in self.scheduled_tasks[i + 1:]:
                t2_start = datetime.strptime(s2, "%H:%M")
                t2_end = t2_start + timedelta(minutes=t2.duration)
                if t1_start < t2_end and t2_start < t1_end:
                    warnings.append(
                        f'WARNING{pet_label}: "{t1.name}" '
                        f'({s1}–{t1_end.strftime("%H:%M")}) overlaps '
                        f'"{t2.name}" ({s2}–{t2_end.strftime("%H:%M")})'
                    )
        return warnings

    @staticmethod
    def detect_cross_pet_conflicts(
        schedulers: dict[str, "Scheduler"]
    ) -> list[str]:
        """Return warning strings for time-window overlaps across different pets.

        Args:
            schedulers: {pet_name: Scheduler} — each scheduler must have already
                        had generate() called on it.

        Never raises — always returns a (possibly empty) list of strings.
        """
        # Flatten all scheduled slots with their pet label
        all_slots: list[tuple[str, Task, str]] = []
        for pet_name, sched in schedulers.items():
            for slot, task in sched.scheduled_tasks:
                all_slots.append((slot, task, pet_name))

        warnings = []
        for i, (s1, t1, p1) in enumerate(all_slots):
            t1_start = datetime.strptime(s1, "%H:%M")
            t1_end = t1_start + timedelta(minutes=t1.duration)
            for s2, t2, p2 in all_slots[i + 1:]:
                if p1 == p2:
                    continue   # same-pet overlaps handled by detect_conflicts()
                t2_start = datetime.strptime(s2, "%H:%M")
                t2_end = t2_start + timedelta(minutes=t2.duration)
                if t1_start < t2_end and t2_start < t1_end:
                    warnings.append(
                        f'WARNING [cross-pet]: "{t1.name}" ({p1}, '
                        f'{s1}–{t1_end.strftime("%H:%M")}) overlaps '
                        f'"{t2.name}" ({p2}, {s2}–{t2_end.strftime("%H:%M")})'
                    )
        return warnings

    def display(self) -> str:
        """Return the scheduled plan as a formatted string with a summary footer."""
        if not self.scheduled_tasks and not self.skipped_tasks:
            return "No tasks scheduled."

        lines = []
        total_minutes = 0
        for time_slot, task in self.scheduled_tasks:
            lines.append(
                f"  {time_slot} — {task.name} ({task.duration} min)"
                f" [{task.priority} · {task.recurring}]"
            )
            total_minutes += task.duration

        lines.append("")
        lines.append(
            f"  Scheduled: {len(self.scheduled_tasks)} task(s) · {total_minutes} min used"
        )

        if self.skipped_tasks:
            skipped_names = ", ".join(
                f"{t.name} ({t.priority} · {t.duration} min)" for t in self.skipped_tasks
            )
            lines.append(f"  Skipped:   {len(self.skipped_tasks)} task(s) — {skipped_names}")

        return "\n".join(lines)
