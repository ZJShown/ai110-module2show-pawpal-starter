"""Demo: scheduling, conflict detection (same-pet and cross-pet)."""

from datetime import date
from pawpal_system import Task, Pet, Owner, Scheduler


def print_warnings(warnings: list[str], label: str) -> None:
    """Print a labelled block of conflict warnings, or a clean-bill if none."""
    print(f"\n  -- {label} --")
    if warnings:
        for w in warnings:
            print(f"  {w}")
    else:
        print("  No conflicts detected.")


def main():
    """Schedule Biscuit and Mochi, then demonstrate same-pet and cross-pet conflict detection."""
    today = date.today()

    owner = Owner(name="Alex", wake_time="07:30", activity_level="high")

    biscuit = Pet(name="Biscuit", breed="Golden Retriever")
    mochi = Pet(name="Mochi", breed="Shih Tzu")

    biscuit.add_task(Task(
        name="Morning Walk", task_type="walk",
        duration=30, priority="high", recurring="daily",
    ))
    biscuit.add_task(Task(
        name="Breakfast", task_type="feeding",
        duration=10, priority="high", recurring="daily",
    ))
    biscuit.add_task(Task(
        name="Fetch Session", task_type="enrichment",
        duration=20, priority="low", recurring="daily",
    ))

    mochi.add_task(Task(
        name="Breakfast", task_type="feeding",
        duration=10, priority="high", recurring="daily",
    ))
    mochi.add_task(Task(
        name="Brushing", task_type="grooming",
        duration=15, priority="medium", recurring="daily",
    ))
    mochi.add_task(Task(
        name="Indoor Playtime", task_type="enrichment",
        duration=20, priority="low", recurring="daily",
    ))

    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    # ── Generate one scheduler per pet ───────────────────────────────────────
    sched_biscuit = Scheduler(time_available=90)
    sched_biscuit.generate(biscuit, owner)
    sched_biscuit.sort_by_time()

    sched_mochi = Scheduler(time_available=90)
    sched_mochi.generate(mochi, owner)
    sched_mochi.sort_by_time()

    print("=" * 58)
    print(f"  Schedules for {owner.get_name()}  ({today})")
    print("=" * 58)
    print(f"\n  Biscuit ({biscuit.get_breed()})")
    print(sched_biscuit.display())
    print(f"\n  Mochi ({mochi.get_breed()})")
    print(sched_mochi.display())

    # ── Same-pet conflict: no conflicts yet (sequential scheduler) ────────────
    print_warnings(sched_biscuit.detect_conflicts(), "Same-pet conflicts (Biscuit, clean)")

    # ── Force a same-pet conflict by manually injecting an overlapping slot ───
    # "Emergency Vet" starts at 07:30, same as Morning Walk → clear overlap
    emergency = Task(
        name="Emergency Vet", task_type="meds",
        duration=20, priority="high", recurring="once",
    )
    sched_biscuit.scheduled_tasks.append(("07:30", emergency))

    print_warnings(
        sched_biscuit.detect_conflicts(),
        "Same-pet conflicts (Biscuit, after injecting 07:30 overlap)",
    )

    # ── Cross-pet conflict: both pets start at 07:30 → owner can't do both ───
    cross = Scheduler.detect_cross_pet_conflicts({
        biscuit.get_name(): sched_biscuit,
        mochi.get_name():   sched_mochi,
    })
    print_warnings(cross, "Cross-pet conflicts (Biscuit vs Mochi)")


if __name__ == "__main__":
    main()
