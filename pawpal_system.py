"""Core domain classes and scheduling logic for PawPal+."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    """A single pet care activity with type, duration, priority, and recurrence."""
    name: str
    task_type: str        # "walk", "feeding", "meds", "enrichment", "grooming"
    duration: int         # minutes
    priority: str         # "high", "medium", "low"
    recurring: str        # "daily", "weekly", "once"
    completed: bool = False

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


class Scheduler:
    """Generates a time-slotted daily plan from a pet's tasks and owner preferences."""

    def __init__(self, time_available: int):
        """Initialise the scheduler with total minutes available for the day."""
        self.time_available: int = time_available  # total minutes available for the day
        self.scheduled_tasks: list[tuple[str, Task]] = []  # (time_slot, task)

    def generate(self, pet: Pet, owner: Owner) -> None:
        """Sort pending tasks by priority and greedily schedule within available time."""
        self.scheduled_tasks = []
        pending = [t for t in pet.get_tasks() if not t.completed]
        pending.sort(key=lambda t: PRIORITY_ORDER.get(t.priority, 99))

        current_time = datetime.strptime(owner.wake_time, "%H:%M")
        remaining = self.time_available

        for task in pending:
            if task.duration <= remaining:
                self.scheduled_tasks.append((current_time.strftime("%H:%M"), task))
                current_time += timedelta(minutes=task.duration)
                remaining -= task.duration

    def get_time_available(self) -> int:
        """Return the total minutes available for scheduling."""
        return self.time_available

    def display(self) -> str:
        """Return the scheduled plan as a formatted string."""
        if not self.scheduled_tasks:
            return "No tasks scheduled."
        lines = []
        for time_slot, task in self.scheduled_tasks:
            lines.append(
                f"  {time_slot} — {task.name} ({task.duration} min) [priority: {task.priority}]"
            )
        return "\n".join(lines)
