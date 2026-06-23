from dataclasses import dataclass, field


@dataclass
class Task:
    priority: str
    duration: int

    def update_priority(self, priority: str) -> None:
        pass

    def get_duration(self) -> int:
        pass


@dataclass
class Pet:
    name: str
    type: str
    daily_plan: "DailyPlan" = field(default=None)

    def get_name(self) -> str:
        pass

    def get_type(self) -> str:
        pass

    def get_daily_plan(self) -> "DailyPlan":
        pass

    def generate(self) -> "DailyPlan":
        pass


class DailyPlan:
    def __init__(self, time_available: int):
        self.tasks: list[Task] = []
        self.time_available: int = time_available

    def add_task(self, task: Task) -> None:
        pass

    def delete_task(self, task: Task) -> None:
        pass

    def get_time_available(self) -> int:
        pass


class Owner:
    def __init__(self, name: str, preferences: dict = None):
        self.name: str = name
        self.pet: Pet = None
        self.preferences: dict = preferences or {}

    def add_pet(self, pet: Pet) -> None:
        pass

    def delete_pet(self) -> None:
        pass

    def update_preference(self, key: str, value) -> None:
        pass

    def get_name(self) -> str:
        pass
