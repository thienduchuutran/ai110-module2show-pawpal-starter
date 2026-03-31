import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet


def test_mark_complete_changes_status():
    task = Task(name="Morning Walk", duration=30, priority=3)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Buddy", species="dog", age=3)
    initial_count = len(pet.tasks)
    pet.add_task(Task(name="Feeding", duration=10, priority=3))
    assert len(pet.tasks) == initial_count + 1
