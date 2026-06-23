from pawpal_system import Task, Pet


def test_mark_complete_changes_status():
    task = Task(name="Morning Walk", task_type="walk", duration=30, priority="high", recurring="daily")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Biscuit", breed="Golden Retriever")
    assert len(pet.get_tasks()) == 0
    pet.add_task(Task(name="Breakfast", task_type="feeding", duration=10, priority="high", recurring="daily"))
    assert len(pet.get_tasks()) == 1
