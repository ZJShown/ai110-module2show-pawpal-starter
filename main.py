from pawpal_system import Task, Pet, Owner, Scheduler


def main():
    # Set up owner
    owner = Owner(name="Alex", wake_time="07:30", activity_level="medium")

    # Set up pets
    biscuit = Pet(name="Biscuit", breed="Golden Retriever")
    mochi = Pet(name="Mochi", breed="Shih Tzu")

    # Tasks for Biscuit
    biscuit.add_task(Task(name="Morning Walk",  task_type="walk",       duration=30, priority="high",   recurring="daily"))
    biscuit.add_task(Task(name="Breakfast",     task_type="feeding",    duration=10, priority="high",   recurring="daily"))
    biscuit.add_task(Task(name="Flea Medicine", task_type="meds",       duration=5,  priority="medium", recurring="weekly"))
    biscuit.add_task(Task(name="Fetch Session", task_type="enrichment", duration=20, priority="low",    recurring="daily"))

    # Tasks for Mochi
    mochi.add_task(Task(name="Breakfast",       task_type="feeding",    duration=10, priority="high",   recurring="daily"))
    mochi.add_task(Task(name="Brushing",        task_type="grooming",   duration=15, priority="medium", recurring="daily"))
    mochi.add_task(Task(name="Indoor Playtime", task_type="enrichment", duration=20, priority="low",    recurring="daily"))

    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    # Generate and display schedule for each pet
    print(f"=== Today's Schedule for {owner.get_name()} ===\n")

    for pet in owner.pets:
        scheduler = Scheduler(time_available=60)
        scheduler.generate(pet, owner)
        print(f"  {pet.get_name()} ({pet.get_breed()})")
        print(scheduler.display())
        print()


if __name__ == "__main__":
    main()
